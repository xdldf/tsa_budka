from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Photo Booth API"
    storage_dir: Path = Path("/tmp/ai-photo-booth")
    image_provider: str = "demo"
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-image-2"
    job_max_attempts: int = 3
    cleanup_max_age_hours: int = 24
    saved_dir: Path = Path("saved_photos")
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Printing (DNP QW410 / any CUPS queue).
    printer_enabled: bool = True
    printer_name: str = "DP-QW410"
    printer_media: str = "w288h288"   # 4x4 photo for the QW410
    printer_options: str = "print-color-mode=color print-quality=high StpiShrinkOutput=Expand"
    printer_timeout: int = 120
    print_pixel_size: tuple[int, int, int] = (1200, 1200, 300)  # width, height, dpi (4x4 @300)

    # Nextcloud sharing (QR download). Leave webdav url empty to disable.
    nextcloud_webdav_url: str = ""      # e.g. https://cloud.example.com/remote.php/dav/files/<user-id>
    nextcloud_user: str = ""
    nextcloud_password: str = ""
    nextcloud_folder: str = "driveephotos"
    nextcloud_public_url: str = ""      # e.g. https://cloud.example.com/public.php/dav/files/<share-token>

    # The booth is normally launched from the repository root, while the
    # deployment secrets live beside the backend.  Load that file first and
    # keep .env as a convenient local override when running inside backend/.
    model_config = SettingsConfigDict(env_file=("backend/.env", ".env"), env_file_encoding="utf-8", extra="ignore")


settings = Settings()
