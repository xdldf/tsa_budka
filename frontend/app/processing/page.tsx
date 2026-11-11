"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/services/api";
import { HomeButton } from "@/components/home-button";
import { Processing } from "@/components/processing";
import { useBoothStore } from "@/store/booth";

const RESTART_AFTER_SECONDS = 600;

export default function ProcessingPage() {
  const router = useRouter();
  const { style, photoFormat, imageIds, jobId, jobVersion, statusMessage, startedAt, updateJob, startJob, setStatus } = useBoothStore();
  const [now, setNow] = useState(Date.now());
  const elapsed = startedAt ? Math.floor((now - startedAt) / 1000) : 0;
  const timedOut = elapsed >= RESTART_AFTER_SECONDS;
  const restartLock = useRef(false);

  const poll = useCallback(async () => {
    if (!jobId) return;
    const polledJobId = jobId;
    const polledVersion = jobVersion;
    try {
      const job = await api.status(polledJobId);
      if (job.state === "completed" && job.result_url) {
        if (updateJob(polledJobId, polledVersion, { status: "completed", statusMessage: job.message, resultUrl: api.imageUrl(job.result_url) })) router.replace("/result");
      } else if (job.state === "failed" || job.state === "cancelled") {
        updateJob(polledJobId, polledVersion, { status: "failed", statusMessage: job.message });
      } else {
        updateJob(polledJobId, polledVersion, { status: "generating", statusMessage: job.message });
      }
    } catch {
      updateJob(polledJobId, polledVersion, { status: "failed", statusMessage: "Не удалось получить статус обработки." });
    }
  }, [jobId, jobVersion, router, updateJob]);

  useEffect(() => {
    if (!style || !photoFormat || imageIds.length === 0 || !jobId) { router.replace("/"); return; }
    void poll();
    const pollTimer = window.setInterval(() => void poll(), 1000);
    const clockTimer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => { window.clearInterval(pollTimer); window.clearInterval(clockTimer); };
  }, [imageIds.length, jobId, photoFormat, poll, router, style]);

  const restart = async () => {
    if (restartLock.current) return;
    restartLock.current = true;
    if (!style || !photoFormat || imageIds.length === 0 || !jobId) return;
    const previousJobId = jobId;
    // Cancellation is deliberately best-effort: a new job must not wait on it.
    void api.cancel(previousJobId).catch(() => undefined);
    try {
      setStatus("generating", "Запускаем новую обработку...");
      const job = await api.generate(imageIds, style.id, photoFormat);
      startJob(job.job_id);
      setNow(Date.now());
    } catch {
      setStatus("failed", "Не удалось перезапустить обработку.");
    }
  };

  return <main className="booth-shell"><HomeButton /><Processing message={statusMessage} elapsed={elapsed} timedOut={timedOut} onCancel={async () => { if (jobId) void api.cancel(jobId).catch(() => undefined); router.push("/preview"); }} onRestart={() => void restart()} /></main>;
}
