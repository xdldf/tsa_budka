"use client";

import { Grid2X2, RectangleVertical, Columns2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useBoothStore } from "@/store/booth";
import type { PhotoFormat } from "@/types";

const formats: Array<{ id: PhotoFormat; title: string; subtitle: string; Icon: typeof Grid2X2 }> = [
  { id: "square", title: "Квадрат", subtitle: "10 × 10 см · 1 фото", Icon: Grid2X2 },
  { id: "portrait", title: "Классика", subtitle: "10 × 15 см · 1 фото", Icon: RectangleVertical },
  { id: "double_strip", title: "Две фотополоски", subtitle: "10 × 15 см · 6 разных фото", Icon: Columns2 },
];

export default function FormatPage() {
  const router = useRouter();
  const selectFormat = useBoothStore((state) => state.selectFormat);
  const choose = (format: PhotoFormat) => { selectFormat(format); router.push("/styles"); };
  return <main className="booth-shell diamond-shell"><section className="kiosk-screen flex h-[100svh] flex-col justify-center">
    <header className="text-center"><p className="event-kicker">Форум «Цифровой алмаз»</p><h1 className="m-0 text-4xl font-bold">Выберите формат фотографии</h1></header>
    <div className="format-grid grid min-h-0 flex-1 grid-cols-3 gap-4">
      {formats.map(({ id, title, subtitle, Icon }) => <button key={id} onClick={() => choose(id)} className="glass format-card">
        <span className={`format-paper format-paper-${id}`}><Icon size={64} strokeWidth={1.4} /></span>
        <strong>{title}</strong><span>{subtitle}</span>
      </button>)}
    </div>
  </section></main>;
}
