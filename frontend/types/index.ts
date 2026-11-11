export type JobState = "queued" | "processing" | "completed" | "failed" | "cancelled";

export type PhotoFormat = "square" | "portrait" | "double_strip";
export type BoothMode = "themes";
export type Gender = "male" | "female";
export type FilterMode = "filter" | "nofilter";

export interface Style {
  id: string;
  name: string;
  description: string;
  preview_color: string;
  category: string;
  background_images: string[];
  outfit_images: Record<string, string[]>;
  example_filter?: string | null;
  example_nofilter?: string | null;
  example?: string | null;
  example_male?: string | null;
  example_female?: string | null;
  location_preview?: string | null;
}

export interface Job {
  job_id: string;
  state: JobState;
  message: string;
  result_url?: string;
  attempt: number;
}
