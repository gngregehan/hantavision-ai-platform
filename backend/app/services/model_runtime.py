from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ..config import settings


class ModelUnavailableError(RuntimeError):
    """Raised when production inference is requested before a validated model exists."""


class ValidatedModelRuntime:
    def __init__(self, manifest_path: Path | None = None) -> None:
        self.manifest_path = manifest_path or settings.model_manifest_path
        self._manifest: dict[str, Any] | None = None
        self._load_error: str | None = None
        self._torch_model: Any | None = None
        self._torch_device: Any | None = None

    def status(self) -> dict[str, Any]:
        manifest = self._read_manifest()
        if not manifest:
            return {
                "ready": False,
                "mode": "strict-validated-model",
                "reason": (
                    "Validated model manifest is not installed. HantaVision will not generate "
                    "medical risk predictions from demo heuristics."
                ),
                "manifestPath": str(self.manifest_path),
                "requiredArtifacts": ["model_manifest.json", "best.pt or approved inference artifact"],
                "strictModelMode": settings.strict_model_mode,
                "metrics": None,
            }

        artifact_path = self._artifact_path(manifest)
        validation = manifest.get("validation") or {}
        approved = bool(validation.get("approvedForUse"))
        if not artifact_path.exists():
            return {
                "ready": False,
                "mode": "strict-validated-model",
                "reason": f"Model artifact is missing: {artifact_path}",
                "manifestPath": str(self.manifest_path),
                "artifactPath": str(artifact_path),
                "strictModelMode": settings.strict_model_mode,
                "manifest": self._public_manifest(manifest),
                "metrics": validation.get("metrics"),
            }
        if not approved:
            return {
                "ready": False,
                "mode": "strict-validated-model",
                "reason": "Manifest exists, but validation.approvedForUse is not true.",
                "manifestPath": str(self.manifest_path),
                "artifactPath": str(artifact_path),
                "strictModelMode": settings.strict_model_mode,
                "manifest": self._public_manifest(manifest),
                "metrics": validation.get("metrics"),
            }
        if manifest.get("runtime") == "torchvision" and not self._torch_available():
            return {
                "ready": False,
                "mode": "strict-validated-model",
                "reason": "Torch/Torchvision runtime is not installed in this API environment.",
                "manifestPath": str(self.manifest_path),
                "artifactPath": str(artifact_path),
                "strictModelMode": settings.strict_model_mode,
                "manifest": self._public_manifest(manifest),
                "metrics": validation.get("metrics"),
            }

        return {
            "ready": True,
            "mode": "validated-inference",
            "reason": "Validated model artifact is installed and approved for research inference.",
            "manifestPath": str(self.manifest_path),
            "artifactPath": str(artifact_path),
            "strictModelMode": settings.strict_model_mode,
            "manifest": self._public_manifest(manifest),
            "metrics": validation.get("metrics"),
        }

    def predict(self, image: Image.Image, image_type: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
        status = self.status()
        if not status["ready"]:
            raise ModelUnavailableError(status["reason"])

        manifest = self._read_manifest()
        if not manifest:
            raise ModelUnavailableError("Validated model manifest is not installed.")

        runtime = manifest.get("runtime")
        if runtime != "torchvision":
            raise ModelUnavailableError(f"Unsupported model runtime: {runtime!r}")

        probabilities = self._predict_torchvision(image, manifest)
        classes = list(manifest.get("classes") or [])
        if not classes:
            raise ModelUnavailableError("Model manifest does not define classes.")

        max_index = int(np.argmax(probabilities))
        predicted_class = classes[max_index]
        confidence = float(probabilities[max_index])
        positive_probability = self._positive_probability(classes, probabilities)
        risk_level = self._risk_from_probability(positive_probability)
        validation = manifest.get("validation") or {}

        if positive_probability >= 0.5:
            label = "Hantavirus-positive visual signal detected"
        else:
            label = "No hantavirus-positive visual signal detected"

        return {
            "hantavirusResult": label,
            "confidence": round(confidence, 4),
            "riskLevel": risk_level,
            "reliabilityScore": round(min(confidence, metrics.get("qualityScore", 0.0)), 4),
            "explanation": (
                f"Validated {manifest.get('architecture', 'image')} model predicted class "
                f"'{predicted_class}' with {confidence:.1%} confidence. Positive-class probability "
                f"is {positive_probability:.1%}. This is research decision support, not a diagnosis."
            ),
            "attention": {
                "method": manifest.get("explainability", "Grad-CAM not configured for this artifact"),
                "regions": manifest.get("staticAttentionRegions", []),
                "heatmap": manifest.get("staticHeatmap", []),
            },
            "modelStack": [
                {"stage": "Image type routing", "model": "quality-aware router", "runtime": "active"},
                {
                    "stage": "Hantavirus classifier",
                    "model": manifest.get("architecture", "validated artifact"),
                    "runtime": "validated",
                },
                {"stage": "Validation metrics", "model": "held-out test report", "runtime": "loaded"},
            ],
            "runtime": {
                "architecture": manifest.get("architecture"),
                "classes": classes,
                "predictedClass": predicted_class,
                "positiveProbability": round(positive_probability, 4),
                "validationMetrics": validation.get("metrics"),
                "imageRoute": image_type.get("route"),
            },
        }

    def _read_manifest(self) -> dict[str, Any] | None:
        if self._manifest is not None:
            return self._manifest
        if not self.manifest_path.exists():
            return None
        try:
            self._manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            self._load_error = None
        except (OSError, json.JSONDecodeError) as exc:
            self._load_error = str(exc)
            self._manifest = None
        return self._manifest

    def _artifact_path(self, manifest: dict[str, Any]) -> Path:
        raw_path = manifest.get("artifactPath") or manifest.get("weightsPath") or "best.pt"
        artifact_path = Path(raw_path)
        if artifact_path.is_absolute():
            return artifact_path
        return (self.manifest_path.parent / artifact_path).resolve()

    def _public_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        keys = [
            "modelId",
            "architecture",
            "runtime",
            "classes",
            "imageSize",
            "datasetScope",
            "createdAt",
            "trainingRunId",
            "validation",
        ]
        return {key: manifest.get(key) for key in keys if key in manifest}

    def _torch_available(self) -> bool:
        try:
            import torch  # noqa: F401
            import torchvision  # noqa: F401
        except Exception:
            return False
        return True

    def _predict_torchvision(self, image: Image.Image, manifest: dict[str, Any]) -> np.ndarray:
        import torch
        from torchvision import transforms

        model = self._load_torch_model(manifest)
        image_size = int(manifest.get("imageSize", 224))
        transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        tensor = transform(image.convert("RGB")).unsqueeze(0).to(self._torch_device)
        with torch.no_grad():
            logits = model(tensor)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()[0]
        return probabilities.astype(float)

    def _load_torch_model(self, manifest: dict[str, Any]) -> Any:
        if self._torch_model is not None:
            return self._torch_model

        import torch
        from torch import nn
        from torchvision import models

        classes = list(manifest.get("classes") or [])
        if not classes:
            raise ModelUnavailableError("Model manifest does not define classes.")
        architecture = str(manifest.get("architecture") or "").lower()
        num_classes = len(classes)

        if architecture == "cnn":
            model = _SmallCNN(num_classes)
        elif architecture == "resnet50":
            model = models.resnet50(weights=None)
            model.fc = nn.Linear(model.fc.in_features, num_classes)
        elif architecture == "efficientnet_b0":
            model = models.efficientnet_b0(weights=None)
            model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        else:
            raise ModelUnavailableError(f"Unsupported torchvision architecture: {architecture}")

        checkpoint = torch.load(self._artifact_path(manifest), map_location="cpu")
        state_dict = checkpoint.get("state_dict", checkpoint)
        model.load_state_dict(state_dict)
        self._torch_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(self._torch_device)
        model.eval()
        self._torch_model = model
        return model

    def _positive_probability(self, classes: list[str], probabilities: np.ndarray) -> float:
        positive_tokens = ("infected", "positive", "hantavirus")
        negative_tokens = ("non", "negative", "control", "healthy")
        positive_indexes = [
            index
            for index, label in enumerate(classes)
            if any(token in label.lower() for token in positive_tokens)
            and not any(token in label.lower() for token in negative_tokens)
        ]
        if not positive_indexes and len(classes) == 2:
            positive_indexes = [1]
        return float(sum(probabilities[index] for index in positive_indexes))

    def _risk_from_probability(self, probability: float) -> str:
        if probability >= 0.85:
            return "critical"
        if probability >= 0.65:
            return "high"
        if probability >= 0.4:
            return "medium"
        return "low"


class _SmallCNN:
    def __new__(cls, num_classes: int) -> Any:
        import torch
        from torch import nn

        class SmallCNN(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.features = nn.Sequential(
                    nn.Conv2d(3, 32, kernel_size=3, padding=1),
                    nn.BatchNorm2d(32),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                    nn.Conv2d(32, 64, kernel_size=3, padding=1),
                    nn.BatchNorm2d(64),
                    nn.ReLU(inplace=True),
                    nn.MaxPool2d(2),
                    nn.Conv2d(64, 128, kernel_size=3, padding=1),
                    nn.BatchNorm2d(128),
                    nn.ReLU(inplace=True),
                    nn.AdaptiveAvgPool2d((1, 1)),
                )
                self.classifier = nn.Linear(128, num_classes)

            def forward(self, x: torch.Tensor) -> torch.Tensor:
                x = self.features(x)
                x = torch.flatten(x, 1)
                return self.classifier(x)

        return SmallCNN()


model_runtime = ValidatedModelRuntime()
