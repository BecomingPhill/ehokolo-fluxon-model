import os
import shutil
import sys
import PyInstaller.__main__

def build():
    print("Starting build process for Flux Chem Studio...")
    
    # Define directories
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "dist")
    build_dir = os.path.join(base_dir, "build")
    
    # Clean previous build artifacts
    for directory in [dist_dir, build_dir]:
        if os.path.exists(directory):
            print(f"Cleaning {directory}...")
            try:
                shutil.rmtree(directory)
            except Exception as e:
                print(f"Warning: Could not clean {directory}: {e}")
            
    # Detect current platform
    is_mac = sys.platform == "darwin"
    is_linux = sys.platform.startswith("linux")
    
    if not is_mac and not is_linux:
        print(f"Warning: Building on unsupported platform '{sys.platform}'. Defaulting to standard packaging.")

    # PyInstaller arguments
    args = [
        "main.py",
        "--name=Flux Chem Studio",
        f"--add-data={os.path.join(base_dir, 'frontend')}{os.pathsep}frontend",
        f"--add-data={os.path.join(base_dir, 'data')}{os.pathsep}data",
        "--hidden-import=uvicorn.protocols.http.h11_impl",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.protocols.websockets.websockets_impl",
        "--hidden-import=uvicorn.protocols.websockets.wsproto_impl",
        "--clean"
    ]
    
    if is_mac:
        args.append("--windowed")  # Create a macOS app bundle (.app)
    elif is_linux:
        args.append("--windowed")  # Suppress terminal window spawning in desktop environment

    
    print(f"Running PyInstaller with arguments: {args}")
    try:
        PyInstaller.__main__.run(args)
        print("Build completed successfully!")
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
