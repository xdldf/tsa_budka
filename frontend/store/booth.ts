"use client";

import { create } from "zustand";
import type { PhotoFormat, Style } from "@/types";

export type BoothStatus = "idle" | "uploading" | "generating" | "completed" | "failed" | "printing" | "printed";

type BoothStore = {
  photoFormat?: PhotoFormat;
  style?: Style;
  photos: Blob[];
  imageIds: string[];
  resultUrl?: string;
  shareUrl?: string;
  jobId?: string;
  jobVersion: number;
  status: BoothStatus;
  statusMessage: string;
  startedAt?: number;
  selectFormat: (photoFormat: PhotoFormat) => void;
  selectStyle: (style: Style) => void;
  addPhoto: (photo: Blob) => void;
  replaceLastPhoto: (photo: Blob) => void;
  discardLastPhoto: () => void;
  setImageIds: (imageIds: string[]) => void;
  setShareUrl: (shareUrl?: string) => void;
  startJob: (jobId: string) => number;
  updateJob: (jobId: string, version: number, updates: Partial<Pick<BoothStore, "status" | "statusMessage" | "resultUrl">>) => boolean;
  setStatus: (status: BoothStatus, message: string) => void;
  reset: () => void;
};

export const useBoothStore = create<BoothStore>((set, get) => ({
  photos: [],
  imageIds: [],
  jobVersion: 0,
  status: "idle",
  statusMessage: "",
  selectFormat: (photoFormat) => set({ photoFormat, photos: [], imageIds: [], style: undefined }),
  selectStyle: (style) => set({ style }),
  addPhoto: (photo) => set((state) => ({ photos: [...state.photos, photo], imageIds: [], resultUrl: undefined, jobId: undefined, status: "idle", statusMessage: "" })),
  replaceLastPhoto: (photo) => set((state) => ({ photos: [...state.photos.slice(0, -1), photo] })),
  discardLastPhoto: () => set((state) => ({ photos: state.photos.slice(0, -1), imageIds: [] })),
  setImageIds: (imageIds) => set({ imageIds }),
  startJob: (jobId) => {
    const jobVersion = get().jobVersion + 1;
    set({ jobId, jobVersion, status: "generating", statusMessage: "Готовим фото к обработке...", resultUrl: undefined, shareUrl: undefined, startedAt: Date.now() });
    return jobVersion;
  },
  updateJob: (jobId, version, updates) => {
    if (get().jobId !== jobId || get().jobVersion !== version) return false;
    set(updates);
    return true;
  },
  setStatus: (status, statusMessage) => set({ status, statusMessage }),
  setShareUrl: (shareUrl) => set({ shareUrl }),
  reset: () => set({ photoFormat: undefined, style: undefined, photos: [], imageIds: [], resultUrl: undefined, shareUrl: undefined, jobId: undefined, jobVersion: 0, status: "idle", statusMessage: "", startedAt: undefined }),
}));
