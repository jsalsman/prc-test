# AGENTS

This repository, prc-test, is for experimentally evaluating how robust the PRC watermark is against cropping attacks on images, using the official PRC-Watermark implementation and the accompanying paper in the root directory.

Repository layout (expected)

- AGENTS.md
- PLAN.md (optional; working prompt for the main agent)
- 2410.07369v4.pdf (PRC watermark paper)
- PRC-Watermark/ (git subdirectory; clone of https://github.com/XuandongZhao/PRC-Watermark)
- results/
  - cropping/
    - prc_cropping_raw_512bits.csv
    - prc_cropping_raw_2500bits.csv
    - prc_cropping_results_512bits.csv
    - prc_cropping_results_2500bits.csv
    - prc_cropping_summary_512bits.png.base64
    - prc_cropping_summary_2500bits.png.base64
    - REPORT.md
- scripts/ (optional; orchestration, plotting, utilities)
- data/ (runtime data only; should be gitignored)
  - images/
    - 512bits/
      - original/
      - crop_100/, crop_90/, …, crop_10/
    - 2500bits/
      - original/
      - crop_100/, …, crop_10/

Binary and image file policy

- Pull requests must not contain any binary or image files. In particular, do not commit:
  - Image formats such as .png, .jpg, .jpeg, .gif, .bmp
  - Document formats such as .pdf
  - Model and data formats such as .pt, .pth, .ckpt, .bin, .onnx, .npy, .npz, .pkl
  - Any other opaque binary format
- Experimental images and other binary artifacts (for example original watermarked images, cropped images, temporary plots) must live only in runtime directories that are gitignored (such as data/ and any temporary files in results/).
- If a binary artifact must be preserved in the repository for review, it must be converted to a base64-encoded text file and the original binary deleted before committing. For example:
  - Instead of committing prc_cropping_summary_512bits.png, commit prc_cropping_summary_512bits.png.base64 and delete the .png.
  - Use the naming pattern “original_name.ext.base64” for any such files (for example .png.base64, .jpg.base64, .pdf.base64).
- Before opening a pull request:
  - Ensure that no .png, .jpg, .jpeg, .gif, .bmp, .pdf, model files, or similar binaries are staged.
  - Either keep binaries only in gitignored paths, or convert them to .base64 and delete the originals before committing.
- A helper script in scripts/ may automate base64 conversion, but the invariant is strict: pull requests must be text-only, with binary artifacts represented as base64 text files.

Primary agent: PRC Cropping Experiment Agent

Responsibilities

1) Environment and code

- Treat PRC-Watermark as the authoritative implementation. Use its code and configuration; do not reimplement the PRC watermark or modify its cryptographic or detection logic.
- Follow the PRC-Watermark README to:
  - Install dependencies.
  - Download and configure the required models and datasets.
  - Run the encoding and decoding scripts.
- Basic usage of PRC-Watermark:
  - To generate N watermarked images and corresponding keys, create the keys directory and run the encode script with a test_num parameter.
  - To test watermark detection on the default test images, run the decode script with the same test_num.
  - To test detection on attacked or cropped images, run the decode script with test_num and a test_path pointing to the directory containing the attacked images.
  - The detection output is binary: watermark detected or not detected.
  - The decode script supports setting a targeted False Positive Rate (FPR); the default is 0.00001. You may adjust this only if required, and should record any change.
  - Model and dataset can be changed using configuration options (for example model_id and dataset_id) if necessary, but for this experiment the defaults are acceptable unless there is a clear motivation to change them.
  - If there are issues with the HuggingFace cache directory in encode or decode, adjust the cache path as suggested in the PRC-Watermark documentation.
- All new orchestration and analysis code should live in prc-test (for example in scripts/), not inside PRC-Watermark. Call into PRC-Watermark via imports or subprocesses.

2) Experimental design

Goal: quantify the robustness of PRC watermark detection against cropping by systematically cropping watermarked images to different retained-area levels and measuring detection success rates.

Key parameters:

- Bit lengths:
  - 512 bits (primary robust setting in the paper)
  - 2500 bits (higher-capacity setting)
- Prompts:
  - Reuse or adapt prompts from the PRC-Watermark repository or its default dataset.
  - Use a fixed set of prompts so that 512-bit and 2500-bit experiments are comparable.
- Number of images:
  - Choose a fixed N per bit length (for example, between 200 and 1000) so that estimated detection rates are meaningful.
- Crop percentages:
  - Keep-area percentages: 100, 90, 80, 70, 60, 50, 40, 30, 20, and 10.
- Cropping strategy:
  - Use deterministic central cropping so the experiment is repeatable.
  - For a chosen keep-area fraction a between 0 and 1, compute a scale factor s equal to the square root of a and crop a centered region whose width and height are s times the original dimensions.
  - If the detector expects a fixed resolution, resize the cropped images back to that resolution.

3) Image generation

For each bit length configuration (512 and 2500 bits):

- Configure PRC-Watermark so that the encoder produces images carrying a watermark with the desired bit length and an appropriate FPR (for example the default).
- Using the chosen prompt set, generate a total of N watermarked images for each bit length.
- For each generated image, record metadata such as:
  - Image identifier or filename
  - Prompt identifier or prompt text
  - Bit length
  - Generation random seed
  - Any relevant key or configuration identifiers
