from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from tqdm import tqdm


IMAGE_SIZE = 224
CLASSES = ("infected", "non_infected")


class SmallCNN(nn.Module):
    def __init__(self, num_classes: int) -> None:
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


def build_model(arch: str, num_classes: int) -> nn.Module:
    if arch == "cnn":
        return SmallCNN(num_classes)
    if arch == "resnet50":
        model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model
    if arch == "efficientnet_b0":
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        return model
    raise ValueError(f"Unsupported architecture: {arch}")


def build_loaders(data_dir: Path, batch_size: int) -> tuple[dict[str, DataLoader], dict[str, datasets.ImageFolder]]:
    train_tfms = transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(8),
            transforms.ColorJitter(brightness=0.12, contrast=0.12),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    eval_tfms = transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    image_sets = {
        "train": datasets.ImageFolder(data_dir / "train", transform=train_tfms),
        "val": datasets.ImageFolder(data_dir / "val", transform=eval_tfms),
        "test": datasets.ImageFolder(data_dir / "test", transform=eval_tfms),
    }
    loaders = {
        split: DataLoader(dataset, batch_size=batch_size, shuffle=(split == "train"), num_workers=2)
        for split, dataset in image_sets.items()
    }
    return loaders, image_sets


def run_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer | None, device: torch.device) -> float:
    training = optimizer is not None
    model.train(training)
    criterion = nn.CrossEntropyLoss()
    total_loss = 0.0

    for images, labels in tqdm(loader, leave=False):
        images = images.to(device)
        labels = labels.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            logits = model(images)
            loss = criterion(logits, labels)
            if training:
                loss.backward()
                optimizer.step()
        total_loss += float(loss.item()) * images.size(0)

    return total_loss / max(len(loader.dataset), 1)


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, class_names: list[str]) -> dict[str, object]:
    model.eval()
    labels_all: list[int] = []
    preds_all: list[int] = []
    binary_labels_all: list[int] = []
    prob_all: list[float] = []
    positive_index = class_names.index("infected") if "infected" in class_names else min(1, len(class_names) - 1)

    for images, labels in loader:
        images = images.to(device)
        logits = model(images)
        probs = torch.softmax(logits, dim=1)
        preds = torch.argmax(probs, dim=1)
        labels_all.extend(labels.tolist())
        preds_all.extend(preds.cpu().tolist())
        binary_labels_all.extend([1 if int(label) == positive_index else 0 for label in labels.tolist()])
        prob_all.extend(probs[:, positive_index].cpu().tolist())

    metrics = {
        "accuracy": float(accuracy_score(labels_all, preds_all)),
        "precision": float(precision_score(labels_all, preds_all, average="weighted", zero_division=0)),
        "recall": float(recall_score(labels_all, preds_all, average="weighted", zero_division=0)),
        "f1": float(f1_score(labels_all, preds_all, average="weighted", zero_division=0)),
        "confusionMatrix": confusion_matrix(labels_all, preds_all).tolist(),
        "classes": class_names,
    }
    try:
        metrics["auroc"] = float(roc_auc_score(binary_labels_all, prob_all))
    except ValueError:
        metrics["auroc"] = None
    return metrics


def write_model_manifest(
    run_dir: Path,
    args: argparse.Namespace,
    class_names: list[str],
    test_metrics: dict[str, object],
    best_val_f1: float,
) -> dict[str, object]:
    manifest = {
        "modelId": args.model_id,
        "architecture": args.arch,
        "runtime": "torchvision",
        "artifactPath": "best.pt",
        "classes": class_names,
        "imageSize": IMAGE_SIZE,
        "datasetScope": "hantavirus-only curated split",
        "trainingRunId": run_dir.name,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "explainability": "Grad-CAM must be generated and reviewed before clinical-style presentation.",
        "validation": {
            "approvedForUse": bool(args.approve_for_research_use),
            "validatedAt": datetime.now(timezone.utc).date().isoformat(),
            "bestValidationF1": best_val_f1,
            "metrics": test_metrics,
            "approvalNote": (
                "Approved for research inference by command-line flag."
                if args.approve_for_research_use
                else "Not approved yet. Review labels, leakage, confusion matrix, and Grad-CAM before deployment."
            ),
        },
    }
    (run_dir / "model_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if args.publish_dir:
        args.publish_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run_dir / "best.pt", args.publish_dir / "best.pt")
        (args.publish_dir / "model_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Train hantavirus-only CNN/ResNet/EfficientNet models.")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--arch", choices=["cnn", "resnet50", "efficientnet_b0"], required=True)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--out-dir", type=Path, default=Path("ml/runs"))
    parser.add_argument("--model-id", default="hantacell-research-classifier")
    parser.add_argument("--publish-dir", type=Path, help="Optional API model directory to receive best.pt and model_manifest.json.")
    parser.add_argument("--approve-for-research-use", action="store_true", help="Mark manifest as approved after expert review.")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    loaders, image_sets = build_loaders(args.data_dir, args.batch_size)
    class_names = image_sets["train"].classes
    model = build_model(args.arch, len(class_names)).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)

    best_val = 0.0
    run_id = datetime.now(timezone.utc).strftime(f"{args.arch}-%Y%m%d-%H%M%S")
    run_dir = args.out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    best_path = run_dir / "best.pt"

    for epoch in range(1, args.epochs + 1):
        train_loss = run_epoch(model, loaders["train"], optimizer, device)
        val_loss = run_epoch(model, loaders["val"], None, device)
        val_metrics = evaluate(model, loaders["val"], device, class_names)
        if float(val_metrics["f1"]) >= best_val:
            best_val = float(val_metrics["f1"])
            torch.save({"arch": args.arch, "classes": class_names, "state_dict": model.state_dict()}, best_path)
        print(f"epoch={epoch} train_loss={train_loss:.4f} val_loss={val_loss:.4f} val_f1={val_metrics['f1']:.4f}")

    checkpoint = torch.load(best_path, map_location=device)
    model.load_state_dict(checkpoint["state_dict"])
    test_metrics = evaluate(model, loaders["test"], device, class_names)
    metrics = {
        "architecture": args.arch,
        "datasetScope": "hantavirus-only curated split",
        "bestValidationF1": best_val,
        "metrics": test_metrics,
        "warning": "Publish only after expert review and leakage checks.",
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    manifest = write_model_manifest(run_dir, args, class_names, test_metrics, best_val)
    (run_dir / "deployment_note.txt").write_text(
        "Copy best.pt and model_manifest.json to the API model directory, then set "
        "MODEL_MANIFEST_PATH to that model_manifest.json. Do not approve before expert review.\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))
    print(json.dumps({"manifest": manifest}, indent=2))


if __name__ == "__main__":
    main()
