"""FotoDerp Backend — Foto-Import Service"""

import os
import hashlib
from datetime import datetime
from PIL import Image
import exifread
from typing import List, Dict, Optional

# Import database models
try:
    from ..database import Photo, get_db, SessionLocal
except ImportError:
    pass


SUPPORTED_FORMATS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.tiff', '.tif', '.raw', '.cr2', '.nef', '.arw',
    '.dng', '.heic', '.heif',
}


def calculate_phash(image_path: str) -> Optional[str]:
    """Perceptual Hash für Duplikat-Erkennung berechnen"""
    try:
        img = Image.open(image_path).convert('L').resize((8, 8), Image.LANCZOS)
        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)
        bits = ''.join('1' if p > avg else '0' for p in pixels)
        return hashlib.md5(bits.encode()).hexdigest()
    except Exception:
        return None


def extract_exif(image_path: str) -> Dict:
    """EXIF-Metadaten extrahieren"""
    result = {
        'width': None,
        'height': None,
        'format': None,
        'size': None,
        'captured_at': None,
        'gps_lat': None,
        'gps_lon': None,
    }

    try:
        # File info
        result['size'] = os.path.getsize(image_path)
        result['format'] = image_path.split('.')[-1].upper()

        # Image dimensions
        with Image.open(image_path) as img:
            result['width'], result['height'] = img.size

        # EXIF Daten
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)

                # Aufnahme-Datum
                if 'EXIF TimeOriginal' in tags:
                    date_str = str(tags['EXIF TimeOriginal'])
                    try:
                        result['captured_at'] = datetime.strptime(
                            date_str[:19], '%Y:%m:%d %H:%M:%S'
                        )
                    except ValueError:
                        pass

                # GPS Koordinaten
                if 'GPS GPSLatitude' in tags and 'GPS GPSLongitude' in tags:
                    lat = _convert_exif_to_deg(tags['GPS GPSLatitude'], tags.get('GPS GPSLatitudeRef', 'N'))
                    lon = _convert_exif_to_deg(tags['GPS GPSLongitude'], tags.get('GPS GPSLongitudeRef', 'E'))
                    result['gps_lat'] = lat
                    result['gps_lon'] = lon
        except Exception:
            pass

    except Exception as e:
        print(f"[FotoDerp] EXIF-Fehler bei {image_path}: {e}")

    return result


def _convert_exif_to_deg(values, ref):
    """EXIF GPS-Werte zu Dezimalgrad konvertieren"""
    try:
        deg = float(values.values[0].num) + \
              float(values.values[1].num) / 60 + \
              float(values.values[2].num) / 3600
        return -deg if ref in ['S', 'W'] else deg
    except Exception:
        return None


def scan_directory(directory: str) -> List[str]:
    """Verzeichnis rekursiv nach Bildern durchsuchen"""
    images = []
    for root, _, files in os.walk(directory):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SUPPORTED_FORMATS:
                images.append(os.path.join(root, filename))
    return images


def import_photos(paths: List[str]) -> Dict:
    """Fotos importieren und indizieren"""
    result = {
        'imported': 0,
        'errors': [],
        'skipped': 0,
    }

    db = SessionLocal()

    try:
        for path in paths:
            if os.path.isdir(path):
                # Verzeichnis durchsuchen
                image_files = scan_directory(path)
            elif os.path.isfile(path):
                ext = os.path.splitext(path)[1].lower()
                if ext in SUPPORTED_FORMATS:
                    image_files = [path]
                else:
                    result['errors'].append(f"Unterstütztes Format erwartet: {path}")
                    continue
            else:
                result['errors'].append(f"Pfad nicht gefunden: {path}")
                continue

            for image_path in image_files:
                try:
                    # Prüfe ob schon importiert (via phash)
                    phash = calculate_phash(image_path)
                    existing = db.query(Photo).filter_by(phash=phash).first()
                    if existing:
                        result['skipped'] += 1
                        continue

                    # Metadaten extrahieren
                    exif = extract_exif(image_path)

                    # Photo-Eintrag erstellen
                    photo = Photo(
                        id=hashlib.sha256(image_path.encode()).hexdigest()[:16],
                        path=image_path,
                        filename=os.path.basename(image_path),
                        **exif,
                        status='pending',
                    )
                    db.add(photo)
                    result['imported'] += 1

                except Exception as e:
                    result['errors'].append(f"Fehler bei {image_path}: {e}")

        db.commit()
    finally:
        db.close()

    return result
