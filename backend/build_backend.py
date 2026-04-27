#!/usr/bin/env python3
"""Nuitka-Build-Skript für FotoDerp Backend.

Kompiliert das Python-Backend zu einem nativen Binary.
Unterstützt: Windows (x64), macOS (ARM64/x86_64), Linux (x64).

Verwendung:
    python build_backend.py                    # Current platform
    python build_backend.py --target linux     # Cross-compile (needs Linux toolchain)
    python build_backend.py --target win       # Cross-compile (needs Windows VM/CI)
    python build_backend.py --target mac        # Cross-compile (needs macOS VM)

Output: dist/<platform>/fotoerp-backend (executable)
"""

import argparse
import os
import platform as plat
import subprocess
import sys
import shutil
from pathlib import Path


def download_dependency_walker_windows():
    """Dependency Walker für Windows herunterladen und bereitstellen."""
    import urllib.request
    import zipfile
    
    nuitka_cache = Path.home() / ".nuitka"
    nuitka_cache.mkdir(parents=True, exist_ok=True)
    
    deps_exe = nuitka_cache / "Dependencies.exe"
    
    if deps_exe.exists():
        print(f"Dependencies.exe bereits vorhanden: {deps_exe}")
        return str(deps_exe)
    
    print("Downloading Dependency Walker for Windows...")
    url = "https://github.com/lucasg/Dependencies/releases/download/v1.11.1/Dependencies_x64_Release.zip"
    zip_path = nuitka_cache / "deps.zip"
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        print(f"Downloaded: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find Dependencies.exe in archive
            for name in zip_ref.namelist():
                if name.endswith("Dependencies.exe"):
                    zip_ref.extract(name, nuitka_cache)
                    extracted = nuitka_cache / name
                    if extracted.exists() and extracted != deps_exe:
                        shutil.move(str(extracted), str(deps_exe))
                    print(f"Dependencies.exe extracted to: {deps_exe}")
                    break
        
        zip_path.unlink(missing_ok=True)
        return str(deps_exe)
        
    except Exception as e:
        print(f"WARNING: Could not download Dependency Walker: {e}")
        return None


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
        # macOS — ARM64 (Apple Silicon) oder x86_64
        machine = plat.machine()
        if machine == "arm64":
            return "darwin-arm64"
        return "darwin-x86_64"
    else:
        return "linux"


def build(target_platform: str):
    """Nuitka-Build für Zielplattform."""
    backend_dir = Path(__file__).parent.resolve()
    dist_dir = backend_dir / "dist"
    output_dir = dist_dir / target_platform

    # Output-Verzeichnis erstellen
    output_dir.mkdir(parents=True, exist_ok=True)

    entry_point = backend_dir / "fotoerp_backend" / "main.py"
    if not entry_point.exists():
        print(f"ERROR: Entry point not found: {entry_point}")
        sys.exit(1)

    # For Windows: Download Dependency Walker first!
    if target_platform == "windows":
        dep_tool = download_dependency_walker_windows()
        if dep_tool:
            os.environ["NUITKA_WINDOWS_DEPENDENCY_TOOL"] = dep_tool
            print(f"Set NUITKA_WINDOWS_DEPENDENCY_TOOL={dep_tool}")

    # Nuitka-Befehl zusammenstellen
    nuitka_opts = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=pytest",
        "--python-flag=-OO",
        "--show-progress",
        f"--output-dir={output_dir}",
        "--output-filename=fotoerp-backend",
    ]

    if target_platform == "windows":
        nuitka_opts.append("--windows-icon-from-ico=../icons/icon.ico")
        # Tell Nuitka to auto-download dependencies
        os.environ["NUITKA_ASSUME_YES"] = "1"

    # Compile main.py directly with all dependencies
    entry = backend_dir / "fotoerp_backend" / "main.py"
    nuitka_opts.append(str(entry))

    print(f"Building for {target_platform}...")
    print(f"Command: {' '.join(nuitka_opts)}")
    print()

    env = os.environ.copy()
    result = subprocess.run(nuitka_opts, cwd=str(backend_dir), env=env)
    if result.returncode != 0:
        print(f"\nERROR: Build failed with exit code {result.returncode}")
        sys.exit(1)

    # Binary ins richtige Verzeichnis verschieben
    if target_platform == "windows":
        exe = output_dir / "fotoerp-backend.exe"
        if exe.exists():
            print(f"\nBinary: {exe}")
        else:
            # Fallback: check .dist directory
            for d in [output_dir / "fotoerp-backend.dist", output_dir / "main.dist"]:
                if d.exists():
                    exe = d / "fotoerp-backend.exe"
                    if exe.exists():
                        shutil.move(str(exe), str(output_dir / "fotoerp-backend.exe"))
                        print(f"\nBinary: {output_dir / 'fotoerp-backend.exe'}")
                        break
    else:
        exe = output_dir / "fotoerp-backend"
        if exe.exists():
            print(f"\nBinary: {exe}")
        else:
            # Fallback: check .dist directory
            for d in [output_dir / "fotoerp-backend.dist", output_dir / "main.dist"]:
                if d.exists():
                    binary = d / "fotoerp-backend"
                    if not binary.exists():
                        binary = d / "fotoerp-backend.exe"
                    if binary.exists():
                        shutil.move(str(binary), str(exe))
                        print(f"\nBinary: {exe}")
                        break

    # Abhängigkeiten kopieren (Pillow, exifread etc.)
    # Nuitka --standalone sollte alles automatisch kopieren
    print(f"\nBuild complete for {target_platform}: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Nuitka-Build für FotoDerp Backend")
    parser.add_argument("--target", type=str, help="Zielplattform: linux, win, mac, mac-arm")
    args = parser.parse_args()

    target = get_target_platform(args.target)
    build(target)


if __name__ == "__main__":
    main()
