const BACKEND_URL = window.location.origin;

let targetAtoms = [];
let ligandAtoms = [];
let pocketCenter = null;
let rawPdbContent = "";
let rawSdfContent = "";
let synergyPool = [];

// Initialize 3Dmol.js viewer
const viewport = document.getElementById("viewport-3d");
const viewer = $3Dmol.createViewer(viewport, { defaultcolors: $3Dmol.rasmolElementColors });
viewer.setBackgroundColor('#05060A');

// Slider Label Sync
const sliders = [
    { id: "grid-size", valId: "grid-val", suffix: "" },
    { id: "box-size", valId: "box-val", suffix: ".0" },
    { id: "sim-steps", valId: "steps-val", suffix: "" },
    { id: "damping", valId: "damping-val", suffix: "" }
];

sliders.forEach(slider => {
    const el = document.getElementById(slider.id);
    const valEl = document.getElementById(slider.valId);
    el.addEventListener("input", (e) => {
        valEl.textContent = e.target.value + slider.suffix;
    });
});

// Style Switchers
let currentStyle = "cartoon";
const styleButtons = {
    "style-cartoon": "cartoon",
    "style-sphere": "sphere",
    "style-stick": "stick"
};

Object.keys(styleButtons).forEach(btnId => {
    document.getElementById(btnId).addEventListener("click", (e) => {
        // Toggle active class
        Object.keys(styleButtons).forEach(id => {
            document.getElementById(id).classList.remove("active");
        });
        e.target.classList.add("active");
        
        currentStyle = styleButtons[btnId];
        updateViewerStyle();
    });
});

function updateViewerStyle() {
    if (!rawPdbContent) return;
    
    viewer.clear();
    
    // Add Target model
    const m_target = viewer.addModel(rawPdbContent, "pdb");
    
    if (currentStyle === "cartoon") {
        viewer.setStyle({ model: m_target }, { cartoon: { color: 'grey', opacity: 0.8 } });
        
        // Highlight active site ASP 25/ASP 25' residues if present
        viewer.addStyle(
            { resn: 'ASP', resi: 25 },
            { stick: { colorscheme: 'Jmol', radius: 0.15 } }
        );
    } else if (currentStyle === "sphere") {
        viewer.setStyle({ model: m_target }, { sphere: { scale: 0.3, colorscheme: 'carbon' } });
    } else {
        viewer.setStyle({ model: m_target }, { stick: { colorscheme: 'carbon', radius: 0.1 } });
    }
    
    const synergyMode = document.getElementById("synergy-mode-toggle") && document.getElementById("synergy-mode-toggle").checked;
    
    // Add Synergy Pool Ligand models if Synergy Mode is active
    if (synergyMode && synergyPool.length > 0) {
        const colors = ['greenCarbon', 'purpleCarbon', 'yellowCarbon'];
        synergyPool.forEach((lig, index) => {
            if (lig.rawSdf) {
                try {
                    const m_lig = viewer.addModel(lig.rawSdf, "sdf");
                    const color = colors[index % colors.length];
                    viewer.setStyle({ model: m_lig }, { sphere: { scale: 0.9, colorscheme: color }, stick: { colorscheme: color, radius: 0.2 } });
                } catch (err) {
                    console.error("Failed to load synergy pool ligand model:", err);
                }
            }
        });
        viewer.zoomTo();
    } else if (rawSdfContent) {
        // Add single Ligand model if loaded
        try {
            const m_ligand = viewer.addModel(rawSdfContent, "sdf");
            viewer.setStyle({ model: m_ligand }, { sphere: { scale: 0.9, colorscheme: 'greenCarbon' }, stick: { colorscheme: 'greenCarbon', radius: 0.2 } });
            const atomCount = m_ligand.selectedAtoms ? m_ligand.selectedAtoms({}).length : 0;
            if (atomCount > 0 && atomCount < 5) {
                viewer.zoomTo({ within: { distance: 8.0, sel: { model: m_ligand } } });
            } else {
                viewer.zoomTo({ model: m_ligand });
            }
        } catch (err) {
            console.error("Failed to load ligand model or zoom:", err);
            viewer.zoomTo();
        }
    } else {
        viewer.zoomTo();
    }
    
    viewer.render();
}

// Search PDB Targets Modal & Keyboard Event Listeners
const searchBtn = document.getElementById("search-target-btn");
const searchQuery = document.getElementById("search-query");
const searchModal = document.getElementById("search-results-modal");
const closeSearchModalBtn = document.getElementById("close-search-modal-btn");
const searchModalResultsBody = document.getElementById("search-modal-results-body");

