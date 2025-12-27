import os
import shutil
import re
import subprocess
from datetime import datetime

# Configuration
RESEARCH_DIR = "research"
BUILD_DIR = "latex_build"
OUTPUT_FILENAME = f"Eholoko_Fluxon_Model_Compendium_{datetime.now().strftime('%Y-%m-%d')}.pdf"

# Structure Definition (Same as before, but we will look for .tex files)
STRUCTURE = {
    "Introduction & Foundations": [
        r"Introduction_Theory_of_Mind.pdf",
        r"Introduction to Eholoko Fluxon Model v 1.3.pdf", 
        # r"Introduction to Eholoko Fluxon Model.pdf", # Superseded by v1.3
        r"The Foundational Hierarchy of the Eholoko Fluxon Model- An Axiomatic Ordering of the Harmonic Density States.pdf",
        r"The Eholoko Fluxon Model's Universal Scaling Laws- A Definitive Framework for Converting Simulation to Physical Reality.pdf",
        r"The EFM's Tri-State Reality- A Computational Validation of State-Dependent Scaling Laws and Particle Populations.pdf"
    ],
    "N1 (S/T) - Cosmology & Astrophysics": [
        # Cosmology
        r"The Cosmic Engine- A First-Principles Derivation of the Universe's Eight-Fold Thermodynamic Structure in the Eholoko Fluxon Model V2.pdf",
        # r"The Cosmic Engine- A First-Principles Derivation of the Universe's Eight-Fold Thermodynamic Structure in the Eholoko Fluxon Model Validation.pdf", # Likely covered in V2
        # r"The Cosmic Engine- A First-Principles Derivation of the Universe's Eight-Fold Thermodynamic Structure in the Eholoko Fluxon Model.pdf", # Superseded by V2
        r"V2 A First-Principles Derivation of a Unified Cosmology- The Definitive Validation of the Eholoko Fluxon Model.pdf",
        # r"A First-Principles Derivation of a Unified Cosmology- The Definitive Validation of the Eholoko Fluxon Model.pdf", # Superseded by V2
        r"Cosmogenesis in EFM.pdf",
        r"The Ehokolo Fluxon Model- A First-Principles Derivation of a Deterministic, Unified Universe.pdf",
        r"The Great Recrystallization- A First-Principles EFM Solution to the Crises in Modern Cosmology.pdf",
        # r"The Eholoko Fluxon Model and the Great Recrystallization- A Unified, First-Principles Explanation for the Universe's Late-Time Transition at z \\approx 0.16.pdf", # Similar to above, checking content... keeping 'Great Recrystallization' as it seems more definitive, or maybe keep both if distinct? Let's keep the more specific title 'Great Recrystallization'
        r"EFM- The Hubble Constant as a Resonant-State Observable and the Prediction of a Fundamental Cosmic Frequency.pdf",
        r"Emergent Particles and a Solution to the Cosmological Constant Problem.pdf",
        r"Statistical Properties of the Emergent Cosmic Web in the Ehokolo Fluxon Model- A Dark-Matter-Free Paradigm.pdf",
        
        # Galaxies
        # r"A First-Principles Derivation of a Barred Spiral Galaxy Without Dark Matter in the Ehokolo Fluxon Model v2.pdf", # Superseded by v5 validation?
        r"A First-Principles Derivation of a Barred Spiral Galaxy Without Dark Matter in the Ehokolo Fluxon Model - A Validation v5.pdf",
        # r"A First-Principles Derivation of a Barred Spiral Galaxy Without Dark Matter in the Ehokolo Fluxon Model - Validation.pdf", # Superseded by v5
        r"A First-Principles Derivation of Galactic Structure, Dynamics, and Scaling Laws Without Dark Matter in the Eholoko Fluxon Model v4.pdf",
        r"From Nebula to Galaxy- A First-Principles Derivation of Structure Formation and Flat Rotation Curves in the Eholoko Fluxon Model.pdf",
        r"From Halo to Globular Cluster- A First-Principles Derivation of Structure, Dynamics, and Mass Segregation Without Dark Matter in the Eholoko Fluxon Model.pdf",
        r"From Nebula to Radiation- A First-Principles Derivation of the Structure, Spectrum, and Variability of High-Energy Astrophysical Objects in the Eholoko Fluxon Model.pdf",

        # Gravitational Waves
        r"A Unified Mass-Frequency Relation for Compact Objects- The Origin of Astrophysical Periodicity in the Ehokolo Fluxon Model.pdf",
        r"The Origin of the Nanohertz Gravitational Wave Background from Stable, Oscillating Ehokolo Fluxon Model Remnants.pdf"
    ],
    "N2 (T/S) - Quantum & Particle Physics": [
        # Particle Physics
        r"Derivation of Forces in the Eholoko Fluxon Model.pdf",
        r"EFM Mass Generation- Deriving Particle Mass from Eholokon Self-Interactions v4.pdf",
        # r"EFM Mass Generation- Deriving Particle Mass from Eholokon Self-Interactions.pdf", # Superseded by v4
        # r"EFM Mass Generation- Deriving Particle Mass from Eholokon Self-Interactions v3.pdf", # Superseded by v4
        r"Resolving the Electron Size Paradox via State-Dependent Scattering in the Ehokolo Fluxon Model.pdf",
        # r"From Plasma to Nuclei- A Computational Derivation of Cosmogenesis and State-Dependent Physics in the Ehokolo Fluxon Model.pdf", # Duplicate of Chemistry section?

        # Quantum Measurement / Spectrum
        r"The Unified Mass Spectrum of the Ehokolo Fluxon Model- A First-Principles Derivation of the Lepton and Hadron Masses.pdf",
        r"The EFM Mass Spectrum- A First-Principles Derivation of the Masses of the Electron, Muon, Tau, Proton, and Neutron.pdf",
        r"The Emergent Particle Spectrum of the Ehokolo Fluxon Model.pdf",
        r"A First-Principles Computational Derivation of the Hadron Spectrum from a Unified Scalar Field.pdf"
    ],
    "N3 (S=T) - Matter & Life": [
        # Atomic Structure
        r"A First-Principles Derivation of Atomic Structure for the First Ten Elements in the Ehokolo Fluxon Model.pdf",
        r"An EFM-Based Derivation of Atomic Structure- Ionization, Shielding, and Electron Repulsion.pdf",
        r"From Force to Fusion- A First-Principles Derivation of the Nucleus in the Eholoko Fluxon Model.pdf",
        r"The Ehokolo Fluxon Model's Constituent Theory of the Atomic Nucleus.pdf",
        
        # Chemistry
        r"The Periodic Table of Elements Derived from First Principles in the Eholoko Fluxon Model.pdf",
        r"The Emergence of Chemistry from a Unified Field- A First-Principles Derivation of Molecular Structure and Dynamics.pdf",
        r"The Emergence of Chemistry from a Unified Field- A First-Principles Derivation of the Covalent Bond in the Eholoko Fluxon Model.pdf",
        r"The Law of Harmonic Resonance- A First-Principles Derivation of the Hadron Spectrum in the Eholoko Fluxon Model.pdf",
        r"From Plasma to Nuclei- A Computational Derivation of Cosmogenesis and the EFM's Law of Abundance v3.pdf",
        # r"From Plasma to Nuclei- A Computational Derivation of Cosmogenesis and the EFM's Law of Abundance.pdf", # Superseded by v3
        r"A First-Principles Derivation of a Unified Cosmology- The Definitive Validation of the Eholoko Fluxon Model at High Resolution.pdf",

        # Biology
        r"The Physics of Mind- A First-Principles Derivation of the Timescales of Life, from Consciousness to the Cell.pdf",
        r"The Thermodynamic Origin of Homochirality- A First-Principles Derivation of Functional States in a Unified Field.pdf",
        r"From Stability to Function- The Principle of Optimal Lability and the Thermodynamic Origin of Biological Catalysis in the Eholoko Fluxon Model v1.pdf",
        r"A First-Principles Derivation of a Universal Biological Timescale from a Unified Field v2.pdf",

        # Physics (General/Other)
        r"A Definitive, Stable Solution to the Three-Body Problem and the Discovery of the Trefoil Orbit via the Eholoko Fluxon Model.pdf",
        r"The Law of Dissipation and Harmony- A Unified Principle for Stellar and Galactic Dynamics Validated by a Solution to the Three-Body Problem.pdf"
    ]
}

