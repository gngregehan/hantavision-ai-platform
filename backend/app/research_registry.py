from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


UPDATED_AT = "2026-05-20"


HANTAVIRUS_DATASETS: list[dict[str, Any]] = [
    {
        "id": "zenodo-10417810-hantavirus-infected-cells",
        "name": "Image dataset for quantification of virus-infected cells",
        "source": "Zenodo / Helmholtz Centre for Infection Research",
        "url": "https://zenodo.org/records/10417810",
        "doi": "10.5281/zenodo.10417810",
        "modality": "Fluorescence microscopy",
        "hantavirusRelation": "Hantavirus strain 76-118 infected cells stained against viral nucleocapsid protein.",
        "labelSignal": "Infected-cell / nucleocapsid-positive microscopy signal; negative controls must be curated from the source experiment.",
        "files": ["Test_dataset_CellProfiler.zip", "Test_dataset_NIS_elements.zip"],
        "size": "547.0 MB",
        "trainingSuitability": "Best current hantavirus-only image source for a microscopy classifier after train/validation/test curation.",
        "status": "curation-ready",
        "recommendedModels": ["CNN", "ResNet-50", "EfficientNet-B0"],
    },
    {
        "id": "dryad-seoul-hantaan-endothelial-imaging",
        "name": "Data from: Seoul orthohantavirus evades innate immune activation by reservoir endothelial cells",
        "source": "Dryad / PLOS Pathogens companion dataset",
        "url": "https://datadryad.org/dataset/doi:10.5061/dryad.gf1vhhmzd",
        "doi": "10.5061/dryad.gf1vhhmzd",
        "modality": "Immunofluorescence microscopy and raw experiment media",
        "hantavirusRelation": "Seoul orthohantavirus and Hantaan orthohantavirus infection experiments in endothelial cells.",
        "labelSignal": "SEOV/HTNV N-positive cell experiments; figure-level folders require label extraction before model training.",
        "files": ["Data_repository.zip", "README.md"],
        "size": "87.98 MB",
        "trainingSuitability": "Research-grade supporting source; usable after manual label mapping and leakage checks.",
        "status": "requires-label-curation",
        "recommendedModels": ["CNN", "ResNet-18", "EfficientNet-B0"],
    },
]


REFERENCE_MEDIA: list[dict[str, Any]] = [
    {
        "id": "cdc-phil-6078-hps-xray",
        "name": "HPS chest x-ray with pulmonary effusion",
        "source": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=6078",
        "modality": "Chest radiograph",
        "labelSignal": "Hantavirus pulmonary syndrome reference x-ray.",
        "trainingSuitability": "Reference media only; not a balanced clinical x-ray dataset.",
    },
    {
        "id": "cdc-phil-1137-sin-nombre-tem",
        "name": "Sin Nombre virus transmission electron micrograph",
        "source": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1137",
        "modality": "Transmission electron microscopy",
        "labelSignal": "Sin Nombre virus particles, HPS-associated hantavirus.",
        "trainingSuitability": "Reference media only; useful for source-backed examples and education.",
    },
    {
        "id": "cdc-phil-1138-deer-mouse",
        "name": "North American deer mouse reservoir image",
        "source": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1138",
        "modality": "Reservoir host photograph",
        "labelSignal": "Peromyscus maniculatus, major carrier of Sin Nombre virus.",
        "trainingSuitability": "Reference media only; a rodent detector needs a larger labeled host/non-host corpus.",
    },
]


MODEL_VALIDATION: list[dict[str, Any]] = [
    {
        "id": "hantacell-cnn-baseline",
        "architecture": "CNN",
        "target": "Hantavirus infected-cell microscopy screening",
        "datasetScope": ["Zenodo 10.5281/zenodo.10417810", "Dryad 10.5061/dryad.gf1vhhmzd"],
        "trainingStatus": "pipeline-ready",
        "validationStatus": "pending-real-training-run",
        "metrics": {
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "auroc": None,
            "note": "No metric is shown until a curated hantavirus-only split is trained and validated.",
        },
    },
    {
        "id": "hantacell-resnet50-transfer",
        "architecture": "ResNet-50",
        "target": "Transfer learning for microscopy and reference-media feature extraction",
        "datasetScope": ["Zenodo 10.5281/zenodo.10417810", "CDC PHIL hantavirus reference media"],
        "trainingStatus": "pipeline-ready",
        "validationStatus": "pending-real-training-run",
        "metrics": {
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "auroc": None,
            "note": "Clinical HPS x-ray validation cannot be claimed from the small public reference images.",
        },
    },
    {
        "id": "hantacell-efficientnet-b0",
        "architecture": "EfficientNet-B0",
        "target": "Efficient high-content microscopy classifier",
        "datasetScope": ["Zenodo 10.5281/zenodo.10417810"],
        "trainingStatus": "pipeline-ready",
        "validationStatus": "pending-real-training-run",
        "metrics": {
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "auroc": None,
            "note": "Metrics must be generated by the included training protocol after label curation.",
        },
    },
]


VALIDATION_PROTOCOL: list[str] = [
    "Download only hantavirus-related sources listed in the registry.",
    "Curate labels into train/validation/test folders without patient, plate, or experiment leakage.",
    "Train CNN, ResNet-50, and EfficientNet-B0 with identical splits.",
    "Report accuracy, precision, recall, F1, AUROC, confusion matrix, and Grad-CAM review notes.",
    "Keep the platform in education/research mode until an expert-reviewed validation report exists.",
]


