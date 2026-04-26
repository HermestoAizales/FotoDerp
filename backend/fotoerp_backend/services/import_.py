"""FotoDerp Backend — Foto-Import Service

Schlank: nur Pillow + exifread, kein rawpy (optional).
Kein ORM, direkt sqlite3 über database.py.
"""

import os
import hashlib
from datetime import datetime
from PIL import Image
from typing import List, Dict, Optional

from ..database import add_photo, find_duplicate, set_photo_status


SUPPORTED_FORMATS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.tiff', '.tif', '.raw', '.cr2', '.nef', '.arw',
    '.dng', '.heic', '.heif',
}


def calculate_phash(image_path: str) -> Optional[str]:
    """Perceptual Hash (MD5 von 8x8 grayscale)."""
    try:
        img = Image.open(image_path).convert('L').resize((8, 8), Image.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = ''.join('1' if p > avg else '0' for p in pixels)
        return hashlib.md5(bits.encode()).hexdigest()
    except Exception:
        return None


def extract_exif(image_path: str) -> Dict:
    """EXIF-Metadaten extrahieren."""
    result = {
        'width': None, 'height': None, 'format': None,
        'size': None, 'captured_at': None,
        'gps_lat': None, 'gps_lon': None,
    }

    try:
        result['size'] = os.path.getsize(image_path)
        ext = os.path.splitext(image_path)[1].lstrip('.').upper()
        result['format'] = ext if ext else 'UNKNOWN'

        with Image.open(image_path) as img:
            result['width'], result['height'] = img.size

        # EXIF mit exifread
        try:
            import exifread
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)

                if 'EXIF TimeOriginal' in tags:
                    date_str = str(tags['EXIF TimeOriginal'])
                    try:
                        result['captured_at'] = datetime.strptime(
                            date_str[:19], '%Y:%m:%d %H:%M:%S'
                        ).isoformat()
                    except ValueError:
                        pass

                if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                    lat = _exif_to_deg(tags['GPS GPSLatitude'],
                                       tags.get('GPS GPSLatitudeRef', 'N'))
                    lon = _exif_to_deg(tags['GPS GPSLongitude'],
                                       tags.get('GPS GPSLongitudeRef', 'E'))
                    result['gps_lat'] = lat
                    result['gps_lon'] = lon
        except ImportError:
            pass  # exifread optional
        except Exception:
            pass

    except Exception as e:
        print(f"[FotoDerp] EXIF-Fehler bei {image_path}: {e}")

    return result


def _exif_to_deg(values, ref):
    """EXIF GPS-Werte → Dezimalgrad."""
    try:
        deg = float(values.values[0].num) + \
              float(values.values[1].num) / 60 + \
              float(values.values[2].num) / 3600
        return -deg if ref in ['S', 'W'] else deg
    except Exception:
        return None


def scan_directory(directory: str) -> List[str]:
    """Verzeichnis rekursiv nach Bildern durchsuchen."""
    images = []
    for root, _, files in os.walk(directory):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SUPPORTED_FORMATS:
                images.append(os.path.join(root, filename))
    return images


def import_photos(paths: List[str]) -> Dict:
    """Fotos importieren und indizieren.

    Keine DB-Session mehr, jede Operation committet selbst.
    """
    result = {'imported': 0, 'errors': [], 'skipped': 0}

    for path in paths:
        if os.path.isdir(path):
            image_files = scan_directory(path)
        elif os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_FORMATS:
                image_files = [path]
            else:
                result['errors'].append(f"Format nicht unterstützt: {path}")
                continue
        else:
            result['errors'].append(f"Pfad nicht gefunden: {path}")
            continue

        for image_path in image_files:
            try:
                phash = calculate_phash(image_path)

                # Duplikat-Check
                if phash:
                    existing = find_duplicate(phash)
                    if existing:
                        result['skipped'] += 1
                        continue

                exif = extract_exif(image_path)
                photo_id = hashlib.sha256(image_path.encode()).hexdigest()[:16]

                added = add_photo(photo_id, image_path, os.path.basename(image_path),
                                  **exif, status='pending')
                if added:
                    result['imported'] += 1
                else:
                    result['skipped'] += 1

            except Exception as e:
                result['errors'].append(f"Fehler bei {image_path}: {e}")

    return result


def mark_analyzing(photo_id: str):
    """Foto als 'in Analyse' markieren."""
    set_photo_status(photo_id, 'analyzing')


def mark_done(photo_id: str):
    """Foto als 'analyisiert' markieren."""
    set_photo_status(photo_id, 'done')