def find_tex_file(pdf_filename, search_path):
    """Recursively find the .tex file corresponding to the pdf filename."""
    tex_filename = pdf_filename.replace(".pdf", ".tex")
    for root, dirs, files in os.walk(search_path):
        if tex_filename in files:
            return os.path.join(root, tex_filename)
    return None

def clean_tex_content(content):
    """Remove preamble and document environment wrappers."""
    # Remove everything before \begin{document}
    content = re.sub(r'.*?\\begin\{document\}', '', content, flags=re.DOTALL)
    # Remove \end{document}
    content = re.sub(r'\\end\{document\}', '', content)
    # Remove \maketitle
    content = re.sub(r'\\maketitle', '', content)
    # Remove \tableofcontents
    content = re.sub(r'\\tableofcontents', '', content)
    # Remove \clearpage (optional, but maybe good to keep for separation)
    # Remove \clearpage to let master control flow
    content = re.sub(r'\\clearpage', '', content)
    content = re.sub(r'\\cleardoublepage', '', content)
    content = re.sub(r'\\newpage', '', content)
    
    # Do NOT manually replace bibliography. We will redefine the environment in master.
    # content = re.sub(r'\\begin\{thebibliography\}\{.*?\}', r'\\section*{References}\\begin{itemize}', content)
    # content = re.sub(r'\\end\{thebibliography\}', r'\\end{itemize}', content)
    # content = re.sub(r'\\bibitem\{(.*?)\}', r'\\item[\1] ', content) 
    
    return content

