from __future__ import annotations

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db, init_db
from .models import Analysis, User
from .security import create_access_token, decode_access_token, hash_password, oauth2_scheme, verify_password
from .services.pdf import build_analysis_pdf
from .services.pipeline import pipeline
from .services.storage import save_image_upload

app = FastAPI(
    title=settings.api_title,
    version="1.0.0",
    description="AI-assisted Hantavirus medical and biological image triage platform API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterPayload(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginPayload(BaseModel):
    email: str
    password: str


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "fullName": user.full_name,
        "email": user.email,
        "role": user.role,
        "createdAt": user.created_at.isoformat(),
    }


def serialize_analysis(analysis: Analysis) -> dict:
    return {
        "id": analysis.id,
        "fileName": analysis.file_name,
        "sha256": analysis.sha256,
        "contentType": analysis.content_type,
        "imageType": analysis.image_type,
        "imageTypeStatement": analysis.image_type_statement,
        "hantavirusResult": analysis.hantavirus_result,
        "confidence": analysis.confidence,
        "riskLevel": analysis.risk_level,
        "reliabilityScore": analysis.reliability_score,
        "qualityScore": analysis.quality_score,
        "explanation": analysis.explanation,
        "medicalNotice": analysis.medical_notice,
        "warnings": analysis.warnings,
        "attention": analysis.attention,
        "metrics": analysis.metrics,
        "modelStack": analysis.model_stack,
        "createdAt": analysis.created_at.isoformat(),
    }


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    claims = decode_access_token(token)
    user_id = claims.get("sub")
    user = db.execute(select(User).where(User.id == int(user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin yetkisi gerekir.")
    return current_user


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": settings.api_title}


@app.post("/api/auth/register")
def register(payload: RegisterPayload, db: Session = Depends(get_db)) -> dict:
    email = payload.email.strip().lower()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Bu e-posta adresi zaten kayıtlı.")
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role="clinician",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"accessToken": token, "tokenType": "bearer", "user": serialize_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict:
    user = db.execute(select(User).where(User.email == payload.email.strip().lower())).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-posta veya parola hatalı.")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"accessToken": token, "tokenType": "bearer", "user": serialize_user(user)}


@app.get("/api/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return serialize_user(current_user)


@app.post("/api/analyses")
async def create_analysis(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    saved = await save_image_upload(file)
    result = pipeline.analyze(saved.image, saved.original_name)
    analysis = Analysis(
        owner_id=current_user.id,
        file_name=saved.original_name,
        stored_path=str(saved.stored_path),
        sha256=saved.sha256,
        content_type=saved.content_type,
        image_type=result["imageType"],
        image_type_statement=result["imageTypeStatement"],
        hantavirus_result=result["hantavirusResult"],
        confidence=result["confidence"],
        risk_level=result["riskLevel"],
        reliability_score=result["reliabilityScore"],
        quality_score=result["qualityScore"],
        explanation=result["explanation"],
        medical_notice=result["medicalNotice"],
        warnings=result["warnings"],
        attention=result["attention"],
        metrics=result["metrics"],
        model_stack=result["modelStack"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return serialize_analysis(analysis)


@app.get("/api/analyses")
def list_analyses(
    include_all: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Analysis).order_by(desc(Analysis.created_at)).limit(50)
    if not include_all or current_user.role != "admin":
        query = query.where(Analysis.owner_id == current_user.id)
    return [serialize_analysis(item) for item in db.execute(query).scalars().all()]


@app.get("/api/analyses/{analysis_id}")
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    if analysis.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bu rapora erişim yetkiniz yok.")
    return serialize_analysis(analysis)


@app.get("/api/analyses/{analysis_id}/report.pdf")
def get_report_pdf(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
    if analysis.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bu rapora erişim yetkiniz yok.")
    pdf = build_analysis_pdf(analysis, current_user)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="hantavision-report-{analysis.id}.pdf"'},
    )


@app.get("/api/model-stack")
def model_stack() -> dict:
    return {"modelStack": pipeline.model_stack}


@app.get("/api/admin/model-performance")
def model_performance(_: User = Depends(require_admin)) -> dict:
    return pipeline.performance_card()


@app.get("/api/admin/overview")
def admin_overview(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    total = db.execute(select(func.count(Analysis.id))).scalar_one()
    high_risk = db.execute(select(func.count(Analysis.id)).where(Analysis.risk_level == "yüksek")).scalar_one()
    uncertain = db.execute(
        select(func.count(Analysis.id)).where(Analysis.hantavirus_result == "Belirsiz / uzman incelemesi gerekli")
    ).scalar_one()
    users = db.execute(select(func.count(User.id))).scalar_one()
    return {
        "totalAnalyses": total,
        "highRisk": high_risk,
        "expertReview": uncertain,
        "users": users,
    }
