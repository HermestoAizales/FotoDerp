"""FotoDerp Backend — KI-Analyse Worker

Hintergrund-Worker für parallele KI-Analyse von Fotos.
Nutzt asyncio für asynchrone Verarbeitung.

Verwendung:
    python -m fotoerp_backend.workers.analyze_worker --batch-size 5
"""

import asyncio
import argparse
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fotoerp.worker")


class AnalyzeWorker:
    """Worker für parallele KI-Analyse"""

    def __init__(self, batch_size: int = 10, llama_endpoint: str = None):
        self.batch_size = batch_size
        self.llama_endpoint = llama_endpoint or "http://127.0.0.1:8080/v1"
        self.processed = 0
        self.errors = []

    async def process_queue(self, photo_ids: List[str]):
        """Batch-Weise Fotos analysieren"""
        total = len(photo_ids)
        
        for i in range(0, total, self.batch_size):
            batch = photo_ids[i:i + self.batch_size]
            logger.info(f"Analysiere Batch {i // self.batch_size + 1}: "
                       f"{len(batch)} Bilder")
            
            # Parallele Analyse im Batch
            tasks = [self._analyze_single(pid) for pid in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Ergebnisse verarbeiten
            for pid, result in zip(batch, results):
                if isinstance(result, Exception):
                    self.errors.append((pid, str(result)))
                    logger.error(f"Fehler bei {pid}: {result}")
                else:
                    self.processed += 1
            
            logger.info(f"Fortschritt: {self.processed}/{total}")

    async def _analyze_single(self, photo_id: str):
        """Einzelnes Foto analysieren"""
        from ..database import Photo, SessionLocal
        from ..services.analysis import analyze_photo
        from ..models import AnalysisResult
        
        db = SessionLocal()
        try:
            photo = db.query(Photo).filter_by(id=photo_id).first()
            if not photo:
                raise ValueError(f"Foto nicht gefunden: {photo_id}")
            
            # Analyse durchführen
            result = await analyze_photo(
                photo.path,
                self.llama_endpoint,
            )
            
            # Ergebnisse speichern
            photo.status = 'done'
            db.add(result)  # TODO: Richtig speichern
            db.commit()
            
        finally:
            db.close()


async def main():
    parser = argparse.ArgumentParser(description="FotoDerp KI-Analyse Worker")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Batch-Größe für parallele Analyse")
    parser.add_argument("--llama-endpoint", type=str, default=None,
                       help="llama.cpp Endpoint URL")
    parser.add_argument("--photo-ids", nargs="+", default=None,
                       help="Zu analysierende Foto-IDs")
    
    args = parser.parse_args()
    
    worker = AnalyzeWorker(
        batch_size=args.batch_size,
        llama_endpoint=args.llama_endpoint,
    )
    
    # Falls keine IDs angegeben, alle pending Fotos laden
    if not args.photo_ids:
        from ..database import Photo, SessionLocal
        db = SessionLocal()
        photos = db.query(Photo).filter_by(status='pending').all()
        args.photo_ids = [p.id for p in photos]
        db.close()
    
    logger.info(f"Starte Analyse: {len(args.photo_ids)} Bilder")
    await worker.process_queue(args.photo_ids)
    
    logger.info(f"Analyse abgeschlossen: "
               f"{worker.processed} verarbeitet, "
               f"{len(worker.errors)} Fehler")


if __name__ == "__main__":
    asyncio.run(main())
