from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import UUID

import httpx


class NextcloudShareService:
    """Uploads photos to a Nextcloud folder and returns the public share URL
    that gets encoded into the QR code (same scheme as ai_photobooth)."""

    def __init__(self, webdav_url: str, user: str, password: str, folder: str, public_url: str):
        self.webdav_url = webdav_url.rstrip("/")
        self.user = user
        self.password = password
        self.folder = folder.strip("/")
        self.public_url = public_url.rstrip("/")
        self._cache: dict[UUID, str] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.webdav_url and self.public_url and self.user)

    def url_for(self, job_id: UUID) -> str | None:
        return self._cache.get(job_id)

    async def upload(self, job_id: UUID, file_path: Path) -> str | None:
        """PUT the file to Nextcloud WebDAV; returns the public URL or None on failure."""
        if not self.enabled or not file_path.is_file():
            return None
        cached = self._cache.get(job_id)
        if cached:
            return cached
        remote_name = f"{file_path.stem}{file_path.suffix or '.png'}"
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                data = await client.put(
                    f"{self.webdav_url}/{self.folder}/{remote_name}",
                    content=await asyncio.to_thread(file_path.read_bytes),
                    auth=(self.user, self.password),
                )
            if data.status_code not in {201, 204}:
                print(f"[BOOTH] nextcloud upload failed: HTTP {data.status_code}: {data.text[:200]}", flush=True)
                return None
        except Exception as exc:  # noqa: BLE001
            print(f"[BOOTH] nextcloud upload error: {exc!r}", flush=True)
            return None
        share_url = f"{self.public_url}/{remote_name}"
        self._cache[job_id] = share_url
        return share_url


def build_share_service(settings) -> NextcloudShareService:
    return NextcloudShareService(
        settings.nextcloud_webdav_url,
        settings.nextcloud_user,
        settings.nextcloud_password,
        settings.nextcloud_folder,
        settings.nextcloud_public_url,
    )
