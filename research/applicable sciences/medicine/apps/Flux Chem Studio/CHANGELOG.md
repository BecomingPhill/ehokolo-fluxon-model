# Changelog

All notable changes to **Flux Chem Studio** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-22

### Added
- **EFM Biophysics Solver Engine**: High-performance PyTorch implementation of the 3D density-dependent Nonlinear Klein-Gordon (NLKG) solver with automated target class detection and custom calibration regression fits (Kinases, GPCRs, Nuclear Receptors, Proteases).
- **De Novo Topological growth**: EFM-guided grew-and-branch algorithm utilizing progressive steric clash relaxation (down to 1.0 Å limit) and realistic carbon/nitrogen/oxygen/sulfur valency limits.
- **3D Molecular Visualization Panel**: Embedded 3Dmol.js viewer supporting cartoon, stick, and sphere representations, active site zoom, and dynamic alignment.
- **Interactive Statistical Benchmarking**: Standardized 100-target validation dataset and runtime statistics (Pearson correlation, Spearman correlation, MAE, residual error plotting) available via the `/docs.html` page.
- **Documentation & User Guide**: Embedded biochemical translation guide explaining NLKG equations, electrostatic mapping, and EFM descriptors.
- **Standard python Packaging**: modern setuptools metadata (`pyproject.toml`, `setup.py`) and a command-line entry point `flux-chem-studio`.
- **Standalone Build Pipeline**: `build_app.py` script to compile the application into a double-clickable macOS bundle (`Flux Chem Studio.app`).

### Fixed
- **Export Redirection on macOS**: Resolved an issue where clicking the "Export Results" button inside the compiled desktop app redirected the window to a raw view of the SDF file. Implemented a native file save dialog interface (`window.create_file_dialog`) bridged between Python (PyWebView) and JavaScript (`app.js`) to prompt standard macOS save panels for JSON results and SDF ligands.
