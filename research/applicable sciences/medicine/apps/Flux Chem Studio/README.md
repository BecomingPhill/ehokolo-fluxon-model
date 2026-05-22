# Flux Chem Studio

Flux Chem Studio is an offline-first molecular design desktop application integrating EFM (Electrostatic Field Model) biophysical solvers, 3D molecular visualization, virtual screening, and topological de novo ligand evolution.

## Features

- **EFM Biophysical Engine**: PyTorch-accelerated 3D density-dependent NLKG solver.
- **Topological De Novo Evolution**: EFM-guided grew-and-branch chemical scaffold search.
- **Offline Molecular Viewer**: 3Dmol.js viewer for real-time visualization of pockets, ligands, and docking scores.
- **Statistical Benchmarking Suite**: Stratified 100-target validation pipeline.

## Installation

To install Flux Chem Studio in editable mode, run:

```bash
pip install -e .
```

### Linux System Prerequisites
On Linux, the desktop GUI wrapper (`pywebview`) requires system-level GUI and WebKit libraries. We recommend installing the GTK/WebKit2Gtk components:

* **Ubuntu/Debian**:
  ```bash
  sudo apt update
  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
  ```
  *(For older releases, substitute `gir1.2-webkit2-4.1` with `gir1.2-webkit2-4.0`)*

* **Fedora/RHEL**:
  ```bash
  sudo dnf install python3-gobject webkit2gtk4.1
  ```

## Running the Application

After installation, you can launch the application via:

```bash
flux-chem-studio
```

## Development and Building

To compile the application as a standalone desktop executable:

```bash
python build_app.py
```
* **On macOS**: Compiles a double-clickable `dist/Flux Chem Studio.app` bundle.
* **On Linux**: Compiles a standalone executable folder under `dist/Flux Chem Studio/`.

See the detailed developer manual in [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md).

