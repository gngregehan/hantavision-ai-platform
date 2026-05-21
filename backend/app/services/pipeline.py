from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from .model_runtime import ModelUnavailableError, model_runtime

MEDICAL_NOTICE = (
    "Bu sistem kesin tıbbi tanı koymaz. Çıktılar yalnızca araştırma/eğitim amaçlı "
    "ön değerlendirme desteğidir ve uzman hekim tarafından yorumlanmalıdır."
)


class HantavirusPipeline:
    model_stack = [
        {"stage": "Görüntü alımı ve kalite kontrol", "model": "çözünürlük/kontrast/netlik kapıları", "runtime": "aktif"},
        {"stage": "Görüntü türü yönlendirme", "model": "kalite duyarlı modalite yönlendirici", "runtime": "aktif"},
        {"stage": "Hantavirüs sınıflandırma", "model": "doğrulanmış CNN/ResNet/EfficientNet artefact", "runtime": "gerekli"},
        {"stage": "Açıklanabilirlik", "model": "artefact destekli Grad-CAM/dikkat verisi", "runtime": "gerekli"},
    ]

    def analyze(self, image: Image.Image, original_filename: str) -> dict[str, Any]:
        metrics = self._extract_metrics(image)
        warnings = self._quality_warnings(metrics)
        image_type = self._classify_type(metrics, original_filename)

        try:
            prediction = model_runtime.predict(image, image_type, metrics)
        except ModelUnavailableError as exc:
            prediction = self._pending_prediction(str(exc), image_type, metrics)
            warnings.append(
                "Görüntü kabul edildi; doğrulanmış hantavirüs modeli henüz kurulu olmadığı için tıbbi risk tahmini üretilmedi."
            )

        reliability = self._clamp(
            prediction["reliabilityScore"] * 0.55 + metrics["qualityScore"] * 0.3 + image_type["confidence"] * 0.15
        )
        if warnings:
            reliability = self._clamp(reliability - min(0.18, 0.06 * len(warnings)))

        return {
            "fileName": original_filename,
            "imageType": image_type["label"],
            "imageTypeStatement": image_type["statement"],
            "hantavirusResult": prediction["hantavirusResult"],
            "confidence": prediction["confidence"],
            "riskLevel": prediction["riskLevel"],
            "reliabilityScore": round(reliability, 4),
            "qualityScore": round(metrics["qualityScore"], 4),
            "explanation": prediction["explanation"],
            "medicalNotice": MEDICAL_NOTICE,
            "warnings": warnings,
            "attention": prediction["attention"],
            "metrics": {**metrics, "runtime": prediction.get("runtime", {})},
            "modelStack": prediction.get("modelStack") or self.model_stack,
        }

    def status(self) -> dict[str, Any]:
        runtime_status = model_runtime.status()
        return {
            "pipeline": "HantaVision profesyonel doğrulanmış çıkarım hattı",
            "modelStack": self.model_stack,
            "runtime": runtime_status,
            "acceptsUploads": True,
            "acceptsDiagnosticPredictions": bool(runtime_status["ready"]),
            "predictionPolicy": (
                "Geçerli görüntüler kabul edilir ve kalite/mod yönlendirme kaydı oluşturulur. "
                "Tıbbi risk tahmini için doğrulanmış model artefact, ayrılmış test metrikleri ve onay bilgisi gerekir."
            ),
        }

    def performance_card(self) -> dict[str, Any]:
        runtime_status = model_runtime.status()
        metrics = runtime_status.get("metrics")
        manifest = runtime_status.get("manifest") or {}
        return {
            "registryStatus": runtime_status["reason"],
            "lastValidationRun": manifest.get("validation", {}).get("validatedAt"),
            "datasets": manifest.get("datasetScope", []),
            "metrics": metrics or {"accuracy": None, "precision": None, "recall": None, "f1": None, "auroc": None},
            "confusionMatrix": (metrics or {}).get("confusionMatrix", []),
            "rocCurve": (metrics or {}).get("rocCurve", []),
            "modelStack": self.model_stack,
            "runtime": runtime_status,
        }

    def _extract_metrics(self, image: Image.Image) -> dict[str, Any]:
        resized = image.convert("RGB")
        resized.thumbnail((512, 512))
        arr = np.asarray(resized).astype(np.float32) / 255.0
        gray = arr.mean(axis=2)
        width, height = image.size
        gx_values = np.abs(np.diff(gray, axis=1))
        gy_values = np.abs(np.diff(gray, axis=0))
        gx = float(gx_values.mean()) if gx_values.size else 0.0
        gy = float(gy_values.mean()) if gy_values.size else 0.0
        edge_density = float((gx + gy) / 2)
        gradient_variance = float((np.var(gy_values) if gy_values.size else 0.0) + (np.var(gx_values) if gx_values.size else 0.0))
        brightness = float(gray.mean())
        contrast = float(gray.std())
        saturation = float(np.mean(arr.max(axis=2) - arr.min(axis=2)))
        rgb_spread = float(np.mean(np.abs(arr[:, :, 0] - arr[:, :, 1]) + np.abs(arr[:, :, 1] - arr[:, :, 2])))
        resolution_score = self._clamp((min(width, height) - 160) / 640)
        contrast_score = self._clamp(contrast / 0.22)
        focus_score = self._clamp(gradient_variance / 0.006)
        exposure_penalty = 0.2 if brightness < 0.1 or brightness > 0.94 else 0.0
        quality_score = self._clamp(resolution_score * 0.35 + contrast_score * 0.35 + focus_score * 0.3 - exposure_penalty)
        return {
            "width": width,
            "height": height,
            "aspectRatio": round(width / max(height, 1), 3),
            "brightness": round(brightness, 4),
            "contrast": round(contrast, 4),
            "edgeDensity": round(edge_density, 4),
            "gradientVariance": round(gradient_variance, 5),
            "saturation": round(saturation, 4),
            "grayProbability": round(1 - self._clamp(rgb_spread / 0.16), 4),
            "qualityScore": round(quality_score, 4),
        }

    def _quality_warnings(self, metrics: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        if min(metrics["width"], metrics["height"]) < 256:
            warnings.append("Görüntü çözünürlüğü düşük; güvenilirlik azalabilir.")
        if metrics["contrast"] < 0.065:
            warnings.append("Görüntü kontrastı düşük; medikal örüntüler ayrışmayabilir.")
        if metrics["gradientVariance"] < 0.001:
            warnings.append("Görüntü bulanık veya odak dışı olabilir.")
        if metrics["brightness"] < 0.1 or metrics["brightness"] > 0.94:
            warnings.append("Pozlama tercih edilen aralığın dışında.")
        return warnings

    def _classify_type(self, metrics: dict[str, Any], filename: str) -> dict[str, Any]:
        name = filename.lower()
        if metrics["qualityScore"] < 0.22:
            return {
                "label": "Bilinmeyen Görüntü",
                "statement": "Görüntü kalitesi doğrulanmış çıkarım rotası için yeterli değil.",
                "route": "expert_review",
                "confidence": 0.42,
            }
        if any(token in name for token in ["xray", "x-ray", "rontgen", "chest", "lung", ".dcm", ".dicom"]):
            return {
                "label": "Akciğer Röntgeni",
                "statement": "Görüntü akciğer radyografisi rotasına yönlendirildi.",
                "route": "medical_imaging",
                "confidence": 0.82,
            }
        if any(token in name for token in ["rodent", "mouse", "rat", "fare", "kemirgen"]):
            return {
                "label": "Kemirgen Fotoğrafı",
                "statement": "Görüntü taşıyıcı konak görsel değerlendirme rotasına yönlendirildi.",
                "route": "carrier_detection",
                "confidence": 0.72,
            }
        if any(token in name for token in ["micro", "mikroskop", "cell", "tissue", "doku"]) or (
            metrics["saturation"] > 0.18 and metrics["edgeDensity"] > 0.05
        ):
            return {
                "label": "Mikroskop Görüntüsü",
                "statement": "Görüntü mikroskop analizi rotasına yönlendirildi.",
                "route": "microscopy",
                "confidence": 0.72,
            }
        if any(token in name for token in ["lab", "assay", "culture", "serum", "plate"]) or (
            metrics["saturation"] > 0.09 and metrics["brightness"] > 0.42 and metrics["edgeDensity"] < 0.07
        ):
            return {
                "label": "Laboratuvar Görüntüsü",
                "statement": "Görüntü laboratuvar görsel analizi rotasına yönlendirildi.",
                "route": "laboratory",
                "confidence": 0.66,
            }
        if metrics["grayProbability"] > 0.72 and metrics["contrast"] > 0.08:
            return {
                "label": "Akciğer Röntgeni",
                "statement": "Gri ton dağılımı ve kontrast röntgen rotasıyla eşleşti.",
                "route": "medical_imaging",
                "confidence": 0.64,
            }
        return {
            "label": "Bilinmeyen Görüntü",
            "statement": "Doğrulanmış çıkarım öncesinde görüntü uzman incelemesi gerektirir.",
            "route": "expert_review",
            "confidence": 0.58,
        }

    def _pending_prediction(self, reason: str, image_type: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "hantavirusResult": "Görüntü kabul edildi; doğrulanmış model bekleniyor",
            "confidence": 0.0,
            "riskLevel": "Model bekleniyor",
            "reliabilityScore": 0.0,
            "explanation": (
                "Görüntü başarıyla yüklendi ve kalite/görüntü türü kontrollerinden geçirildi. "
                "Doğrulanmış CNN/ResNet/EfficientNet artefact kurulmadığı için sistem tıbbi risk sonucu üretmedi."
            ),
            "attention": {
                "method": "Önizleme ısı haritası; gerçek Grad-CAM için doğrulanmış model gerekir.",
                "regions": self._preview_regions(image_type.get("route")),
                "heatmap": [],
            },
            "modelStack": [
                {"stage": "Görüntü alımı", "model": "güvenli dosya doğrulama", "runtime": "tamamlandı"},
                {"stage": "Kalite ölçümü", "model": "çözünürlük/kontrast/netlik ölçümü", "runtime": "tamamlandı"},
                {"stage": "Model kapısı", "model": "doğrulanmış artefact kontrolü", "runtime": "model bekleniyor"},
            ],
            "runtime": {
                "mode": "model-bekleniyor",
                "reason": reason,
                "imageRoute": image_type.get("route"),
                "qualityScore": metrics.get("qualityScore"),
            },
        }

    def _preview_regions(self, route: str | None) -> list[dict[str, Any]]:
        if route == "medical_imaging":
            return [
                {"x": 22, "y": 24, "w": 24, "h": 50, "label": "Sol pulmoner alan", "score": 0.0},
                {"x": 55, "y": 24, "w": 24, "h": 50, "label": "Sağ pulmoner alan", "score": 0.0},
            ]
        if route == "carrier_detection":
            return [{"x": 22, "y": 18, "w": 56, "h": 62, "label": "Kemirgen aday alanı", "score": 0.0}]
        if route in {"microscopy", "laboratory"}:
            return [
                {"x": 16, "y": 18, "w": 25, "h": 25, "label": "Doku/örnek yoğunluğu", "score": 0.0},
                {"x": 54, "y": 34, "w": 28, "h": 25, "label": "Tekstür değişimi", "score": 0.0},
            ]
        return [{"x": 34, "y": 28, "w": 32, "h": 34, "label": "Uzman inceleme alanı", "score": 0.0}]

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 0.98) -> float:
        return max(minimum, min(maximum, float(value)))


pipeline = HantavirusPipeline()