BIBLIOGRAPHY: list[dict[str, str]] = [
    {
        "title": "Image dataset for quantification of virus-infected cells",
        "publisher": "Zenodo",
        "url": "https://zenodo.org/records/10417810",
        "note": "Primary hantavirus-infected cell microscopy dataset used as the strongest training candidate.",
    },
    {
        "title": "An Improved Workflow for the Quantification of Orthohantavirus Infection Using Automated Imaging and Flow Cytometry",
        "publisher": "Viruses / PubMed Central",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10891500/",
        "note": "Paper describing the imaging workflow and linking the Zenodo raw data.",
    },
    {
        "title": "Data from: Seoul orthohantavirus evades innate immune activation by reservoir endothelial cells",
        "publisher": "Dryad",
        "url": "https://datadryad.org/dataset/doi:10.5061/dryad.gf1vhhmzd",
        "note": "Supporting SEOV/HTNV immunofluorescence and raw experiment data; label curation required.",
    },
    {
        "title": "CDC PHIL ID 6078: HPS chest x-ray",
        "publisher": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=6078",
        "note": "Reference HPS x-ray media, not a balanced training dataset.",
    },
    {
        "title": "CDC PHIL ID 1137: Sin Nombre virus electron micrograph",
        "publisher": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1137",
        "note": "Reference hantavirus micrograph media.",
    },
    {
        "title": "CDC PHIL ID 1138: North American deer mouse",
        "publisher": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1138",
        "note": "Reference reservoir-host media.",
    },
    {
        "title": "Clinician Brief: Hantavirus Pulmonary Syndrome",
        "publisher": "CDC",
        "url": "https://www.cdc.gov/hantavirus/hcp/clinical-overview/hps.html",
        "note": "Clinical context and diagnostic caution used for platform disclaimers.",
    },
]


def evidence_payload() -> dict[str, Any]:
    return {
        "updatedAt": UPDATED_AT,
        "mode": "Hantavirus-only evidence mode",
        "datasets": HANTAVIRUS_DATASETS,
        "referenceMedia": REFERENCE_MEDIA,
        "models": MODEL_VALIDATION,
        "validationProtocol": VALIDATION_PROTOCOL,
        "bibliography": BIBLIOGRAPHY,
        "honestyNotice": (
            "Public, balanced, clinical-grade hantavirus image benchmarks and validated pretrained "
            "CNN/ResNet/EfficientNet models were not found. The platform therefore marks metrics as "
            "pending until the listed hantavirus-only sources are curated and trained."
        ),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def assistant_reply(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    text = message.strip().lower()
    risk = context.get("risk") or "beklemede"
    image_type = context.get("imageType") or "gorsel henuz secilmedi"
    model = context.get("model") or "otomatik model router"

    if any(word in text for word in ["veri", "dataset", "kaynak", "egitim", "eğitim"]):
        reply = (
            "Bu platformda sadece hantavirus iliskili kaynaklar listeleniyor: Zenodo infected-cell "
            "microscopy seti ana egitim adayi, Dryad SEOV/HTNV verisi destekleyici kaynak, CDC PHIL "
            "gorselleri ise referans medya. CDC PHIL tek basina egitim seti degil."
        )
    elif any(word in text for word in ["metrik", "accuracy", "dogrulama", "doğrulama", "basari", "başarı"]):
        reply = (
            "Dogrulama metrikleri su an bilincli olarak bos: sahte accuracy yazmiyoruz. Once etiketli "
            "train/validation/test ayrimi yapilmali, sonra CNN, ResNet-50 ve EfficientNet-B0 icin "
            "accuracy, precision, recall, F1 ve AUROC raporlanmali."
        )
    elif any(word in text for word in ["risk", "sonuc", "sonuç", "ne anlama"]):
        reply = (
            f"Bu ekrandaki sonuc {risk} risk olarak okunuyor. Gorsel turu {image_type}, secilen model "
            f"{model}. Bu bir tani degil; uzman hekim ve laboratuvar testiyle dogrulanmasi gerekir."
        )
    elif any(word in text for word in ["model", "cnn", "resnet", "efficientnet"]):
        reply = (
            "Model katmani uc adayla tasarlandi: CNN hizli mikroskopi baseline, ResNet-50 transfer "
            "learning ve EfficientNet-B0 verimli mikroskopi siniflandirma. Klinik HPS x-ray icin "
            "yeterli acik etiketli veri bulunmadigi icin o kisim research-only tutuluyor."
        )
    elif any(word in text for word in ["tani", "tanı", "doktor", "hekim"]):
        reply = (
            "HantaVision kesin tibbi tani koymaz. Hantavirus supesinde resmi tani klinik degerlendirme "
            "ve laboratuvar testleriyle yapilmalidir."
        )
    else:
        reply = (
            "Sorunu dataset, model, risk, metrik veya rapor olarak sorabilirsin. Ben mevcut analiz "
            "sonucunu ve sadece hantavirus kaynakli evidence registry bilgisini kullanarak cevap veririm."
        )

    return {
        "reply": reply,
        "context": {"risk": risk, "imageType": image_type, "model": model},
        "disclaimer": "Research/education purpose only; not a medical diagnosis.",
        "sources": [item["url"] for item in BIBLIOGRAPHY[:4]],
    }
