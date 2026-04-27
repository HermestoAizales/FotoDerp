#!/usr/bin/env python3
"""PyInstaller Build-Skript für FotoDerp Backend.

Kompilert das Python-Backend zu einem nativen Binary.
Unterstützt: Windows (x64), macOS (ARM64/x86_64), Linux (x64).

Verwendung:
    python build_backend.py                    # Current platform
    python build_backend.py --target linux
    python build_backend.py --target win
    python build_backend.py --target mac
"""

import argparse
import os
import platform as plat
import subprocess
import sys
from pathlib import Path


def get_target_platform(target: str | None) -> str:
    """Zielplattform bestimmen."""
    if target:
        mapping = {
            "linux": "linux",
            "win": "windows",
            "windows": "windows",
            "mac": "darwin",
            "macos": "darwin",
        }
        return mapping.get(target, target)

    system = plat.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "darwin"
    else:
        return "linux"


def build_windows(backend_dir: Path, output_dir: Path):
    """Build für Windows mit PyInstaller."""
    print("Building for Windows with PyInstaller...")
    
    # PyInstaller installieren falls nicht vorhanden
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    entry = backend_dir / "fotoerp_backend" / "main.py"
    
    # PyInstaller Kommando
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "fotoerp-backend",
        "--distpath", str(output_dir),
        "--workpath", str(backend_dir / "build"),
        "--specpath", str(backend_dir),
        # Python-Pfade hinzufügen
        "--paths", str(backend_dir),
        "--paths", str(backend_dir / "fotoerp_backend"),
        # Versteckte Importe (falls nötig)
        "--hidden-import", "uvicorn",
        "--hidden-import", "fastapi",
        str(entry)
    ]
    
    print(f"Command: {' '.join(pyinstaller_cmd)}")
    result = subprocess.run(pyinstaller_cmd, cwd=str(backend_dir))
    
    if result.returncode != 0:
        print(f"ERROR: PyInstaller build failed with exit code {result.returncode}")
        sys.exit(1)
    
    # Binary prüfen
    output_binary = output_dir / "fotoerp-backend.exe"
    if output_binary.exists():
        print(f"SUCCESS: Built {output_binary} ({output_binary.stat().st_size} bytes)")
    else:
        print("ERROR: Output binary not found!")
        sys.exit(1)


def build_linux(backend_dir: Path, output_dir: Path):
    """Build für Linux mit PyInstaller."""
    print("Building for Linux with PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    entry = backend_dir / "fotoerp_backend" / "main.py"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "fotoerp-backend",
        "--distpath", str(output_dir),
        str(entry)
    ]
    
    result = subprocess.run(pyinstaller_cmd, cwd=str(backend_dir))
    if result.returncode != 0:
        print(f"ERROR: Build failed with exit code {result.returncode}")
        sys.exit(1)


def build_macos(backend_dir: Path, output_dir: Path):
    """Build für macOS."""
    print("Building for macOS...")
    # Ähnlich wie Linux, ggf. mit --windowed für GUI
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    entry = backend_dir / "fotoerp_backend" / "main.py"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "fotoerp-backend",
        "--distpath", str(output_dir),
        str(entry)
    ]
    
    result = subprocess.run(pyinstaller_cmd, cwd=str(backend_dir))
    if result.returncode != 0:
        print(f"ERROR: Build failed with exit code {result.returncode}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Build FotoDerp Backend")
    parser.add_argument("--target", help="Target platform (linux, win, mac)")
    args = parser.parse_args()
    
    backend_dir = Path(__file__).parent.resolve()
    target_platform = get_target_platform(args.target)
    
    # Output-Verzeichnis
    output_dir = backend_dir / "dist" / target_platform
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Building for {target_platform}...")
    print(f"Backend dir: {backend_dir}")
    print(f"Output dir: {output_dir}")
    
    if target_platform == "windows":
        build_windows(backend_dir, output_dir)
    elif target_platform == "darwin":
        build_macos(backend_dir, output_dir)
    else:
        build_linux(backend_dir, output_dir)
    
    print(f"\nBuild complete! Binary in {output_dir}")


if __name__ == "__main__":
    main()