async function executeSearch() {
    const query = searchQuery.value.trim();
    if (!query) return;
    
    searchModalResultsBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 30px;">Searching RCSB PDB for "${query}"...</td></tr>`;
    searchModal.classList.remove("hidden");
    
    try {
        const res = await fetch(`${BACKEND_URL}/search_target?query=${encodeURIComponent(query)}`);
        const data = await res.json();
        
        searchModalResultsBody.innerHTML = "";
        if (!data.entries || data.entries.length === 0) {
            searchModalResultsBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--accent-magenta); padding: 30px;">No structures found. Try another search term.</td></tr>`;
        } else {
            data.entries.forEach(entry => {
                const tr = document.createElement("tr");
                
                // PDB ID cell
                const tdId = document.createElement("td");
                const badge = document.createElement("span");
                badge.className = "pdb-id-badge";
                badge.textContent = entry.pdb_id.toUpperCase();
                tdId.appendChild(badge);
                
                // Classification
                const tdClass = document.createElement("td");
                tdClass.textContent = entry.classification;
                
                // Title
                const tdTitle = document.createElement("td");
                tdTitle.textContent = entry.title;
                tdTitle.style.lineHeight = "1.4";
                
                // Organism
                const tdOrg = document.createElement("td");
                tdOrg.textContent = entry.organism;
                
                // Action
                const tdAction = document.createElement("td");
                const loadBtn = document.createElement("button");
                loadBtn.className = "primary-btn";
                loadBtn.style.padding = "5px 10px";
                loadBtn.style.fontSize = "11px";
                loadBtn.textContent = "Load";
                loadBtn.addEventListener("click", () => {
                    document.getElementById("pdb-id-input").value = entry.pdb_id.toUpperCase();
                    searchModal.classList.add("hidden");
                    fetchTarget(entry.pdb_id);
                });
                tdAction.appendChild(loadBtn);
                
                tr.appendChild(tdId);
                tr.appendChild(tdClass);
                tr.appendChild(tdTitle);
                tr.appendChild(tdOrg);
                tr.appendChild(tdAction);
                
                searchModalResultsBody.appendChild(tr);
            });
        }
    } catch (e) {
        searchModalResultsBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--accent-magenta); padding: 30px;">Error: ${e.message}</td></tr>`;
    }
}

if (searchBtn) {
    searchBtn.addEventListener("click", executeSearch);
}

if (searchQuery) {
    searchQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            executeSearch();
        }
    });
}

if (closeSearchModalBtn && searchModal) {
    closeSearchModalBtn.addEventListener("click", () => {
        searchModal.classList.add("hidden");
    });
}

if (searchModal) {
    searchModal.addEventListener("click", (e) => {
        if (e.target === searchModal) {
            searchModal.classList.add("hidden");
        }
    });
}

// Fetch PDB Button
document.getElementById("fetch-target-btn").addEventListener("click", () => {
    const pdbId = document.getElementById("pdb-id-input").value.trim();
    if (pdbId) fetchTarget(pdbId);
});

function hasUnsavedResults() {
    const exportBtn = document.getElementById("export-results-btn");
    return exportBtn && !exportBtn.disabled;
}

