Working prompt plan:

You are an engineering agent working inside a private GitHub repository named "prc-test". In the root of this repo there is:

- A directory "PRC-Watermark", which is a clone of https://github.com/XuandongZhao/PRC-Watermark.
- A PDF named "2410.07369v4.pdf", which describes the PRC watermark and reports watermark capacities (including 512 bits and higher capacities like 2500 bits for non-attacked images).
- An AGENTS.md file describing your responsibilities for a cropping-robustness experiment and the repository’s binary file policy.

Your goal is to experimentally evaluate how robust the PRC watermark is to image cropping, using the official PRC-Watermark implementation, and to produce clean, reproducible code and results.

High-level objectives

1) Use the PRC-Watermark code to generate images that carry PRC watermarks at two bit lengths: 512 bits and 2500 bits.
2) For each watermark configuration, systematically crop the images so that only specific percentages of the original area are retained: 100, 90, 80, 70, 60, 50, 40, 30, 20, and 10 percent.
3) Use the official PRC detection scripts (from the PRC-Watermark repo) to test detection on each cropped image.
4) For each bit length and each keep percentage, compute detection rates; then:
   - Summarize the results in CSV tables.
   - Plot detection-rate curves.
   - Determine and clearly report robustness thresholds: the smallest keep percentage at which the detection rate is at least 100, 99, 95, and 90 percent.

Binary and image file policy

- Do not commit raw binary or image files into pull requests:
  - No .png, .jpg, .jpeg, .gif, .bmp, .pdf, .pt, .pth, .ckpt, .bin, .npy, .npz, .pkl, .onnx, or similar binary files in PRs.
- Experimental images (original watermarked images, cropped images, temporary plots) should live only in gitignored runtime directories (for example ./data/ and any temporary binaries in ./results/).
- Any artifact that must be versioned and is naturally an image or binary must be converted to a base64-encoded text file before being committed:
  - For example, prc_cropping_summary_512bits.png should be converted to prc_cropping_summary_512bits.png.base64; the original .png must then be deleted before committing.
- Always check git status before a pull request to confirm that only text files (including *.base64) are staged; if any binary slips in, remove it from git and either gitignore it or convert it to base64 first.

You may create a helper script (for example in ./scripts/) to perform base64 conversion and deletion, and you should document how to decode these artifacts back to binaries (e.g. in REPORT.md).

Basic PRC-Watermark usage you should rely on

All of these commands are run inside the PRC-Watermark directory; you must adapt test_num N and paths as appropriate.

- Generate N watermarked images and a key:

  mkdir -p keys
  python encode.py --test_num N

- Decode watermarks from the default test images:

  python decode.py --test_num N

- Decode watermarks from attacked (cropped) images stored in a different test folder:

  python decode.py --test_num N --test_path path_to_cropped_images

- Optionally set the targeted False Positive Rate (FPR), default is 0.00001:

  python decode.py --test_num N --fpr 0.00001

You may adjust model_id and dataset_id in configuration files if necessary, but keep changes minimal; follow the defaults for this experiment unless there is a compelling reason to change them.

Concrete workflow to implement

1) Environment setup
   - Inspect "./PRC-Watermark" and its README to learn:
     - How to install dependencies.
     - How to download and configure the required diffusion model weights.
     - How encode.py and decode.py expect their inputs and configuration.
   - Provide a short setup script or README section in the prc-test repo (not inside PRC-Watermark) that lists the exact commands needed to prepare the environment.
   - Ensure ./data/ and any other heavy/binary directories are gitignored.

2) Image generation

   For each bit length b in {512, 2500}:

   - Configure PRC-Watermark so that encode.py produces watermarked images with b watermark bits.
   - Choose a fixed set of prompts, either from PRC-Watermark’s default dataset or a small curated list; use the same prompt set for both bit lengths.
   - Decide on a test_num N (e.g. between 200 and 1000 per bit length) and generate N watermarked images for each b using encode.py.
   - Save original watermarked images into runtime-only directories:
     - ./data/images/512bits/original/
     - ./data/images/2500bits/original/
   - Log metadata for each image in a CSV (safe to commit), including:
     - image_id or filename
     - prompt_id or prompt text
     - bit_length
     - generation seed
     - any key/config identifiers as needed.
   - Verify that detections on unmodified images are as expected:
     - Use decode.py (with or without test_path, depending on where images are stored).
     - Confirm high true positive rate for both 512-bit and 2500-bit settings; log any unexpected failures.

