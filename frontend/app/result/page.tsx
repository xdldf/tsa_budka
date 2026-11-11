"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/services/api";
import { HomeButton } from "@/components/home-button";
import { Result } from "@/components/result";
import { useBoothStore } from "@/store/booth";

export default function ResultPage() {
  const router = useRouter();
  const { style, photoFormat, imageIds, jobId, resultUrl, startJob, setStatus, setShareUrl } = useBoothStore();
  const [isPrinting, setIsPrinting] = useState(false);
  const [printMessage, setPrintMessage] = useState("");
  const [isSharing, setIsSharing] = useState(false);
  const [shareMessage, setShareMessage] = useState("");
  const regenerateLock = useRef(false);
  const printLock = useRef(false);
  const shareLock = useRef(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      if (pollTimer.current) clearTimeout(pollTimer.current);
    };
  }, []);

  useEffect(() => {
    if (!style || !photoFormat || imageIds.length === 0 || !resultUrl) router.replace("/");
  }, [imageIds.length, photoFormat, resultUrl, router, style]);

  if (!style || !photoFormat || imageIds.length === 0 || !resultUrl) return null;

  const regenerate = async () => {
    if (regenerateLock.current || printLock.current || shareLock.current) return;
    regenerateLock.current = true;
    setIsRegenerating(true);
    setPrintMessage("");
    setShareMessage("");
    try {
      setStatus("generating", "Запускаем ещё один вариант...");
      const job = await api.generate(imageIds, style.id, photoFormat);
      startJob(job.job_id);
      router.push("/processing");
    } catch {
      regenerateLock.current = false;
      setIsRegenerating(false);
      setShareMessage("Не удалось создать новый вариант. Попробуйте ещё раз.");
      setStatus("failed", "Не удалось запустить новый вариант.");
    }
  };

  const shareAndShowQr = async () => {
    if (shareLock.current || printLock.current || regenerateLock.current) return;
    shareLock.current = true;
    setPrintMessage("");
    setIsSharing(true);
    setShareMessage("Готовим QR-код...");
    try {
      const { url } = await api.share(jobId ?? "");
      setShareUrl(url);
      router.push("/qr");
    } catch {
      setShareMessage("Не удалось подготовить QR-код. Попробуйте ещё раз.");
      setIsSharing(false);
      shareLock.current = false;
    }
  };

  const print = async () => {
    if (printLock.current || shareLock.current || regenerateLock.current) return;
    if (!jobId) {
      setPrintMessage("Не найдено готовое фото. Создайте новый вариант.");
      return;
    }
    printLock.current = true;
    setIsPrinting(true);
    setShareMessage("");
    setPrintMessage("Отправляем фото на принтер…");
    const finish = () => {
      printLock.current = false;
      if (mounted.current) setIsPrinting(false);
    };
    const started = Date.now();
    const showStatus = (job: Awaited<ReturnType<typeof api.print>>) => {
      if (!mounted.current) return;
      setPrintMessage(job.message || (job.state === "completed" ? "Фото отправлено на принтер." : "Ожидаем принтер…"));
      if (job.state === "queued" || job.state === "processing") {
        if (Date.now() - started > 180000) {
          setPrintMessage("Статус печати пока неизвестен. Проверьте принтер перед повторной отправкой.");
          finish();
          return;
        }
        pollTimer.current = setTimeout(async () => {
          try { showStatus(await api.status(job.job_id)); }
          catch {
            if (mounted.current) setPrintMessage("Не удалось проверить печать. Проверьте принтер перед повторной отправкой.");
            finish();
          }
        }, 1000);
      } else finish();
    };
    try { showStatus(await api.print(jobId)); }
    catch (error) {
      if (mounted.current) setPrintMessage(error instanceof Error ? error.message : "Не удалось отправить фото.");
      finish();
    }
  };

  return <main className="booth-shell"><HomeButton /><Result imageUrl={resultUrl} isRegenerating={isRegenerating} isPrinting={isPrinting} printMessage={printMessage} isSharing={isSharing} shareMessage={shareMessage} onPrint={() => void print()} onRegenerate={() => void regenerate()} onShareQr={() => void shareAndShowQr()} /></main>;
}
