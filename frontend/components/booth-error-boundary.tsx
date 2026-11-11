"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

export class BoothErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Booth render error", error, info);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <main className="booth-shell">
        <section className="kiosk-screen flex items-center justify-center">
          <div className="glass w-full max-w-xl rounded-[32px] p-8 text-center">
            <h1 className="m-0 text-2xl font-bold">Экран временно недоступен</h1>
            <p className="mt-3 text-white/65">Вернитесь в начало и попробуйте ещё раз.</p>
            <button className="action action-primary mt-6" onClick={() => window.location.reload()}>
              Обновить экран
            </button>
          </div>
        </section>
      </main>
    );
  }
}
