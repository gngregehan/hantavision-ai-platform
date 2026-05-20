import os
from pathlib import Path


class Settings:
    api_title = os.getenv("API_TITLE", "HantaVision AI Clinical Imaging API")
    secret_key = os.getenv("SECRET_KEY", "change-this-secret-before-production")
    database_url = os.getenv("DATABASE_URL", "sqlite:///./storage/hantavision.db")
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./storage/uploads"))
    max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "12"))
    access_token_minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "720"))
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]
    admin_email = os.getenv("ADMIN_EMAIL", "admin@hantavision.local")
    admin_password = os.getenv("ADMIN_PASSWORD", "ChangeMe!2026")
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff",
    }


settings = Settings()
