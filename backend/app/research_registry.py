from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


UPDATED_AT = "2026-05-21"


HANTAVIRUS_DATASETS: list[dict[str, Any]] = [
    {
        "id": "zenodo-10417810-hantavirus-infected-cells",
        "name": "Virüs enfekte hücrelerin nicelendirilmesi için görüntü veri seti",
        "source": "Zenodo / Helmholtz Centre for Infection Research",
        "url": "https://zenodo.org/records/10417810",
        "doi": "10.5281/zenodo.10417810",
        "modality": "Floresan mikroskopi",
        "hantavirusRelation": "Hantavirüs 76-118 suşuyla enfekte hücreler, viral nükleokapsid proteinine karşı boyanmıştır.",
        "labelSignal": "Enfekte hücre / nükleokapsid pozitif mikroskopi sinyali; negatif kontroller kaynak deneyden dikkatle ayrıştırılmalıdır.",
        "files": ["Test_dataset_CellProfiler.zip", "Test_dataset_NIS_elements.zip"],
        "size": "547.0 MB",
        "trainingSuitability": "Eğitim/doğrulama/test ayrımı yapıldıktan sonra mikroskopi sınıflandırıcısı için en güçlü hantavirüs odaklı görüntü kaynağı.",
        "status": "curation-ready",
        "recommendedModels": ["CNN", "ResNet-50", "EfficientNet-B0"],
    },
    {
        "id": "dryad-seoul-hantaan-endothelial-imaging",
        "name": "Seoul orthohantavirüs rezervuar endotel hücrelerinde doğuştan bağışıklık aktivasyonundan kaçar veri seti",
        "source": "Dryad / PLOS Pathogens companion dataset",
        "url": "https://datadryad.org/dataset/doi:10.5061/dryad.gf1vhhmzd",
        "doi": "10.5061/dryad.gf1vhhmzd",
        "modality": "İmmünfloresan mikroskopi ve ham deney medyası",
        "hantavirusRelation": "Endotel hücrelerinde Seoul orthohantavirüs ve Hantaan orthohantavirüs enfeksiyon deneyleri.",
        "labelSignal": "SEOV/HTNV N-pozitif hücre deneyleri; model eğitimi öncesinde klasörlerden etiket çıkarımı gerekir.",
        "files": ["Data_repository.zip", "README.md"],
        "size": "87.98 MB",
        "trainingSuitability": "Araştırma düzeyinde destekleyici kaynak; manuel etiket eşleme ve veri sızıntısı kontrolünden sonra kullanılabilir.",
        "status": "requires-label-curation",
        "recommendedModels": ["CNN", "ResNet-18", "EfficientNet-B0"],
    },
]


REFERENCE_MEDIA: list[dict[str, Any]] = [
    {
        "id": "cdc-phil-6078-hps-xray",
        "name": "Pulmoner efüzyonlu HPS akciğer röntgeni",
        "source": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=6078",
        "modality": "Akciğer radyografisi",
        "labelSignal": "Hantavirüs pulmoner sendromu referans röntgeni.",
        "trainingSuitability": "Yalnızca referans medya; dengeli klinik röntgen veri seti değildir.",
    },
    {
        "id": "cdc-phil-1137-sin-nombre-tem",
        "name": "Sin Nombre virüsü transmisyon elektron mikrografı",
        "source": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1137",
        "modality": "Transmisyon elektron mikroskopisi",
        "labelSignal": "Sin Nombre virüs parçacıkları, HPS ilişkili hantavirüs.",
        "trainingSuitability": "Yalnızca referans medya; kaynaklı örnekler ve eğitim için uygundur.",
    },
    {
        "id": "cdc-phil-1138-deer-mouse",
        "name": "Kuzey Amerika geyik faresi rezervuar görüntüsü",
        "source": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1138",
        "modality": "Rezervuar konak fotoğrafı",
        "labelSignal": "Peromyscus maniculatus, Sin Nombre virüsünün başlıca taşıyıcısı.",
        "trainingSuitability": "Yalnızca referans medya; kemirgen dedektörü için daha büyük etiketli konak/konak dışı veri gerekir.",
    },
]


