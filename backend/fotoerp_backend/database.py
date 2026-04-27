"""FotoDerp Backend — SQLite Datenbank (stdlib, kein ORM)

Schlank, schnell, kein SQLAlchemy-Overhead.
Nutzt FTS5 für Volltextsuche und BLOB-Embeddings für Vektorsuche.
"""

import sqlite3
import struct
import os
import json
from pathlib import Path
from typing import Optional


# Datenbank-Pfad — im App-Datenverzeichnis (nicht im Installationsordner!)
def _db_path() -> str:
    """Datenbankpfad plattformübergehend."""
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home()))
    elif hasattr(os, "uname") and os.uname().sysname == "Darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    app_dir = Path(base) / "FotoDerp"
    app_dir.mkdir(parents=True, exist_ok=True)
    return str(app_dir / "fotoerp.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """DB-Connection mit Row-Factory."""
    if db_path is None:
        db_path = _db_path()
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Bessere Concurrency
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: Optional[str] = None):
    """Datenbank-Tabellen erstellen (idempotent)."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    # --- photos ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id          TEXT PRIMARY KEY,
            path        TEXT NOT NULL UNIQUE,
            filename    TEXT NOT NULL,
            width       INTEGER,
            height      INTEGER,
            format      TEXT,
            size        INTEGER,
            captured_at TEXT,
            gps_lat     REAL,
            gps_lon     REAL,
            phash       TEXT,           -- perceptual hash (dup detection)
            preview_path TEXT,
            status      TEXT DEFAULT 'pending',  -- pending|analyzing|done|error
            rating      INTEGER CHECK(rating BETWEEN 1 AND 5),
            created_at  TEXT DEFAULT (datetime('now')),
            updated_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # FTS5 virtual table für Volltextsuche (spiegelt photos)
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS photos_fts
        USING fts5(filename, format, captured_at, phash, content='photos', content_rowid='rowid')
    """)

    # FTS5-Sync Triggers
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS photos_ai AFTER INSERT ON photos
        BEGIN
            INSERT INTO photos_fts(rowid, filename, format, captured_at, phash)
            VALUES (new.rowid, new.filename, new.format, new.captured_at, new.phash);
        END
    """)
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS photos_ad AFTER DELETE ON photos
        BEGIN
            INSERT INTO photos_fts(photos_fts, rowid, filename, format, captured_at, phash)
            VALUES ('delete', old.rowid, old.filename, old.format, old.captured_at, old.phash);
        END
    """)
    cur.execute("""
        CREATE TRIGGER IF NOT EXISTS photos_au AFTER UPDATE ON photos
        BEGIN
            INSERT INTO photos_fts(photos_fts, rowid, filename, format, captured_at, phash)
            VALUES ('delete', old.rowid, old.filename, old.format, old.captured_at, old.phash);
            INSERT INTO photos_fts(rowid, filename, format, captured_at, phash)
            VALUES (new.rowid, new.filename, new.format, new.captured_at, new.phash);
        END
    """)

    # --- faces ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id          TEXT PRIMARY KEY,
            photo_id    TEXT NOT NULL REFERENCES photos(id),
            person_id   TEXT,
            x           REAL NOT NULL,
            y           REAL NOT NULL,
            width       REAL NOT NULL,
            height      REAL NOT NULL,
            confidence  REAL NOT NULL
        )
    """)

    # --- persons ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            embedding   BLOB,         -- float[] als packed bytes
            face_count  INTEGER DEFAULT 0,
            unknown     INTEGER DEFAULT 1
        )
    """)

    # --- tags ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id          TEXT PRIMARY KEY,
            name        TEXT UNIQUE NOT NULL,
            category    TEXT DEFAULT 'auto',
            usage_count INTEGER DEFAULT 0
        )
    """)

    # --- photo_tags (M:N) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS photo_tags (
            photo_id  TEXT NOT NULL REFERENCES photos(id),
            tag_id    TEXT NOT NULL REFERENCES tags(id),
            PRIMARY KEY (photo_id, tag_id)
        )
    """)

    # --- analyses ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id            TEXT PRIMARY KEY,
            photo_id      TEXT NOT NULL REFERENCES photos(id),
            type          TEXT NOT NULL,  -- object|scene|aesthetic|ocr|face
            data          TEXT,           -- JSON
            confidence    REAL,
            model_version TEXT,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    # --- embeddings ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            photo_id  TEXT PRIMARY KEY REFERENCES photos(id),
            vector    BLOB NOT NULL      -- float[] als packed bytes
        )
    """)

    # --- collections ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            photo_ids  TEXT DEFAULT '[]',  -- JSON array of photo IDs
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # --- Indexes ---
    cur.execute("CREATE INDEX IF NOT EXISTS idx_photos_status ON photos(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_faces_photo ON faces(photo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_analyses_photo ON analyses(photo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")

    conn.commit()
    conn.close()


