import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Цифровой алмаз — ИИ-фотобудка",
    short_name: "Цифровой алмаз",
    description: "ИИ-фотобудка форума «Цифровой алмаз»",
    start_url: "/",
    display: "standalone",
    background_color: "#07111f",
    theme_color: "#07111f",
    lang: "ru",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml" }],
  };
}