async function fetchTarget(pdbId) {
    if (hasUnsavedResults()) {
        if (!confirm("You have unsaved simulation results. Loading a new target will discard them. Do you want to proceed?")) {
            return;
        }
    }
    const infoEl = document.getElementById("target-info");
    infoEl.textContent = `Fetching PDB ${pdbId}...`;
    infoEl.style.borderLeftColor = "var(--accent-purple)";
    
    // Clear previous ligand and simulation states
    rawSdfContent = "";
    ligandAtoms = [];
    const compoundInput = document.getElementById("compound-name-input");
    if (compoundInput) {
        compoundInput.value = "";
    }
    const ligandInfo = document.getElementById("ligand-info");
    if (ligandInfo) {
        ligandInfo.textContent = "No compound loaded.";
        ligandInfo.style.borderLeftColor = "var(--text-disabled)";
    }
    resetSimulationState();
    
    try {
        const response = await fetch(`${BACKEND_URL}/fetch_target`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pdb_id: pdbId })
        });
        
        if (!response.ok) throw new Error(await response.text());
        
        const data = await response.json();
        targetAtoms = data.atoms;
        rawPdbContent = data.raw_pdb;
        
        // Find Asp25/Asp25' active dyad center for centering the pocket
        const activeSiteAtoms = targetAtoms.filter(a => a.residue === "ASP" && a.residue_id === 25);
        if (activeSiteAtoms.length > 0) {
            const sumX = activeSiteAtoms.reduce((sum, a) => sum + a.x, 0);
            const sumY = activeSiteAtoms.reduce((sum, a) => sum + a.y, 0);
            const sumZ = activeSiteAtoms.reduce((sum, a) => sum + a.z, 0);
            pocketCenter = [sumX / activeSiteAtoms.length, sumY / activeSiteAtoms.length, sumZ / activeSiteAtoms.length];
        } else {
            // Look for co-crystallized ligands (non-standard residues)
            const STANDARD_AMINO_ACIDS = new Set([
                "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
                "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL",
                "ASX", "GLX", "UNK"
            ]);
            const WATER_AND_IONS = new Set([
                "HOH", "WAT", "SOL", "TIP", "CL", "NA", "MG", "SO4", "PO4", "ZN", "CA", "K", "EDT", "ACT",
                "DMS", "EDO", "GOL", "PEG", "NH4", "CO3", "NO3", "MES", "HEZ", "TRS", "IMD", "IMZ"
            ]);

            const ligandGroups = {};
            targetAtoms.forEach(a => {
                if (a.residue) {
                    const resName = a.residue.trim().toUpperCase();
                    if (!STANDARD_AMINO_ACIDS.has(resName) && !WATER_AND_IONS.has(resName)) {
                        const key = `${resName}_${a.residue_id}`;
                        if (!ligandGroups[key]) {
                            ligandGroups[key] = [];
                        }
                        ligandGroups[key].push(a);
                    }
                }
            });

            let bestGroup = null;
            let maxCount = 0;
            for (const key in ligandGroups) {
                if (ligandGroups[key].length > maxCount) {
                    maxCount = ligandGroups[key].length;
                    bestGroup = ligandGroups[key];
                }
            }

            if (bestGroup && bestGroup.length > 0) {
                const sumX = bestGroup.reduce((sum, a) => sum + a.x, 0);
                const sumY = bestGroup.reduce((sum, a) => sum + a.y, 0);
                const sumZ = bestGroup.reduce((sum, a) => sum + a.z, 0);
                pocketCenter = [sumX / bestGroup.length, sumY / bestGroup.length, sumZ / bestGroup.length];
            } else {
                // Default center of mass of the entire target protein
                const sumX = targetAtoms.reduce((sum, a) => sum + a.x, 0);
                const sumY = targetAtoms.reduce((sum, a) => sum + a.y, 0);
                const sumZ = targetAtoms.reduce((sum, a) => sum + a.z, 0);
                pocketCenter = [sumX / targetAtoms.length, sumY / targetAtoms.length, sumZ / targetAtoms.length];
            }
        }
        
        if (data.detected_class) {
            document.getElementById("target-class-select").value = data.detected_class;
        }
        
        infoEl.textContent = `PDB ${pdbId} (${data.detected_class || "General"}) Loaded. Total Atoms: ${targetAtoms.length}. Pocket Center: [${pocketCenter.map(v => v.toFixed(2)).join(', ')}]. Auto-selected Calibration: ${data.detected_class || "General"}.`;
        infoEl.style.borderLeftColor = "var(--accent-teal)";
        
        updateViewerStyle();
    } catch (e) {
        infoEl.textContent = `Error loading PDB: ${e.message}`;
        infoEl.style.borderLeftColor = "var(--accent-magenta)";
    }
}

