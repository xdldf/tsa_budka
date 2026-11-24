"use client";

import { PhotoChoice } from "@/components/photo-choice";
import { api } from "@/services/api";
import type { Gender, Style } from "@/types";

export function StyleCard({ style, gender, selected, onSelect }: { style: Style; gender?: Gender; selected: boolean; onSelect: () => void }) {
  let previewUrl: string | null = null;
  if (style.category === "culture") {
    const outfits = (style.outfit_images[gender ?? ""] ?? Object.values(style.outfit_images)[0]) ?? [];
    previewUrl = outfits.length > 0 ? api.imageUrl(`/static/outfits/${outfits[0]}`) : null;
  } else if (style.location_preview) {
    previewUrl = api.imageUrl(style.location_preview);
  } else if (style.background_images.length > 0) {
    previewUrl = api.imageUrl(`/static/backgrounds/${style.background_images[0]}`);
  }

  if (previewUrl) return <PhotoChoice src={previewUrl} label={style.name} selected={selected} onSelect={onSelect} />;
  return <button className={`theme-card ${selected ? "theme-card-selected" : ""}`} style={{ "--theme-color": style.preview_color } as React.CSSProperties} onClick={onSelect}>
    <span className="theme-orbit" /><span className="theme-gem">◆</span><strong>{style.name}</strong><small>{style.description}</small>
  </button>;
}
