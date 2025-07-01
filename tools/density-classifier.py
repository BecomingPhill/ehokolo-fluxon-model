#!/usr/bin/env python3
"""
Density Classifier for Ehokolo Fluxon Model Repository

This script categorizes hypothesis papers by density based on their content and keywords.
"""

import os
import shutil
import re
from pathlib import Path
import argparse

class DensityClassifier:
    def __init__(self, repo_root):
        self.repo_root = Path(repo_root)
        self.hypothesis_dir = self.repo_root / "hypothesis-papers"
        
        # Keywords for each density
        self.density_keywords = {
            'n1-st': {
                'keywords': [
                    'black hole', 'cosmology', 'gravitational', 'astrophysics',
                    'large-scale structure', 'CMB', 'inflation', 'universe',
                    'galaxy', 'star formation', 'gravitational waves',
                    'spacetime', 'curvature', 'Hubble tension'
                ],
                'description': 'N1 (S/T) - Time/Space ratio > 1'
            },
            'n2-ts': {
                'keywords': [
                    'quantum', 'measurement', 'nuclear', 'particle physics',
                    'wavefunction', 'superposition', 'entanglement',
                    'nuclear forces', 'strong force', 'weak force',
                    'quantum field theory', 'quantum mechanics'
                ],
                'description': 'N2 (T/S) - Space/Time ratio > 1'
            },
            'n3-st': {
                'keywords': [
                    'electromagnetic', 'atomic', 'chemistry', 'biology',
                    'consciousness', 'bioelectronics', 'molecular',
                    'visible spectrum', 'light', 'photon', 'electron',
                    'atomic structure', 'chemical', 'biological'
                ],
                'description': 'N3 (S=T) - Space = Time'
            }
        }
    
    def classify_paper(self, file_path):
        """Classify a paper based on its filename and content"""
        filename = file_path.name.lower()
        
        # Check filename first
        for density, info in self.density_keywords.items():
            for keyword in info['keywords']:
                if keyword.lower() in filename:
                    return density
        
        # If filename doesn't give clear indication, check content
        if file_path.suffix.lower() in ['.tex', '.pdf']:
            try:
                # For .tex files, read content
                if file_path.suffix.lower() == '.tex':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                else:
                    # For PDFs, we'll rely on filename for now
                    # Could add PDF text extraction later
                    return None
                
                # Count keyword matches
                density_scores = {}
                for density, info in self.density_keywords.items():
                    score = 0
                    for keyword in info['keywords']:
                        score += len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', content))
                    density_scores[density] = score
                
                # Return density with highest score
                if density_scores:
                    best_density = max(density_scores, key=density_scores.get)
                    if density_scores[best_density] > 0:
                        return best_density
                        
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return None
    
    def organize_hypothesis_papers(self, source_dir):
        """Organize hypothesis papers from source directory"""
        source_path = Path(source_dir)
        
        if not source_path.exists():
            print(f"Source directory not found: {source_path}")
            return
        
        # Find all .tex and .pdf files
        files = list(source_path.glob("*.tex")) + list(source_path.glob("*.pdf"))
        
        print(f"Found {len(files)} hypothesis papers to organize")
        
        # Track classifications
        classifications = {}
        unclassified = []
        
        for file_path in files:
            print(f"\nProcessing: {file_path.name}")
            
            density = self.classify_paper(file_path)
            
            if density:
                classifications[file_path.name] = density
                print(f"  → Classified as {density}: {self.density_keywords[density]['description']}")
                
                # Copy to appropriate directory
                target_dir = self.hypothesis_dir / density
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Determine subcategory based on content
                subcategory = self.determine_subcategory(file_path, density)
                if subcategory:
                    target_dir = target_dir / subcategory
                    target_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = target_dir / file_path.name
                shutil.copy2(file_path, target_path)
                print(f"  → Copied to: {target_path}")
                
            else:
                unclassified.append(file_path.name)
                print(f"  → Could not classify")
        
        # Summary
        print(f"\n=== Classification Summary ===")
        for density in self.density_keywords:
            count = sum(1 for f, d in classifications.items() if d == density)
            print(f"{density}: {count} papers")
        
        if unclassified:
            print(f"\nUnclassified papers ({len(unclassified)}):")
            for paper in unclassified:
                print(f"  - {paper}")
    
    def determine_subcategory(self, file_path, density):
        """Determine subcategory within a density"""
        filename = file_path.name.lower()
        
        if density == 'n1-st':
            if any(word in filename for word in ['black hole', 'blackhole']):
                return 'astrophysics'
            elif any(word in filename for word in ['cosmology', 'universe', 'CMB', 'inflation']):
                return 'cosmology'
            elif any(word in filename for word in ['gravitational', 'gravity']):
                return 'gravitational'
        
        elif density == 'n2-ts':
            if any(word in filename for word in ['quantum', 'measurement', 'wavefunction']):
                return 'quantum'
            elif any(word in filename for word in ['nuclear', 'particle', 'strong force', 'weak force']):
                return 'nuclear'
        
        elif density == 'n3-st':
            if any(word in filename for word in ['electromagnetic', 'photon', 'light']):
                return 'electromagnetic'
            elif any(word in filename for word in ['atomic', 'electron']):
                return 'atomic'
            elif any(word in filename for word in ['chemistry', 'chemical', 'molecular']):
                return 'chemistry'
            elif any(word in filename for word in ['biology', 'consciousness', 'bioelectronics']):
                return 'biology'
        
        return None

def main():
    parser = argparse.ArgumentParser(description="Classify hypothesis papers by density")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--source", required=True, help="Source directory containing hypothesis papers")
    
    args = parser.parse_args()
    
    classifier = DensityClassifier(args.repo_root)
    classifier.organize_hypothesis_papers(args.source)

if __name__ == "__main__":
    main() 