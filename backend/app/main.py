from __future__ import annotations

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .config import settings
from .datastore import pdf_analysis, pdf_user, public_user, store
from .research_registry import assistant_reply, evidence_payload
from .security import create_access_token, decode_access_token, oauth2_scheme, verify_password
from .services.pdf import build_analysis_pdf
from .services.pipeline import pipeline
from .services.storage import save_image_upload

app = FastAPI(
    title=settings.api_title,
    version="1.0.0",
    description="AI destekli hantavirüs medikal ve biyolojik görüntü ön değerlendirme platformu API'si.",
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


class AssistantPayload(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    context: dict | None = None


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    claims = decode_access_token(token)
    user_id = claims.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Oturum bilgisi geçersiz.")
    user = store.get_user_by_id(str(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı bulunamadı.")
    return user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin yetkisi gerekir.")
    return current_user


@app.on_event("startup")
def startup_event() -> None:
    store.init()


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": settings.api_title,
        "database": store.backend,
        "modelReady": pipeline.status()["acceptsDiagnosticPredictions"],
    }


@app.post("/api/auth/register")
def register(payload: RegisterPayload) -> dict:
    email = payload.email.strip().lower()
    if store.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Bu e-posta adresi zaten kayitli.")
    user = store.create_user(payload.full_name, email, payload.password, role="clinician")
    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return {"accessToken": token, "tokenType": "bearer", "user": public_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginPayload) -> dict:
    user = store.get_user_by_email(payload.email.strip().lower())
    if not user or not verify_password(payload.password, user["passwordHash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-posta veya parola hatali.")
    token = create_access_token({"sub": str(user["id"]), "role": user["role"]})
    return {"accessToken": token, "tokenType": "bearer", "user": public_user(user)}


@app.get("/api/me")
def me(current_user: dict = Depends(get_current_user)) -> dict:
    return public_user(current_user)


@app.post("/api/analyses")
async def create_analysis(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
) -> dict:
    saved = await save_image_upload(file)
    result = pipeline.analyze(saved.image, saved.original_name)
    return store.create_analysis(str(current_user["id"]), saved, result)


@app.get("/api/analyses")
def list_analyses(
    include_all: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    return store.list_analyses(current_user, include_all)


@app.get("/api/analyses/{analysis_id}")
def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    analysis = store.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadi.")
    if analysis["ownerId"] != str(current_user["id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu rapora erisim yetkiniz yok.")
    return analysis


@app.get("/api/analyses/{analysis_id}/report.pdf")
def get_report_pdf(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
) -> Response:
    analysis = store.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analiz bulunamadi.")
    if analysis["ownerId"] != str(current_user["id"]) and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Bu rapora erisim yetkiniz yok.")
    pdf = build_analysis_pdf(pdf_analysis(analysis), pdf_user(current_user))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="hantavision-report-{analysis["id"]}.pdf"'},
    )


@app.get("/api/model-stack")
def model_stack() -> dict:
    return {"modelStack": pipeline.model_stack}


@app.get("/api/model-status")
def model_status() -> dict:
    return pipeline.status()


@app.get("/api/research/evidence")
def research_evidence() -> dict:
    return evidence_payload()


@app.post("/api/assistant/chat")
def assistant_chat(payload: AssistantPayload) -> dict:
    return assistant_reply(payload.message, payload.context)


@app.get("/api/admin/model-performance")
def model_performance(_: dict = Depends(require_admin)) -> dict:
    evidence = evidence_payload()
    performance = pipeline.performance_card()
    return {
        "registryStatus": performance["registryStatus"],
        "lastValidationRun": performance["lastValidationRun"],
        "datasets": evidence["datasets"] + evidence["referenceMedia"],
        "models": evidence["models"],
        "metrics": performance["metrics"],
        "confusionMatrix": performance["confusionMatrix"],
        "rocCurve": performance["rocCurve"],
        "validationProtocol": evidence["validationProtocol"],
        "modelStack": pipeline.model_stack,
        "runtime": performance["runtime"],
    }


@app.get("/api/admin/overview")
def admin_overview(_: dict = Depends(require_admin)) -> dict:
    return store.overview()
