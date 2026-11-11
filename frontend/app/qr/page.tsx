"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";
import { HomeButton } from "@/components/home-button";
import { useBoothStore } from "@/store/booth";

export default function QrPage() {
  const router = useRouter();
  const shareUrl = useBoothStore((state) => state.shareUrl);

  useEffect(() => {
    if (!shareUrl) router.replace("/");
  }, [router, shareUrl]);

  if (!shareUrl) return null;

  return (
    <main className="booth-shell">
      <HomeButton />
      <section className="kiosk-screen kiosk-screen-portrait flex h-[100svh] flex-col">
        <header className="shrink-0 pb-8 pt-4 text-center">
          <h1 className="m-0 text-4xl font-bold">Заберите фото</h1>
          <p className="mb-0 mt-3 text-lg text-white/65">Отсканируйте QR-код камерой телефона, чтобы скачать фотографию</p>
        </header>
        <div className="flex min-h-0 flex-1 items-center justify-center">
          <div className="qr-code flex items-center justify-center rounded-[32px] bg-white p-6 shadow-2xl">
            <QRCodeSVG value={shareUrl} size={520} level="H" marginSize={2} />
          </div>
        </div>
        <div className="kiosk-actions shrink-0 pb-2 pt-6">
          <button className="action flex-1" onClick={() => router.push("/result")}>
            <ChevronLeft className="mr-1 inline" />Назад
          </button>
          <span className="flex-1" />
        </div>
      </section>
    </main>
  );
}
