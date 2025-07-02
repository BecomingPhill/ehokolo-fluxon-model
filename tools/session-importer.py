#!/usr/bin/env python3
"""
LLM Session Importer for Eholoko Fluxon Model Repository

This script helps import and organize LLM chat sessions from Google AI Studio and Grok.
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
import argparse

class SessionImporter:
    def __init__(self, repo_root):
        self.repo_root = Path(repo_root)
        self.sessions_dir = self.repo_root / "llm-sessions"
        
    def import_google_ai_studio(self, source_path):
        """Import Google AI Studio sessions from Google Drive"""
        source_path = Path(source_path)
        
        if not source_path.exists():
            print(f"Source path not found: {source_path}")
            return
            
        # Look for JSON files that might be Google AI Studio sessions
        json_files = list(source_path.glob("**/*.json"))
        
        print(f"Found {len(json_files)} potential session files")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Try to extract session info
                session_info = self.extract_session_info(data, json_file.name)
                
                if session_info:
                    print(f"\nSession: {session_info['title']}")
                    print(f"Date: {session_info['date']}")
                    print(f"Tokens: {session_info.get('token_count', 'Unknown')}")
                    
                    # Ask user if they want to import this session
                    response = input("Import this session? (y/n/p for private): ").lower()
                    
                    if response in ['y', 'p']:
                        self.save_session(data, session_info, response == 'p')
                        
            except Exception as e:
                print(f"Error processing {json_file}: {e}")
    
    def import_grok_sessions(self, source_path):
        """Import Grok sessions from exported archive"""
        source_path = Path(source_path)
        
        if not source_path.exists():
            print(f"Source path not found: {source_path}")
            return
            
        # Look for Grok session files (might be JSON or other formats)
        session_files = list(source_path.glob("**/*"))
        
        print(f"Found {len(session_files)} potential Grok session files")
        
        for session_file in session_files:
            if session_file.is_file():
                print(f"\nGrok session: {session_file.name}")
                
                # Ask user if they want to import this session
                response = input("Import this session? (y/n/p for private): ").lower()
                
                if response in ['y', 'p']:
                    self.save_grok_session(session_file, response == 'p')
    
    def extract_session_info(self, data, filename):
        """Extract session information from Google AI Studio JSON"""
        try:
            # Google AI Studio JSON structure might vary
            # Try common patterns
            if isinstance(data, dict):
                # Look for common fields
                title = data.get('title', data.get('name', filename))
                date = data.get('created_at', data.get('date', 'Unknown'))
                token_count = data.get('token_count', data.get('tokens', 'Unknown'))
                
                return {
                    'title': title,
                    'date': date,
                    'token_count': token_count,
                    'source': 'google-ai-studio'
                }
        except Exception as e:
            print(f"Error extracting session info: {e}")
        
        return None
    
    def save_session(self, data, session_info, is_private=False):
        """Save session to appropriate directory"""
        # Create filename
        safe_title = "".join(c for c in session_info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{safe_title}.json"
        
        # Determine target directory
        if is_private:
            target_dir = self.sessions_dir / "private"
        else:
            target_dir = self.sessions_dir / "google-ai-studio"
        
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        
        # Save session
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': session_info,
                'session_data': data
            }, f, indent=2)
        
        print(f"Saved session to: {target_path}")
    
    def save_grok_session(self, session_file, is_private=False):
        """Save Grok session to appropriate directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{session_file.name}"
        
        # Determine target directory
        if is_private:
            target_dir = self.sessions_dir / "private"
        else:
            target_dir = self.sessions_dir / "grok"
        
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        
        # Copy session file
        shutil.copy2(session_file, target_path)
        print(f"Saved Grok session to: {target_path}")

def main():
    parser = argparse.ArgumentParser(description="Import LLM sessions for EFM repository")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    parser.add_argument("--google-drive", help="Path to Google Drive AI Studio sessions")
    parser.add_argument("--grok-archive", help="Path to Grok session archive")
    
    args = parser.parse_args()
    
    importer = SessionImporter(args.repo_root)
    
    if args.google_drive:
        print("Importing Google AI Studio sessions...")
        importer.import_google_ai_studio(args.google_drive)
    
    if args.grok_archive:
        print("Importing Grok sessions...")
        importer.import_grok_sessions(args.grok_archive)
    
    if not args.google_drive and not args.grok_archive:
        print("Please specify --google-drive or --grok-archive path")
        print("Example: python session-importer.py --google-drive ~/Google\ Drive/AI\ Studio")

if __name__ == "__main__":
    main() 