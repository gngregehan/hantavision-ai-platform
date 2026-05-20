import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from ..config import settings


@dataclass
class SavedImage:
    original_name: str
    stored_path: Path
    sha256: str
    content_type: str
    image: Image.Image
    size_bytes: int


def _safe_name(filename: str) -> str:
    stem = Path(filename or "upload").stem
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip(".-")[:80]
    return stem or "upload"


def _dicom_to_image(data: bytes) -> Image.Image:
    try:
        import pydicom
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="DICOM desteği için pydicom paketi kurulu olmalıdır.") from exc

    try:
        dataset = pydicom.dcmread(BytesIO(data), force=True)
        pixels = dataset.pixel_array.astype(np.float32)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="DICOM dosyası okunamadı veya piksel verisi bulunamadı.") from exc

    if pixels.ndim == 3:
        pixels = pixels.mean(axis=-1)
    pixels = pixels - float(pixels.min())
    max_value = float(pixels.max()) or 1.0
    pixels = np.clip((pixels / max_value) * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(pixels).convert("RGB")


async def save_image_upload(file: UploadFile) -> SavedImage:
    suffix = Path(file.filename or "").suffix.lower()
    is_dicom = suffix in {".dcm", ".dicom"}
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Desteklenmeyen dosya türü. JPG, PNG, WEBP, BMP, TIFF veya DICOM yükleyin.",
        )
    if not is_dicom and file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Dosya içerik türü güvenli görüntü formatları arasında değil.",
        )

    limit = settings.max_upload_mb * 1024 * 1024
    data = bytearray()
    while chunk := await file.read(1024 * 1024):
        data.extend(chunk)
        if len(data) > limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Dosya çok büyük. En fazla {settings.max_upload_mb} MB yüklenebilir.",
            )

    digest = hashlib.sha256(data).hexdigest()
    if is_dicom:
        image = _dicom_to_image(bytes(data))
    else:
        try:
            probe = Image.open(BytesIO(data))
            probe.verify()
            image = Image.open(BytesIO(data)).convert("RGB")
        except (UnidentifiedImageError, OSError, SyntaxError) as exc:
            raise HTTPException(status_code=400, detail="Yüklenen dosya geçerli bir görüntü değil.") from exc

    today = datetime.utcnow().strftime("%Y%m%d")
    target_dir = settings.upload_dir / today
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_suffix = ".jpg" if is_dicom else suffix
    filename = f"{_safe_name(file.filename or 'upload')}-{digest[:12]}{stored_suffix}"
    target_path = target_dir / filename
    if is_dicom:
        image.save(target_path, format="JPEG", quality=92)
    else:
        target_path.write_bytes(bytes(data))

    return SavedImage(
        original_name=file.filename or filename,
        stored_path=target_path,
        sha256=digest,
        content_type=file.content_type or ("application/dicom" if is_dicom else "application/octet-stream"),
        image=image,
        size_bytes=len(data),
    )
