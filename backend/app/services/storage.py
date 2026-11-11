from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile


class StorageService:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> UUID:
        image_id = uuid4()
        suffix = Path(upload.filename or "photo.jpg").suffix or ".jpg"
        path = self.root / f"{image_id}{suffix}"
        path.write_bytes(await upload.read())
        return image_id

    def path_for(self, image_id: UUID) -> Path | None:
        matches = list(self.root.glob(f"{image_id}.*"))
        return matches[0] if matches else None

    def url_for(self, image_id: UUID) -> str:
        return f"/images/{image_id}"
