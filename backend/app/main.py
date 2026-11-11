from contextlib import asynccontextmanager
import subprocess
from uuid import UUID

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.booth_config import booth_config
from app.core.config import settings
from app.models import CaptureResponse, GenerateRequest, JobResponse, PrintRequest, ShareResponse
from app.services import JobManager, StorageService, build_print_service, build_provider, build_share_service
from app.services.image_provider import BACKGROUNDS_DIR
from app.services.styles import STYLES

storage = StorageService(settings.storage_dir)
jobs = JobManager(storage, build_provider(settings), settings)
printer = build_print_service()
sharer = build_share_service(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
app.mount("/static/backgrounds", StaticFiles(directory=BACKGROUNDS_DIR), name="backgrounds")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
async def get_config() -> dict:
    return {
        "image": booth_config.image.model_dump(),
        "print": booth_config.print.model_dump(),
        "timer": booth_config.timer.model_dump(),
    }


@app.get("/styles")
async def get_styles():
    result = []
    for style in STYLES:
        item = style.model_copy()
        result.append(item)
    return result


@app.post("/capture", response_model=CaptureResponse)
async def capture(photo: UploadFile = File(...)) -> CaptureResponse:
    if not (photo.content_type or "").startswith("image/"):
        raise HTTPException(415, "Photo must be an image")
    image_id = await storage.save_upload(photo)
    return CaptureResponse(image_id=image_id, image_url=storage.url_for(image_id))


@app.get("/images/{image_id}")
async def image(image_id: UUID):
    path = storage.path_for(image_id)
    if not path:
        raise HTTPException(404, "Image not found")
    return FileResponse(path)


@app.post("/generate", response_model=JobResponse)
async def generate(payload: GenerateRequest) -> JobResponse:
    expected = 6 if payload.photo_format == "double_strip" else 1
    if len(payload.image_ids) != expected:
        raise HTTPException(422, f"Format {payload.photo_format} requires {expected} photo(s)")
    if any(not storage.path_for(image_id) for image_id in payload.image_ids):
        raise HTTPException(404, "Image not found")
    if not any(style.id == payload.style_id for style in STYLES):
        raise HTTPException(404, "Style not found")
    return jobs.response(jobs.start_generation(payload.image_ids, payload.style_id, payload.photo_format))


@app.get("/status/{job_id}", response_model=JobResponse)
async def status(job_id: UUID) -> JobResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return jobs.response(job)


@app.post("/cancel/{job_id}", response_model=JobResponse)
async def cancel(job_id: UUID) -> JobResponse:
    job = jobs.cancel(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return jobs.response(job)


@app.post("/print", response_model=JobResponse)
async def print_photo(payload: PrintRequest) -> JobResponse:
    job = jobs.get(payload.job_id)
    if not job or not job.result_image_id:
        raise HTTPException(404, "Job result not found")
    path = storage.path_for(job.result_image_id)
    if not path:
        raise HTTPException(404, "Image not found")
    if not booth_config.print.enabled:
        raise HTTPException(503, "Печать отключена в настройках фотобудки. / Printing is disabled in booth settings.")
    try:
        await printer.print_image(path)
    except FileNotFoundError:
        raise HTTPException(503, "Принтер недоступен. Проверьте подключение и CUPS. / Printer unavailable. Check connection and CUPS.") from None
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Принтер не ответил вовремя. Проверьте очередь перед повторной печатью. / Printer timed out. Check the queue before retrying.") from None
    except (RuntimeError, OSError):
        raise HTTPException(503, "Не удалось отправить фото на принтер. Проверьте очередь, подключение и бумагу. / Could not submit photo. Check printer queue, connection and paper.") from None
    return JobResponse(job_id=job.id, state="completed", message="Фото успешно отправлено на печать / Photo successfully sent for printing")


@app.post("/share/{job_id}", response_model=ShareResponse)
async def share_photo(job_id: UUID) -> ShareResponse:
    job = jobs.get(job_id)
    if not job or not job.result_image_id:
        raise HTTPException(404, "Job result not found")
    cached = sharer.url_for(job.id)
    if cached:
        return ShareResponse(url=cached)
    if not sharer.enabled:
        raise HTTPException(503, "Sharing is not configured")
    path = storage.path_for(job.result_image_id)
    if not path:
        raise HTTPException(404, "Image not found")
    url = await sharer.upload(job.id, path)
    if not url:
        raise HTTPException(502, "Не удалось выгрузить фото. Попробуйте ещё раз. / Failed to upload the photo. Please try again.")
    return ShareResponse(url=url)
