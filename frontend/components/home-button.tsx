"use client";

import { useRouter } from "next/navigation";
import { Home } from "lucide-react";
import { useBoothStore } from "@/store/booth";

export function HomeButton() {
  const router = useRouter();
  const reset = useBoothStore((state) => state.reset);

  return <button className="home" onClick={() => { reset(); router.push("/"); }} aria-label="На главную"><Home size={22} /><span>Главная</span></button>;
}