- Save original, uncropped watermarked images only in runtime directories that are gitignored, for example:
  - data/images/512bits/original/
  - data/images/2500bits/original/
- Immediately verify detection on the uncropped images using the decode script:
  - Run detection with test_num and with test_path pointing to the directory containing the generated images, if required by the code.
  - Confirm that detection on unmodified images is at or near the expected true positive rate; record any unexpected failures.

4) Cropping procedure

For each bit length and each original image:

- For each keep percentage in 100, 90, 80, 70, 60, 50, 40, 30, 20, 10:
  - Compute a keep-area fraction equal to the keep percentage divided by 100.
  - Compute a scale factor equal to the square root of the keep-area fraction.
  - For an image of width W and height H, compute cropped width and height by multiplying W and H by the scale factor and rounding appropriately.
  - Crop a centered region of those dimensions.
  - If necessary, resize the cropped image back to the resolution expected by the detector.
  - Save cropped images only in gitignored directories, such as:
    - data/images/512bits/crop_90/, data/images/512bits/crop_80/, and so on
    - data/images/2500bits/crop_90/, etc.
  - Record metadata linking each cropped image to its original image, including bit length, keep percentage, and crop dimensions.
- Ensure that all cropped images remain uncommitted; they are runtime artifacts only.

5) Detection and logging

Use the official detection scripts from PRC-Watermark for all detection; do not modify detection logic.

For each bit length and each keep percentage:

- Run the decode script on the corresponding cropped image directory:
  - Use test_num equal to the number of images in that crop level.
  - Use test_path pointing at the directory containing cropped images for that bit length and keep percentage.
- The decode script outputs a binary decision per image (watermark detected or not). If it also provides a detection score or statistic, capture that as well.
- For every image, record at least:
  - Image identifier
  - Prompt identifier
  - Bit length (512 or 2500)
  - Keep percentage
  - Binary detection result (for example 1 if detected, 0 if not detected)
  - Any available detection score (optional)
- Store raw detection data in text CSV files that are safe to commit:
  - results/cropping/prc_cropping_raw_512bits.csv
  - results/cropping/prc_cropping_raw_2500bits.csv

6) Aggregation and detection-rate computation

From the raw CSVs, compute detection rates for each combination of bit length and keep percentage.

For each bit length and keep percentage:

- Count the total number of images evaluated.
- Count how many images were detected as watermarked.
- Compute the detection rate as the number detected divided by the total number.

Write the aggregated results to:

- results/cropping/prc_cropping_results_512bits.csv
- results/cropping/prc_cropping_results_2500bits.csv

Each row of these summary CSVs should contain, at a minimum:

- Bit length
- Keep percentage
- Number of images
- Number detected
- Detection rate

7) Robustness threshold determination

Define robustness thresholds per bit length as the smallest keep percentage at which detection remains at or above specific success levels.

For each bit length separately:

- For each target success level (100 percent, 99 percent, 95 percent, 90 percent):
  - Identify the smallest keep percentage where the detection rate is at or above that level.
  - Record that keep percentage as the robustness threshold for that success level and bit length.
  - If no tested keep percentage meets the level, record that the threshold is not achieved within the tested range.
- Summarize these thresholds in a small markdown-style table in the report, with columns such as:
  - Bit length
  - Target success level
  - Threshold keep percentage

8) Plotting and visualization

Create two plots to visualize cropping robustness:

- One plot for the 512-bit watermark
- One plot for the 2500-bit watermark

For each plot:

- The horizontal axis is the keep percentage (100 down to 10).
- The vertical axis is the detection rate (from 0 to 1).
- Plot the detection-rate curve across keep percentages.
- Add reference lines at detection rates of 1.0, 0.99, 0.95, and 0.90.
- Visually mark or annotate the robustness thresholds where these success levels are achieved.

Handle plot files according to the binary policy:

- Initially, plots may be generated as .png files in results/cropping/ during local work.
- Before committing, convert each .png to a base64 text file with the same name plus the .base64 suffix (for example prc_cropping_summary_512bits.png.base64).
- Delete the original .png files and commit only the .base64 files.

9) Reporting

Prepare a concise report in results/cropping/REPORT.md that includes:

- A short description of the experimental setup:
  - Model and configuration choices (including bit lengths and FPR).
  - Prompt selection strategy.
  - Number of images per bit length.
- The detection-rate tables per bit length and keep percentage.
- The robustness-threshold table summarizing the keep percentage at which detection remains at or above 100, 99, 95, and 90 percent, for each bit length.
- References to the plot artifacts by filename (the .png.base64 files), along with a brief explanation of how to decode them back into viewable .png files using standard base64 tools.
- Any noteworthy findings or anomalies, such as:
  - Differences in robustness between 512-bit and 2500-bit watermarks.
  - Unexpected failures at high keep percentages.

Expectations

- Prefer simple, reproducible scripts as entry points, such as a single driver script that runs the full experiment for a given bit length.
- Keep configuration (paths, prompts, number of images, crop percentages) centralized so that the experiment can be rerun or extended easily.
- Do not modify the cryptographic or detection logic of PRC-Watermark; all changes should be in orchestration, data handling, or plotting.
- Maintain the strict invariant that pull requests contain no binary or image files; only text files, including base64 encodings of any necessary binary artifacts, may be committed.
