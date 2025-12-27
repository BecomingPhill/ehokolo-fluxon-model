# Eholoko Fluxon Model Compendium Build System

This document explains how to generate the **Eholoko Fluxon Model Compendium**, a comprehensive PDF volume compiled from the project's LaTeX research papers.

## Overview

The Compendium is built using a Python script, `build_latex_compendium.py`, which orchestrates the following:
1.  **Structure Definition**: Defines the order of papers (Chapters/Sections) in the `STRUCTURE` dictionary.
2.  **Content Aggregation**: Finds the `.tex` source files for each paper in the `research/` directory.
3.  **Image Recovery**: 
    - Looks for images in the local `media/` folder relative to the paper.
    - **Fallback**: If an image is missing locally, it searches the `EFM V4` directory (defined in the script) and copies it.
4.  **Normalization**: 
    - Removes individual paper preambles (`\documentclass`, `\begin{document}`, etc.).
    - Extracts custom definitions (`\newcommand`) to the master preamble.
    - Redefines `thebibliography` to fit within sections.
    - Formats code blocks using `listings`.
5.  **Compilation**: Uses `pdflatex` to build the master `compendium.tex` file in a temporary `latex_build/` directory.

## Prerequisites

- **Python 3.x**
- **LaTeX Distribution** (e.g., TeX Live, MacTeX) with `pdflatex`.
- **EFM V4 Directory**: A reference directory containing image assets. Update the `EFM_V4_DIR` variable in the script if this location changes.

## How to Build

1.  Open a terminal in the project root.
2.  Run the build script:
    ```bash
    python3 build_latex_compendium.py
    ```
3.  The script will:
    - Create a `latex_build/` directory.
    - Copy and process all files.
    - Run `pdflatex` (twice, to resolve references).
    - Move the final PDF to the project root with the name `Eholoko_Fluxon_Model_Compendium_YYYY-MM-DD.pdf`.

## Updating the Compendium

### Adding a New Paper
1.  Ensure the paper's `.tex` file and associated `media/` folder are in the `research/` directory.
2.  Open `build_latex_compendium.py`.
3.  Add the paper's **PDF filename** (which corresponds to the `.tex` file) to the appropriate list in the `STRUCTURE` dictionary.
    ```python
    STRUCTURE = {
        "New Chapter Name": [
            r"My New Paper Title.pdf",
            ...
        ]
    }
    ```
    *Note: The script searches for `My New Paper Title.tex` based on this entry.*

### Modifying Build Settings
- **LaTeX Preamble**: Edit the `master_content_start` list in the `main()` function to add packages or change global styles.
- **Code Formatting**: Adjust the `\lstset` block in `master_content_start`.

## Troubleshooting

- **Missing Images**: If an image is not found, check if it exists in `research/.../media` or the `EFM V4` directory. The script prints warnings for missing images.
- **Compilation Errors**: Check `latex_build/compendium.log` for detailed LaTeX error messages. Common issues include special characters in titles (handled by the script, but check source) or missing packages.