AUXILIARY_DATASETS: list[dict[str, Any]] = [
    {
        "id": "kaggle-jakabcsatri-viruses-ncbi",
        "name": "NCBI kaynaklı virus veri seti",
        "source": "Kaggle / NCBI",
        "url": "https://www.kaggle.com/datasets/jakabcsatri/viruses-ncbi",
        "modality": "virus genom/metadata veri seti",
        "labelSignal": (
            "Genel virus sınıflandırma ve NCBI kaynaklı taksonomi/sequence bilgisi; "
            "Hantaviridae kayıtları filtrelenerek genomik model kanıtı için kullanılabilir."
        ),
        "trainingSuitability": (
            "Hocanın verdiği kaynak sisteme eklendi. Bu kaynak görüntü etiketi taşımadığı için "
            "CNN/ResNet/EfficientNet görüntü modelini tek başına doğrulamaz; sequence/taksonomi modeli için uygundur."
        ),
        "status": "teacher-provided-genomic-source",
    },
    {
        "id": "kaggle-hantavirus-search",
        "name": "Kaggle hantavirüs veri seti araması",
        "source": "Kaggle Datasets",
        "url": "https://www.kaggle.com/datasets?search=hantavirus",
        "modality": "veri seti keşfi",
        "labelSignal": "Mevcut aramada doğrulanmış, herkese açık, hantavirüse özel klinik görüntü benchmark'ı bulunmadı.",
        "trainingSuitability": (
            "Veri seti bağlantısı manuel olarak hantavirüs görüntü etiketleri içerdiği kanıtlanmadan kanıt olarak kullanılmamalıdır."
        ),
        "status": "manual-verification-required",
    },
    {
        "id": "zenodo-irodent-8250392",
        "name": "iRodent: doğal ortamda kemirgen anahtar nokta ve segmentasyon veri seti",
        "source": "Zenodo / EPFL",
        "url": "https://zenodo.org/records/8250392",
        "doi": "10.5281/zenodo.8250392",
        "modality": "segmentasyon/anahtar nokta etiketli kemirgen fotoğrafları",
        "labelSignal": "Kemirgen türü ve segmentasyon etiketleri; hantavirüs enfeksiyon etiketi değildir.",
        "trainingSuitability": (
            "Yalnızca kemirgen konak tespiti için yardımcı veri. Hantavirüs tanı modeli eğitmek için kullanılamaz."
        ),
        "status": "auxiliary-only",
    },
]


MODEL_VALIDATION: list[dict[str, Any]] = [
    {
        "id": "hantacell-cnn-baseline",
        "architecture": "CNN",
        "target": "Hantavirüs enfekte hücre mikroskopi taraması",
        "datasetScope": ["Zenodo 10.5281/zenodo.10417810", "Dryad 10.5061/dryad.gf1vhhmzd"],
        "trainingStatus": "pipeline-ready",
        "validationStatus": "pending-real-training-run",
        "metrics": {
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "auroc": None,
            "note": "Kürasyonlu yalnızca hantavirüs ayrımı eğitilip doğrulanmadan metrik gösterilmez.",
        },
    },
    {
        "id": "hantacell-resnet50-transfer",
        "architecture": "ResNet-50",
        "target": "Mikroskopi ve referans medya özellik çıkarımı için transfer öğrenme",
        "datasetScope": ["Zenodo 10.5281/zenodo.10417810", "CDC PHIL hantavirus reference media"],
        "trainingStatus": "pipeline-ready",
        "validationStatus": "pending-real-training-run",
        "metrics": {
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "auroc": None,
            "note": "Az sayıdaki açık referans görselden klinik HPS röntgen doğrulaması iddia edilemez.",
        },
    },
    {
        "id": "hantacell-efficientnet-b0",
        "architecture": "EfficientNet-B0",
        "target": "Verimli yüksek içerikli mikroskopi sınıflandırıcısı",
        "datasetScope": ["Zenodo 10.5281/zenodo.10417810"],
        "trainingStatus": "pipeline-ready",
        "validationStatus": "pending-real-training-run",
        "metrics": {
            "accuracy": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "auroc": None,
            "note": "Metrikler etiket kürasyonundan sonra dahil edilen eğitim protokolüyle üretilmelidir.",
        },
    },
]


VALIDATION_PROTOCOL: list[str] = [
    "Yalnızca kayıt sisteminde listelenen hantavirüs ilişkili kaynakları indir.",
    "Hasta, plaka veya deney sızıntısı olmadan etiketleri eğitim/doğrulama/test klasörlerine ayır.",
    "CNN, ResNet-50 ve EfficientNet-B0 modellerini aynı veri ayrımıyla eğit.",
    "Doğruluk, kesinlik, duyarlılık, F1, AUROC, karmaşıklık matrisi ve Grad-CAM inceleme notlarını raporla.",
    "Uzman incelemeli doğrulama raporu oluşana kadar platformu eğitim/araştırma modunda tut.",
    "Yükleme tahminlerini açmadan önce doğrulanmış model_manifest.json ve onaylı artefact kur.",
]


