"use client";

import { useEffect } from "react";
import { Grid2X2, RectangleVertical, Columns2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { HomeButton } from "@/components/home-button";
import { useBoothStore } from "@/store/booth";
import type { PhotoFormat } from "@/types";

const formats: Array<{ id: PhotoFormat; title: string; subtitle: string; Icon: typeof Grid2X2 }> = [
  { id: "square", title: "Квадрат", subtitle: "10 × 10 см · 1 фото", Icon: Grid2X2 },
  { id: "portrait", title: "Классика", subtitle: "10 × 15 см · 1 фото", Icon: RectangleVertical },
  { id: "double_strip", title: "Две фотополоски", subtitle: "10 × 15 см · 6 фото из одного кадра", Icon: Columns2 },
];

export default function FormatPage() {
  const router = useRouter();
  const { style, selectFormat } = useBoothStore();
  useEffect(() => { if (!style) router.replace("/styles"); }, [router, style]);
  if (!style) return null;
  const availableFormats = formats.filter((format) => format.id !== "double_strip" || style.supports_double_strip);
  const choose = (format: PhotoFormat) => { selectFormat(format); router.push("/camera"); };
  return <main className="booth-shell diamond-shell"><HomeButton /><section className="kiosk-screen flex h-[100svh] flex-col justify-center">
    <header className="text-center"><p className="event-kicker">{style.name}</p><h1 className="m-0 text-4xl font-bold">Выберите формат фотографии</h1></header>
    <div className={`format-grid grid min-h-0 flex-1 gap-4 ${availableFormats.length === 2 ? "grid-cols-2" : "grid-cols-3"}`}>
      {availableFormats.map(({ id, title, subtitle, Icon }) => <button key={id} onClick={() => choose(id)} className="glass format-card">
        <span className={`format-paper format-paper-${id}`}><Icon size={64} strokeWidth={1.4} /></span>
        <strong>{title}</strong><span>{subtitle}</span>
      </button>)}
    </div>
    <div className="kiosk-actions"><button className="action" onClick={() => router.push("/styles")}>Назад к стилям</button></div>
  </section></main>;
}
