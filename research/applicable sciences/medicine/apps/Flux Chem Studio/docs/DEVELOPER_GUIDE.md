# Flux Chem Studio - Developer Guide

This document provides a technical guide for developers onboarding, extending, or building **Flux Chem Studio**.

---

## 1. System Architecture

Flux Chem Studio is structured as an offline-first desktop application consisting of a web-based GUI frontend and a Python-based biophysical solver backend.

```mermaid
graph TD
    A[macOS/Linux Desktop Window (PyWebView)] -->|HTTP / JSON / JS Bridge| B[FastAPI Local Server (Uvicorn)]
    B --> C[EFM Biophysics Solver (PyTorch)]
    B --> D[API Client (RCSB, PubChem, ChEMBL)]
    B --> E[Static Assets (frontend/ HTML/CSS/JS/3Dmol.js)]
    C --> F[PDB Pocket Core / Density Fitting]
```

### Frontend (`frontend/`)
- **`index.html` & `index.css`**: Core UI layout using premium dark-mode glassmorphism and modern flexbox-based LaTeX math notation formatting.
- **`app.js`**: Core UI logic, 3Dmol.js viewer initialization, events binding, and async endpoints interaction.
- **`docs.html` & `docs.css`**: In-app documentation, user guides, and interactive benchmarking suite interface.
- **`3Dmol-min.js`**: Local 3D molecular visualizer (100% offline compliant, no CDN dependency).

### Backend (`engine/`)
- **`server.py`**: FastAPI server handling local endpoints (`/fetch_target`, `/fetch_ligand`, `/run_screening`, `/run_evolution`, `/run_validation_benchmark`, `/run_statistical_validation`, `/version`). Serves static files and manages background statistical validation tasks.
- **`solver.py`**: The biophysical core. Solves the 3D density-dependent Nonlinear Klein-Gordon (NLKG) equation using PyTorch tensor operations.
- **`api_client.py`**: Local caching wrapper around RCSB PDB GraphQL, PubChem REST, and ChEMBL APIs.
- **`validation_pipeline.py`**: Statistical engine for regression validation. Calculates Pearson, Spearman, MAE, and generates calibration data.

---

## 2. Mathematical Equations

The Eholoko Fluxon Model (EFM) score is derived from the **Nonlinear Klein-Gordon (NLKG)** equation:

$$\nabla^2 \phi - m^2 \phi + \lambda \phi^3 = -4\pi \rho(\mathbf{r})$$

Where:
- $\phi$ is the electrostatic potential.
- $m$ is the screening parameter representing the ionic strength of the pocket.
- $\lambda$ is the self-interaction coupling constant representing local dielectric polarization.
- $\rho(\mathbf{r})$ is the 3D density distribution of the protein atoms.

The EFM docking score $S_{\text{EFM}}$ is computed over the overlap of the ligand density $\rho_L$ and the potential field $\phi_P$:

$$S_{\text{EFM}} = \int \phi_P(\mathbf{r}) \rho_L(\mathbf{r}) \, d^3\mathbf{r}$$

To correct for ligand size bias, the score is normalized by the number of heavy atoms $N$:

$$S_{\text{EFM, corrected}} = \frac{S_{\text{EFM}}}{N^{\alpha}}$$

---

## 3. Development Workflow

### Prerequisites
- Python 3.9 to 3.13
- PyTorch, FastAPI, PyWebView, Uvicorn, NumPy, Requests
- **For Linux Development**: System-level GUI and WebKit libraries are required (e.g. `python3-gi`, `python3-gi-cairo`, `gir1.2-webkit2-4.1` on Debian/Ubuntu, or `webkit2gtk4.1` on Fedora/RHEL).

### Setting Up a Development Environment
1. Clone the repository.
2. Initialize virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies in editable mode:
   ```bash
   pip install -e .
   ```
4. Run the application locally:
   ```bash
   flux-chem-studio
   ```

### Running the Test Suite
Tests are written with `pytest`. Ensure the virtual environment is active:
```bash
# Run all tests
PYTHONPATH=. pytest

# Run specific unit/UI tests
PYTHONPATH=. pytest tests/test_solver.py
PYTHONPATH=. pytest tests/test_ui.py
```

---

## 4. Calibration & Statistical Benchmarks

### Class-Stratified Calibration Fits
Different target protein classes (Kinases, GPCRs, Nuclear Receptors, Proteases) require specific regression calibrations to map raw EFM scores to predicted $pK_i$ values:

$$pK_i = \text{Slope} \times S_{\text{EFM, corrected}} + \text{Intercept}$$

Calibration regression coefficients are maintained in `engine/server.py` inside `compute_calibration_for_class`.

### Re-running the 100-Target Validation Dataset
To update or recalibrate the validation statistics:
1. Compile the validation set (requires internet for initial caching):
   ```bash
   PYTHONPATH=. python scratch/compile_validation_set.py
   ```
2. Execute the validation pipeline:
   ```bash
   PYTHONPATH=. python engine/validation_pipeline.py 500 100
   ```
This updates `data/validation_results.json` and creates a detailed `docs/VALIDATION_REPORT.md`.

---

## 5. Building Standalone Desktop Executables

The build pipeline uses **PyInstaller** to package the application into a platform-native executable. Note that PyInstaller does not support cross-compilation; you must build on the target operating system.

```bash
# Activate virtual environment
source venv/bin/activate

# Install pyinstaller (if not present)
pip install pyinstaller

# Run the build script
python build_app.py
```

### Build Artifacts
- **On macOS**: Compiles a double-clickable macOS app bundle under `dist/Flux Chem Studio.app`.
- **On Linux**: Compiles a standalone directory containing the executable binary under `dist/Flux Chem Studio/`.
- The packaged executable includes all local frontend resources (`frontend/3Dmol-min.js`) and local benchmark data (`data/validation_dataset.json`), satisfying all offline-compliance requirements.