BIBLIOGRAPHY: list[dict[str, str]] = [
    {
        "title": "Image dataset for quantification of virus-infected cells",
        "publisher": "Zenodo",
        "url": "https://zenodo.org/records/10417810",
        "note": "En güçlü eğitim adayı olarak kullanılan birincil hantavirüs enfekte hücre mikroskopi veri seti.",
    },
    {
        "title": "An Improved Workflow for the Quantification of Orthohantavirus Infection Using Automated Imaging and Flow Cytometry",
        "publisher": "Viruses / PubMed Central",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10891500/",
        "note": "Görüntüleme iş akışını açıklayan ve Zenodo ham verisine bağlanan makale.",
    },
    {
        "title": "Data from: Seoul orthohantavirus evades innate immune activation by reservoir endothelial cells",
        "publisher": "Dryad",
        "url": "https://datadryad.org/dataset/doi:10.5061/dryad.gf1vhhmzd",
        "note": "Destekleyici SEOV/HTNV immünfloresan ve ham deney verisi; etiket kürasyonu gerekir.",
    },
    {
        "title": "CDC PHIL ID 6078: HPS chest x-ray",
        "publisher": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=6078",
        "note": "Referans HPS röntgen medyası; dengeli eğitim veri seti değildir.",
    },
    {
        "title": "CDC PHIL ID 1137: Sin Nombre virus electron micrograph",
        "publisher": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1137",
        "note": "Referans hantavirüs mikrograf medyası.",
    },
    {
        "title": "CDC PHIL ID 1138: North American deer mouse",
        "publisher": "CDC Public Health Image Library",
        "url": "https://wwwn.cdc.gov/phil/Details.aspx?pid=1138",
        "note": "Referans rezervuar konak medyası.",
    },
    {
        "title": "Kaggle veri seti araması",
        "publisher": "Kaggle",
        "url": "https://www.kaggle.com/datasets?search=hantavirus",
        "note": "Olası kaynak olarak kontrol edildi; manuel veri seti doğrulaması olmadan hantavirüse özel klinik görüntü benchmark'ı iddia edilmez.",
    },
    {
        "title": "Viruses dataset from NCBI",
        "publisher": "Kaggle / NCBI",
        "url": "https://www.kaggle.com/datasets/jakabcsatri/viruses-ncbi",
        "note": "Hocanın önerdiği NCBI kökenli genel virus veri seti; görüntü modeli değil, genom/taksonomi kanıt katmanı için eklendi.",
    },
    {
        "title": "iRodent: a keypoint and segmentation dataset of rodents in the wild",
        "publisher": "Zenodo",
        "url": "https://zenodo.org/records/8250392",
        "note": "Yardımcı kemirgen görsel veri seti; konak görüntü yönlendirmesi için yararlı, enfeksiyon tanısı için değildir.",
    },
    {
        "title": "Clinician Brief: Hantavirus Pulmonary Syndrome",
        "publisher": "CDC",
        "url": "https://www.cdc.gov/hantavirus/hcp/clinical-overview/hps.html",
        "note": "Platform uyarılarında kullanılan klinik bağlam ve tanısal dikkat bilgisi.",
    },
]


