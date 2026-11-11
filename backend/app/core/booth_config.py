from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ImageConfig(BaseModel):
    aspect_ratio: str = "2:3"
    quality: Literal["low", "medium", "high"] = "medium"


class PrintConfig(BaseModel):
    enabled: bool = True
    queue: str = "DP-QW410"
    media: str = "w288h432"
    width_px: int = 1200
    height_px: int = 1800
    dpi: int = 300
    fit: Literal["fit", "fill"] = "fill"
    timeout: int = 120
    options: str = "print-color-mode=color print-quality=high"
    # Borderless overscan compensation for the DNP QW410 (Gutenprint).
    # The driver's borderless path enlarges the raster by ~x1.0033 and the
    # paper shows the center-cropped window, losing a few px per edge.
    # We pre-shrink the photo by 1/(1+overscan) and add a mirrored edge bleed
    # so the overscan eats only sacrificial pixels and the visible photo is 1:1.
    # 0 disables compensation.
    borderless_overscan: float = 0.0034


class TimerConfig(BaseModel):
    countdown_seconds: int = 5


class BoothConfig(BaseModel):
    image: ImageConfig = Field(default_factory=ImageConfig)
    print: PrintConfig = Field(default_factory=PrintConfig)
    timer: TimerConfig = Field(default_factory=TimerConfig)


def _config_path() -> Path:
    env = os.environ.get("BOOTH_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    here = Path(__file__).resolve()
    candidates = [
        Path.cwd() / "booth.config.toml",
        Path.cwd() / "backend" / "booth.config.toml",
        here.parents[3] / "booth.config.toml",
        here.parents[2] / "booth.config.toml",  # /app/booth.config.toml in Docker/kiosk
        Path("/app/booth.config.toml"),
        Path("/app/backend/booth.config.toml"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def load_booth_config() -> BoothConfig:
    path = _config_path()
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except FileNotFoundError:
        data = {}
    booth = BoothConfig.model_validate(data)
    print(f"[BOOTH] config loaded from {path}", flush=True)
    return booth


booth_config = load_booth_config()
