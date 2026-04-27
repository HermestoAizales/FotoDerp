--
title: FotoDerp Windows RDP Testing
description: Automate testing of FotoDerp on Windows VM via RDP using xfreerdp + XTest input injection
category: testing
created: 2026-04-26
--

# FotoDerp Windows RDP Testing Skill

Automated testing of FotoDerp on a Windows 10 VM via RDP connection.

## VM Connection Details

| Parameter | Wert |
|-----------|------|
| **IP** | `192.168.1.223` |
| **Protokoll** | RDP (Port 3389) |
| **Benutzer** | `User` |
| **Passwort** | `user` |
| **OS** | Windows 10 |

## Prerequisites

Auf dem Linux-Host müssen installiert sein:
```bash
sudo apt install freerdp3-x11 xvfb xdotool imagemagick python3-pip
pip install --break-system-packages python-xlib
```

## Architecture

```
pi (Agent)
  ├── xfreerdp3 → RDP → Windows VM (192.168.1.223)
  │                 └── Virtual Framebuffer (Xvfb :99)
  │
  ├── python-xlib (XTestFakeKeyEvent) → Xvfb :99
  │         └── Injects keystrokes at X server level
  │
  ├── xdotool → Xvfb :99
  │         └── Window management & screenshots
  │
  └── import (ImageMagick) → Xvfb :99
              └── Screenshot capture
```

## Key Files

- `/home/hermes/FotoDerpTest/rdp_automation.py` — Python controller for RDP session
- `/home/hermes/FotoDerpTest/start_rdp.sh` — Start script for RDP session
- `/home/hermes/FotoDerpTest/test_fotoderp.ps1` — PowerShell test script for Windows side

## Quick Start

### 1. RDP Session starten

```bash
cd /home/hermes/FotoDerpTest
./start_rdp.sh
```

Oder manuell:
```bash
# Virtual Framebuffer starten
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# RDP Verbindung
nohup xfreerdp3 /v:192.168.1.223 /u:User /p:user /size:1920x1080 /cert:ignore > /tmp/xfreerdp.log 2>&1 &
sleep 10
```

### 2. Testen mit rdp_automation.py

```bash
export DISPLAY=:99
python3 /home/hermes/FotoDerpTest/rdp_automation.py test
```

### 3. Screenshots machen

```bash
export DISPLAY=:99
import -window root /tmp/screenshot.png
```

## Testing Workflow

### FotoDerp Test-Szenario

1. **FotoDerp auf Windows VM vorbereiten**
   - Installer von GitHub holen

2. **FotoDerp starten**
   - Installer installieren und starten

3. **Fotos importieren**
   - "Bilder" Ordner auf Desktop der VM enthält 3 Testbilder
   - Import-Button klicken → Ordner auswählen

4. **KI-Analyse starten**
   - "Analysieren" Button klicken
   - Fortschritt beobachten

5. **Ergebnisse prüfen**
   - Tags sichtbar?
   - Similarity search funktioniert?
   - Rating möglich?

## rdp_automation.py Usage

```python
from rdp_automation import RDPController

ctrl = RDPController()  # Uses DISPLAY=:99 by default

# Keyboard
ctrl.key('super')              # Windows key
ctrl.key('return')             # Enter
ctrl.key('escape')             # Escape
ctrl.key('a', modifiers=['ctrl'])  # Ctrl+A

# Typing
ctrl.type('hello world')       # Type text
ctrl.type('PowerShell')        # Opens search

# Mouse
ctrl.click()                   # Left click
ctrl.double_click()            # Double click
ctrl.move(500, 300)            # Move mouse
ctrl.scroll(1)                 # Scroll up

# Combined actions
ctrl.key('super')              # Open Start menu
time.sleep(2)
ctrl.type('cmd')               # Type 'cmd'
time.sleep(1)
ctrl.key('return')             # Press Enter
```

## PowerShell Test Script (auf Windows VM)

Auf der Windows VM kann ein PowerShell-Skript laufen das:
- FotoDerp installiert/updated
- Tests automatisiert
- Screenshots/Logs zurück nach Linux kopiert

Siehe `test_fotoderp.ps1` für ein Beispiel.

## Troubleshooting

### RDP Verbindung funktioniert nicht
```bash
# VM erreichbar?
nc -zv 192.168.1.223 3389

# xfreerdp neu starten
pkill -f xfreerdp3
# ... neu starten ...
```

### Tasten werden nicht gesendet
- Xvfb läuft? `ps aux | grep Xvfb`
- DISPLAY gesetzt? `echo $DISPLAY` (sollte :99 sein)
- xfreerdp hat Focus? Window ID prüfen: `xdotool search --name "192.168"`

### Screenshots leer/dunkel
- import braucht DISPLAY: `export DISPLAY=:99`
- xfreerdp muss verbunden sein (nicht nur gestartet)

### FotoDerp auf Windows VM finden
```powershell
# Auf der VM ausführen (via RDP):
Get-ChildItem "C:\Users\User\FotoDerp" -Recurse -Filter "*.exe" | Select-Object FullName
```

## Notes

- **NICHT** `~/.pi/skills/` verwenden — richtig ist `~/.pi/agent/skills/`
- RDP-Session bleibt bestehen bis xfreerdp beendet wird
- Screenshots werden im Xvfb gemacht, nicht auf der Windows VM selbst
- Für persistente Tests: PowerShell-Skript auf der VM + SSH/RDP Befehle