def extract_definitions(content):
    """Extract newcommand and def from preamble."""
    preamble = content.split(r'\begin{document}')[0]
    definitions = []
    
    # Find lines starting with \newcommand or \def
    for line in preamble.split('\n'):
        line = line.strip()
        if line.startswith(r'\newcommand') or line.startswith(r'\def') or line.startswith(r'\DeclareMathOperator'):
            definitions.append(line)
    return definitions

def main():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

def generate_slug(title):
    """Generate a label slug from a title."""
    # Remove non-alphanumeric chars and lower case
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', title).lower().strip('-')
    return f"paper:{slug}"

def link_bibliography(content, title_to_label):
    """Inject links into bibliography items."""
    # We need to find \bibitem{...} text
    # This is tricky with regex because of nested braces and multiline.
    # But usually bibitem is \bibitem{key} ...text... until next \bibitem or \end{thebibliography}
    
    # Split by \bibitem
    parts = re.split(r'(\\bibitem\{.*?\})', content)
    
    new_content = parts[0] # Preamble before first bibitem
    
    for i in range(1, len(parts), 2):
        bibitem_cmd = parts[i]
        bibitem_text = parts[i+1]
        
        # Check for matches
        for title, label in title_to_label.items():
            # Normalize title and text for matching?
            # The titles in filenames are quite specific.
            # Let's try simple substring match.
            # We need to be careful not to match self.
            
            # Clean title for matching (remove v2, v3 etc if needed, but filenames have them)
            # Actually, bibliography might cite "The Cosmic Engine" but we have "The Cosmic Engine... V2.pdf"
            # We should probably match the "Core" title.
            # For now, let's try matching the full filename title (minus extension)
            # If that fails, we might need fuzzy matching.
            
            # Let's strip " v\d+" from the title for matching purposes
            match_title = re.sub(r' [vV]\d+(\.\d+)?$', '', title)
            match_title = re.sub(r' - Validation$', '', match_title)
            
            if match_title.lower() in bibitem_text.lower():
                # Avoid double linking if already linked (unlikely in source)
                # Add link
                link_text = f" \\textbf{{(See Chapter \\ref{{{label}}})}}"
                # Only add if not already there (idempotency check not strictly needed if running once)
                bibitem_text = bibitem_text.rstrip() + link_text + "\n"
                # Break after finding one match to avoid clutter? 
                # Or allow multiple? Usually one paper per bibitem.
                break
        
        new_content += bibitem_cmd + bibitem_text
        
    return new_content

EFM_V4_DIR = r"/Users/tshuutheniemvula/Documents/Fun/analysis/copies/EFM V4"

