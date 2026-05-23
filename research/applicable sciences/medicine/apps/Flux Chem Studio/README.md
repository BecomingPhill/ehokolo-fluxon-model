# Flux Chem Studio

Flux Chem Studio is an offline-first molecular design and drug discovery desktop application that integrates the **Eholoko Fluxon Model (EFM)** biophysical solvers with 3D molecular visualization, virtual screening, and topological de novo ligand evolution.

---

## Features

* **EFM Biophysical Engine**: PyTorch-accelerated 3D density-dependent Nonlinear Klein-Gordon (NLKG) solver.
* **Topological De Novo Evolution**: EFM-guided grew-and-branch chemical scaffold search.
* **Offline Molecular Viewer**: 3Dmol.js viewer for real-time visualization of pockets, ligands, and docking scores.
* **Statistical Benchmarking Suite**: Stratified 100-target validation pipeline.

---

## Installation

To install Flux Chem Studio in editable mode, run:

```bash
pip install -e .
```

### Linux System Prerequisites
On Linux, the desktop GUI wrapper (`pywebview`) requires system-level GUI and WebKit libraries:

* **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
  ```
* **Fedora/RHEL**:
  ```bash
  sudo dnf install python3-gobject webkit2gtk4.1
  ```

---

## The Core Science: EFM Biophysical Docking

Unlike traditional molecular docking tools that rely on empirical force fields or classical quantum mechanics, Flux Chem Studio models molecules as continuous, complex scalar wave fields ($\psi$) governed by state-dependent physics.

* **Specific Phase Friction ($E$)**: Measures wave gradient energy, representing localized phase alignment and wave curvature:
  $$E = \frac{\int |\nabla \psi|^2 d^3r}{\int |\psi|^2 d^3r}$$
* **Friction Shift ($\Delta E$)**: The docking score. Calculated as:
  $$\Delta E = E_{\text{complex}} - E_{\text{target}}$$
  * **Stable Binding ($\Delta E < 0$)**: The ligand forms a low-energy, complementary wave state with the active pocket.
  * **Steric Clash ($\Delta E > 0$)**: Indicates phase mismatch and steric collision.

---

## Step-by-Step Usage Guide

### 1. Launch the Application
Run the launcher command:
```bash
flux-chem-studio
```
This opens the desktop interface. The application operates offline, caching all downloaded structural files in the local `data/` directory.

### 2. Fetch the Target Protein
1. In the **Target Protein** panel, enter a four-letter PDB ID (e.g., `1HSG` for HIV-1 Protease) or search for targets by name.
2. Click **Fetch PDB** to download the coordinates. The engine automatically filters pocket residues and centers the simulation box on the active site.

### 3. Load or Fetch the Ligand (Online / Offline)
* **Online Mode (PubChem)**: Set the ligand source to **PubChem**, enter the compound name (e.g., `Saquinavir` or `Artemisinin`), and click **Fetch PubChem** to retrieve its 3D coordinates.
* **Offline Mode (Local Library)**: Set the ligand source to **Cached African Natural Product Library** and select a compound from the dropdown (e.g., *Artemisinin*, *Quinine*, *Nimbolide*, or *Cryptolepine*). This loads structures directly from the pre-compiled SQLite database (`data/african_natural_products.db`), isolated from indigenous medicinal plants, allowing complete offline screening.

### 4. Run the Docking Simulation
1. Set the **Simulation Steps** (default `500`) and click **Run EFM Docking**.
2. The PyTorch solver will relax the wave field using a semi-implicit Verlet integrator. The 3D viewer will display the pocket and ligand, while the sidebar outputs the final $\Delta E$ score and calibrated $pK_i$ binding affinity.

### 5. Run De Novo Evolution
1. Click **De Novo Evolution** to grow a complementary ligand scaffold atom-by-atom.
2. The algorithm searches 26 grid directions, selecting elements and coordinates that minimize the EFM specific phase friction, exporting a customized `.sdf` file of the evolved compound.

---

## Statistical Benchmarking Suite

The application includes a local validation suite of 100 target-ligand complexes with known wet-lab affinities. To execute this benchmark offline and verify the solver's predictive correlation ($r \approx 0.75$):

```bash
python engine/validation_pipeline.py
```
This generates a detailed validation report in `docs/VALIDATION_REPORT.md`.

---

## Development and Building

To compile the application as a standalone desktop executable:

```bash
python build_app.py
```
* **On macOS**: Compiles a double-clickable `dist/Flux Chem Studio.app` bundle.
* **On Linux**: Compiles a standalone executable folder under `dist/Flux Chem Studio/`.

For code guidelines and architecture, see [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md). Refer to [EFM_BIOCHEM_GUIDE.md](docs/EFM_BIOCHEM_GUIDE.md) for detailed biophysical theory.