// Fetch Ligand Button
document.getElementById("fetch-ligand-btn").addEventListener("click", async () => {
    const name = document.getElementById("compound-name-input").value.trim();
    if (!name) return;
    
    if (hasUnsavedResults()) {
        if (!confirm("You have unsaved simulation results. Loading a new compound will discard them. Do you want to proceed?")) {
            return;
        }
    }
    
    const infoEl = document.getElementById("ligand-info");
    infoEl.textContent = `Fetching ligand '${name}' from PubChem...`;
    infoEl.style.borderLeftColor = "var(--accent-purple)";
    
    // Clear simulation states
    resetSimulationState();
    
    try {
        const response = await fetch(`${BACKEND_URL}/fetch_ligand`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        
        if (!response.ok) throw new Error(await response.text());
        
        const data = await response.json();
        ligandAtoms = data.atoms;
        rawSdfContent = data.raw_sdf;
        
        infoEl.textContent = `Ligand '${name}' Loaded. Total Atoms: ${ligandAtoms.length}`;
        infoEl.style.borderLeftColor = "var(--accent-teal)";
        
        // Enable Add to pool
        document.getElementById("add-to-pool-btn").disabled = false;
        
        updateViewerStyle();
    } catch (e) {
        infoEl.textContent = `Error loading compound: ${e.message}`;
        infoEl.style.borderLeftColor = "var(--accent-magenta)";
    }
});

// Run Docking
document.getElementById("run-docking-btn").addEventListener("click", async () => {
    resetSimulationState();
    if (targetAtoms.length === 0) {
        alert("Please load a target protein first.");
        return;
    }
    
    const synergyMode = document.getElementById("synergy-mode-toggle") && document.getElementById("synergy-mode-toggle").checked;
    
    if (synergyMode) {
        if (synergyPool.length === 0) {
            alert("Synergy Pool is empty. Please add compounds to the pool first.");
            return;
        }
    } else {
        if (ligandAtoms.length === 0) {
            alert("Please load a compound / ligand first.");
            return;
        }
    }
    
    const statusEl = document.getElementById("binding-status");
    statusEl.className = "binding-status";
    statusEl.textContent = synergyMode ? "Running EFM multi-ligand synergy simulation..." : "Running EFM NLKG simulation & field relaxation...";
    
    const steps = parseInt(document.getElementById("sim-steps").value);
    const targetClass = document.getElementById("target-class-select").value;
    const gridSize = parseInt(document.getElementById("grid-size").value);
    const boxSize = parseFloat(document.getElementById("box-size").value);
    const lowSpecMode = document.getElementById("low-spec-toggle").checked;
    
    try {
        let response;
        if (synergyMode) {
            response = await fetch(`${BACKEND_URL}/run_synergy_screening`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target_atoms: targetAtoms,
                    ligands: synergyPool.map(c => c.atoms),
                    pocket_center: pocketCenter,
                    simulation_steps: steps,
                    target_class: targetClass,
                    grid_size: gridSize,
                    box_size: boxSize,
                    low_spec_mode: lowSpecMode
                })
            });
        } else {
            response = await fetch(`${BACKEND_URL}/run_screening`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    target_atoms: targetAtoms,
                    ligand_atoms: ligandAtoms,
                    pocket_center: pocketCenter,
                    simulation_steps: steps,
                    target_class: targetClass,
                    grid_size: gridSize,
                    box_size: boxSize,
                    low_spec_mode: lowSpecMode
                })
            });
        }
        
        if (!response.ok) throw new Error(await response.text());
        
        const data = await response.json();
        
        document.getElementById("score-ea").textContent = data.E_target.toFixed(4);
        document.getElementById("score-eab").textContent = data.E_complex.toFixed(4);
        document.getElementById("score-delta").textContent = data.delta_E.toFixed(4);
        
        // Display calibrated pKi
        document.getElementById("score-pki").textContent = data.predicted_pki ? data.predicted_pki.toFixed(2) : "-";
        
        // Display lability index and tag
        document.getElementById("score-lability").textContent = data.lability_index !== undefined ? `${data.lability_index.toFixed(3)} (${data.lability_tag})` : "-";
        
        if (data.is_favorable) {
            statusEl.className = "binding-status success";
            statusEl.innerHTML = `<strong>SUCCESS</strong>: Favorable binding profile detected (&Delta;E = ${data.delta_E >= 0 ? "+" : ""}${data.delta_E.toFixed(4)}). Thermodynamically stable covalent/hydrogen-bonded resonance formed.<br/><span style="font-size: 0.95em; opacity: 0.9; display: block; margin-top: 5px;">Calibrated Affinity: pK<sub>i</sub> = ${data.predicted_pki ? data.predicted_pki.toFixed(2) : "-"} (using ${data.calibration_used || "General"})</span>`;
        } else {
            statusEl.className = "binding-status clash";
            statusEl.innerHTML = `<strong>CLASH</strong>: Unfavorable binding profile (&Delta;E = +${data.delta_E.toFixed(4)}). Strong Pauli phase repulsion or weak affinity detected.<br/><span style="font-size: 0.95em; opacity: 0.9; display: block; margin-top: 5px;">Calibrated Affinity: pK<sub>i</sub> = ${data.predicted_pki ? data.predicted_pki.toFixed(2) : "-"} (using ${data.calibration_used || "General"})</span>`;
        }
        
        // Enable Export Results button
        document.getElementById("export-results-btn").disabled = false;
    } catch (e) {
        statusEl.className = "binding-status clash";
        statusEl.textContent = `Simulation Error: ${e.message}`;
    }
});

