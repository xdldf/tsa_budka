import type { Job, PhotoFormat, Style } from "@/types";

export interface BoothConfig {
  image: { aspect_ratio: string; quality: string };
  print: {
    enabled: boolean;
    queue: string;
    media: string;
    width_px: number;
    height_px: number;
    dpi: number;
    fit: string;
    timeout: number;
    options: string;
  };
  timer: { countdown_seconds: number };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// The API catalog and job messages may still include an English translation.
const russianText = (text: string) => text.split(/\s+\/\s+(?=[A-Za-z])/)[0].trim();

async function requestJob(path: string, init?: RequestInit): Promise<Job> {
  const job = await request<Job>(path, init);
  return { ...job, message: russianText(job.message) };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "";
    throw new Error(/[А-Яа-яЁё]/.test(detail) ? russianText(detail) : "Не удалось выполнить запрос. Попробуйте ещё раз.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  config: () => request<BoothConfig>("/config"),
  styles: async () => (await request<Style[]>("/styles")).map((style) => ({ ...style, name: russianText(style.name), description: russianText(style.description) })),
  capture: async (file: Blob) => {
    const body = new FormData();
    body.append("photo", file, "capture.jpg");
    return request<{ image_id: string; image_url: string }>("/capture", { method: "POST", body });
  },
  generate: (imageIds: string[], styleId: string, photoFormat: PhotoFormat, signal?: AbortSignal) =>
    requestJob("/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ image_ids: imageIds, style_id: styleId, photo_format: photoFormat }), signal }),
  status: (jobId: string) => requestJob(`/status/${jobId}`),
  cancel: (jobId: string) => requestJob(`/cancel/${jobId}`, { method: "POST" }),
  print: (jobId: string) => requestJob("/print", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ job_id: jobId }) }),
  share: (jobId: string) => request<{ url: string }>(`/share/${jobId}`, { method: "POST" }),
  imageUrl: (path: string) => `${API_URL}${path}`,
};