# ============================================================
# Helper: Embedding als BLOB packen/unpacken
# ============================================================

def pack_embedding(vec: list[float]) -> bytes:
    """float[] → packed bytes (little-endian float32)."""
    return struct.pack(f"<{len(vec)}f", *vec)


def unpack_embedding(blob: bytes) -> list[float]:
    """packed bytes → float[]."""
    n = len(blob) // 4
    return list(struct.unpack(f"<{n}f", blob))


# ============================================================
# Convenience functions (keine Klasse, einfach halten)
# ============================================================

def add_photo(photo_id: str, path: str, filename: str, **kwargs) -> bool:
    """Foto-Eintrag erstellen."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO photos (id, path, filename, width, height, format, size,
               captured_at, gps_lat, gps_lon, phash, preview_path, status, rating)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (photo_id, path, filename,
             kwargs.get("width"), kwargs.get("height"), kwargs.get("format"),
             kwargs.get("size"), kwargs.get("captured_at"),
             kwargs.get("gps_lat"), kwargs.get("gps_lon"),
             kwargs.get("phash"), kwargs.get("preview_path"),
             kwargs.get("status", "pending"),
             kwargs.get("rating")),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Already exists
    finally:
        conn.close()


def get_photo(photo_id: str) -> dict | None:
    """Foto-Detail laden."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_photos(status: Optional[str] = None, limit: int = 50, offset: int = 0,
                min_rating: Optional[int] = None) -> list[dict]:
    """List photos with optional filters."""
    conn = get_connection()
    conditions = []
    params: list = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if min_rating is not None and min_rating > 0:
        conditions.append("rating >= ?")
        params.append(min_rating)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"SELECT * FROM photos{where} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_photos(status: Optional[str] = None, min_rating: Optional[int] = None) -> int:
    """Count photos with optional filters."""
    conn = get_connection()
    conditions = []
    params: list = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if min_rating is not None and min_rating > 0:
        conditions.append("rating >= ?")
        params.append(min_rating)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    query = f"SELECT COUNT(*) as c FROM photos{where}"

    row = conn.execute(query, params).fetchone()
    conn.close()
    return row["c"]


def search_photos(query: str, limit: int = 50, offset: int = 0) -> list[dict]:
    """FTS5 full-text search with pagination."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.* FROM photos_fts f
           JOIN photos p ON p.rowid = f.rowid
           WHERE photos_fts MATCH ?
           ORDER BY rank LIMIT ? OFFSET ?""",
        (query, limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_search_results(query: str) -> int:
    """Count total FTS5 search results."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as c FROM photos_fts WHERE photos_fts MATCH ?",
        (query,),
    ).fetchone()
    conn.close()
    return row["c"]


def add_tag(tag_id: str, name: str, category: str = "auto") -> bool:
    """Tag erstellen."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO tags (id, name, category) VALUES (?, ?, ?)",
            (tag_id, name, category),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def assign_tag(photo_id: str, tag_id: str):
    """Tag einem Foto zuweisen."""
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO photo_tags (photo_id, tag_id) VALUES (?, ?)",
        (photo_id, tag_id),
    )
    conn.execute(
        "UPDATE tags SET usage_count = usage_count + 1 WHERE id = ?",
        (tag_id,),
    )
    conn.commit()
    conn.close()


