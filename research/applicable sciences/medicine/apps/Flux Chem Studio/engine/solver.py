import torch
import numpy as np

class EFMSolver:
    def __init__(self, grid_size=32, box_size=16.0, device=None):
        self.N = grid_size
        self.L = box_size
        self.dx = self.L / self.N
        self.device = device if device is not None else ("cuda" if torch.cuda.is_available() else "cpu")
        
        # EFM Biophysical Parameters (HDS 3 - Matter / Electroweak State)
        self.k_density = 0.01
        self.m_sq_binding = -1.2
        self.g_binding = 10.0
        
        self.rho_mantle_thresh = 1.0e-11
        self.m_sq_mantle = 1.0
        self.g_mantle = -0.1
        
        self.rho_core_thresh = 5.0e-11
        self.m_sq_core = 2.0
        self.g_core = 0.5
        
        self.eta = 0.01
        self.c_sq = 1.0
        self.delta = 0.2  # Dissipation / damping coefficient for relaxation
        self.dt = 0.02    # Timestep
        
        # EFM Periodic Table Harmonic Constants
        self.R_H = 1.001227
        self.S_L = 0.4186  # Angstroms per simulation unit
        self.sigma_0 = 0.4 / self.S_L  # Baseline Hydrogen core radius (0.4 Å)
        self.sigma_core = 0.5 / self.S_L  # Legacy fallback core radius
        
        # Create grid coordinates
        x = torch.linspace(-self.L/2, self.L/2, self.N, device=self.device)
        y = torch.linspace(-self.L/2, self.L/2, self.N, device=self.device)
        z = torch.linspace(-self.L/2, self.L/2, self.N, device=self.device)
        self.X, self.Y, self.Z = torch.meshgrid(x, y, z, indexing="ij")

    def _compute_laplacian(self, field):
        """Computes 3D Laplacian using a 7-point finite difference stencil with wrapping (periodic BCs)."""
        lap = (
            torch.roll(field, shifts=1, dims=0) + torch.roll(field, shifts=-1, dims=0) +
            torch.roll(field, shifts=1, dims=1) + torch.roll(field, shifts=-1, dims=1) +
            torch.roll(field, shifts=1, dims=2) + torch.roll(field, shifts=-1, dims=2) -
            6.0 * field
        ) / (self.dx ** 2)
        return lap

    def build_nuclear_potential(self, atom_coords, atomic_numbers):
        """
        Builds the nuclear potential using State-Dependent Core Scaling (SDNS):
        V_i = -Z_i * erf(dist / sigma_i) / dist
        where core radius scales with Z: sigma_i = sigma_0 * (R_H)^Z_i
        """
        V = torch.zeros((self.N, self.N, self.N), device=self.device)
        if len(atom_coords) == 0:
            return V
            
        coords_sim = torch.tensor(atom_coords, dtype=torch.float32, device=self.device) / self.S_L
        charges = torch.tensor(atomic_numbers, dtype=torch.float32, device=self.device)
        
        # Sum potential fields over all atoms
        for i in range(coords_sim.shape[0]):
            dx_sq = (self.X - coords_sim[i, 0]) ** 2
            dy_sq = (self.Y - coords_sim[i, 1]) ** 2
            dz_sq = (self.Z - coords_sim[i, 2]) ** 2
            dist = torch.sqrt(dx_sq + dy_sq + dz_sq)
            
            # SDNS: Core size scales geometrically with atomic number Z
            sigma_i = self.sigma_0 * (self.R_H ** charges[i].item())
            
            # Smooth Gaussian-regularized potential to prevent grid aliasing
            eps = 1e-6
            V_i = -charges[i] * torch.erf(dist / sigma_i) / (dist + eps)
            V += V_i
            
        return V

    def run_simulation(self, V_nuc, atom_coords=None, steps=500):
        """
        Evolves a complex scalar field psi under the nuclear potential V_nuc,
        allowing it to relax to the EFM ground state using a stable semi-implicit Verlet scheme.
        """
        # Initialize field as a sum of local wavepackets on each atom if coordinates are provided
        if atom_coords is not None and len(atom_coords) > 0:
            psi_r = torch.zeros_like(self.X)
            coords_sim = torch.tensor(atom_coords, dtype=torch.float32, device=self.device) / self.S_L
            for coord in coords_sim:
                d_sq = (self.X - coord[0])**2 + (self.Y - coord[1])**2 + (self.Z - coord[2])**2
                psi_r += torch.exp(-d_sq / 2.0) * 0.1
            # Clamp initial amplitude to 0.1 to avoid blowup
            psi_r = torch.clamp(psi_r, max=0.1)
        else:
            dist_sq = self.X**2 + self.Y**2 + self.Z**2
            psi_r = torch.exp(-dist_sq / 2.0) * 0.1
            
        psi_i = torch.zeros_like(psi_r)
        
        psi_prev_r = psi_r.clone()
        psi_prev_i = psi_i.clone()
        
        for step in range(steps):
            # Calculate local field density rho = k * |psi|^2
            rho = self.k_density * (psi_r**2 + psi_i**2)
            
            # Determine Harmonic Density State masks
            core_mask = (rho > self.rho_core_thresh).to(torch.float32)
            mantle_mask = ((rho > self.rho_mantle_thresh) & (rho <= self.rho_core_thresh)).to(torch.float32)
            binding_mask = (rho <= self.rho_mantle_thresh).to(torch.float32)
            
            m_sq = binding_mask * self.m_sq_binding + mantle_mask * self.m_sq_mantle + core_mask * self.m_sq_core
            g = binding_mask * self.g_binding + mantle_mask * self.g_mantle + core_mask * self.g_core
            
            # Compute forces from NLKG terms
            mag_sq = psi_r**2 + psi_i**2
            force_r = m_sq * psi_r + g * mag_sq * psi_r + self.eta * (mag_sq**2) * psi_r
            force_i = m_sq * psi_i + g * mag_sq * psi_i + self.eta * (mag_sq**2) * psi_i
            
            # Laplacians
            lap_r = self._compute_laplacian(psi_r)
            lap_i = self._compute_laplacian(psi_i)
            
            # Force without damping (Verlet step F_t)
            F_t_r = self.c_sq * lap_r - force_r - V_nuc * psi_r
            F_t_i = self.c_sq * lap_i - force_i - V_nuc * psi_i
            
            # Centered semi-implicit Verlet integration for damped wave equations:
            coef_prev = 1.0 - (self.delta * self.dt / 2.0)
            coef_next = 1.0 + (self.delta * self.dt / 2.0)
            
            psi_next_r = (2.0 * psi_r - coef_prev * psi_prev_r + (self.dt**2) * F_t_r) / coef_next
            psi_next_i = (2.0 * psi_i - coef_prev * psi_prev_i + (self.dt**2) * F_t_i) / coef_next
            
            psi_prev_r, psi_r = psi_r, psi_next_r
            psi_prev_i, psi_i = psi_i, psi_next_i
            
            # Numerical cutoff to prevent instability
            if torch.isnan(psi_r).any():
                psi_r = torch.zeros_like(psi_r)
                psi_i = torch.zeros_like(psi_i)
                break
                
        return psi_r, psi_i

    def calculate_specific_phase_friction(self, psi_r, psi_i):
        """
        Calculates the Specific Phase Friction (E_spec) of the relaxed complex field:
        E_spec = sum( |nabla psi|^2 ) / sum( |psi|^2 )
        """
        # Compute gradient squared of both components
        grad_rx = torch.gradient(psi_r, spacing=self.dx)[0]
        grad_ry = torch.gradient(psi_r, spacing=self.dx)[1]
        grad_rz = torch.gradient(psi_r, spacing=self.dx)[2]
        
        grad_ix = torch.gradient(psi_i, spacing=self.dx)[0]
        grad_iy = torch.gradient(psi_i, spacing=self.dx)[1]
        grad_iz = torch.gradient(psi_i, spacing=self.dx)[2]
        
        grad_mag_sq = (grad_rx**2 + grad_ry**2 + grad_rz**2) + (grad_ix**2 + grad_iy**2 + grad_iz**2)
        field_mag_sq = psi_r**2 + psi_i**2
        
        numerator = torch.sum(grad_mag_sq).item()
        denominator = torch.sum(field_mag_sq).item()
        
        if denominator < 1e-12:
            return 0.0
            
        return numerator / denominator

    def calculate_lability_index(self, V_nuc, psi_ground_r, psi_ground_i, steps=100, noise_amplitude=0.01):
        """Calculates the Dynamical Soliton Lability (L_sol) under Langevin noise."""
        device = self.device
        psi_r = psi_ground_r.clone()
        psi_i = psi_ground_i.clone()
        psi_prev_r = psi_r.clone()
        psi_prev_i = psi_i.clone()
        
        ground_norm = torch.sum(psi_ground_r**2 + psi_ground_i**2).item()
        if ground_norm < 1e-12:
            return 0.0
            
        variance_sum = 0.0
        
        for t in range(steps):
            V_perturbed = V_nuc + torch.randn_like(V_nuc, device=device) * noise_amplitude
            
            rho = self.k_density * (psi_r**2 + psi_i**2)
            core_mask = (rho > self.rho_core_thresh).to(torch.float32)
            mantle_mask = ((rho > self.rho_mantle_thresh) & (rho <= self.rho_core_thresh)).to(torch.float32)
            binding_mask = (rho <= self.rho_mantle_thresh).to(torch.float32)
            
            m_sq = binding_mask * self.m_sq_binding + mantle_mask * self.m_sq_mantle + core_mask * self.m_sq_core
            g = binding_mask * self.g_binding + mantle_mask * self.g_mantle + core_mask * self.g_core
            
            mag_sq = psi_r**2 + psi_i**2
            force_r = m_sq * psi_r + g * mag_sq * psi_r + self.eta * (mag_sq**2) * psi_r
            force_i = m_sq * psi_i + g * mag_sq * psi_i + self.eta * (mag_sq**2) * psi_i
            
            lap_r = self._compute_laplacian(psi_r)
            lap_i = self._compute_laplacian(psi_i)
            
            F_t_r = self.c_sq * lap_r - force_r - V_perturbed * psi_r
            F_t_i = self.c_sq * lap_i - force_i - V_perturbed * psi_i
            
            coef_prev = 1.0 - (self.delta * self.dt / 2.0)
            coef_next = 1.0 + (self.delta * self.dt / 2.0)
            
            psi_next_r = (2.0 * psi_r - coef_prev * psi_prev_r + (self.dt**2) * F_t_r) / coef_next
            psi_next_i = (2.0 * psi_i - coef_prev * psi_prev_i + (self.dt**2) * F_t_i) / coef_next
            
            psi_prev_r, psi_r = psi_r, psi_next_r
            psi_prev_i, psi_i = psi_i, psi_next_i
            
            dev_r = psi_r - psi_ground_r
            dev_i = psi_i - psi_ground_i
            variance_sum += torch.sum(dev_r**2 + dev_i**2).item() / ground_norm
            
        return variance_sum / steps
