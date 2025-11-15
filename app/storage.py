"""Utilities for handling uploaded media files."""

from __future__ import annotations

from pathlib import Path
from secrets import token_hex

from fastapi import UploadFile

from .config import settings

CHUNK_SIZE = 1024 * 1024


def ensure_upload_dir(subdir: str | None = None) -> Path:
    """Ensure upload directory (and optional subdir) exists and return path."""

    target = settings.uploads_path
    if subdir:
        target = target / subdir
    target.mkdir(parents=True, exist_ok=True)
    return target


async def save_upload_file(upload: UploadFile, *, subdir: str | None = None) -> str:
    """Persist UploadFile contents and return the public URL."""

    if not upload.filename:
        raise ValueError("Upload must include filename.")

    target_dir = ensure_upload_dir(subdir)
    suffix = Path(upload.filename).suffix.lower()
    filename = f"{token_hex(16)}{suffix}"
    destination = target_dir / filename

    await _write_file(upload, destination)

    relative_path = destination.relative_to(settings.uploads_path).as_posix()
    prefix = settings.uploads_url_prefix_clean
    return f"{prefix}/{relative_path}"


async def _write_file(upload: UploadFile, destination: Path) -> None:
    await upload.seek(0)
    with destination.open("wb") as buffer:
        while True:
            chunk = await upload.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer.write(chunk)
    await upload.close()
