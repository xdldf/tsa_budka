import asyncio
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image

import app.main as main
from app.main import app
from app.models import Job, JobState, PhotoFormat
from app.services.graphics import compose_double_strip, normalize_to_format


def request(method: str, path: str, **kwargs) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)
    return asyncio.run(run())


def test_health_and_theme_catalog() -> None:
    assert request("GET", "/health").json() == {"status": "ok"}
    styles = request("GET", "/styles").json()
    assert len(styles) == 20
    assert {style["id"] for style in styles} >= {"costume-male-botur", "lena-pillars-winter", "anime", "postcard-soviet"}
    assert not next(style for style in styles if style["id"] == "postcard-soviet")["supports_double_strip"]


def test_rejects_non_image_capture() -> None:
    response = request("POST", "/capture", files={"photo": ("notes.txt", b"not a photo", "text/plain")})
    assert response.status_code == 415


def test_double_strip_accepts_one_source_photo() -> None:
    response = request("POST", "/generate", json={
        "image_ids": [str(uuid4())], "style_id": "digital-diamond", "photo_format": "double_strip",
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Image not found"


def test_postcard_rejects_double_strip_with_real_source() -> None:
    image_id = uuid4()
    source = main.storage.root / f"{image_id}.jpg"
    Image.new("RGB", (32, 32), "white").save(source)
    try:
        response = request("POST", "/generate", json={
            "image_ids": [str(image_id)], "style_id": "postcard-soviet", "photo_format": "double_strip",
        })
        assert response.status_code == 422
        assert response.json()["detail"] == "Double photo strip is not available for this style"
    finally:
        source.unlink(missing_ok=True)


def test_reference_assets_exist_for_reference_driven_styles() -> None:
    for style in main.STYLES:
        for filename in style.background_images:
            assert (main.BACKGROUNDS_DIR / filename).is_file()
        for filenames in style.outfit_images.values():
            for filename in filenames:
                assert (main.OUTFITS_DIR / filename).is_file()


def test_format_normalization_and_six_photo_composition(tmp_path: Path) -> None:
    sources = []
    colors = [(240, 10, 10), (10, 240, 10), (10, 10, 240), (240, 240, 10), (240, 10, 240), (10, 240, 240)]
    for index, color in enumerate(colors):
        path = tmp_path / f"{index}.png"
        Image.new("RGB", (900, 700), color).save(path)
        normalize_to_format(path, "double_strip")
        sources.append(path)
    output = tmp_path / "sheet.png"
    compose_double_strip(sources, output)
    with Image.open(output) as sheet:
        assert sheet.size == (1200, 1800)
        assert [sheet.getpixel(point) for point in ((300, 300), (300, 900), (300, 1500), (900, 300), (900, 900), (900, 1500))] == colors


def test_print_targets_result_image(monkeypatch, tmp_path: Path) -> None:
    printed: list[str] = []
    class FakePrinter:
        async def print_image(self, path): printed.append(str(path))
    result_id = uuid4()
    result_path = main.storage.root / f"{result_id}.png"
    result_path.write_bytes(b"RESULT")
    job = Job(source_image_ids=[uuid4()], style_id="digital-diamond", photo_format=PhotoFormat.SQUARE, state=JobState.COMPLETED, result_image_id=result_id)
    main.jobs.jobs[job.id] = job
    monkeypatch.setattr(main, "printer", FakePrinter())
    try:
        response = request("POST", "/print", json={"job_id": str(job.id)})
        assert response.status_code == 200
        assert printed == [str(result_path)]
    finally:
        result_path.unlink(missing_ok=True)
        main.jobs.jobs.pop(job.id)


def test_print_unknown_job_returns_404() -> None:
    assert request("POST", "/print", json={"job_id": str(uuid4())}).status_code == 404
