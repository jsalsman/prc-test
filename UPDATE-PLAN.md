# UPDATE PLAN: Parameterizing PRC bit-length for cropping robustness experiments

## Goal
Enable the Colab "Master Script for Cropping Robustness Experiment" in `PLAN.md` to run for both 512-bit and 2500-bit PRC watermarks by plumbing a `--bits` (message length) option through the upstream `PRC-Watermark` CLI scripts and the local orchestration helpers. The key objective is to make `KeyGen()` receive the requested `message_length` and to segregate keys/results per bit length so the 512-bit and 2500-bit runs no longer collide or silently reuse 512-bit keys.

## Why this is needed
- The master script loops over `[512, 2500]` bit lengths and constructs `exp_id = f"prc_num_{TEST_NUM}_steps_{INF_STEPS}_fpr_{FPR}_nowm_{NOWM}_bits_{bit_length}"`, then expects corresponding `results/<exp_id>/original_images` folders and key files. However, `PRC-Watermark/encode.py` lacks a `--bits` argument and always calls `KeyGen` with its default `message_length=512`, while also omitting the bit length from `exp_id`. This mismatch prevents 2500-bit keys/results from being generated and makes the master script’s paths invalid. (See `PLAN.md` master script block and `PRC-Watermark/encode.py`.)

## Required script modifications

### 1) `PRC-Watermark/encode.py`
- Add a `--bits` (or `--message-length`) CLI argument with default `512`.
- Use this value when calling `KeyGen(n, message_length=bits, ...)` so the codeword matches the requested payload size.
- Incorporate the bit length into `exp_id` (e.g., append `_bits_<bits>`) so keys and results are namespaced per payload size.
- Ensure key file paths (`keys/<exp_id>.pkl`) and output directories (`results/<exp_id>/original_images`) follow the new `exp_id` format to avoid collisions between 512-bit and 2500-bit runs.

### 2) `PRC-Watermark/decode.py`
- Add a matching `--bits` argument (default `512`).
- Mirror the `exp_id` construction used in `encode.py`, including the bit suffix, so decode loads the correct key file and reads images from the correct `results/<exp_id>/<test_path>` folder.
- Preserve backward compatibility by keeping defaults aligned with the encode script and allowing an override only via the CLI flag.

### 3) `scripts/run_prc_cropping_experiment.py`
- Accept a `--bits` argument and forward it when reconstructing `exp_id` (include `_bits_<bits>` in `build_exp_id`).
- Pass `--bits` through to the upstream `decode.py` invocation so detection uses the matching key namespace.
- Keep `--exp-id` override functionality, but note in the help text that `--bits` participates in the default `exp_id` and must match the one used during encoding if an override is supplied.

### 4) `PLAN.md` master script block
- Update the encode command to include `--bits` inside the bit-length loop so each run actually produces the requested payload size.
- Remove the manual `exp_id` string construction (or align it) to match the new default pattern from `encode.py`/`decode.py` (including `_bits_<bit_length>`). Use that consistent `exp_id` when pointing `run_prc_cropping_experiment.py` at `results/<exp_id>/original_images` and when storing raw CSVs.
- Note that these changes still require GPU execution in Colab; no local run is feasible here.

### 5) Optional bookkeeping
- If any downstream scripts assume the old `exp_id` format when reading from `PRC-Watermark/results/`, adjust those paths to include the bit suffix (e.g., plotting or aggregation scripts that might inspect `exp_id`). The existing CSV schemas already record `bit_length`, so no structural change is needed there.

## Expected outcome
After implementing the above changes, the Colab master script will:
- Generate distinct key files and image folders for 512-bit and 2500-bit PRC watermarks.
- Successfully call `KeyGen` with the correct `message_length` for each bit-length loop iteration.
- Run cropping and detection using the matching keys without path mismatches, enabling the full experiment to execute on GPU-backed Colab as intended.
