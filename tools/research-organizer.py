#!/usr/bin/env python3
"""
Research Organizer for Ehokolo Fluxon Model Repository

This script organizes current research from EFM V4 into the new density-based structure.
"""

import os
import shutil
from pathlib import Path
import argparse

class ResearchOrganizer:
    def __init__(self, repo_root):
        self.repo_root = Path(repo_root)
        self.research_dir = self.repo_root / "research"
        
        # Mapping from EFM V4 folders to density categories
        self.folder_mapping = {
            'Black Holes': 'n1-st/black-holes',
            'Hubble Tension': 'n1-st/cosmology',
            'Inlfation': 'n1-st/cosmology',  # Note: typo in original folder name
            'EFM Universe': 'n1-st/cosmology',
            'Densities': 'n2-ts/quantum-measurement',
            'derivations': 'n2-ts/particle-physics',
            'Mass': 'n3-st/atomic-structure',
            'Spin': 'n3-st/atomic-structure',
            'Interference': 'n3-st/electromagnetic',
            'new sim': 'n3-st/chemistry',
            'Intro': 'n3-st/atomic-structure',
            'Dimensonless': 'n2-ts/particle-physics',  # Note: typo in original folder name
            'Physics Foundation': 'n2-ts/particle-physics'
        }
    
    def organize_research(self, source_dir):
        """Organize research from EFM V4 source directory"""
        source_path = Path(source_dir)
        
        if not source_path.exists():
            print(f"Source directory not found: {source_path}")
            return
        
        print(f"Organizing research from: {source_path}")
        
        # Process each folder in EFM V4
        for folder in source_path.iterdir():
            if folder.is_dir() and folder.name in self.folder_mapping:
                target_path = self.research_dir / self.folder_mapping[folder.name]
                print(f"\nProcessing: {folder.name} → {target_path}")
                
                # Create target directory
                target_path.mkdir(parents=True, exist_ok=True)
                
                # Copy contents
                self.copy_folder_contents(folder, target_path)
                
                # Create README for the research area
                self.create_research_readme(target_path, folder.name)
                
            elif folder.is_file() and folder.name.endswith('.ipynb'):
                # Handle standalone notebooks
                print(f"\nProcessing standalone notebook: {folder.name}")
                target_path = self.research_dir / "n3-st/chemistry"  # Default to chemistry
                target_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(folder, target_path)
                print(f"  → Copied to: {target_path}")
    
    def copy_folder_contents(self, source_folder, target_folder):
        """Copy folder contents with organization"""
        notebooks_dir = target_folder / "notebooks"
        results_dir = target_folder / "results"
        papers_dir = target_folder / "papers"
        
        # Create subdirectories
        notebooks_dir.mkdir(exist_ok=True)
        results_dir.mkdir(exist_ok=True)
        papers_dir.mkdir(exist_ok=True)
        
        # Copy files by type
        for item in source_folder.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(source_folder)
                
                # Determine target subdirectory based on file type
                if item.suffix.lower() == '.ipynb':
                    target_path = notebooks_dir / relative_path
                elif item.suffix.lower() in ['.png', '.jpg', '.jpeg', '.pdf', '.csv', '.txt']:
                    target_path = results_dir / relative_path
                elif item.suffix.lower() in ['.tex', '.md']:
                    target_path = papers_dir / relative_path
                else:
                    target_path = results_dir / relative_path
                
                # Create parent directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(item, target_path)
                print(f"  → {relative_path} → {target_path.relative_to(self.research_dir)}")
    
    def create_research_readme(self, target_path, original_folder_name):
        """Create a README for the research area"""
        readme_content = f"""# {original_folder_name.replace('_', ' ').title()}

## Overview
Research area derived from EFM V4: {original_folder_name}

## Contents
- `notebooks/` - Jupyter notebooks for simulations and analysis
- `results/` - Generated plots, data, and media files
- `papers/` - LaTeX papers and documentation

## Current Status
[To be updated with current research status]

## Next Steps
[To be updated with planned research directions]

## Related Hypothesis Papers
[To be linked to relevant hypothesis papers]
"""
        
        readme_path = target_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print(f"  → Created README: {readme_path}")

def main():
    parser = argparse.ArgumentParser(description="Organize EFM V4 research into new structure")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--source", required=True, help="Source EFM V4 directory")
    
    args = parser.parse_args()
    
    organizer = ResearchOrganizer(args.repo_root)
    organizer.organize_research(args.source)

if __name__ == "__main__":
    main() 