# Mathematical Framework

This section provides detailed mathematical derivations and computational approaches for the Ehokolo Fluxon Model.

## Governing Equation

The Ehokolo Fluxon Field φ(x,t) satisfies the non-linear Klein-Gordon equation:

$$\frac{\partial^2 \phi}{\partial t^2} - c^2 \nabla^2 \phi + m^2 \phi + g \phi^3 + \eta \phi^5 + \alpha \phi \frac{\partial \phi}{\partial t} \nabla \phi + \delta \left(\frac{\partial \phi}{\partial t}\right)^2 \phi + \gamma \phi - \beta \cos(\omega_n t) \phi = 8\pi G k \phi^2$$

## Parameter Definitions

!!! important "Dimensionless Parameters"
    All parameters below are dimensionless simulation parameters. They do not represent physical constants but rather control the dimensionless field dynamics. Physical constants emerge through the scaling and anchoring process described in the [Theory of Mind](theory-of-mind.md).

### Simulation Parameters

| Parameter | Description | Units | Density Dependence |
|-----------|-------------|-------|-------------------|
| $m$ | Mass parameter | $[L^{-1}]$ | State-dependent |
| $g$ | Cubic coupling | $[L^{-2}]$ | State-dependent |
| $\eta$ | Quintic coupling | $[L^{-4}]$ | State-dependent |
| $\alpha$ | Convective coupling | $[L^{-1}]$ | State-dependent |
| $\delta$ | Kinetic coupling | $[L^{-2}]$ | State-dependent |
| $\gamma$ | Linear potential | $[L^{-2}]$ | State-dependent |
| $\beta$ | Driving amplitude | $[L^{-2}]$ | State-dependent |
| $\omega_n$ | Harmonic frequency | $[T^{-1}]$ | Density-dependent |
| $k$ | Gravitational coupling | $[L^2]$ | Universal constant |

### Density-Specific Values

#### N1 (S/T) - Space over Time
```python
# Cosmological scale parameters
m_n1 = 1.0e-26  # Very small mass parameter
g_n1 = 1.0e-15  # Weak cubic coupling
eta_n1 = 1.0e-30  # Very weak quintic coupling
alpha_n1 = 1.0e-20  # Weak convective effects
delta_n1 = 1.0e-25  # Weak kinetic effects
gamma_n1 = 1.0e-30  # Weak linear potential
beta_n1 = 1.0e-18  # Moderate driving
omega_n1 = 1.0e-18  # Very low frequency
```

#### N2 (T/S) - Time over Space
```python
# Quantum scale parameters
m_n2 = 1.0e-15  # Moderate mass parameter
g_n2 = 1.0e-8   # Strong cubic coupling
eta_n2 = 1.0e-12  # Moderate quintic coupling
alpha_n2 = 1.0e-10  # Strong convective effects
delta_n2 = 1.0e-8   # Strong kinetic effects
gamma_n2 = 1.0e-12  # Moderate linear potential
beta_n2 = 1.0e-6    # Strong driving
omega_n2 = 1.0e-12  # High frequency
```

#### N3 (S=T) - Space equals Time
```python
# Atomic scale parameters
m_n3 = 1.0e-6   # Large mass parameter
g_n3 = 1.0e-3   # Very strong cubic coupling
eta_n3 = 1.0e-6  # Strong quintic coupling
alpha_n3 = 1.0e-4  # Very strong convective effects
delta_n3 = 1.0e-3  # Very strong kinetic effects
gamma_n3 = 1.0e-6  # Strong linear potential
beta_n3 = 1.0e-2   # Very strong driving
omega_n3 = 1.0e-6  # Very high frequency
```

## Soliton Solutions

### Static Solitons
For time-independent solutions ($\frac{\partial \phi}{\partial t} = 0$):

$$-c^2 \nabla^2 \phi + m^2 \phi + g \phi^3 + \eta \phi^5 + \gamma \phi = 8\pi G k \phi^2$$

### Traveling Solitons
For solutions of the form $\phi(x-vt)$:

$$\frac{\partial^2 \phi}{\partial t^2} - c^2 \nabla^2 \phi = \text{nonlinear terms}$$

## Computational Methods

### Finite Difference Discretization

#### Spatial Discretization
$$\nabla^2 \phi \approx \frac{\phi_{i+1} - 2\phi_i + \phi_{i-1}}{(\Delta x)^2}$$

#### Temporal Discretization
$$\frac{\partial^2 \phi}{\partial t^2} \approx \frac{\phi^{n+1} - 2\phi^n + \phi^{n-1}}{(\Delta t)^2}$$

### Numerical Scheme
Using central differences and explicit time stepping:

$$\phi_i^{n+1} = 2\phi_i^n - \phi_i^{n-1} + (\Delta t)^2 \left[ c^2 \frac{\phi_{i+1}^n - 2\phi_i^n + \phi_{i-1}^n}{(\Delta x)^2} - \text{nonlinear terms} \right]$$

## Scaling Analysis

### Dimensionless Formulation
Introduce dimensionless variables:
- $\tilde{x} = x/L_0$
- $\tilde{t} = t/T_0$  
- $\tilde{\phi} = \phi/\phi_0$

Where $L_0$, $T_0$, and $\phi_0$ are characteristic scales.

### Physical Scaling
To convert dimensionless results to physical units:

1. **Anchor a key observable** (e.g., soliton mass, wavelength)
2. **Establish scaling factors** from the anchor
3. **Apply scaling** to all dimensionless quantities

### Example Scaling Procedure
```python
def scale_to_physical(dimless_mass, dimless_length, anchor_mass, anchor_length):
    """
    Scale dimensionless simulation results to physical units
    """
    mass_scale = anchor_mass / dimless_mass
    length_scale = anchor_length / dimless_length
    time_scale = length_scale / c  # Assuming c = 1 in simulation
    
    return {
        'mass_scale': mass_scale,
        'length_scale': length_scale, 
        'time_scale': time_scale
    }
```

## Stability Analysis

### Linear Stability
For small perturbations $\delta \phi$ around a solution $\phi_0$:

$$\frac{\partial^2 \delta \phi}{\partial t^2} - c^2 \nabla^2 \delta \phi + V''(\phi_0) \delta \phi = 0$$

Where $V''(\phi_0)$ is the second derivative of the potential.

### Energy Conservation
The total energy of the system:

$$E = \int \left[ \frac{1}{2}\left(\frac{\partial \phi}{\partial t}\right)^2 + \frac{c^2}{2}(\nabla \phi)^2 + V(\phi) \right] d^3x$$

Where $V(\phi)$ is the potential energy density.

## Validation Metrics

### Soliton Properties
- **Mass**: $M = \int \rho(\phi) d^3x$
- **Charge**: $Q = \int j^0(\phi) d^3x$  
- **Size**: Characteristic width of soliton
- **Stability**: Lifetime and decay modes

### Observational Predictions
- **Gravitational effects**: Derived from $8\pi G k \phi^2$ term
- **Electromagnetic properties**: From N3 density interactions
- **Particle masses**: From soliton configurations

## Implementation Notes

### Numerical Stability
- Use adaptive time stepping for stability
- Implement absorbing boundary conditions
- Monitor energy conservation

### Computational Efficiency
- Parallelize spatial derivatives
- Use spectral methods for periodic domains
- Implement adaptive mesh refinement

## References

- [Density States](density-states.md): Parameter values for each density
- [Active Research Papers](../papers/index.md): Validation of the frameworknal studies
- [Computational Tools](../tools/computational.md): Implementation examples
