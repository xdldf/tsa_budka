"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Camera, RotateCcw } from "lucide-react";
import { api } from "@/services/api";
import { HomeButton } from "@/components/home-button";
import { useBoothStore } from "@/store/booth";

export default function PreviewPage() {
  const router = useRouter();
  const { style, photoFormat, photos, imageIds, discardLastPhoto, setImageIds, startJob, setStatus } = useBoothStore();
  const [submitting, setSubmitting] = useState(false);
  const [previewUrl, setPreviewUrl] = useState("");
  const lock = useRef(false);
  const total = photoFormat === "double_strip" ? 6 : 1;
  const photo = photos.at(-1);
  useEffect(() => { if (!style || !photoFormat || !photo) router.replace(style ? "/camera" : "/"); }, [photo, photoFormat, router, style]);
  useEffect(() => { if (!photo) return; const url = URL.createObjectURL(photo); setPreviewUrl(url); return () => URL.revokeObjectURL(url); }, [photo]);
  if (!style || !photoFormat || !photo || !previewUrl) return null;
  const approve = async () => {
    if (lock.current) return;
    if (photos.length < total) { router.push("/camera"); return; }
    lock.current = true; setSubmitting(true); setStatus("uploading", "Загружаем фотографии…");
    try {
      const ids = imageIds.length === photos.length ? imageIds : (await Promise.all(photos.map(api.capture))).map((item) => item.image_id);
      setImageIds(ids);
      const job = await api.generate(ids, style.id, photoFormat);
      startJob(job.job_id); router.push("/processing");
    } catch { lock.current = false; setSubmitting(false); setStatus("failed", "Не удалось начать обработку. Попробуйте ещё раз."); }
  };
  return <main className="booth-shell diamond-shell"><HomeButton /><section className="kiosk-screen flex flex-col">
    <header className="text-center"><p className="event-kicker">Кадр {photos.length} из {total}</p><h1>{photos.length < total ? "Отлично! Готовы к следующему?" : "Все кадры готовы"}</h1></header>
    <div className="kiosk-content flex min-h-0 flex-1 flex-col items-center justify-center gap-4"><div className="glass media-frame overflow-hidden rounded-[32px]"><img className="h-full w-full object-contain" src={previewUrl} alt="Предпросмотр" /></div>
      <div className="kiosk-actions w-full"><button className="action" disabled={submitting} onClick={() => { discardLastPhoto(); router.push("/camera"); }}><RotateCcw />Переснять</button><button className="action action-primary" disabled={submitting} onClick={() => void approve()}>{photos.length < total ? <><Camera />Следующий кадр</> : <><Check />{submitting ? "Подготавливаем…" : "Создать фото"}</>}</button></div>
    </div></section></main>;
}
