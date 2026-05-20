from __future__ import annotations

from datetime import datetime
from typing import Iterable


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
    safe = _clean(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return safe[:120]


def _content_stream(lines: Iterable[str]) -> bytes:
    commands = ["BT", "/F1 12 Tf", "50 790 Td", "16 TL"]
    for line in lines:
        commands.append(f"({_escape_pdf(line)}) Tj")
        commands.append("T*")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def build_analysis_pdf(analysis, user) -> bytes:
    lines = [
        "HantaVision AI - Medical Imaging Analysis Report",
        f"Report date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        f"Patient/User: {user.full_name}",
        f"File: {analysis.file_name}",
        f"Image type: {analysis.image_type}",
        f"Hantavirus analysis: {analysis.hantavirus_result}",
        f"Confidence: {round(analysis.confidence * 100, 1)}%",
        f"Reliability: {round(analysis.reliability_score * 100, 1)}%",
        f"Quality score: {round(analysis.quality_score * 100, 1)}%",
        f"Risk level: {analysis.risk_level}",
        "",
        "Explanation:",
        analysis.explanation,
        "",
        "Warnings:",
        *(analysis.warnings or ["No quality warnings."]),
        "",
        analysis.medical_notice,
    ]
    stream = _content_stream(lines)
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
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
