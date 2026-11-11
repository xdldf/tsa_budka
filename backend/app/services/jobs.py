from __future__ import annotations

import asyncio
import shutil
import time
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.core.config import Settings
from app.models import Job, JobResponse, JobState, PhotoFormat
from app.services.graphics import compose_double_strip, normalize_to_format
from app.services.image_provider import ImageProvider
from app.services.storage import StorageService
from app.services.styles import get_style

DEDUPE_WINDOW_SECONDS = 8.0


class JobManager:
    def __init__(self, storage: StorageService, provider: ImageProvider, settings: Settings):
        self.storage = storage
        self.provider = provider
        self.settings = settings
        self.jobs: dict[UUID, Job] = {}
        self.tasks: dict[UUID, asyncio.Task[None]] = {}
        self.events: dict[UUID, asyncio.Event] = {}
        # Dedupe: key = (all source photos, style, output format) -> (timestamp, job_id).
        # Guarantees a single accidental double-trigger never spawns two photos.
        self._recent: dict[tuple, tuple[float, UUID]] = {}

    @property
    def _now(self) -> float:
        return time.time()

    def response(self, job: Job) -> JobResponse:
        return JobResponse(job_id=job.id, state=job.state, message=job.message, result_url=self.storage.url_for(job.result_image_id) if job.result_image_id else None, attempt=job.attempt)

    def start_generation(self, image_ids: list[UUID], style_id: str, photo_format: PhotoFormat) -> Job:
        key = (tuple(map(str, image_ids)), style_id, photo_format)
        recent = self._recent.get(key)
        if recent and (self._now - recent[0]) < DEDUPE_WINDOW_SECONDS and recent[1] in self.jobs:
            existing = self.jobs[recent[1]]
            if existing.state in {JobState.QUEUED, JobState.PROCESSING}:
                print(f"[BOOTH] de-duplicated duplicate generation request for {key}", flush=True)
                return existing
        job = Job(source_image_ids=image_ids, style_id=style_id, photo_format=photo_format)
        self._recent[key] = (self._now, job.id)
        self.jobs[job.id] = job
        self.events[job.id] = asyncio.Event()
        self.tasks[job.id] = asyncio.create_task(self._generate(job))
        return job

    async def _generate(self, job: Job) -> None:
        sources = [self.storage.path_for(image_id) for image_id in job.source_image_ids]
        style = get_style(job.style_id or "")
        if not all(sources) or not style:
            job.state, job.message = JobState.FAILED, "Не удалось обработать фотографию. Попробуйте ещё раз. / Failed to process the photo. Please try again."
            return
        job.state = JobState.PROCESSING
        for attempt in range(1, self.settings.job_max_attempts + 1):
            if self.events[job.id].is_set():
                job.state, job.message = JobState.CANCELLED, "Обработка отменена / Processing cancelled"
                return
            job.attempt = attempt
            try:
                result_id = uuid4()
                output = self.storage.root / f"{result_id}.png"
                aspect = "1:1" if job.photo_format in {PhotoFormat.SQUARE, PhotoFormat.DOUBLE_STRIP} else "2:3"
                generated: list[Path] = []
                for index, source in enumerate(sources):
                    assert source is not None
                    target = output if len(sources) == 1 else self.storage.root / f"{result_id}_{index}.png"
                    await self.provider.generate(source, style, target, aspect)
                    normalize_to_format(target, job.photo_format)
                    generated.append(target)
                if job.photo_format == PhotoFormat.DOUBLE_STRIP:
                    compose_double_strip(generated, output)
                    for target in generated:
                        target.unlink(missing_ok=True)
                if self.events[job.id].is_set():
                    output.unlink(missing_ok=True)
                    job.state, job.message = JobState.CANCELLED, "Обработка отменена / Processing cancelled"
                    return
                job.state, job.message, job.result_image_id = JobState.COMPLETED, "Готово / Done", result_id
                self._save_result(job, output)
                return
            except Exception as exc:  # noqa: BLE001
                print(f"[BOOTH] generation failed for job {job.id}: {exc!r}", flush=True)
                if attempt < self.settings.job_max_attempts:
                    job.message = "Произошла ошибка. Пробую ещё... / An error occurred. Trying again..."
                    await asyncio.sleep(2 ** (attempt - 1))
        job.state, job.message = JobState.FAILED, "Не удалось обработать фотографию. Попробуйте ещё раз. / Failed to process the photo. Please try again."

    def get(self, job_id: UUID) -> Job | None:
        return self.jobs.get(job_id)

    def _save_result(self, job: Job, output: Path) -> None:
        """Persist the ORIGINAL (base) and EDITED photos under the SAME base name,
        in separate folders, linked by name (edited gets a `_edited` suffix)."""
        try:
            saved_dir = self.settings.saved_dir
            base_dir = saved_dir / "base"
            edited_dir = saved_dir / "edited"
            base_dir.mkdir(parents=True, exist_ok=True)
            edited_dir.mkdir(parents=True, exist_ok=True)

            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            base_name = (job.style_id or "unnamed").replace("/", "_")
            base_name = f"{stamp}_{base_name}"

            for index, image_id in enumerate(job.source_image_ids, 1):
                source = self.storage.path_for(image_id)
                if source:
                    dest_base = base_dir / f"{base_name}_{index}{source.suffix or '.jpg'}"
                    shutil.copyfile(source, dest_base)
                    print(f"[BOOTH] saved base photo to {dest_base}", flush=True)

            dest_edited = edited_dir / f"{base_name}_edited{output.suffix or '.jpg'}"
            shutil.copyfile(output, dest_edited)
            print(f"[BOOTH] saved edited photo to {dest_edited}", flush=True)
        except Exception as exc:  # noqa: BLE001
            print(f"[BOOTH] failed to save result for job {job.id}: {exc!r}", flush=True)

    def cancel(self, job_id: UUID) -> Job | None:
        job = self.get(job_id)
        if job and job.state in {JobState.QUEUED, JobState.PROCESSING}:
            self.events[job_id].set()
            job.message = "Обработка отменена / Processing cancelled"
        return job
