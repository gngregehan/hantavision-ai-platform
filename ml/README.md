# HantaVision AI Model Training

This folder is intentionally separate from the Render API runtime. It defines the real training path for a hantavirus-only medical AI model without adding heavy Torch dependencies to the live web service.

## Dataset Rule

Use only hantavirus-related sources listed in `hantavirus_datasets.json`.

Current training candidates:

- Zenodo `10.5281/zenodo.10417810`: hantavirus-infected cell microscopy images.
- Dryad `10.5061/dryad.gf1vhhmzd`: SEOV/HTNV immunofluorescence and raw experiment media that requires label curation.

CDC PHIL images are included only as reference media. They should not be presented as a balanced clinical dataset.

Kaggle is supported only as a manually verified auxiliary source. Do not train the infection classifier on a Kaggle slug unless the images, labels, license, and hantavirus relation have been reviewed.

## Download Source Archives

Dry-run first:

```bash
python ml/download_sources.py
```

Download primary sources:

```bash
python ml/download_sources.py --execute
```

Optional auxiliary source discovery:

```bash
python ml/download_sources.py --include-auxiliary --execute
python ml/download_sources.py --kaggle-slug owner/dataset-slug --execute
```

Kaggle requires a local Kaggle API token. Auxiliary downloads do not become training data automatically.

## Label Curation

Create a reviewed CSV:

```csv
source_id,relative_path,label,split
zenodo-10417810-hantavirus-infected-cells,path/to/image_001.tif,infected,train
zenodo-10417810-hantavirus-infected-cells,path/to/control_001.tif,non_infected,val
```

Then build the ImageFolder split:

```bash
python ml/curate_hantavirus_dataset.py --labels-csv data/labels/hantavirus_labels.csv --copy
```

## Expected Curated Folder Layout

```text
data/hantavirus/
  train/
    infected/
    non_infected/
  val/
    infected/
    non_infected/
  test/
    infected/
    non_infected/
```

Keep experiment, plate, patient, or source leakage out of the split.

## Train

```bash
pip install -r ml/requirements.txt
python ml/train_hantavirus_models.py --data-dir data/hantavirus --arch cnn
python ml/train_hantavirus_models.py --data-dir data/hantavirus --arch resnet50
python ml/train_hantavirus_models.py --data-dir data/hantavirus --arch efficientnet_b0
```

Each run writes `best.pt`, `metrics.json`, and `model_manifest.json` to `ml/runs/<arch>-<timestamp>/`.

After expert review, publish an approved research artefact to the API model directory:

```bash
python ml/train_hantavirus_models.py --data-dir data/hantavirus --arch efficientnet_b0 --publish-dir models/hantacell --approve-for-research-use
```

Then configure the API:

```bash
MODEL_MANIFEST_PATH=./models/hantacell/model_manifest.json
STRICT_MODEL_MODE=true
```

## Validation Metrics

Required metrics:

- accuracy
- precision
- recall
- F1
- AUROC
- confusion matrix

Do not publish placeholder clinical performance. The live site marks metrics as pending until this training flow is run on a curated hantavirus-only split.

The production API blocks user-facing predictions until `model_manifest.json` exists, the artifact exists, and `validation.approvedForUse` is `true`.
