"use client";

import { useState } from "react";
import { LoaderCircle, Printer, QrCode, Sparkles } from "lucide-react";

type ResultProps = {
  imageUrl: string;
  isPrinting: boolean;
  printMessage: string;
  isSharing: boolean;
  shareMessage: string;
  isRegenerating: boolean;
  onPrint: () => void;
  onRegenerate: () => void;
  onShareQr: () => void;
};

export function Result({ imageUrl, isPrinting, printMessage, isSharing, shareMessage, isRegenerating, onPrint, onRegenerate, onShareQr }: ResultProps) {
  const [ratio, setRatio] = useState(2 / 3);
  const busy = isPrinting || isSharing || isRegenerating;
  return <section className="kiosk-screen"><div className="result-layout">
    <div className="result-frame"><div className="glass result-photo" style={{ aspectRatio: ratio, width: `min(100cqw, calc(100cqh * ${ratio}))` }}><img src={imageUrl} onLoad={(event) => { const img = event.currentTarget; if (img.naturalHeight) setRatio(img.naturalWidth / img.naturalHeight); }} alt="Сгенерированное фото" /></div></div>
    <div className="result-panel">
      <div className="result-actions">
        <button className="action action-primary" disabled={busy} onClick={onPrint}>{isPrinting ? <LoaderCircle className="animate-spin" size={22} /> : <Printer size={22} />}{isPrinting ? "Печатаем..." : "Печать"}</button>
        <button className="action" disabled={busy} onClick={onRegenerate}>{isRegenerating ? <LoaderCircle className="animate-spin" size={20} /> : <Sparkles size={20} />}Ещё вариант</button>
        <button className="action" disabled={busy} onClick={onShareQr}>{isSharing ? <LoaderCircle className="animate-spin" size={20} /> : <QrCode size={20} />}Скачать по QR-коду</button>
      </div>
      {printMessage && <p className="glass result-message" role="status" aria-live="polite">{printMessage}</p>}
      {shareMessage && <p className="glass result-message" role="status" aria-live="polite">{shareMessage}</p>}
    </div>
  </div></section>;
}
