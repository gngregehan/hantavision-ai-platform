from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
import numpy as np
from PIL import Image

from .model_runtime import ModelUnavailableError, model_runtime

MEDICAL_NOTICE = (
    "This system is not a definitive medical diagnosis. Outputs are research/education "
    "decision support only and must be reviewed by qualified clinicians."
)


class HantavirusPipeline:
    model_stack = [
        {"stage": "Image intake and quality control", "model": "resolution/contrast/focus gates", "runtime": "active"},
        {"stage": "Image type routing", "model": "quality-aware modality router", "runtime": "active"},
        {"stage": "Hantavirus classification", "model": "validated CNN/ResNet/EfficientNet artifact", "runtime": "required"},
        {"stage": "Explainability", "model": "artifact-provided Grad-CAM/attention metadata", "runtime": "required"},
    ]

    def analyze(self, image: Image.Image, original_filename: str) -> dict[str, Any]:
        metrics = self._extract_metrics(image)
        warnings = self._quality_warnings(metrics)
        image_type = self._classify_type(metrics, original_filename)

        try:
            prediction = model_runtime.predict(image, image_type, metrics)
        except ModelUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"{exc} Train and install a validated hantavirus model artifact before enabling "
                    "user-facing diagnostic predictions."
                ),
            ) from exc

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
            "pipeline": "HantaVision strict professional inference",
            "modelStack": self.model_stack,
            "runtime": runtime_status,
            "acceptsUploads": bool(runtime_status["ready"]),
            "predictionPolicy": (
                "No placeholder medical predictions are emitted. Upload analysis requires a validated "
                "model artifact with held-out metrics and approval metadata."
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
            warnings.append("Image resolution is low; inference reliability may decrease.")
        if metrics["contrast"] < 0.065:
            warnings.append("Image contrast is low; medical features may not be separable.")
        if metrics["gradientVariance"] < 0.001:
            warnings.append("Image may be blurred or out of focus.")
        if metrics["brightness"] < 0.1 or metrics["brightness"] > 0.94:
            warnings.append("Exposure is outside the preferred range.")
        return warnings

    def _classify_type(self, metrics: dict[str, Any], filename: str) -> dict[str, Any]:
        name = filename.lower()
        if metrics["qualityScore"] < 0.22:
            return {
                "label": "Unknown image",
                "statement": "Image quality is not sufficient for the validated inference route.",
                "route": "expert_review",
                "confidence": 0.42,
            }
        if any(token in name for token in ["xray", "x-ray", "rontgen", "chest", "lung", ".dcm", ".dicom"]):
            return {
                "label": "Chest X-ray",
                "statement": "The image was routed as a chest radiograph.",
                "route": "medical_imaging",
                "confidence": 0.82,
            }
        if any(token in name for token in ["rodent", "mouse", "rat", "fare", "kemirgen"]):
            return {
                "label": "Rodent photograph",
                "statement": "The image was routed to carrier-host visual assessment.",
                "route": "carrier_detection",
                "confidence": 0.72,
            }
        if any(token in name for token in ["micro", "mikroskop", "cell", "tissue", "doku"]) or (
            metrics["saturation"] > 0.18 and metrics["edgeDensity"] > 0.05
        ):
            return {
                "label": "Microscopy image",
                "statement": "The image was routed to microscopy analysis.",
                "route": "microscopy",
                "confidence": 0.72,
            }
        if any(token in name for token in ["lab", "assay", "culture", "serum", "plate"]) or (
            metrics["saturation"] > 0.09 and metrics["brightness"] > 0.42 and metrics["edgeDensity"] < 0.07
        ):
            return {
                "label": "Laboratory image",
                "statement": "The image was routed to laboratory visual analysis.",
                "route": "laboratory",
                "confidence": 0.66,
            }
        if metrics["grayProbability"] > 0.72 and metrics["contrast"] > 0.08:
            return {
                "label": "Chest X-ray",
                "statement": "Grayscale distribution and contrast matched the radiograph route.",
                "route": "medical_imaging",
                "confidence": 0.64,
            }
        return {
            "label": "Unknown image",
            "statement": "The image requires expert review before validated inference.",
            "route": "expert_review",
            "confidence": 0.58,
        }

    @staticmethod
    def _clamp(value: float, minimum: float = 0.0, maximum: float = 0.98) -> float:
        return max(minimum, min(maximum, float(value)))


pipeline = HantavirusPipeline()
