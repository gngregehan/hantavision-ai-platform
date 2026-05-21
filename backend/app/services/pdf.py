from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Iterable

from PIL import Image, UnidentifiedImageError


def _clean(text: str) -> str:
    replacements = str.maketrans(
        {
            "ı": "i",
            "İ": "I",
            "ğ": "g",
            "Ğ": "G",
            "ü": "u",
            "Ü": "U",
            "ş": "s",
            "Ş": "S",
            "ö": "o",
            "Ö": "O",
            "ç": "c",
            "Ç": "C",
        }
    )
    return text.translate(replacements)


def _escape_pdf(text: str) -> str:
    safe = _clean(str(text)).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return safe[:120]


def _prepare_image(stored_path: str | None) -> dict | None:
    if not stored_path:
        return None
    path = Path(stored_path)
    if not path.exists():
        return None
    try:
        image = Image.open(path).convert("RGB")
        image.thumbnail((220, 160))
    except (UnidentifiedImageError, OSError):
        return None
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=84, optimize=True)
    return {"bytes": buffer.getvalue(), "width": image.width, "height": image.height}


def _content_stream(lines: Iterable[str], image: dict | None) -> bytes:
    commands = []
    if image:
        commands.extend([
            "q",
            f"{image['width']} 0 0 {image['height']} 342 612 cm",
            "/Im1 Do",
            "Q",
        ])
    commands.extend(["BT", "/F1 12 Tf", "50 790 Td", "16 TL"])
    for line in lines:
        commands.append(f"({_escape_pdf(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _image_object(image: dict) -> bytes:
    data = image["bytes"]
    header = (
        f"<< /Type /XObject /Subtype /Image /Width {image['width']} /Height {image['height']} "
        f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(data)} >>\n"
    ).encode("ascii")
    return header + b"stream\n" + data + b"\nendstream"


def build_analysis_pdf(analysis, user) -> bytes:
    image = _prepare_image(getattr(analysis, "stored_path", None))
    lines = [
        "HantaVision AI - AI Medikal Rapor PDF",
        f"Rapor tarihi: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"Hasta/Kullanıcı: {user.full_name}",
        f"Dosya: {analysis.file_name}",
        f"Görüntü türü: {analysis.image_type}",
        f"Hantavirüs analizi: {analysis.hantavirus_result}",
        f"Güven skoru: {round(analysis.confidence * 100, 1)}%",
        f"Güvenilirlik: {round(analysis.reliability_score * 100, 1)}%",
        f"Kalite skoru: {round(analysis.quality_score * 100, 1)}%",
        f"Risk seviyesi: {analysis.risk_level}",
        "Model: EfficientNet / ResNet / CNN + Grad-CAM",
        "",
        "Açıklama:",
        analysis.explanation,
        "",
        "Uyarılar:",
        *(analysis.warnings or ["Kalite uyarısı yok."]),
        "",
        analysis.medical_notice,
    ]
    stream = _content_stream(lines, image)
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    if image:
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
            b"/Resources << /Font << /F1 4 0 R >> /XObject << /Im1 5 0 R >> >> /Contents 6 0 R >>"
        )
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        objects.append(_image_object(image))
        objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
    else:
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        )
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_at = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF".encode(
            "ascii"
        )
    )
    return bytes(pdf)