def evidence_payload() -> dict[str, Any]:
    return {
        "updatedAt": UPDATED_AT,
        "mode": "Yalnızca hantavirüs kanıt modu",
        "datasets": HANTAVIRUS_DATASETS,
        "referenceMedia": REFERENCE_MEDIA,
        "auxiliaryDatasets": AUXILIARY_DATASETS,
        "models": MODEL_VALIDATION,
        "validationProtocol": VALIDATION_PROTOCOL,
        "bibliography": BIBLIOGRAPHY,
        "honestyNotice": (
            "Herkese açık, dengeli, klinik düzeyde hantavirüs görüntü benchmark'ı ve doğrulanmış hazır "
            "CNN/ResNet/EfficientNet modeli bulunmadı. Listelenen kaynaklar kürasyon, eğitim, doğrulama "
            "ve model artefact kurulumu tamamlanana kadar API sahte tıbbi tahmin üretmez."
        ),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def assistant_reply(message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    text = message.strip().lower()
    risk = context.get("risk") or "beklemede"
    image_type = context.get("imageType") or "gorsel henuz secilmedi"
    model = context.get("model") or "otomatik model yönlendirici"
    mode = context.get("mode") or "araştırma modu"
    model_ready = bool(context.get("modelReady"))

    if any(word in text for word in ["selam", "merhaba", "naber", "nasılsın", "nasilsin"]):
        reply = (
            "Merhaba knk, buradayım. Bana görüntü sonucu, model, veri seti, Kaggle/NCBI kaynağı, PDF rapor, "
            "hantavirüs bilgisi veya hocaya nasıl anlatılacağı hakkında istediğin gibi sorabilirsin."
        )
    elif any(word in text for word in ["kaggle", "ncbi", "jakab", "viruses"]):
        reply = (
            "Hocanın verdiği Kaggle NCBI virus veri seti sisteme kaynak olarak eklendi. Bu kaynak genel virus "
            "genom/metadata tarafını güçlendirir ve Hantaviridae filtreleme için kullanılabilir; fakat görüntü "
            "etiketi taşımadığı için akciğer röntgeni veya mikroskopi CNN modelini tek başına doğrulamaz."
        )
    elif any(word in text for word in ["veri", "dataset", "kaynak", "egitim", "eğitim"]):
        reply = (
            "Bu platformda sadece hantavirüs ilişkili kaynaklar listeleniyor: Zenodo enfekte hücre "
            "mikroskopi seti ana eğitim adayı, Dryad SEOV/HTNV verisi destekleyici kaynak, CDC PHIL "
            "görselleri ise referans medyadır. Kaggle NCBI virus veri seti genom/taksonomi kanıt katmanı "
            "olarak eklendi; görüntü modeli doğrulaması için ayrı etiketli görüntü verisi gerekir."
        )
    elif any(word in text for word in ["metrik", "accuracy", "dogrulama", "doğrulama", "basari", "başarı"]):
        reply = (
            "Doğrulama metrikleri şu an bilinçli olarak boş: sahte doğruluk yazmıyoruz. Önce etiketli "
            "eğitim/doğrulama/test ayrımı yapılmalı, sonra CNN, ResNet-50 ve EfficientNet-B0 için "
            "doğruluk, kesinlik, duyarlılık, F1 ve AUROC raporlanmalı."
        )
    elif any(word in text for word in ["risk", "sonuc", "sonuç", "ne anlama"]):
        reply = (
            f"Bu ekrandaki sonuç {risk} risk olarak okunuyor. Görsel türü {image_type}, seçilen model "
            f"{model}. Bu bir tanı değil; uzman hekim ve laboratuvar testiyle doğrulanması gerekir."
        )
    elif any(word in text for word in ["model", "cnn", "resnet", "efficientnet"]):
        reply = (
            "Model katmanı üç adayla tasarlandı: CNN hızlı mikroskopi başlangıç modeli, ResNet-50 transfer "
            "öğrenme ve EfficientNet-B0 verimli mikroskopi sınıflandırma. Klinik HPS röntgeni için "
            "yeterli açık etiketli veri bulunmadığı için o kısım araştırma amaçlı tutuluyor."
        )
    elif any(word in text for word in ["tani", "tanı", "doktor", "hekim"]):
        reply = (
            "HantaVision kesin tıbbi tanı koymaz. Hantavirüs şüphesinde resmi tanı klinik değerlendirme "
            "ve laboratuvar testleriyle yapılmalıdır."
        )
    elif any(word in text for word in ["tasarım", "tasarim", "sunum", "hoca", "anlat"]):
        reply = (
            "Hocaya şöyle anlatabilirsin: sistem önce görüntüyü güvenli biçimde kabul ediyor, kalite ve tür "
            "analizi yapıyor, uygun model rotasını seçiyor, doğrulanmış model varsa risk raporu ve Grad-CAM "
            "üretiyor. Doğrulanmış model yoksa sahte sonuç üretmeyip model bekleniyor diyor; bu profesyonel "
            "medikal AI davranışıdır."
        )
    elif any(word in text for word in ["pdf", "rapor", "indir", "export"]):
        reply = (
            "PDF rapor; yüklenen dosya adı, görüntü türü, risk durumu, güven skoru, kalite skoru, model bilgisi, "
            "açıklama ve tıbbi uyarıyı içerir. Rapor indirme butonu analiz kaydı oluştuktan sonra aktif olur."
        )
    elif any(word in text for word in ["mod", "mode", "clinical", "research", "educational", "klinik"]):
        reply = (
            f"Şu an seçili çalışma modu {mode}. Klinik mod daha ciddi rapor dilini, araştırma modu veri/model "
            "kanıtlarını, eğitim modu ise açıklayıcı anlatımı öne çıkarır."
        )
    else:
        reply = (
            f"Sorunu anladım. Mevcut bağlam: görüntü türü {image_type}, model {model}, risk {risk}, "
            f"doğrulanmış model durumu {'hazır' if model_ready else 'beklemede'}. İstersen bunu daha sade, "
            "hoca sunumu diliyle veya teknik rapor diliyle açıklayabilirim."
        )

    return {
        "reply": reply,
        "context": {"risk": risk, "imageType": image_type, "model": model},
        "disclaimer": "Yalnızca araştırma/eğitim amaçlıdır; tıbbi tanı değildir.",
        "sources": [item["url"] for item in BIBLIOGRAPHY[:4]],
    }
