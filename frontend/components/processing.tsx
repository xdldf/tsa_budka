"use client";

import { LoaderCircle, RotateCcw, X } from "lucide-react";

export function Processing({ message, elapsed, timedOut, onCancel, onRestart }: { message: string; elapsed: number; timedOut: boolean; onCancel: () => void; onRestart: () => void }) {
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;
  const progress = Math.min(100, Math.round((elapsed / 180) * 100));

  return <section className="kiosk-screen flex items-center justify-center"><div className="glass w-full max-w-md rounded-[32px] px-8 py-10 text-center"><LoaderCircle className="mx-auto animate-spin text-[#ffffff]" size={68} /><h1 className="mb-0 mt-6 text-2xl font-bold md:text-3xl">{timedOut ? "Обработка занимает больше обычного" : "Обрабатываем фотографию"}</h1><p className="mb-0 mt-3 text-white/70">{message || "Пожалуйста, подождите"}</p><div className="mt-7"><div className="mb-2 flex justify-between text-sm text-white/65"><span>Прошло{minutes}:{String(seconds).padStart(2, "0")}</span><span>{progress}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-[#222222] transition-[width] duration-500" style={{ width: `${progress}%` }} /></div></div>{timedOut ? <button className="action action-primary mt-8" onClick={onRestart}><RotateCcw className="mr-2 inline" size={20} />Перезапустить генерацию</button> : <button className="action mt-8" onClick={onCancel}><X className="mr-2 inline" size={20} />Отмена</button>}</div></section>;
}
