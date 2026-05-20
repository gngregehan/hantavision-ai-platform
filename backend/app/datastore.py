from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from sqlalchemy import desc, func, select

from .config import settings
from .database import SessionLocal, init_db
from .models import Analysis, User
from .security import hash_password


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return _now().isoformat()


def _firebase_credentials_available() -> bool:
    return bool(settings.firebase_service_account_json or settings.firebase_service_account_path)


def _decode_service_account(raw: str) -> dict[str, Any]:
    value = raw.strip()
    if value.startswith("{"):
        return json.loads(value)
    return json.loads(base64.b64decode(value).decode("utf-8"))


def _collection(name: str) -> str:
    return f"{settings.firebase_collection_prefix}{name}"


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(user["id"]),
        "fullName": user["fullName"],
        "email": user["email"],
        "role": user["role"],
        "createdAt": _iso(user.get("createdAt")),
    }


def public_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "id": str(analysis["id"]),
        "ownerId": str(analysis["ownerId"]),
        "fileName": analysis["fileName"],
        "sha256": analysis["sha256"],
        "contentType": analysis["contentType"],
        "imageType": analysis["imageType"],
        "imageTypeStatement": analysis["imageTypeStatement"],
        "hantavirusResult": analysis["hantavirusResult"],
        "confidence": analysis["confidence"],
        "riskLevel": analysis["riskLevel"],
        "reliabilityScore": analysis["reliabilityScore"],
        "qualityScore": analysis["qualityScore"],
        "explanation": analysis["explanation"],
        "medicalNotice": analysis["medicalNotice"],
        "warnings": analysis.get("warnings", []),
        "attention": analysis.get("attention", {}),
        "metrics": analysis.get("metrics", {}),
        "modelStack": analysis.get("modelStack", []),
        "createdAt": _iso(analysis.get("createdAt")),
    }
    if analysis.get("storedPath"):
        payload["storedPath"] = analysis["storedPath"]
    return payload


