"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Camera, RotateCcw } from "lucide-react";
import { api } from "@/services/api";

type CameraDevice = { id: string; label: string; isVideo: boolean };

type CanvasMediaDevices = MediaDevices & {
  getUserMediaDevices?: () => Promise<unknown[] | { video: unknown[] }> | Promise<unknown[]>;
};

type RawDevice = { id?: string; label?: string; name?: string; kind?: string };

// Ability to pass `deviceId` in constraints is emulated on the camera API used
// by the kiosk runtime, so make the constraint type accept it defensively.
type VideoConstraint = Record<string, unknown> & { deviceId?: { ideal: string } };

export function CameraCapture({ onCapture, onBack }: { onCapture: (photo: Blob) => void; onBack: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [cameraError, setCameraError] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [shutterSeconds, setShutterSeconds] = useState(5);
  const [deviceId, setDeviceId] = useState<string>("");
  const deviceLockedRef = useRef(false);
  const capturingRef = useRef(false);

  useEffect(() => {
    api
      .config()
      .then((config) => setShutterSeconds(config.timer.countdown_seconds))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const enumerate = async () => {
      try {
        let mapped: RawDevice[] = [];
        // Try standard enumerateDevices first (needs permission for labels)
        if (navigator.mediaDevices?.enumerateDevices) {
          const list = await navigator.mediaDevices.enumerateDevices();
          mapped = list.filter((d) => d.kind === "videoinput").map((d) => ({
            id: d.deviceId,
            label: d.label,
            kind: "videoinput",
          }));
        }
        // Fallback to canvas-runtime-specific getUserMediaDevices
        if (mapped.length === 0) {
          const list = (navigator.mediaDevices as CanvasMediaDevices)?.getUserMediaDevices?.();
          if (list && typeof list.then === "function") {
            const res = await list;
            if (cancelled) return;
            const arr = Array.isArray(res) ? res : (Array.isArray((res as { video?: unknown[] })?.video) ? (res as { video: unknown[] }).video : []);
            mapped = arr
              .filter((d): d is RawDevice => !!d && typeof d === "object")
              .map((d) => ({ id: d.id ?? "", label: d.label ?? d.name ?? d.id ?? "Камера", kind: "videoinput" }));
          }
        }
        if (cancelled) return;
        const parsed: CameraDevice[] = mapped
          .filter((d): d is RawDevice => !!d && typeof d === "object")
          .map((d, i) => ({ id: d.id ?? `index-${i}`, label: d.label || d.name || d.id || `Камера ${i + 1}`, isVideo: d.kind === "videoinput" }));
        // Pick the first available camera once and lock it forever.
        if (parsed.length > 0 && !deviceLockedRef.current) {
          deviceLockedRef.current = true;
          setDeviceId(parsed[0].id);
        }
      } catch {
        // Device enumeration is optional; the camera effect will still start.
      }
    };
    void enumerate();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const startCamera = async () => {
      try {
        if (!navigator.mediaDevices?.getUserMedia) throw new Error("Camera API unavailable");
        let stream: MediaStream;
        const videoConstraint: VideoConstraint = { facingMode: { ideal: "user" }, width: { ideal: 1280 }, height: { ideal: 960 } };
        if (deviceId) videoConstraint.deviceId = { ideal: deviceId };
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraint, audio: false });
        } catch {
          stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch {
        if (!cancelled) setCameraError(true);
      }
    };

    void startCamera();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, [deviceId]);

  const capture = useCallback(() => {
    if (capturingRef.current) return;
    const video = videoRef.current;
    if (!video || !cameraReady || video.videoWidth === 0 || video.videoHeight === 0) {
      setCountdown(null);
      return;
    }
    capturingRef.current = true;

    const saveFrame = () => {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const context = canvas.getContext("2d");

      if (!context) {
        capturingRef.current = false;
        setCountdown(null);
        return;
      }

      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => {
        capturingRef.current = false;
        setCountdown(null);
        if (blob) onCapture(blob);
      }, "image/jpeg", 0.95);
    };

    if ("requestVideoFrameCallback" in video) {
      video.requestVideoFrameCallback(saveFrame);
    } else {
      window.requestAnimationFrame(saveFrame);
    }
  }, [cameraReady, onCapture]);

  useEffect(() => {
    if (countdown === null) return;
    if (countdown === 0) {
      capture();
      return;
    }
    const timer = window.setTimeout(() => setCountdown((value) => (value ?? 1) - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [capture, countdown]);

  return <section className="kiosk-screen flex flex-col">
    <div className="kiosk-content flex min-h-0 flex-1 flex-col items-center justify-center gap-4">
      <div className="glass media-frame relative mx-auto overflow-hidden rounded-[32px] bg-[#080808]">
        {cameraError ? <div className="flex h-full flex-col items-center justify-center gap-4 text-center"><Camera size={52} className="text-white/45" /><p className="m-0 text-xl">Разрешите доступ к камере<br /><span className="text-base text-white/55">и обновите страницу</span></p></div> : <video ref={videoRef} onCanPlay={() => setCameraReady(true)} autoPlay playsInline muted className="h-full w-full object-contain" />}
        <div className="absolute inset-5 rounded-[22px] border border-white/30" />
        {countdown !== null && <div className="absolute inset-0 flex items-center justify-center bg-[#070707]/75"><span className="text-[10rem] font-black leading-none text-white">{countdown}</span></div>}
      </div>
      <div className="kiosk-actions shrink-0 mx-auto w-full max-w-4xl"><button className="action" onClick={onBack}><RotateCcw className="mr-2 inline" size={20} />Назад</button>    <button disabled={cameraError || !cameraReady || countdown !== null} className="action action-primary" onClick={() => setCountdown(shutterSeconds)}>Сделать снимок</button></div>
    </div>
  </section>;
}