3) Cropping implementation

   - Implement a deterministic central cropping function in a script under ./scripts/, such as crop_images.py.
   - For each image and each keep percentage p in {100, 90, 80, 70, 60, 50, 40, 30, 20, 10}:
     - Let a = p / 100.
     - Compute s = sqrt(a).
     - For an image of size W x H, compute:
       - Wc = round(W * s)
       - Hc = round(H * s)
     - Crop the centered Wc x Hc patch.
     - Resize back to the resolution expected by decode.py if necessary.
     - Save cropped images into runtime-only directories:
       - ./data/images/{bit_length}bits/crop_{p}/
   - Maintain a CSV mapping original images to cropped images and recording crop parameters.

   These image directories are for local experiments only and must not be committed.

4) Detection on cropped images

   - For each bit_length and each keep percentage p:
     - Run decode.py with:
       - test_num equal to the number of images being evaluated.
       - test_path pointing at the relevant cropped directory; for example:

         python decode.py --test_num N --test_path ./data/images/512bits/crop_90

     - Capture the binary detection outputs (detected/not detected) and any scores, if decode.py exposes them.
   - Record detection results in text CSV files in ./results/cropping/:
     - prc_cropping_raw_512bits.csv
     - prc_cropping_raw_2500bits.csv

   Each row should contain at least:

   - image_id
   - prompt_id
   - bit_length
   - keep_percentage
   - detected (0 or 1)
   - detector_score (optional)

5) Aggregation and robustness thresholds

   - Write a separate analysis script (for example ./scripts/analyze_cropping_results.py) that:
     - Loads prc_cropping_raw_*.csv.
     - Aggregates detection statistics by bit_length and keep_percentage:
       - n_images
       - n_detected
       - detection_rate = n_detected / n_images
     - Writes summary CSV files:
       - prc_cropping_results_512bits.csv
       - prc_cropping_results_2500bits.csv
   - For each bit length separately, compute robustness thresholds for target success levels s in {1.0, 0.99, 0.95, 0.90}:
     - Find the smallest keep_percentage p with detection_rate >= s.
     - If no such p exists, note that the threshold is not achieved within the tested crop levels.

6) Plotting and handling plot artifacts

   - Using a plotting script (for example ./scripts/plot_cropping_results.py), construct two plots:

     Plot 1: 512-bit watermark

     - x-axis: keep percentage.
     - y-axis: detection rate.
     - Curve: detection_rate for each keep_percentage.
     - Horizontal reference lines at 1.0, 0.99, 0.95, 0.90.
     - Annotations marking robustness thresholds.

     Plot 2: 2500-bit watermark

     - Same design for 2500-bit results.

   - Save each plot initially as a .png file:
     - ./results/cropping/prc_cropping_summary_512bits.png
     - ./results/cropping/prc_cropping_summary_2500bits.png

   - Then convert them to base64 text and delete the original .png files, committing only:
     - ./results/cropping/prc_cropping_summary_512bits.png.base64
     - ./results/cropping/prc_cropping_summary_2500bits.png.base64

   - Include in REPORT.md a brief instruction block describing how to decode these .png.base64 files back to .png for viewing.

7) Final report

   - Create or update ./results/cropping/REPORT.md with:
     - A concise description of:
       - Models and configuration used (bit lengths, FPR, default model/dataset).
       - Prompt selection and number of images per bit length.
     - Tables showing detection rates by keep percentage for each bit length.
     - A table summarizing robustness thresholds (bit_length, target_success_level, threshold_keep_percentage).
     - References to the base64-encoded plot files and a short “how to decode” snippet.
     - Any observations about differences between 512-bit and 2500-bit robustness under cropping.

Quality expectations

- Use simple, reproducible entry points, for example:

  - python scripts/run_prc_cropping_experiment.py --bit-length 512
  - python scripts/run_prc_cropping_experiment.py --bit-length 2500

- Keep all new code and scripts under the prc-test repo (not within PRC-Watermark itself), and refer into PRC-Watermark via imports or subprocess calls.
- Keep all configuration (paths, prompts, number of images, crop percentages) centralized.
- Maintain the invariant that pull requests contain no binary/image files, only text (including base64-encoded representations where necessary).
