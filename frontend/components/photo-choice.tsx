"use client";

import { useState } from "react";

export function PhotoChoice({ src, label, selected = false, onSelect }: { src: string | null; label: string; selected?: boolean; onSelect: () => void }) {
  const [ratio, setRatio] = useState(2 / 3);
  return <div className="photo-choice-cell">
    <button className={`glass photo-choice ${selected ? "photo-choice-selected" : ""}`} style={{ aspectRatio: ratio, width: `min(100cqw, calc((100cqh - var(--photo-caption-height) - 12px) * ${ratio}))` }} onClick={onSelect} aria-label={label} aria-pressed={selected}>
      {src ? <img src={src} alt="" draggable={false} onLoad={(event) => { const image = event.currentTarget; if (image.naturalHeight) setRatio(image.naturalWidth / image.naturalHeight); }} /> : <div className="photo-placeholder" />}
    </button>
    <span className="photo-choice-label" aria-hidden="true">{label}</span>
  </div>;
}
