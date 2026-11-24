"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { api } from "@/services/api";
import { HomeButton } from "@/components/home-button";
import { StyleCard } from "@/components/style-card";
import { useBoothStore } from "@/store/booth";

const PER_PAGE = 4;
export default function StyleSelectionPage() {
  const router = useRouter();
  const { data: styles = [], isLoading, isError, refetch } = useQuery({ queryKey: ["styles"], queryFn: api.styles });
  const [page, setPage] = useState(0);
  const { style, selectStyle } = useBoothStore();
  const pages = Math.max(1, Math.ceil(styles.length / PER_PAGE));
  const visible = useMemo(() => styles.slice(page * PER_PAGE, (page + 1) * PER_PAGE), [page, styles]);
  return <main className="booth-shell diamond-shell"><HomeButton /><section className="kiosk-screen flex h-[100svh] flex-col">
    <header className="text-center"><p className="event-kicker">Цифровой алмаз</p><h1>Выберите стиль</h1></header>
    {isError ? <div className="glass m-auto rounded-3xl p-8 text-center"><p>Не удалось загрузить темы</p><button className="action mt-4" onClick={() => void refetch()}>Повторить</button></div> : isLoading ? <p className="flex flex-1 items-center justify-center">Загружаем темы…</p> :
      <div className="catalog-grid grid min-h-0 flex-1 grid-cols-2 grid-rows-2 gap-4">{visible.map((item) => <StyleCard key={item.id} style={item} selected={style?.id === item.id} onSelect={() => { selectStyle(item); router.push("/format"); }} />)}</div>}
    <div className="kiosk-actions"><button className="action flex-1" disabled={!page} onClick={() => setPage(page - 1)}><ChevronLeft />Назад</button><span>{page + 1} / {pages}</span><button className="action flex-1" disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>Далее<ChevronRight /></button></div>
  </section></main>;
}