def index_images(root_dir):
    """Recursively index all image files in a directory."""
    image_index = {}
    print(f"Indexing images in {root_dir}...")
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
                image_index[file] = os.path.join(root, file)
    print(f"Indexed {len(image_index)} images.")
    return image_index

def copy_referenced_images(content, paper_build_dir, local_media_dir, local_paper_dir, global_image_index):
    """Find \includegraphics and copy images from local or global sources."""
    # Regex to find filenames in \includegraphics{...}
    # Handles optional arguments [width=...]
    matches = re.findall(r'\\includegraphics(?:\[.*?\])?\{(.*?)\}', content)
    
    for image_name in matches:
        # Clean image name (remove path if present in tex, though usually relative)
        image_filename = os.path.basename(image_name)
        
        # 1. Try local media dir
        src_path = None
        if local_media_dir and os.path.exists(os.path.join(local_media_dir, image_filename)):
            src_path = os.path.join(local_media_dir, image_filename)
        # 2. Try local paper dir
        elif os.path.exists(os.path.join(local_paper_dir, image_filename)):
            src_path = os.path.join(local_paper_dir, image_filename)
        # 3. Try global EFM V4 index
        elif image_filename in global_image_index:
            src_path = global_image_index[image_filename]
            print(f"  Found missing image in EFM V4: {image_filename}")
        
        if src_path:
            dest_path = os.path.join(paper_build_dir, image_filename)
            if not os.path.exists(dest_path): # Avoid re-copying
                shutil.copy(src_path, dest_path)
        else:
            print(f"  WARNING: Image not found: {image_filename}")

