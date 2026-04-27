#!/usr/bin/env python3
"""ULTRA-SIMPLE Nuitka build - DAS MUSS LAUFEN!"""

import sys
import subprocess
import os
from pathlib import Path

def build_windows():
    """Build for Windows - SIMPLE VERSION"""
    print("Building for Windows (SIMPLE VERSION)...")
    
    # Download Dependency Walker first
    nuitka_cache = Path.home() / ".nuitka"
    nuitka_cache.mkdir(exist_ok=True)
    deps_exe = nuitka_cache / "Dependencies.exe"
    
    if not deps_exe.exists():
        print("Downloading Dependency Walker...")
        import urllib.request
        url = "https://github.com/lucasg/Dependencies/releases/download/v1.11.1/Dependencies_x64_Release.zip"
        zip_path = nuitka_cache / "deps.zip"
        try:
            urllib.request.urlretrieve(url, zip_path)
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for name in zip_ref.namelist():
                    if name.endswith("Dependencies.exe"):
                        zip_ref.extract(name, nuitka_cache)
                        extracted = nuitka_cache / name
                        if extracted.exists() and str(extracted) != str(deps_exe):
                            import shutil
                            shutil.move(str(extracted), str(deps_exe))
                        print(f"Dependencies.exe downloaded to: {deps_exe}")
                        break
            zip_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"WARNING: Could not download: {e}")
    
    # SIMPLE build - no icon, no complex options
    backend_dir = Path(__file__).parent.resolve()
    entry = backend_dir / "fotoerp_backend" / "main.py"
    
    nuitka_opts = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=pytest",
    ]
    
    # Add dependency tool path if available
    if deps_exe.exists():
        nuitka_opts.append(f"--dependency-tool-path={deps_exe}")
        print(f"Using Dependency Walker: {deps_exe}")
    
    nuitka_opts.append(str(entry))
    
    print(f"Command: {' '.join(nuitka_opts)}")
    result = subprocess.run(nuitka_opts, cwd=str(backend_dir))
    
    if result.returncode != 0:
        print(f"ERROR: Build failed with exit code {result.returncode}")
        sys.exit(1)
    
    print("Build complete!")
    sys.exit(0)

if __name__ == "__main__":
    build_windows()
