# Flux Chem Studio: EFM & Biochemistry Integration Guide

Welcome to the **Eholoko Fluxon Model (EFM)** guide for biomedical researchers. This document bridges the gap between first-principles scalar wave thermodynamics and classical molecular docking, helping you perform virtual screening and de novo drug discovery without needing proprietary molecular dynamics licenses.

---

## 1. The Core Science: EFM vs. Traditional Biophysics

Traditional molecular docking software (e.g., AutoDock, Schrödinger) relies on empirical force fields or quantum mechanical (QM) calculations that estimate electron densities. EFM models physical matter as a continuous, complex scalar wave field ($\psi$) governed by the Non-Linear Klein-Gordon (NLKG) equation.

Here is how EFM concepts map directly to the biochemical concepts you already use:

### Conceptual Translation Bridge

| EFM Simulation Term | Standard Biochemical Equivalent | What it Means in Practice |
| :--- | :--- | :--- |
| **Harmonic Density State (HDS)** | Atomic/Electron Shell Regions | Matter waves organize into three discrete density states ($\rho = k|\psi|^2$) corresponding to core, mantle, and binding zones. |
| **HDS 1 (Core)** | Atomic Nucleus & Inner Shells | High-density regions that are strongly repulsive, representing nuclear centers and non-overlapping core electrons. |
| **HDS 2 (Mantle)** | Valence Electron / Covalent Shell | Mid-density regions where waves overlap to form stable covalent chemical bonds. |
| **HDS 3 (Binding)** | Electrostatic & Hydrogen Bonds | Low-density tail regions where weak attractions (hydrogen bonds, Van der Waals, polar interactions) occur. |
| **Specific Phase Friction ($E_{\text{spec}}$)** | Molecular Stacking / Wave Gradient Energy | A measure of how cleanly the ligand's matter waves overlap with the protein target. Calculated as: $E_{\text{spec}} = \frac{\int |\nabla \psi|^2 d^3r}{\int |\psi|^2 d^3r}$. |
| **Friction Shift ($\Delta E$)** | Relative Binding Energy / Score | Calculated as $\Delta E = E_{\text{complex}} - E_{\text{target}}$. A negative shift ($\Delta E < 0$) indicates stable binding. A positive shift ($\Delta E > 0$) signifies a steric clash. |
| **Lability Index ($L_{\text{sol}}$)** | Dynamical Soliton Lability | Langevin-perturbed lability. Measures wave stability under thermal noise. $L_{\text{sol}} < 0.05$ indicates a rigid Blocker/Antagonist; $L_{\text{sol}} \in [0.05, 0.15]$ indicates an Activator/Agonist; $L_{\text{sol}} > 0.15$ indicates steric clash. |
| **Verlet Wave Relaxation** | Energy Minimization / Optimization | Resolving the wave fields over time to find the lowest-energy structural conformation inside the pocket. |

---

## 2. Quick-Start Workflow: Running a Docking Assay

Follow these steps to analyze a target-ligand interaction:

### Step 1: Load your Target Protein
1. Enter a four-letter PDB ID (e.g., `1HSG` for HIV-1 Protease) in the **Target Protein** input, or select a pre-calibrated target from the **Quick-Load NTD Target Template** dropdown (e.g. *Plasmodium falciparum* DHFR `1J3J` or *Mycobacterium tuberculosis* InhA `1ZID`).
2. Click **Fetch PDB**. The application queries the RCSB Protein Data Bank, downloads the structure, and automatically centers the simulation grid on the active pocket using the template's pre-calibrated pocket center.

### Step 2: Load your Ligand or Phytocompound
1. Toggle the ligand source dropdown to choose between **Search Online (PubChem)** or **Cached African Natural Product Library** (which lists 15 active phytocompounds isolated from local plants, such as Artemisinin or Cryptolepine, working fully offline).
2. Enter the chemical name of your ligand and click **Fetch PubChem**, or select one from the Cached Phytocompound dropdown.

### Step 3: Run the Docking Assay
1. Click **Run EFM Docking**.
2. The solver starts a wave relaxation simulation. 
3. Observe the **Binding Energy ($\Delta E$)** output:
   * **Stable Resonance ($\Delta E < 0$)**: The ligand forms a low-energy, complementary wave state with the active site.
   * **Steric Clash ($\Delta E > 0$)**: The ligand's matter waves clash with the protein pocket walls, indicating a steric mismatch.

---

## 3. Advanced Features for Resource-Constrained Environments

### 1. Low-Spec CPU Optimization Mode
Resource-constrained laboratories often run simulations on dual-core or quad-core consumer laptops. 
- Enable the **Low-Spec CPU Optimization Mode** checkbox.
- This dynamically scales the grid down to $24^3$ (minimizing memory overhead) and restricts PyTorch to `cores - 1` CPU threads. This prevents thread saturation, keeping the desktop GUI completely smooth and responsive during long simulation loops.

### 2. Multi-Ligand Synergy Docking
Phytochemical extracts (herbal remedies) often work through synergy, where multiple active compounds co-bind a pocket to stabilize it.
- Toggle **Synergy Mode** in the Synergy Pool box.
- Fetch a compound and click **Add to Pool** (up to 3 compounds can be co-docked).
- Click **Run Synergy Docking**. The EFM solver will evolve the complex potential under the combined nuclear fields of all pool ligands, rendering them simultaneously in the 3D viewer and calculating their cooperative specific phase friction shift.

---

## 4. Understanding Solver Parameters

If a simulation fails to converge or runs slowly, adjust these sliders:

*   **Grid Resolution ($N^3$)**: The number of grid points in the 3D simulation.
    *   *Default*: `32` (runs in 1–2 seconds on CPU).
    *   *Biochemical use*: Increase to `48` or `64` for high-precision binding calculations of small atoms. Use lower values for fast initial screening.
*   **Box Size ($L$)**: The physical size of the simulation box in Angstroms centered on the active site.
    *   *Default*: `16.0 Å`.
    *   *Biochemical use*: Expand for larger ligands (e.g., polypeptides) or contract for compact binding sites to exclude irrelevant pocket residues.
*   **Simulation Steps**: The number of Verlet integration steps.
    *   *Default*: `500`.
    *   *Biochemical use*: If the energy metrics fluctuate or fail to flatten, increase steps to allow the wave field to fully relax into the ground state.
*   **Damping ($\delta$)**: Damps the kinetic energy of the waves during relaxation.
    *   *Default*: `0.2`.
    *   *Biochemical use*: Lower values allow the system to escape local energy barriers; higher values speed up relaxation but can cause premature convergence in unstable wells.