def get_photo_tags(photo_id: str) -> list[dict]:
    """Tags eines Fotos laden."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT t.* FROM tags t
           JOIN photo_tags pt ON pt.tag_id = t.id
           WHERE pt.photo_id = ?""",
        (photo_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_analysis(analysis_id: str, photo_id: str, atype: str,
                 data: dict, confidence: Optional[float] = None,
                 model_version: Optional[str] = None):
    """Analyse-Ergebnis speichern."""
    import json
    conn = get_connection()
    conn.execute(
        """INSERT INTO analyses (id, photo_id, type, data, confidence, model_version)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (analysis_id, photo_id, atype, json.dumps(data), confidence, model_version),
    )
    conn.commit()
    conn.close()


def get_analyses(photo_id: str) -> list[dict]:
    """Analysen eines Fotos laden."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM analyses WHERE photo_id = ?", (photo_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_embedding(photo_id: str, vector: list[float]):
    """Embedding speichern (packed float32)."""
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO embeddings (photo_id, vector) VALUES (?, ?)",
        (photo_id, pack_embedding(vector)),
    )
    conn.commit()
    conn.close()


def get_embedding(photo_id: str) -> Optional[list[float]]:
    """Embedding laden."""
    conn = get_connection()
    row = conn.execute("SELECT vector FROM embeddings WHERE photo_id = ?", (photo_id,)).fetchone()
    conn.close()
    if row:
        return unpack_embedding(row["vector"])
    return None


def find_similar_embeddings(photo_id: str, limit: int = 20) -> list[dict]:
    """Ähnliche Bilder via Cosine Similarity finden."""
    import math

    conn = get_connection()
    row = conn.execute("SELECT vector FROM embeddings WHERE photo_id = ?", (photo_id,)).fetchone()
    if not row:
        conn.close()
        return []

    query_vec = unpack_embedding(row["vector"])

    # Alle Embeddings laden (für Desktop-Größen OK)
    all_rows = conn.execute("SELECT photo_id, vector FROM embeddings WHERE photo_id != ?").fetchall()
    conn.close()

    results = []
    for r in all_rows:
        vec = unpack_embedding(r["vector"])
        # Cosine Similarity
        dot = sum(a * b for a, b in zip(query_vec, vec))
        mag_q = math.sqrt(sum(a * a for a in query_vec))
        mag_v = math.sqrt(sum(a * a for a in vec))
        if mag_q > 0 and mag_v > 0:
            similarity = dot / (mag_q * mag_v)
            results.append({"photo_id": r["photo_id"], "score": similarity})

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def set_photo_status(photo_id: str, status: str):
    """Foto-Status aktualisieren."""
    conn = get_connection()
    conn.execute("UPDATE photos SET status = ?, updated_at = datetime('now') WHERE id = ?",
                 (status, photo_id))
    conn.commit()
    conn.close()


def update_photo_preview(photo_id: str, preview_path: str):
    """Preview-Pfad aktualisieren."""
    conn = get_connection()
    conn.execute(
        "UPDATE photos SET preview_path = ?, updated_at = datetime('now') WHERE id = ?",
        (preview_path, photo_id),
    )
    conn.commit()
    conn.close()


def find_duplicate(phash: str) -> Optional[str]:
    """Duplikat via phash finden."""
    conn = get_connection()
    row = conn.execute("SELECT id FROM photos WHERE phash = ? LIMIT 1", (phash,)).fetchone()
    conn.close()
    return row["id"] if row else None


# ============================================================
# Additional query helpers for UI endpoints
# ============================================================

def list_all_tags() -> list[dict]:
    """Alle Tags auflisten."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tags ORDER BY usage_count DESC, name ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_all_persons() -> list[dict]:
    """Erkannte Personen auflisten."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM persons ORDER BY face_count DESC, name ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_photos(limit: int = 10) -> list[dict]:
    """Neueste Fotos laden."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM photos ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_storage_used() -> int:
    """Gespeicherte Datenmenge in Bytes."""
    conn = get_connection()
    row = conn.execute("SELECT COALESCE(SUM(size), 0) as total FROM photos").fetchone()
    conn.close()
    return row["total"]


def add_person(person_id: str, name: Optional[str] = None, embedding: Optional[bytes] = None,
               face_count: int = 0, unknown: int = 1):
    """Person erstellen oder aktualisieren."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO persons (id, name, embedding, face_count, unknown)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
               name=excluded.name,
               embedding=excluded.embedding,
               face_count=excluded.face_count,
               unknown=excluded.unknown""",
        (person_id, name, embedding, face_count, unknown),
    )
    conn.commit()
    conn.close()


def rename_person(person_id: str, name: str) -> bool:
    """Person umbenennen."""
    if not name:
        return False
    conn = get_connection()
    cur = conn.execute(
        "UPDATE persons SET name = ?, unknown = 0 WHERE id = ?",
        (name, person_id),
    )
    conn.commit()
    success = cur.rowcount > 0
    conn.close()
    return success


def add_face(face_id: str, photo_id: str, person_id: Optional[str],
             x: float, y: float, width: float, height: float, confidence: float):
    """Face-Erkennung speichern."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO faces (id, photo_id, person_id, x, y, width, height, confidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (face_id, photo_id, person_id, x, y, width, height, confidence),
    )
    # Person face_count aktualisieren
    if person_id:
        conn.execute(
            "UPDATE persons SET face_count = face_count + 1 WHERE id = ?",
            (person_id,),
        )
    conn.commit()
    conn.close()


def update_photo_rating(photo_id: str, rating: int):
    """Rating eines Fotos setzen (0-5). 0 = Rating löschen."""
    conn = get_connection()
    if rating == 0:
        conn.execute(
            "UPDATE photos SET rating = NULL, updated_at = datetime('now') WHERE id = ?",
            (photo_id,),
        )
    else:
        conn.execute(
            "UPDATE photos SET rating = ?, updated_at = datetime('now') WHERE id = ?",
            (rating, photo_id),
        )
    conn.commit()
    conn.close()


def get_favorites(limit: int = 50, offset: int = 0) -> list[dict]:
    """Fotos mit Rating >= 3 (Favoriten) laden."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM photos WHERE rating >= 3 ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# Collection helpers
# ============================================================

def list_collections() -> list[dict]:
    """Alle Collections auflisten."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM collections ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        # Parse photo_ids JSON
        import json as _json
        try:
            d["photo_count"] = len(_json.loads(d.get("photo_ids", "[]")))
        except (_json.JSONDecodeError, TypeError):
            d["photo_count"] = 0
        result.append(d)
    return result


def create_collection(collection_id: str, name: str) -> dict:
    """Neue Collection erstellen."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO collections (id, name, photo_ids) VALUES (?, ?, '[]')",
        (collection_id, name),
    )
    conn.commit()
    conn.close()
    return {"id": collection_id, "name": name}


def add_to_collection(collection_id: str, photo_id: str):
    """Foto zu Collection hinzufügen."""
    conn = get_connection()
    row = conn.execute("SELECT photo_ids FROM collections WHERE id = ?", (collection_id,)).fetchone()
    if row:
        import json as _json
        try:
            photo_ids = _json.loads(row["photo_ids"])
        except (json.JSONDecodeError, TypeError):
            photo_ids = []
        if photo_id not in photo_ids:
            photo_ids.append(photo_id)
        conn.execute(
            "UPDATE collections SET photo_ids = ? WHERE id = ?",
            (_json.dumps(photo_ids), collection_id),
        )
    conn.commit()
    conn.close()


def remove_from_collection(collection_id: str, photo_id: str):
    """Foto aus Collection entfernen."""
    conn = get_connection()
    row = conn.execute("SELECT photo_ids FROM collections WHERE id = ?", (collection_id,)).fetchone()
    if row:
        import json as _json
        try:
            photo_ids = _json.loads(row["photo_ids"])
        except (_json.JSONDecodeError, TypeError):
            photo_ids = []
        if photo_id in photo_ids:
            photo_ids.remove(photo_id)
        conn.execute(
            "UPDATE collections SET photo_ids = ? WHERE id = ?",
            (_json.dumps(photo_ids), collection_id),
        )
    conn.commit()
    conn.close()


def delete_collection(collection_id: str) -> bool:
    """Collection löschen."""
    conn = get_connection()
    cur = conn.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0
