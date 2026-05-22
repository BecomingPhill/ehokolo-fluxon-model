import os
import sys
import threading
import time
import socket
from playwright.sync_api import sync_playwright

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_diagnostics():
    port = find_free_port()
    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Start FastAPI server
    import uvicorn
    def run_server():
        uvicorn.run("engine.server:app", host="127.0.0.1", port=port, log_level="warning")
        
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Wait for spin up
    time.sleep(2.0)
    server_url = f"http://127.0.0.1:{port}"
    
    # Ensure screenshot output directory exists in artifacts
    artifact_dir = "/Users/tshuutheniemvula/.gemini/antigravity/brain/89246898-d80d-4d92-8009-e997f6ee1ae5"
    os.makedirs(artifact_dir, exist_ok=True)
    
    print("Starting Playwright browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        # Log console and page errors
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        page.on("console", lambda msg: print(f"CONSOLE {msg.type}: {msg.text}"))
        
        print(f"Loading {server_url}...")
        page.goto(server_url)
        
        # Take initial screenshot
        page.screenshot(path=os.path.join(artifact_dir, "step1_init.png"))
        print("Took step1_init.png")
        
        # Fetch PDB 1HSG
        print("Fetching PDB 1HSG...")
        pdb_input = page.locator("#pdb-id-input")
        pdb_input.fill("1HSG")
        page.locator("#fetch-target-btn").click()
        
        # Wait for PDB load (up to 8 seconds)
        page.wait_for_function(
            "document.getElementById('target-info').textContent.includes('Loaded')",
            timeout=10000
        )
        page.wait_for_timeout(1000) # extra wait for 3Dmol render
        
        page.screenshot(path=os.path.join(artifact_dir, "step2_pdb_loaded.png"))
        print("Took step2_pdb_loaded.png")
        
        # Run De Novo Evolution
        print("Running De Novo Evolution...")
        page.locator("#run-evolution-btn").click()
        
        # Wait for evolution log (up to 15 seconds)
        page.wait_for_function(
            "document.getElementById('evolution-log').textContent.includes('Selected Scaffold:')",
            timeout=15000
        )
        page.wait_for_timeout(2000) # extra wait for 3Dmol render/zoom
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=os.path.join(artifact_dir, "step3_evolution_done.png"))
        print("Took step3_evolution_done.png")
        
        browser.close()

if __name__ == "__main__":
    run_diagnostics()
