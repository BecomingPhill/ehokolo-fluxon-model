# Changelog

All notable changes to **Flux Chem Studio** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.2] - 2026-05-23

### Fixed
- **Native Save Panel Extension Enforcement**: Enforced file extension validation inside `main.py`'s `save_file` method. If the user or macOS dialog outputs a filename path without the appropriate extension (e.g., saving `flux_chem_results_1HSG` without `.json` or `ligand_1HSG` without `.sdf`), the backend automatically appends the expected file extension. This guarantees exported files are immediately readable in downstream molecular visualization and drug design workflows.

## [1.2.1] - 2026-05-23

### Fixed
- **Virtual Screening Success Banner**: Aligned the virtual screening results banner condition to evaluate the calibrated `is_favorable` boolean (which accounts for class calibration shifts on positive $\Delta E$ boundary targets like Viral Proteases) instead of strictly checking raw $\Delta E < 0$, correcting erroneous "CLASH" flags for nanomolar active binders.

## [1.2.0] - 2026-05-23

### Added
- **State-Dependent Nuclear Shell Scaling (SDNS)**: Implemented core potential scaling where nuclear potential radii scale geometrically with element atomic numbers ($Z$) based on EFM Periodic Table Harmonic Constants ($R_H = 1.001227$, $\sigma_i = \sigma_0 \cdot R_H^{Z_i}$). Resolves coordination covalent bonding potential depth anomalies.
- **Dynamical Soliton Lability ($L_{\text{sol}}$)**: Integrated a dynamic lability module measuring pocket flexibility variance under small Langevin thermal perturbations. Adds dynamic tagging (Blocker/Antagonist, Activator/Agonist, Unstable/Clash) in virtual screening and de novo evolution scorecards.
- **Lability Scorecard Integration**: Added Lability Index display in the biophysical scorecard and included lability summaries in offline JSON results exports.

### Changed
- **Validation Dataset Recalibration**: Re-ran the 100-target validation pipeline under the upgraded SDNS core potential solver, achieving a physically consistent global Pearson correlation of $r \approx 0.67$ ($p = 0.00e+00$) and Spearman rank correlation of $\rho \approx 0.65$.

## [1.1.0] - 2026-05-23

### Added
- **Localized Wavepacket Initialization**: Integrated target and ligand physical coordinates to initialize matter wave fields locally in `EFMSolver.run_simulation`, improving solver convergence and docking stability.
- **Gaussian-Smoothed Core Potentials**: Eliminated grid translation aliasing by regularizing nuclear core potentials with Gaussian functions.
- **Semi-Implicit Verlet Damping**: Improved numerical stability of wave relaxation under steep gradients using centered Verlet velocity-damping coefficients.
- **Calibrated EFM Energy Regression**: Retrained GPCR, Kinase, and Nuclear Receptor linear regression calibration parameters to strictly incorporate EFM energy terms ($-\Delta E$) rather than ligand size shortcuts, achieving a global Pearson correlation of $r \approx 0.78$ and a Mean Absolute Error of $0.38$ log units.

### Changed
- **Engine Calls Update**: Passed atom coordinates to all EFM simulation runs across virtual screening, de novo evolution, validation benchmarking, and unit/UI testing.

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
