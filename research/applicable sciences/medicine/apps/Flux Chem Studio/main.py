import socket
import threading
import time
import sys
import os
import uvicorn
import webview

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

from engine.server import app

def start_server(port):
    # Ensure local directory is on python path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def wait_for_server(port, timeout=5.0):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
    return False

class Api:
    def __init__(self):
        self.window = None

    def save_file(self, filename, content):
        if not self.window:
            return {"success": False, "error": "Window not initialized"}
        
        file_types = ('All files (*.*)',)
        if filename.endswith('.json'):
            file_types = ('JSON files (*.json)', 'All files (*.*)')
        elif filename.endswith('.sdf'):
            file_types = ('SDF files (*.sdf)', 'All files (*.*)')
            
        result = self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=os.path.expanduser('~/Downloads'),
            save_filename=filename,
            file_types=file_types
        )
        
        if result:
            filepath = result if isinstance(result, str) else result[0]
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                return {"success": True, "path": filepath}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "cancelled"}

def main():
    port = find_free_port()
    
    # Start FastAPI server in a background daemon thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()
    
    if not wait_for_server(port):
        print(f"Error: Local server failed to start on port {port} within 5 seconds.")
        sys.exit(1)
        
    print(f"FastAPI Server running on http://127.0.0.1:{port}")
    
    api = Api()
    # Open PyWebView desktop window pointing to the FastAPI server
    window = webview.create_window(
        title="Flux Chem Studio - EFM Molecular Design",
        url=f"http://127.0.0.1:{port}",
        width=1280,
        height=850,
        min_size=(1024, 768),
        resizable=True,
        js_api=api
    )
    api.window = window
    webview.start(debug=False)


if __name__ == "__main__":
    main()
