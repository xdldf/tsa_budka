"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { CameraCapture } from "@/components/camera-capture";
import { HomeButton } from "@/components/home-button";
import { useBoothStore } from "@/store/booth";

export default function CameraPage() {
  const router = useRouter();
  const { style, photoFormat, photos, addPhoto } = useBoothStore();
  const total = 1;
  useEffect(() => { if (!style || !photoFormat) router.replace("/styles"); }, [photoFormat, router, style]);
  if (!style || !photoFormat) return null;
  return <main className="booth-shell diamond-shell"><HomeButton />
    <div className="capture-progress">Кадр {Math.min(photos.length + 1, total)} из {total}</div>
    <CameraCapture onCapture={(photo) => { addPhoto(photo); router.push("/preview"); }} onBack={() => router.push(photos.length ? "/preview" : "/format")} />
  </main>;
}
