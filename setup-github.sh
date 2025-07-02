#!/bin/bash

# GitHub Repository Setup Script for Eholoko Fluxon Model
# This script helps initialize the GitHub repository

echo "=== Eholoko Fluxon Model GitHub Setup ==="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the Eholoko-fluxon-model directory"
    exit 1
fi

echo "✓ Git is installed"
echo "✓ In correct directory"
echo ""

# Initialize git repository
if [ ! -d ".git" ]; then
    echo "Initializing Git repository..."
    git init
    echo "✓ Git repository initialized"
else
    echo "✓ Git repository already exists"
fi

# Add all files
echo "Adding files to repository..."
git add .

# Check if there are files to commit
if git diff --cached --quiet; then
    echo "⚠ No changes to commit. Repository may already be up to date."
else
    echo "✓ Files staged for commit"
    
    # Make initial commit
    echo "Making initial commit..."
    git commit -m "Initial commit: Eholoko Fluxon Model research repository
    
    - Organized hypothesis papers by density (N1-N3)
    - Structured current research from EFM V4
    - Created density-based categorization system
    - Added tools for LLM session import and organization
    - Established research workflow documentation
    - Implemented dual licensing: GPL v3 for code, CC BY-NC-ND 4.0 for papers"
    
    echo "✓ Initial commit completed"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo "   - Name: Eholoko-fluxon-model"
echo "   - Description: Comprehensive research repository for the Eholoko Fluxon Model"
echo "   - Make it public"
echo "   - Don't initialize with README (we already have one)"
echo ""
echo "2. Connect your local repository to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/Eholoko-fluxon-model.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Import LLM sessions:"
echo "   ./tools/import-sessions.sh"
echo ""
echo "4. Update research documentation:"
echo "   - Review and update README files in research areas"
echo "   - Add current status and next steps"
echo "   - Link to relevant hypothesis papers"
echo ""
echo "5. Continue your research workflow:"
echo "   - Use the organized structure for new research"
echo "   - Store LLM insights in appropriate directories"
echo "   - Keep notebooks and results organized by density"
echo ""

echo "Repository setup complete! 🎉" 