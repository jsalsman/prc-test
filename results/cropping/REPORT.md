# PRC watermark cropping robustness experiment

This report documents the planned workflow and artifacts for measuring how PRC watermarks survive central cropping. The scripts live in the repository root (see `scripts/`) and call directly into the upstream `PRC-Watermark` implementation.

## Configuration
- Bit lengths: **512** and **2500** message bits (set during key generation in `encode.py`; update the `message_length` passed to `KeyGen` when preparing the 2500-bit run).
- Detector: official `decode.py` from `PRC-Watermark` with default `fpr=1e-5`, `prc_t=3`, and 50 inference steps unless overridden.
- Prompts: draw from the default dataset used by `encode.py` (`Gustavosta/Stable-Diffusion-Prompts`) for consistency across bit-length runs.
- Cropping: deterministic center crop retaining 100, 90, 80, 70, 60, 50, 40, 30, 20, and 10 percent of the image area, resized back to the original resolution for detection.

## End-to-end commands (example)
Assuming a default PRC run producing `exp_id=prc_num_200_steps_50_fpr_1e-05_nowm_0`:

```bash
# 1) Generate watermarked images (outside this repo, in PRC-Watermark)
cd PRC-Watermark
python encode.py --test_num 200  # add --fpr / --prc_t / --model_id if you diverge
cd ..

# 2) Crop + decode, logging raw detections (back in repo root)
python scripts/run_prc_cropping_experiment.py \
    --bit-length 512 \
    --test-num 200 \
    --exp-id prc_num_200_steps_50_fpr_1e-05_nowm_0 \
    --resize-back

# Repeat step 2 with --bit-length 2500 (matching how you generated the keys)

# 3) Aggregate and compute thresholds
python scripts/analyze_cropping_results.py

# 4) Plot detection-rate curves and emit base64-encoded artifacts
python scripts/plot_cropping_results.py --base64
```

## Artifacts
- Raw detections: `results/cropping/prc_cropping_raw_512bits.csv`, `results/cropping/prc_cropping_raw_2500bits.csv`
- Aggregated detection rates: `results/cropping/prc_cropping_results_512bits.csv`, `results/cropping/prc_cropping_results_2500bits.csv`
- Robustness thresholds: `results/cropping/prc_cropping_thresholds.csv`
- Plots (base64): `results/cropping/prc_cropping_summary_512bits.png.base64`, `results/cropping/prc_cropping_summary_2500bits.png.base64`

> The CSVs currently contain headers only; fill them by running the pipeline above after generating watermarked images for each bit length.
> The plot base64 files are placeholders for now so reviewers can exercise the decoding workflow; regenerate them with actual detection curves via `scripts/plot_cropping_results.py --base64` once experiment results are available.

## Decoding plot artifacts
To view a plot locally after it has been committed as base64 text:

```bash
base64 -d results/cropping/prc_cropping_summary_512bits.png.base64 > prc_cropping_summary_512bits.png
base64 -d results/cropping/prc_cropping_summary_2500bits.png.base64 > prc_cropping_summary_2500bits.png
```

## Notes
- Keep all images and other binaries confined to gitignored paths (`PRC-Watermark/results/`, `PRC-Watermark/keys/`, `data/`).
- Use the same prompt pool and test size for both bit lengths so detection-rate comparisons remain apples-to-apples.
- If you adjust PRC parameters (e.g., a different `fpr`), pass the same values to `run_prc_cropping_experiment.py` so it can reconstruct the correct `exp_id` for decoding.
