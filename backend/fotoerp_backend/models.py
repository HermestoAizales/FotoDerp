"""FotoDerp Backend — Pydantic Models"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# --- Photo Models ---

class PhotoInfo(BaseModel):
    id: str
    path: str
    filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    size: Optional[int] = None
    captured_at: Optional[datetime] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    tags: List['Tag'] = []
    preview_path: Optional[str] = None


class PhotoListResponse(BaseModel):
    photos: List[PhotoInfo]
    total: int
    page: int
    per_page: int


# --- Tag Models ---

class Tag(BaseModel):
    name: str
    category: str = "auto"
    confidence: float = 1.0


class TagListResponse(BaseModel):
    tags: List[Tag]
    categories: List[str]


# --- Analysis Models ---

class FaceInfo(BaseModel):
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    x: float
    y: float
    width: float
    height: float
    confidence: float


class AnalysisResult(BaseModel):
    photo_id: str
    tags: List[Tag] = []
    faces: List[FaceInfo] = []
    aesthetic_score: Optional[float] = None  # 0.0 - 1.0
    ocr_text: Optional[str] = None
    similarity_hash: Optional[str] = None
    model_version: Optional[str] = None


class AnalysisStatus(BaseModel):
    running: bool
    processed: int
    total: int
    queue_size: int


# --- Person Models ---

class PersonInfo(BaseModel):
    id: str
    name: Optional[str] = None
    face_count: int = 0
    unknown: bool = True


class PersonListResponse(BaseModel):
    persons: List[PersonInfo]


# --- Search Models ---

class SearchResult(BaseModel):
    photo_id: str
    score: float
    photo: PhotoInfo


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


# --- Culling Models ---

class CullingGroup(BaseModel):
    id: str
    type: str  # "similarity", "person", "date", "sequence"
    photos: List[str]  # photo IDs
    selected: List[str] = []
    rejected: List[str] = []


class CullingProject(BaseModel):
    id: str
    folder_paths: List[str]
    profile: str
    photo_count: int
    groups: List[CullingGroup] = []
    created_at: datetime


# --- Analytics Models ---

class AnalyticsOverview(BaseModel):
    total_photos: int
    total_tags: int
    total_persons: int
    storage_used: int  # bytes
    recent_activity: List[dict]


# --- Model Configuration ---

class ModelConfig(BaseModel):
    """Konfiguration eines KI-Modells"""
    id: str
    name: str
    type: str = "vision"       # vision | text | embedding
    endpoint: str = ""          # Leer = lokaler llama.cpp Server
    model_name: str = ""        # Modell-ID für API
    quantization: Optional[str] = None
    context_length: int = 4096
    is_active: bool = False
    description: str = ""


class ModelListResponse(BaseModel):
    models: List[ModelConfig]
    active_model_id: Optional[str] = None


class DownloadStatus(BaseModel):
    model_id: str
    status: str          # "downloading", "ready", "error"
    progress: float = 0.0   # 0.0 - 1.0
    downloaded_mb: float = 0.0
    total_mb: float = 0.0
    error: Optional[str] = None


# --- Settings Models ---

class AppSettings(BaseModel):
    active_model_id: Optional[str] = None
    llama_endpoint: str = "http://127.0.0.1:8080/v1"
    analysis_batch_size: int = 10
    preview_quality: int = 85
    auto_tag_enabled: bool = True
    gpu_layers: int = -1          # -1 = all to GPU
    n_ctx: int = 4096
    n_threads: int = 0            # 0 = auto
    flash_attn: bool = True
    embedding_enabled: bool = True


# --- Import Models ---

class ImportRequest(BaseModel):
    paths: List[str]


class ImportResponse(BaseModel):
    imported: int
    status: str
    errors: List[str] = []


# --- Similarity Models ---

class SimilarPhoto(BaseModel):
    photo_id: str
    score: float
    photo: PhotoInfo


class SimilarResponse(BaseModel):
    photo_id: str
    similar: List[SimilarPhoto]
