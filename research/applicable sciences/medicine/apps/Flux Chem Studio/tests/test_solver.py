import pytest
import torch
import numpy as np
from engine.solver import EFMSolver

def test_solver_initialization():
    solver = EFMSolver(grid_size=16, box_size=10.0, device="cpu")
    assert solver.N == 16
    assert solver.L == 10.0
    assert solver.dx == 10.0 / 16.0
    assert solver.device == "cpu"
    assert solver.X.shape == (16, 16, 16)

def test_compute_laplacian():
    solver = EFMSolver(grid_size=16, box_size=10.0, device="cpu")
    # A uniform field should have a zero Laplacian
    field = torch.ones((16, 16, 16), device="cpu")
    lap = solver._compute_laplacian(field)
    assert torch.allclose(lap, torch.zeros_like(lap), atol=1e-5)
    
    # A localized Gaussian peak should have a negative Laplacian at the center
    dist_sq = solver.X**2 + solver.Y**2 + solver.Z**2
    gaussian = torch.exp(-dist_sq / 2.0)
    lap = solver._compute_laplacian(gaussian)
    center_idx = 16 // 2
    assert lap[center_idx, center_idx, center_idx] < 0.0

def test_nuclear_potential():
    solver = EFMSolver(grid_size=16, box_size=10.0, device="cpu")
    coords = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
    charges = [6, 8]  # Carbon and Oxygen
    V = solver.build_nuclear_potential(coords, charges)
    
    assert V.shape == (16, 16, 16)
    # The potential should be negative (attractive)
    assert (V <= 0).all()
    
    # Near coordinates, potential should be deeper (more negative)
    # Center (index 8) is close to coordinate (0.0, 0.0, 0.0)
    assert V[8, 8, 8] < V[0, 0, 0]

def test_run_simulation_and_friction():
    solver = EFMSolver(grid_size=16, box_size=10.0, device="cpu")
    coords = [[0.0, 0.0, 0.0]]
    charges = [6]
    V = solver.build_nuclear_potential(coords, charges)
    
    psi_r, psi_i = solver.run_simulation(V, atom_coords=coords, steps=5)
    
    assert psi_r.shape == (16, 16, 16)
    assert psi_i.shape == (16, 16, 16)
    assert not torch.isnan(psi_r).any()
    assert not torch.isnan(psi_i).any()
    
    # Test specific phase friction calculation
    E_spec = solver.calculate_specific_phase_friction(psi_r, psi_i)
    assert isinstance(E_spec, float)
    assert E_spec >= 0.0

def test_de_novo_clash_prevention():
    import asyncio
    from engine.server import run_evolution, EvolutionRequest, AtomData
    
    # We place a single target atom exactly at the pocket center [0.0, 0.0, 0.0]
    # If the seed atom is placed at [0.0, 0.0, 0.0], it would clash at 0.0 Å.
    # It must find an offset that is at least 1.2 Å away (all candidate offsets are 1.45 Å away).
    req_body = EvolutionRequest(
        target_atoms=[
            AtomData(element="C", x=0.0, y=0.0, z=0.0)
        ],
        seed_atoms=[],
        mutations=[],
        pocket_center=[0.0, 0.0, 0.0],
        simulation_steps=10,
        target_class="General"
    )
    
    data = asyncio.run(run_evolution(req_body))
    assert "sdf_content" in data
    
    # Parse the SDF content to extract atom positions
    lines = data["sdf_content"].splitlines()
    atom_lines = lines[4:12]  # First 8 atoms
    
    coords = []
    for line in atom_lines:
        parts = line.split()
        x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
        coords.append([x, y, z])
        
    # Check that seed atom (atom 0) is NOT at the target atom coordinate [0.0, 0.0, 0.0]
    seed_coord = coords[0]
    dist_to_target = np.sqrt(seed_coord[0]**2 + seed_coord[1]**2 + seed_coord[2]**2)
    assert dist_to_target > 1.2, f"Seed atom is too close to target atom: {dist_to_target} Å"
    
    # Verify that all evolved atoms are at least 1.0 Å away from the target atom to prevent clashes
    for idx, c in enumerate(coords):
        d = np.sqrt(c[0]**2 + c[1]**2 + c[2]**2)
        assert d >= 1.0, f"Atom {idx} is clashing with target atom: distance is {d} Å"

def test_lability_index():
    solver = EFMSolver(grid_size=16, box_size=10.0, device="cpu")
    coords = [[0.0, 0.0, 0.0]]
    charges = [6]
    V = solver.build_nuclear_potential(coords, charges)
    psi_r, psi_i = solver.run_simulation(V, atom_coords=coords, steps=5)
    
    lability = solver.calculate_lability_index(V, psi_r, psi_i, steps=5, noise_amplitude=0.01)
    assert isinstance(lability, float)
    assert lability >= 0.0

def test_natural_products_api():
    import asyncio
    from engine.server import get_natural_products, fetch_natural_product
    
    # Test get list
    products = asyncio.run(get_natural_products())
    assert isinstance(products, list)
    assert len(products) > 0
    assert products[0]["name"] == "Artemisinin"
    
    # Test fetch single product
    prod_data = asyncio.run(fetch_natural_product(1))
    assert prod_data["name"] == "Artemisinin"
    assert "atoms" in prod_data
    assert len(prod_data["atoms"]) > 0

def test_ntd_templates_api():
    import asyncio
    from engine.server import get_ntd_templates
    
    templates = asyncio.run(get_ntd_templates())
    assert isinstance(templates, list)
    assert len(templates) == 6
    assert templates[0]["pdb_id"] == "1J3J"

def test_synergy_screening_api():
    import asyncio
    from engine.server import run_synergy_screening, SynergyScreeningRequest, AtomData
    
    # 2 ligands, each has 1 atom (Carbon and Oxygen)
    req = SynergyScreeningRequest(
        target_atoms=[AtomData(element="C", x=0.0, y=0.0, z=0.0)],
        ligands=[
            [AtomData(element="C", x=2.0, y=0.0, z=0.0)],
            [AtomData(element="O", x=0.0, y=2.0, z=0.0)]
        ],
        pocket_center=[0.0, 0.0, 0.0],
        simulation_steps=10,
        grid_size=16,
        box_size=10.0,
        low_spec_mode=True
    )
    
    res = asyncio.run(run_synergy_screening(req))
    assert "delta_E" in res
    assert "efm_score" in res
    assert "predicted_pki" in res
    assert isinstance(res["delta_E"], float)


