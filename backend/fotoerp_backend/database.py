"""FotoDerp Backend — Datenbank-Setup (SQLite + PostgreSQL)"""

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL - SQLite by default, PostgreSQL optional
DATABASE_URL = os.getenv(
    "FOTOERP_DATABASE_URL",
    "sqlite:///./fotoerp.db"
)

# Engine setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Models ---

class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True, index=True)
    path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String, nullable=True)
    size = Column(Integer, nullable=True)
    captured_at = Column(DateTime, nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)
    phash = Column(String, nullable=True)  # Perceptual hash für Duplikate
    preview_path = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, analyzing, done, error
    rating = Column(Integer, nullable=True)  # 1-5 Sterne
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Face(Base):
    __tablename__ = "faces"

    id = Column(String, primary_key=True, index=True)
    photo_id = Column(String, nullable=False)
    person_id = Column(String, nullable=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)


class Person(Base):
    __tablename__ = "persons"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    embedding = Column(JSON, nullable=True)  # Embedding als JSON-Array
    face_count = Column(Integer, default=0)
    unknown = Column(Boolean, default=True)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, default="auto")
    usage_count = Column(Integer, default=0)


class PhotoTag(Base):
    __tablename__ = "photo_tags"

    photo_id = Column(String, primary_key=True)
    tag_id = Column(String, primary_key=True)


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, index=True)
    photo_id = Column(String, nullable=False)
    type = Column(String, nullable=False)  # object, scene, aesthetic, ocr
    data = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)


class Collection(Base):
    __tablename__ = "collections"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    photo_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Datenbank initialisieren"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Database Session erhalten"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