def main():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)

    # Index EFM V4 images
    efm_v4_images = index_images(EFM_V4_DIR)

    # Pre-calculate labels
    title_to_label = {}
    for section, pdf_files in STRUCTURE.items():
        for pdf_file in pdf_files:
            title = pdf_file.replace(".pdf", "")
            label = generate_slug(title)
            title_to_label[title] = label

    # Collect all definitions
    all_definitions = []

    master_content_start = [
        r"\documentclass[a4paper,11pt,openany]{report}", # openany avoids blank pages between chapters
        r"\usepackage{graphicx}",
        r"\usepackage{import}",
        r"\usepackage[breaklinks=true]{hyperref}", # breaklinks for long URLs
        r"\usepackage{amsmath}",
        r"\usepackage{amssymb}",
        r"\usepackage{amsthm}",
        r"\usepackage{geometry}",
        r"\geometry{margin=1in}",
        r"\usepackage{fancyhdr}",
        r"\usepackage{float}", 
        r"\usepackage{booktabs}", 
        r"\usepackage{caption}",
        r"\usepackage{subcaption}",
        r"\usepackage{tikz}", 
        r"\usetikzlibrary{shapes.geometric, arrows, positioning, fit, calc, backgrounds}",
        r"\usepackage{listings}", 
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{natbib}",
        r"\usepackage{enumitem}",
        r"\usepackage{tabularx}",
        r"\usepackage{longtable}",
        r"\usepackage{multirow}",
        r"\usepackage{array}",
        r"\usepackage{bm}",
        r"\usepackage{url}",
        r"\def\UrlBreaks{\do\/\do-}", # Allow breaking URLs at / and -
        r"\title{Eholoko Fluxon Model Compendium}",
        r"\author{Tshuutheni Emvula}",
        r"\date{\today}",
        r"\raggedbottom", # Avoid vertical stretching
        r"\setlength{\emergencystretch}{3em}", # Help with overfull hboxes
        
        # Global Listing Settings for Code Blocks
        r"\lstset{",
        r"    basicstyle=\ttfamily\footnotesize,",
        r"    breaklines=true,",
        r"    breakatwhitespace=false,", # Allow breaking anywhere if needed
        r"    frame=single,", # Add a frame
        r"    backgroundcolor=\color{gray!5},", # Light gray background
        r"    captionpos=b,",
        r"    keepspaces=true,",
        r"    columns=flexible,",
        r"    showstringspaces=false,",
        r"    keywordstyle=\color{blue},",
        r"    commentstyle=\color{green!50!black},",
        r"    stringstyle=\color{red}",
        r"}",

        # Redefine thebibliography to be a section, not a chapter
        r"\makeatletter",
        r"\renewenvironment{thebibliography}[1]",
        r"     {\section*{\refname}%",
        r"      \@mkboth{\MakeUppercase\refname}{\MakeUppercase\refname}%",
        r"      \raggedright", # Force ragged right to prevent reference overflow
        r"      \list{\@biblabel{\@arabic\c@enumiv}}%",
        r"           {\settowidth\labelwidth{\@biblabel{#1}}%",
        r"            \leftmargin\labelwidth",
        r"            \advance\leftmargin\labelsep",
        r"            \@openbib@code",
        r"            \usecounter{enumiv}%",
        r"            \let\p@enumiv\@empty",
        r"            \renewcommand\theenumiv{\@arabic\c@enumiv}}%",
        r"      \sloppy",
        r"      \clubpenalty4000",
        r"      \@clubpenalty \clubpenalty",
        r"      \widowpenalty4000%",
        r"      \sfcode`\.\@m}",
        r"     {\def\@noitemerr",
        r"       {\@latex@warning{Empty `thebibliography' environment}}%",
        r"      \endlist}",
        r"\makeatother"
    ]
    
    master_content_body = [
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\clearpage"
    ]

    paper_count = 0
    
    for section, pdf_files in STRUCTURE.items():
        # Escape special characters in section title
        safe_section = section.replace("&", r"\&")
        master_content_body.append(f"\\chapter{{{safe_section}}}")
        
        for pdf_file in pdf_files:
            tex_path = find_tex_file(pdf_file, RESEARCH_DIR)
            if not tex_path:
                print(f"Warning: Could not find source for {pdf_file}")
                continue
            
            print(f"Processing: {pdf_file}")
            
            # Create a unique directory for this paper
            paper_count += 1
            paper_dir_name = f"paper_{paper_count}"
            paper_build_dir = os.path.join(BUILD_DIR, paper_dir_name)
            if not os.path.exists(paper_build_dir):
                os.makedirs(paper_build_dir)
            
            # Copy .tex file
            tex_filename = os.path.basename(tex_path)
            shutil.copy(tex_path, os.path.join(paper_build_dir, tex_filename))
            
            # Identify media directories
            paper_dir = os.path.dirname(tex_path)
            parent_dir = os.path.dirname(paper_dir)
            media_dir = os.path.join(parent_dir, "media")
            if not os.path.exists(media_dir):
                media_dir = None

            # Read and Clean .tex
            with open(tex_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Extract definitions
            defs = extract_definitions(content)
            all_definitions.extend(defs)

            cleaned_content = clean_tex_content(content)
            
            # Inject Links
            cleaned_content = link_bibliography(cleaned_content, title_to_label)
            
            # Copy Images (Smart Find)
            copy_referenced_images(cleaned_content, paper_build_dir, media_dir, paper_dir, efm_v4_images)

            # Write cleaned .tex
            safe_tex_filename = "paper.tex"
            with open(os.path.join(paper_build_dir, safe_tex_filename), 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            # Add import to master
            paper_title = pdf_file.replace(".pdf", "").replace("&", r"\&").replace("_", r"\_")
            paper_label = title_to_label[pdf_file.replace(".pdf", "")]
            
            master_content_body.append(f"\\section{{{paper_title}}}")
            master_content_body.append(f"\\label{{{paper_label}}}") # Add label
            master_content_body.append(f"\\import{{{paper_dir_name}/}}{{{safe_tex_filename}}}")
            master_content_body.append(r"\clearpage")

    master_content_body.append(r"\end{document}")
    
    # Deduplicate definitions
    unique_definitions = sorted(list(set(all_definitions)))
    
    # Combine all content
    full_content = master_content_start + ["% Custom Definitions"] + unique_definitions + master_content_body

    with open(os.path.join(BUILD_DIR, "compendium.tex"), 'w', encoding='utf-8') as f:
        f.write("\n".join(full_content))

    print("Compiling PDF...")
    # Run pdflatex twice for TOC
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "compendium.tex"], cwd=BUILD_DIR)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "compendium.tex"], cwd=BUILD_DIR)
    
    if os.path.exists(os.path.join(BUILD_DIR, "compendium.pdf")):
        print(f"Success! PDF generated at {os.path.join(BUILD_DIR, 'compendium.pdf')}")
    else:
        print("Error: PDF generation failed.")

if __name__ == "__main__":
    main()
