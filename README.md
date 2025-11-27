# PRC Watermark Cropping Robustness Experiment

This repository (`prc-test`) is dedicated to experimentally evaluating the robustness of the PRC watermark against image cropping attacks. It leverages the official PRC-Watermark implementation and the accompanying research paper to systematically test watermark detection rates under various cropping percentages.

## Running the Experiments in Google Colab

To run the full cropping robustness experiment:

### NOTE: I have already added this cell to the end of the notebook, but I have not run it because I ran out of free Colab GPU credits. -jsalsman

1.  Open the `PLAN.md` file in this repository.
2.  Locate the "Master Script for Cropping Robustness Experiment (Colab)" section.
3.  Copy the entire Python code block from that section.
4.  Paste it into a new code cell in your Google Colab environment.
5.  Run the cell.

This master script will orchestrate all necessary steps, including image generation, cropping, watermark detection, result aggregation into CSVs, and the generation of plots directly within Colab.

## Project Overview and Key Findings

### Data Analysis Key Findings

*   **`PLAN.md` Revision**: The `prc-test/PLAN.md` file was updated to remove all references to base64 encoding. Specifically:
    *   The "Binary and image file policy" was revised to explicitly state that experimental images should be gitignored, while final plot files (PNG format) are to be saved directly in `results/cropping/` and committed, removing instructions for base64 conversion and deletion of original PNGs.
    *   The "Plotting and handling plot artifacts" section was modified to instruct direct saving of PNG plot files, replacing previous base64 conversion steps.
    *   References to plot files in the "Final report" and "Quality expectations" sections were updated from `.base64` files to direct `.png` files.
*   **`AGENTS.md` Revision**: The `prc-test/AGENTS.md` file was similarly revised to eliminate base64 encoding requirements. Key changes include:
    *   The "Repository layout (expected)" section updated plot file extensions from `.png.base64` to `.png`.
    *   The "Binary and image file policy" was reworded to permit direct commitment of final plot images (PNG format) into `results/cropping/`, while maintaining the policy against committing other experimental binary/image files.
    *   Instructions in the "Plotting and visualization" and "Reporting" sections were adapted to reflect direct PNG file handling, removing base64 conversion steps.
    *   The "Expectations" section now permits final plot PNGs, alongside text files, in pull requests.
*   **Script Examination**:
    *   `prc-test/PRC-Watermark/encode.py` and `decode.py` were reviewed and found to contain no base64 encoding logic. Their parameters and output/input paths (`results/{exp_id}/original_images/`) were noted for experiment configuration.
    *   Among the cropping scripts in `prc-test/scripts/`, `crop_images.py`, `analyze_cropping_results.py`, and `run_prc_cropping_experiment.py` were found to be free of base64 logic.
    *   **`prc-test/scripts/plot_cropping_results.py` was identified as the sole script requiring modification.** It previously included an import for `convert_base64`, a `--base64` command-line argument, and conditional logic within the `plot_curve` function to perform base64 encoding and delete original PNGs.
*   **`plot_cropping_results.py` Modification**: All base64-related functionalities were removed from `prc-test/scripts/plot_cropping_results.py`, including the `convert_base64` import, the `--base64` argument, the `use_base64` parameter in `plot_curve`, and the conditional base64 encoding block.

### Insights or Next Steps

*   The modifications ensure that the experiment documentation and plotting scripts are fully aligned with a workflow that generates and commits PNG plot files directly, eliminating the overhead and complexity of base64 encoding for visual artifacts within the Google Colab environment.
*   The system is now configured to streamline the generation, analysis, and plotting of cropping experiment results by outputting `.png` files directly, which is crucial for subsequent steps involving result visualization and reporting without intermediate conversion steps.
