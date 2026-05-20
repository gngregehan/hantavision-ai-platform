# HantaVision AI Model Training

This folder is intentionally separate from the Render API runtime. It defines the real training path for a hantavirus-only medical AI model without adding heavy Torch dependencies to the live web service.

## Dataset Rule

Use only hantavirus-related sources listed in `hantavirus_datasets.json`.

Current training candidates:

- Zenodo `10.5281/zenodo.10417810`: hantavirus-infected cell microscopy images.
- Dryad `10.5061/dryad.gf1vhhmzd`: SEOV/HTNV immunofluorescence and raw experiment media that requires label curation.

CDC PHIL images are included only as reference media. They should not be presented as a balanced clinical dataset.

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

Each run writes validation metrics to `ml/runs/<arch>/metrics.json`.

## Validation Metrics

Required metrics:

- accuracy
- precision
- recall
- F1
- AUROC
- confusion matrix

Do not publish placeholder clinical performance. The live site marks metrics as pending until this training flow is run on a curated hantavirus-only split.