def pdf_user(user: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(full_name=user["fullName"], email=user["email"], role=user["role"])


def pdf_analysis(analysis: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(
        id=analysis["id"],
        file_name=analysis["fileName"],
        stored_path=analysis.get("storedPath"),
        image_type=analysis["imageType"],
        hantavirus_result=analysis["hantavirusResult"],
        confidence=analysis["confidence"],
        risk_level=analysis["riskLevel"],
        reliability_score=analysis["reliabilityScore"],
        quality_score=analysis["qualityScore"],
        explanation=analysis["explanation"],
        warnings=analysis.get("warnings", []),
        medical_notice=analysis["medicalNotice"],
    )


class DataStore:
    def __init__(self) -> None:
        self._backend: str | None = None
        self._firebase_db = None

    @property
    def backend(self) -> str:
        if self._backend is None:
            self._backend = self._select_backend()
        return self._backend

    def _select_backend(self) -> str:
        requested = settings.database_backend
        if requested == "firebase":
            return "firebase"
        if requested == "auto" and _firebase_credentials_available():
            return "firebase"
        return "sql"

    def init(self) -> None:
        if self.backend == "firebase":
            self._ensure_admin_user_firebase()
            return
        init_db()

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        if self.backend == "firebase":
            snapshot = self._firebase().collection(_collection("users")).document(user_id).get()
            return self._user_from_snapshot(snapshot) if snapshot.exists else None
        try:
            numeric_id = int(user_id)
        except (TypeError, ValueError):
            return None
        with SessionLocal() as db:
            user = db.get(User, numeric_id)
            return self._user_from_sql(user) if user else None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        normalized = email.strip().lower()
        if self.backend == "firebase":
            snapshot = self._firebase().collection(_collection("users")).document(normalized).get()
            return self._user_from_snapshot(snapshot) if snapshot.exists else None
        with SessionLocal() as db:
            user = db.execute(select(User).where(User.email == normalized)).scalar_one_or_none()
            return self._user_from_sql(user) if user else None

    def create_user(self, full_name: str, email: str, password: str, role: str = "clinician") -> dict[str, Any]:
        normalized = email.strip().lower()
        password_hash = hash_password(password)
        created_at = _now()
        if self.backend == "firebase":
            record = {
                "fullName": full_name.strip(),
                "email": normalized,
                "passwordHash": password_hash,
                "role": role,
                "createdAt": created_at,
            }
            self._firebase().collection(_collection("users")).document(normalized).set(record)
            return {"id": normalized, **record}
        with SessionLocal() as db:
            user = User(
                full_name=full_name.strip(),
                email=normalized,
                password_hash=password_hash,
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return self._user_from_sql(user)

    def create_analysis(self, owner_id: str, saved, result: dict[str, Any]) -> dict[str, Any]:
        created_at = _now()
        if self.backend == "firebase":
            record = self._analysis_record(owner_id, saved, result, created_at)
            ref = self._firebase().collection(_collection("analyses")).document()
            ref.set(record)
            return public_analysis({"id": ref.id, **record})
        with SessionLocal() as db:
            analysis = Analysis(
                owner_id=int(owner_id),
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
            return self._analysis_from_sql(analysis)

    def list_analyses(self, current_user: dict[str, Any], include_all: bool) -> list[dict[str, Any]]:
        if self.backend == "firebase":
            collection = self._firebase().collection(_collection("analyses"))
            if include_all and current_user["role"] == "admin":
                snapshots = collection.order_by("createdAt", direction="DESCENDING").limit(50).stream()
            else:
                snapshots = collection.where("ownerId", "==", str(current_user["id"])).stream()
            records = [public_analysis({"id": item.id, **item.to_dict()}) for item in snapshots]
            return sorted(records, key=lambda item: item["createdAt"], reverse=True)[:50]
        with SessionLocal() as db:
            query = select(Analysis).order_by(desc(Analysis.created_at)).limit(50)
            if not include_all or current_user["role"] != "admin":
                query = query.where(Analysis.owner_id == int(current_user["id"]))
            return [self._analysis_from_sql(item) for item in db.execute(query).scalars().all()]

    def get_analysis(self, analysis_id: str) -> dict[str, Any] | None:
        if self.backend == "firebase":
            snapshot = self._firebase().collection(_collection("analyses")).document(str(analysis_id)).get()
            return public_analysis({"id": snapshot.id, **snapshot.to_dict()}) if snapshot.exists else None
        try:
            numeric_id = int(analysis_id)
        except (TypeError, ValueError):
            return None
        with SessionLocal() as db:
            analysis = db.get(Analysis, numeric_id)
            return self._analysis_from_sql(analysis) if analysis else None

    def overview(self) -> dict[str, int]:
        if self.backend == "firebase":
            analyses = [item.to_dict() for item in self._firebase().collection(_collection("analyses")).stream()]
            users = list(self._firebase().collection(_collection("users")).stream())
            return {
                "totalAnalyses": len(analyses),
                "highRisk": sum(1 for item in analyses if item.get("riskLevel") == "yüksek"),
                "expertReview": sum(1 for item in analyses if item.get("hantavirusResult") == "Belirsiz / uzman incelemesi gerekli"),
                "users": len(users),
            }
        with SessionLocal() as db:
            return {
                "totalAnalyses": db.execute(select(func.count(Analysis.id))).scalar_one(),
                "highRisk": db.execute(select(func.count(Analysis.id)).where(Analysis.risk_level == "yüksek")).scalar_one(),
                "expertReview": db.execute(
                    select(func.count(Analysis.id)).where(
                        Analysis.hantavirus_result == "Belirsiz / uzman incelemesi gerekli"
                    )
                ).scalar_one(),
                "users": db.execute(select(func.count(User.id))).scalar_one(),
            }

    def _firebase(self):
        if self._firebase_db is not None:
            return self._firebase_db
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError as exc:
            raise RuntimeError("firebase-admin paketi kurulu değil.") from exc

        try:
            app = firebase_admin.get_app("hantavision")
        except ValueError:
            options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
            if settings.firebase_service_account_json:
                cred = credentials.Certificate(_decode_service_account(settings.firebase_service_account_json))
            elif settings.firebase_service_account_path:
                cred = credentials.Certificate(str(settings.firebase_service_account_path))
            else:
                cred = credentials.ApplicationDefault()
            app = firebase_admin.initialize_app(cred, options=options, name="hantavision")
        self._firebase_db = firestore.client(app=app)
        return self._firebase_db

    def _ensure_admin_user_firebase(self) -> None:
        if not self.get_user_by_email(settings.admin_email):
            self.create_user(
                full_name="HantaVision Administrator",
                email=settings.admin_email,
                password=settings.admin_password,
                role="admin",
            )

    @staticmethod
    def _analysis_record(owner_id: str, saved, result: dict[str, Any], created_at: datetime) -> dict[str, Any]:
        return {
            "ownerId": str(owner_id),
            "fileName": saved.original_name,
            "storedPath": str(saved.stored_path),
            "sha256": saved.sha256,
            "contentType": saved.content_type,
            "imageType": result["imageType"],
            "imageTypeStatement": result["imageTypeStatement"],
            "hantavirusResult": result["hantavirusResult"],
            "confidence": result["confidence"],
            "riskLevel": result["riskLevel"],
            "reliabilityScore": result["reliabilityScore"],
            "qualityScore": result["qualityScore"],
            "explanation": result["explanation"],
            "medicalNotice": result["medicalNotice"],
            "warnings": result["warnings"],
            "attention": result["attention"],
            "metrics": result["metrics"],
            "modelStack": result["modelStack"],
            "createdAt": created_at,
        }

    @staticmethod
    def _user_from_sql(user: User) -> dict[str, Any]:
        return {
            "id": str(user.id),
            "fullName": user.full_name,
            "email": user.email,
            "passwordHash": user.password_hash,
            "role": user.role,
            "createdAt": user.created_at,
        }

    @staticmethod
    def _user_from_snapshot(snapshot) -> dict[str, Any]:
        data = snapshot.to_dict()
        return {"id": snapshot.id, **data}

    @staticmethod
    def _analysis_from_sql(analysis: Analysis) -> dict[str, Any]:
        return public_analysis(
            {
                "id": str(analysis.id),
                "ownerId": str(analysis.owner_id),
                "fileName": analysis.file_name,
                "storedPath": str(analysis.stored_path),
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
                "createdAt": analysis.created_at,
            }
        )


store = DataStore()
