#!/usr/bin/env python3
"""Nuitka-Build-Skript für FotoDerp Backend.

Kompiliert das Python-Backend zu einem nativen Binary.
Unterstützt: Windows (x64), macOS (ARM64/x86_64), Linux (x64).

Verwendung:
    python build_backend.py                    # Current platform
    python build_backend.py --target linux     # Cross-compile (needs Linux toolchain)
    python build_backend.py --target win       # Cross-compile (needs Windows VM/CI)
    python build_backend.py --target mac-arm   # Cross-compile (needs macOS VM)

Output: dist/fotoerp-backend/<platform>/fotoerp-backend (executable)
"""

import argparse
import os
import platform as plat
import subprocess
import sys
import shutil
from pathlib import Path


def get_target_platform(target: str | None) -> str:
    """Zielplattform bestimmen."""
    if target:
        mapping = {
            "linux": "linux",
            "win": "windows",
            "windows": "windows",
            "mac": "darwin",
            "mac-arm": "darwin",
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
    """Nuitka-Build fuer Zielplattform."""
    backend_dir = Path(__file__).parent.resolve()
    dist_dir = backend_dir / "dist"
    output_dir = dist_dir / target_platform

    # Output-Verzeichnis erstellen
    output_dir.mkdir(parents=True, exist_ok=True)

    entry_point = backend_dir / "fotoerp_backend" / "main.py"
    if not entry_point.exists():
        print(f"ERROR: Entry point not found: {entry_point}")
        sys.exit(1)

    # Nuitka-Befehl zusammenstellen
    # Use --follow-imports to handle all dependencies explicitly
    nuitka_opts = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=pytest",
        "--python-flag=-OO",
        "--output-dir=" + str(output_dir),
        "--output-filename=fotoerp-backend",
    ]

    if target_platform == "windows":
        nuitka_opts.append("--windows-icon-from-ico=../icons/icon.ico")

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
    # onefile mode: single executable directly in output dir
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
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Nuitka-Build fuer FotoDerp Backend")
    parser.add_argument("--target", type=str, help="Zielplattform: linux, win, mac, mac-arm")
    args = parser.parse_args()

    target = get_target_platform(args.target)
    build(target)


if __name__ == "__main__":
    main()