// Run De Novo Evolution
document.getElementById("run-evolution-btn").addEventListener("click", async () => {
    resetSimulationState();
    if (targetAtoms.length === 0) {
        alert("Please load a target protein first.");
        return;
    }
    
    const logEl = document.getElementById("evolution-log");
    logEl.innerHTML = "<div class='log-item'>Initializing Shz-1 de novo growth loop...</div>";
    
    const steps = parseInt(document.getElementById("sim-steps").value);
    
    try {
        const response = await fetch(`${BACKEND_URL}/run_evolution`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                target_atoms: targetAtoms,
                seed_atoms: [], // Seed is generated by server
                mutations: [], // Replaced by topological growth
                pocket_center: pocketCenter,
                simulation_steps: steps,
                target_class: document.getElementById("target-class-select").value,
                grid_size: parseInt(document.getElementById("grid-size").value),
                box_size: parseFloat(document.getElementById("box-size").value),
                low_spec_mode: document.getElementById("low-spec-toggle").checked
            })
        });
        
        if (!response.ok) throw new Error(await response.text());
        
        const data = await response.json();
        
        logEl.innerHTML = "";
        
        data.results.forEach(res => {
            const item = document.createElement("div");
            item.className = "log-item";
            
            const isFavorable = res.is_favorable;
            const statusClass = isFavorable ? "favorable" : "unfavorable";
            const statusText = isFavorable ? "Stable Resonance" : "Steric Clash";
            
            item.innerHTML = `
                <span class="log-name">${res.name}</span>
                <span class="log-status ${statusClass}">&Delta;E = ${res.delta_E.toFixed(4)} (${statusText})</span>
            `;
            logEl.appendChild(item);
        });
        
        // Highlight best selected candidate
        const selectedItem = document.createElement("div");
        selectedItem.className = "log-item";
        selectedItem.style.border = "1px solid var(--accent-teal)";
        selectedItem.style.background = "rgba(0, 242, 254, 0.05)";
        selectedItem.innerHTML = `
            <span class="log-name" style="color: var(--accent-teal)"><strong>Selected Scaffold:</strong> ${data.best_candidate}</span>
            <span class="log-status selected">&Delta;E = ${data.best_score.toFixed(4)}</span>
        `;
        logEl.appendChild(selectedItem);
        
        // Render evolved scaffold in 3D viewer
        rawSdfContent = data.sdf_content;
        updateViewerStyle();
        
        // Update biophysical score card
        document.getElementById("score-ea").textContent = data.E_target !== undefined ? data.E_target.toFixed(4) : "-";
        document.getElementById("score-eab").textContent = data.E_complex !== undefined ? data.E_complex.toFixed(4) : "-";
        document.getElementById("score-pki").textContent = (data.predicted_pki !== undefined && data.predicted_pki !== null) ? data.predicted_pki.toFixed(2) : "-";
        document.getElementById("score-delta").textContent = data.best_score.toFixed(4);
        document.getElementById("score-lability").textContent = data.lability_index !== undefined ? `${data.lability_index.toFixed(3)} (${data.lability_tag})` : "-";
        
        const statusEl = document.getElementById("binding-status");
        statusEl.className = "binding-status success";
        statusEl.innerHTML = `<strong>Selected scaffold: ${data.best_candidate}</strong><br/>Autonomously evolved 8-atom ring-and-branch topology guided by EFM wave equations in the active site.`;
        
        // Enable Export Results button
        document.getElementById("export-results-btn").disabled = false;
    } catch (e) {
        logEl.innerHTML = `<div class='log-item' style='color: var(--accent-magenta)'>Evolution loop failed: ${e.message}</div>`;
    }
});

// Science Guide Modal controls
const guideModal = document.getElementById("science-guide-modal");
const toggleGuideBtn = document.getElementById("toggle-guide-btn");
const closeGuideBtn = document.getElementById("close-guide-btn");

if (toggleGuideBtn && guideModal) {
    toggleGuideBtn.addEventListener("click", () => {
        guideModal.classList.remove("hidden");
    });
}

if (closeGuideBtn && guideModal) {
    closeGuideBtn.addEventListener("click", () => {
        guideModal.classList.add("hidden");
    });
}

// Close modal if clicked outside modal-content
if (guideModal) {
    guideModal.addEventListener("click", (e) => {
        if (e.target === guideModal) {
            guideModal.classList.add("hidden");
        }
    });
}

// Reset simulation results and status logs
function resetSimulationState() {
    document.getElementById("score-ea").textContent = "-";
    document.getElementById("score-eab").textContent = "-";
    document.getElementById("score-delta").textContent = "-";
    document.getElementById("score-pki").textContent = "-";
    document.getElementById("score-lability").textContent = "-";
    
    const statusEl = document.getElementById("binding-status");
    if (statusEl) {
        statusEl.className = "binding-status";
        statusEl.textContent = "Initialize docking or de novo growth to measure phase friction changes.";
    }
    
    const logEl = document.getElementById("evolution-log");
    if (logEl) {
        logEl.innerHTML = `<div class="log-placeholder">Launch De Novo Evolution to grow Carbon backbone mutations and identify steric clashes.</div>`;
    }
    
    const exportBtn = document.getElementById("export-results-btn");
    if (exportBtn) {
        exportBtn.disabled = true;
    }
}

