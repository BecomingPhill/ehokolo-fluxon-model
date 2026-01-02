# EFM Computational Ontology & Engine

This section details the computational framework of the Eholoko Fluxon Model (EFM), as defined in the research paper *The Eholoko Simulation Engine: Architecture, Discretization, and Analysis Protocols for a Unified Field*.

## The Eholoko Ontology

In the EFM, the simulation is not an approximation of theory—it **is** the theory. The model posits that physical reality is fundamentally discrete and deterministic, emerging from the harmonic interactions of a single scalar field, $\Phi$, on a quantized grid.

### Core Axioms
1.  **The Grid is Fundamental**: Space is not a background continuum but a discrete lattice of field values.
2.  **State-Dependent Physics**: Physics changes based on local density ($\rho = k\Phi^2$). The vacuum, matter, and quantum regimes are not separate laws but different density states of the same field.
3.  **Emergence over Input**: Mass, charge, and forces are not input parameters. They are emergent properties of stable field configurations (solitons).

---

## The Simulation Engine

The primary research tool is the **EFM Simulation Engine**, a solver for the density-dependent Nonlinear Klein-Gordon (NLKG) equation.

### Governing Equation
The engine numerically integrates the generalized NLKG equation:
$$
\frac{\partial^2\phi}{\partial t^2} - c^2\nabla^2\phi + m^2(\rho)\phi + g(\rho)\phi^3 + \eta(\rho)\phi^5 = 0
$$

### Numerical Discretization
The engine uses a **7-point finite difference stencil** for spatial discretization (approximating $\nabla^2\phi$) and a symplectic integrator for temporal evolution. This ensures energy conservation over long cosmic timescales.

### State-Switching Logic
The engine does not use global constants. At every timestep, it computes the local density tensor $\boldsymbol{\rho}$ and applies different parameters dynamically:
*   **Vacuum Regime** ($\rho < \rho_{thresh}$): Applies repulsive $g > 0$ to model cosmic expansion.
*   **Matter Regime** ($\rho \ge \rho_{thresh}$): Applies attractive $g < 0$ and high mass parameters to drive soliton formation.

### Conceptual Implementation
The following JAX-based pseudo-code (from the *Eholoko Simulation Engine* paper) illustrates the core logic:

```python
import jax
import jax.numpy as jnp
from jax.scipy.signal import convolve

@jax.jit
def unified_solver_step(phi, phi_prev, dt, dx, params):
    """
    Performs one timestep of the EFM universe evolution using 
    density-dependent masking.
    """
    # 1. Calculate Local Density Tensor
    rho = params['k'] * (phi ** 2)
    
    # 2. State-Switching Logic (The Masks)
    is_matter = rho > params['rho_critical']
    is_vacuum = ~is_matter
    
    # 3. Apply State-Dependent Parameters dynamically
    m_sq = (params['m_vac'] * is_vacuum) + (params['m_mat'] * is_matter)
    g = (params['g_vac'] * is_vacuum) + (params['g_mat'] * is_matter)
    
    # 4. Compute Spatial Laplacian (7-point stencil)
    stencil = jnp.array([[[0,0,0],[0,1,0],[0,0,0]],
                         [[0,1,0],[1,-6,1],[0,1,0]],
                         [[0,0,0],[0,1,0],[0,0,0]]]) / dx**2
    laplacian = convolve(phi, stencil, mode='wrap')
    
    # 5. Compute Forces (NLKG terms)
    # F = m^2*phi + g*phi^3 + ...
    force = (m_sq * phi) + (g * (phi ** 3))
    
    # 6. Evolve Field (Verlet Integration)
    acceleration = laplacian - force
    phi_new = (2 * phi) - phi_prev + (acceleration * (dt ** 2))
    
    return phi_new
```

---

## Analysis Protocols

### The "Rosetta Stone" Protocol
EFM simulations run in dimensionless units ("Sim-Units"). To connect results to physical reality, we use a strict **Anchoring Protocol**:
1.  **Simulate** a known phenomenon (e.g., Large Scale Structure).
2.  **Measure** its dimensionless value in the grid ($r_{sim}$).
3.  **Anchor** to the known physical constant ($L_{phys}$).
4.  **Derive** the scaling factor $S = L_{phys} / r_{sim}$.

This derived scale is then applied to all other outputs (e.g., particle masses, frequencies) to generate falsifiable predictions.

### Particle Census
To extract particles from the field:
1.  **Thresholding**: Isolate high-density regions ($\rho > \rho_{cut}$).
2.  **Labeling**: Identify connected components (topological islands).
3.  **Integration**: Integrate $\phi^2$ and $\phi^3$ over each island to determine Mass and Charge.

## References
*   *The Eholoko Simulation Engine: Architecture, Discretization, and Analysis Protocols for a Unified Field* (`research/ontology/`)
*   *Compendium of the Eholoko Fluxon Model*
