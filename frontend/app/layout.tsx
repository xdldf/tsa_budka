import "./globals.css";
import { Providers } from "./providers";

export const metadata = {
  title: "Цифровой алмаз — ИИ-фотобудка",
  description: "ИИ-фотобудка форума «Цифровой алмаз»",
  applicationName: "Цифровой алмаз",
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "Цифровой алмаз", statusBarStyle: "black-translucent" },
};

export const viewport = { themeColor: "#061558" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru"><body><Providers>{children}</Providers></body></html>;
}