// Clear entire application state
function clearApp() {
    targetAtoms = [];
    ligandAtoms = [];
    synergyPool = [];
    pocketCenter = null;
    rawPdbContent = "";
    rawSdfContent = "";
    
    document.getElementById("pdb-id-input").value = "";
    document.getElementById("compound-name-input").value = "";
    document.getElementById("target-class-select").value = "General";
    document.getElementById("ntd-target-select").value = "";
    document.getElementById("ligand-source-select").value = "pubchem";
    document.getElementById("pubchem-input-group").classList.remove("hidden");
    document.getElementById("african-db-input-group").classList.add("hidden");
    document.getElementById("natural-product-select").value = "";
    document.getElementById("low-spec-toggle").checked = false;
    document.getElementById("grid-size").disabled = false;
    document.getElementById("synergy-mode-toggle").checked = false;
    document.getElementById("run-docking-btn").textContent = "Run EFM Docking";
    document.getElementById("run-docking-btn").className = "action-btn success-btn";
    
    updateSynergyPoolUI();
    
    const targetInfo = document.getElementById("target-info");
    if (targetInfo) {
        targetInfo.textContent = "No target protein loaded.";
        targetInfo.style.borderLeftColor = "var(--text-disabled)";
    }
    
    const ligandInfo = document.getElementById("ligand-info");
    if (ligandInfo) {
        ligandInfo.textContent = "No compound loaded.";
        ligandInfo.style.borderLeftColor = "var(--text-disabled)";
    }
    
    viewer.clear();
    viewer.zoomTo();
    viewer.render();
    
    resetSimulationState();
}

// Export simulation and ligand data as browser download
function exportResults() {
    const pdbId = document.getElementById("pdb-id-input").value.trim() || "unknown";
    const targetClass = document.getElementById("target-class-select").value;
    const scoreEa = document.getElementById("score-ea").textContent;
    const scoreEab = document.getElementById("score-eab").textContent;
    const scoreDelta = document.getElementById("score-delta").textContent;
    const scorePki = document.getElementById("score-pki").textContent;
    const scoreLability = document.getElementById("score-lability").textContent;
    const synergyMode = document.getElementById("synergy-mode-toggle") && document.getElementById("synergy-mode-toggle").checked;
    
    const results = {
        target_pdb: pdbId,
        target_class: targetClass,
        synergy_mode: synergyMode,
        synergy_compounds: synergyMode ? synergyPool.map(c => c.name) : [],
        scores: {
            E_target: scoreEa,
            E_complex: scoreEab,
            delta_E: scoreDelta,
            predicted_pki: scorePki,
            lability_index: scoreLability
        },
        sdf_content: synergyMode ? synergyPool.map(c => c.rawSdf).join("\n") : rawSdfContent
    };
    
    const jsonStr = JSON.stringify(results, null, 2);
    
    // If running in pywebview, use native file save dialogs to prevent page redirection
    if (window.pywebview && window.pywebview.api && window.pywebview.api.save_file) {
        const jsonName = synergyMode ? `flux_chem_synergy_results_${pdbId}.json` : `flux_chem_results_${pdbId}.json`;
        window.pywebview.api.save_file(jsonName, jsonStr).then(resJson => {
            if (resJson && resJson.success) {
                if (synergyMode && synergyPool.length > 0) {
                    const sdfName = `synergy_ligands_${pdbId}.sdf`;
                    const combinedSdf = synergyPool.map(c => c.rawSdf).join("\n");
                    window.pywebview.api.save_file(sdfName, combinedSdf).then(resSdf => {
                        if (resSdf && resSdf.success) {
                            alert(`Results exported successfully:\n- ${resJson.path}\n- ${resSdf.path}`);
                        } else if (resSdf && resSdf.error !== "cancelled") {
                            alert(`Error exporting SDF file: ${resSdf.error}`);
                        }
                    });
                } else if (rawSdfContent) {
                    const isEvolved = document.getElementById("evolution-log").textContent.includes("Selected Scaffold");
                    const sdfName = isEvolved ? `evolved_scaffold_${pdbId}.sdf` : `ligand_${pdbId}.sdf`;
                    window.pywebview.api.save_file(sdfName, rawSdfContent).then(resSdf => {
                        if (resSdf && resSdf.success) {
                            alert(`Results exported successfully:\n- ${resJson.path}\n- ${resSdf.path}`);
                        } else if (resSdf && resSdf.error !== "cancelled") {
                            alert(`Error exporting SDF file: ${resSdf.error}`);
                        }
                    });
                } else {
                    alert(`Results exported successfully:\n- ${resJson.path}`);
                }
            } else if (resJson && resJson.error !== "cancelled") {
                alert(`Error exporting JSON file: ${resJson.error}`);
            }
        });
        return;
    }
    
    // Download JSON (browser fallback)
    const jsonBlob = new Blob([jsonStr], { type: "application/json" });
    const jsonUrl = URL.createObjectURL(jsonBlob);
    const jsonLink = document.createElement("a");
    jsonLink.href = jsonUrl;
    jsonLink.download = `flux_chem_results_${pdbId}.json`;
    document.body.appendChild(jsonLink);
    jsonLink.click();
    document.body.removeChild(jsonLink);
    URL.revokeObjectURL(jsonUrl);
    
    // If there is SDF content, download it too (browser fallback)
    if (rawSdfContent) {
        const sdfBlob = new Blob([rawSdfContent], { type: "text/plain" });
        const sdfUrl = URL.createObjectURL(sdfBlob);
        const sdfLink = document.createElement("a");
        sdfLink.href = sdfUrl;
        const isEvolved = document.getElementById("evolution-log").textContent.includes("Selected Scaffold");
        sdfLink.download = isEvolved ? `evolved_scaffold_${pdbId}.sdf` : `ligand_${pdbId}.sdf`;
        document.body.appendChild(sdfLink);
        sdfLink.click();
        document.body.removeChild(sdfLink);
        URL.revokeObjectURL(sdfUrl);
    }
}

