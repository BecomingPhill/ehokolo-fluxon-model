#!/bin/bash

# LLM Session Import Helper Script
# This script helps import LLM sessions from Google Drive and Grok

echo "=== LLM Session Import Helper ==="
echo ""

# Check if Google Drive is mounted
GOOGLE_DRIVE_PATH="$HOME/Google Drive"
if [ -d "$GOOGLE_DRIVE_PATH" ]; then
    echo "✓ Google Drive found at: $GOOGLE_DRIVE_PATH"
    
    # Look for AI Studio sessions
    AI_STUDIO_PATH="$GOOGLE_DRIVE_PATH/AI Studio"
    if [ -d "$AI_STUDIO_PATH" ]; then
        echo "✓ AI Studio folder found"
        echo "To import Google AI Studio sessions, run:"
        echo "  python tools/session-importer.py --google-drive \"$AI_STUDIO_PATH\""
        echo ""
    else
        echo "⚠ AI Studio folder not found in Google Drive"
        echo "Please check if your AI Studio sessions are stored elsewhere"
        echo ""
    fi
else
    echo "⚠ Google Drive not found at: $GOOGLE_DRIVE_PATH"
    echo "Please check your Google Drive location"
    echo ""
fi

# Check for Grok exports
echo "For Grok sessions:"
echo "1. Export your Grok chat history"
echo "2. Extract the archive to a folder"
echo "3. Run: python tools/session-importer.py --grok-archive /path/to/grok/export"
echo ""

echo "=== Manual Import Process ==="
echo "1. The script will show you each session found"
echo "2. For each session, you can choose:"
echo "   - 'y' to import as public"
echo "   - 'p' to import as private"
echo "   - 'n' to skip"
echo "3. Private sessions will be stored in llm-sessions/private/"
echo "4. Public sessions will be organized by source (google-ai-studio/ or grok/)"
echo ""

echo "=== Next Steps ==="
echo "1. Run the import script with your session paths"
echo "2. Review and organize the imported sessions"
echo "3. Update research README files with relevant LLM insights"
echo "4. Commit the organized repository to GitHub"
echo ""

echo "Ready to import sessions? Run one of the commands above." 