// Bind Clear and Export actions
document.getElementById("clear-all-btn").addEventListener("click", () => {
    if (hasUnsavedResults()) {
        if (!confirm("You have unsaved simulation results. Clearing the application will discard them. Do you want to proceed?")) {
            return;
        }
    }
    clearApp();
});
document.getElementById("export-results-btn").addEventListener("click", exportResults);

async function fetchVersion() {
    try {
        const response = await fetch(`${BACKEND_URL}/version`);
        if (response.ok) {
            const data = await response.json();
            const badges = document.querySelectorAll(".version-badge");
            badges.forEach(badge => {
                badge.textContent = `EFM v${data.version}`;
            });
        }
    } catch (err) {
        console.error("Error fetching version:", err);
    }
}

// Fetch NTD targets on startup
async function loadNtdTemplates() {
    try {
        const res = await fetch(`${BACKEND_URL}/ntd_templates`);
        if (res.ok) {
            const templates = await res.json();
            const select = document.getElementById("ntd-target-select");
            templates.forEach(t => {
                const opt = document.createElement("option");
                opt.value = JSON.stringify({ pdb_id: t.pdb_id, center: t.center, target_class: t.target_class, name: t.name });
                opt.textContent = `${t.name} (${t.pdb_id})`;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Failed to load NTD templates:", e);
    }
}

// Fetch Natural Products on startup
async function loadNaturalProducts() {
    try {
        const res = await fetch(`${BACKEND_URL}/natural_products`);
        if (res.ok) {
            const products = await res.json();
            const select = document.getElementById("natural-product-select");
            products.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.id;
                opt.textContent = `${p.name} [${p.source_organism}] - ${p.therapeutic_area}`;
                select.appendChild(opt);
            });
        }
    } catch (e) {
        console.error("Failed to load Natural Products:", e);
    }
}

// Bind NTD Target dropdown change
document.getElementById("ntd-target-select").addEventListener("change", async (e) => {
    const val = e.target.value;
    if (!val) return;
    
    if (hasUnsavedResults()) {
        if (!confirm("You have unsaved simulation results. Loading a template will discard them. Do you want to proceed?")) {
            e.target.value = "";
            return;
        }
    }
    
    const template = JSON.parse(val);
    document.getElementById("pdb-id-input").value = template.pdb_id;
    
    const infoEl = document.getElementById("target-info");
    infoEl.className = "loaded-info";
    infoEl.textContent = `Fetching NTD Target Template ${template.name} (${template.pdb_id})...`;
    infoEl.style.borderLeftColor = "var(--accent-purple)";
    
    // Clear simulation states
    resetSimulationState();
    
    try {
        const response = await fetch(`${BACKEND_URL}/fetch_target`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pdb_id: template.pdb_id })
        });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        targetAtoms = data.atoms;
        rawPdbContent = data.raw_pdb;
        
        // Override to pre-calibrated center coordinate
        pocketCenter = template.center;
        
        document.getElementById("target-class-select").value = template.target_class || "General";
        
        infoEl.textContent = `PDB ${template.pdb_id} (${template.name}) Loaded. Pre-calibrated Pocket Center: [${pocketCenter.map(v => v.toFixed(2)).join(', ')}]. Calibration: ${template.target_class || "General"}.`;
        infoEl.style.borderLeftColor = "var(--accent-teal)";
        
        updateViewerStyle();
    } catch (err) {
        infoEl.textContent = `Error loading template target: ${err.message}`;
        infoEl.style.borderLeftColor = "var(--accent-magenta)";
    }
});

// Bind ligand source select change
const sourceSelect = document.getElementById("ligand-source-select");
if (sourceSelect) {
    sourceSelect.addEventListener("change", (e) => {
        const val = e.target.value;
        if (val === "pubchem") {
            document.getElementById("pubchem-input-group").classList.remove("hidden");
            document.getElementById("african-db-input-group").classList.add("hidden");
        } else {
            document.getElementById("pubchem-input-group").classList.add("hidden");
            document.getElementById("african-db-input-group").classList.remove("hidden");
        }
    });
}

// Bind Natural Product dropdown change
document.getElementById("natural-product-select").addEventListener("change", async (e) => {
    const npId = e.target.value;
    if (!npId) return;
    
    if (hasUnsavedResults()) {
        if (!confirm("You have unsaved simulation results. Loading a new compound will discard them. Do you want to proceed?")) {
            e.target.value = "";
            return;
        }
    }
    
    const infoEl = document.getElementById("ligand-info");
    infoEl.className = "loaded-info";
    infoEl.textContent = "Loading cached phytocompound...";
    infoEl.style.borderLeftColor = "var(--accent-purple)";
    
    // Clear simulation states
    resetSimulationState();
    
    try {
        const res = await fetch(`${BACKEND_URL}/fetch_natural_product/${npId}`);
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        
        ligandAtoms = data.atoms;
        rawSdfContent = data.raw_sdf;
        
        infoEl.textContent = `Phytocompound '${data.name}' Loaded. [Source: ${data.source_organism}]`;
        infoEl.style.borderLeftColor = "var(--accent-teal)";
        
        // Enable Add to Pool button
        document.getElementById("add-to-pool-btn").disabled = false;
        
        updateViewerStyle();
    } catch (err) {
        infoEl.textContent = `Error loading cached phytocompound: ${err.message}`;
        infoEl.style.borderLeftColor = "var(--accent-magenta)";
    }
});

// Bind Low-Spec Mode checkbox change
document.getElementById("low-spec-toggle").addEventListener("change", (e) => {
    const checked = e.target.checked;
    const gridSlider = document.getElementById("grid-size");
    const gridVal = document.getElementById("grid-val");
    
    if (checked) {
        gridSlider.value = 24;
        gridVal.textContent = "24";
        gridSlider.disabled = true;
    } else {
        gridSlider.disabled = false;
    }
});

// Bind Synergy Pool buttons
const addPoolBtn = document.getElementById("add-to-pool-btn");
const clearPoolBtn = document.getElementById("clear-pool-btn");
const poolList = document.getElementById("synergy-pool-list");
const synergyToggle = document.getElementById("synergy-mode-toggle");

if (addPoolBtn) {
    addPoolBtn.addEventListener("click", () => {
        if (ligandAtoms.length === 0 || !rawSdfContent) {
            alert("Please fetch or load a compound first.");
            return;
        }
        
        const isFromDb = document.getElementById("ligand-source-select").value === "african_db";
        let compName = "";
        if (isFromDb) {
            const selectEl = document.getElementById("natural-product-select");
            compName = selectEl.options[selectEl.selectedIndex].text.split(" [")[0];
        } else {
            compName = document.getElementById("compound-name-input").value.trim();
        }
        if (!compName) compName = "Compound";
        
        // Check if already in pool
        if (synergyPool.some(c => c.name === compName)) {
            alert(`${compName} is already in the synergy pool.`);
            return;
        }
        
        synergyPool.push({
            name: compName,
            atoms: ligandAtoms,
            rawSdf: rawSdfContent
        });
        
        updateSynergyPoolUI();
        updateViewerStyle();
        
        if (synergyPool.length >= 3) {
            addPoolBtn.disabled = true;
        }
    });
}

if (clearPoolBtn) {
    clearPoolBtn.addEventListener("click", () => {
        synergyPool = [];
        updateSynergyPoolUI();
        updateViewerStyle();
    });
}

function updateSynergyPoolUI() {
    if (synergyPool.length === 0) {
        poolList.innerHTML = "Synergy pool is empty. Load a compound and click 'Add to Pool'.";
        clearPoolBtn.disabled = true;
        addPoolBtn.disabled = (ligandAtoms.length === 0);
    } else {
        poolList.innerHTML = "";
        synergyPool.forEach((c, idx) => {
            const item = document.createElement("div");
            item.style.display = "flex";
            item.style.justify = "space-between";
            item.style.background = "rgba(255,255,255,0.05)";
            item.style.padding = "5px 10px";
            item.style.borderRadius = "4px";
            item.style.borderLeft = `3px solid ${['var(--accent-teal)', 'var(--accent-magenta)', 'orange'][idx % 3]}`;
            item.innerHTML = `
                <span><strong>Ligand ${idx+1}:</strong> ${c.name} (${c.atoms.length} atoms)</span>
            `;
            poolList.appendChild(item);
        });
        clearPoolBtn.disabled = false;
        addPoolBtn.disabled = (synergyPool.length >= 3 || ligandAtoms.length === 0);
    }
}

if (synergyToggle) {
    synergyToggle.addEventListener("change", (e) => {
        const checked = e.target.checked;
        const dockingBtn = document.getElementById("run-docking-btn");
        if (checked) {
            dockingBtn.textContent = "Run Synergy Docking";
            dockingBtn.className = "action-btn info-btn";
        } else {
            dockingBtn.textContent = "Run EFM Docking";
            dockingBtn.className = "action-btn success-btn";
        }
        updateViewerStyle();
    });
}

// Auto-load 1HSG (HIV Protease) on start
window.addEventListener("DOMContentLoaded", () => {
    fetchVersion();
    loadNtdTemplates();
    loadNaturalProducts();
    fetchTarget("1HSG");
});

