# FotoDerp — AI Models & Selection

FotoDerp supports multiple open-source models for different tasks.
Users can choose between a built-in llama.cpp backend and configurable
OpenAPI endpoints.

---

## Model Selection for Users

### 1. VLM (Image Tagging / Scene Recognition / Object Detection)

The VLM analyzes images and generates tags, scene descriptions, and detects objects.

| Model | Size | RAM (Q4) | Quality | GGUF | Recommendation |
|-------|------|----------|---------|------|----------------|
| **SmolVLM-500M** | 500M | ~4 GB | Good | ✓ from ggml-org | **Recommended for small hardware** (8GB RAM) |
| **Moondream2** | 2B | ~3 GB | Fair | ✓ from ggml-org | Fastest option, good basic tags |
| **Qwen2.5-VL-3B** | 3B | ~6 GB | Very Good | ✓ from ggml-org | **Best price/performance ratio** |
| **Qwen2.5-VL-7B** | 7B | ~10 GB | Excellent | ✓ from ggml-org | For systems with 16GB+ RAM |

**Default recommendation:** Qwen2.5-VL-3B (good enough for most tasks, runs on 8GB RAM)

### 2. Embedding Model (Visual Similarity Search)

Generates vector embeddings for images and text — enables semantic search and similarity filtering.

| Model | Size | Type | GGUF | Recommendation |
|-------|------|------|------|----------------|
| **nomic-embed-text-v1.5** | 137M | Text | ✓ | **Default** — fast, good, Apache 2.0 |
| **BGE-M3** | 568M | Text + Multilingual | ✓ | For international use (80+ languages) |
| **CLIP ViT-L-14** | 300M | Image + Text | ✓ GGML | Visual similarity (ggml-org/CLIP-ViT-L-14) |

**Default recommendation:** nomic-embed-text-v1.5 (fast, small, good quality)

### 3. Face Recognition

| Library | Type | Recommendation |
|---------|------|----------------|
| **InsightFace** | Python library with ArcFace models | **Default** — best accuracy |
| **RetinaFace** | Detection + Recognition | Alternative for simpler setups |

### 4. OCR (Text in Images)

| Model | Type | GGUF | Recommendation |
|-------|------|------|----------------|
| **PaddleOCR-VL** | Multimodal OCR | ✓ from ggml-org | **Default** — 80+ languages, integrated into llama.cpp |
| **Nougat** | Document OCR | — | Alternative for document photos |

### 5. Aesthetic Scoring (optional)

| Model | Type | Recommendation |
|-------|------|----------------|
| **BLIP-2 OPT-2.7B** | Image Captioning + Scoring | For aesthetic scoring |

---

## Architecture: Two Modes

### Mode A — Built-in llama.cpp Backend (Default)

FotoDerp automatically starts a built-in llama.cpp server:

```
FotoDerp App → built-in llama-server → GGUF models (local)
```

- **Advantage:** No external configuration needed, everything local
- **Disadvantage:** Slower with large models on weak hardware
- **Model download:** Automatic on first start or selectable via UI

### Mode B — External OpenAPI Endpoint (Advanced)

FotoDerp connects to an existing OpenAI-compatible endpoint:

```
FotoDerp App → HTTP → external llama.cpp / vLLM / Ollama instance
```

- **Advantage:** Faster models on separate hardware, GPU usage
- **Disadvantage:** Requires external configuration
- **Supports:** Any OpenAI-compatible API (Ollama, vLLM, TGI, etc.)

---

## Model Selection in UI

Users select their models via Settings:

```
Settings → AI Models

┌─────────────────────────────────────────┐
│ VLM (Image Analysis)                    │
│ ┌─────────────────────────────────────┐ │
│ │ Qwen2.5-VL-3B-Instruct              │ │ ← Dropdown with all available models
│ ├─────────────────────────────────────┤ │
│ │ [✓] SmolVLM-500M-Instruct           │ │ ← Smallest, fastest option
│ │ [✓] Moondream2                      │ │ ← Very small, good basic tags
│ │ [✓] Qwen2.5-VL-3B-Instruct          │ │ ← Recommended (best value)
│ │ [✓] Qwen2.5-VL-7B-Instruct          │ │ ← Best quality
│ └─────────────────────────────────────┘ │
│                                         │
│ Embedding (Search)                      │
│ ┌─────────────────────────────────────┐ │
│ │ nomic-embed-text-v1.5               │ │
│ ├─────────────────────────────────────┤ │
│ │ [✓] nomic-embed-text-v1.5           │ │ ← Recommended
│ │ [✓] BGE-M3                          │ │ ← Multilingual
│ └─────────────────────────────────────┘ │
│                                         │
│ OCR (Text Recognition)                  │
│ ┌─────────────────────────────────────┐ │
│ │ PaddleOCR-VL-1.5                    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Backend Mode                            │
│ ┌─────────────────────────────────────┐ │
│ │ Built-in llama.cpp Backend          │ │ ← Default
│ ├─────────────────────────────────────┤ │
│ │ External OpenAPI Endpoint           │ │ → Shows URL field
│ └─────────────────────────────────────┘ │
│                                         │
│ [ Download Model ]  [ Test ]            │
└─────────────────────────────────────────┘
```

---

## Automatic Model Download Pipeline

1. **First start:** FotoDerp checks hardware (RAM, CPU)
2. **Hardware detection:**
   - < 8GB RAM → SmolVLM-500M + nomic-embed-text-v1.5
   - 8-16GB RAM → Qwen2.5-VL-3B + nomic-embed-text-v1.5
   - > 16GB RAM → Qwen2.5-VL-7B + BGE-M3
3. **Download:** GGUF models from HuggingFace (ggml-org) are downloaded automatically
4. **Installation:** Models are stored in the user data directory
5. **Configuration:** llama.cpp server starts with loaded models

---

## GGUF Sources

All GGUF models come from **ggml-org** (official llama.cpp quantizations):
- https://huggingface.co/collections/ggml-org/multimodal-ggufs

Alternative sources (community GGUF):
- unsloth/ — often faster quantizations
- lmstudio-community/ — well-tested quantizations
- bartowski/ — specialized quantizations

---

## License Notes

All recommended models have permissive licenses:
- **Apache 2.0:** SmolVLM, Moondream2, nomic-embed-text, BGE-M3
- **MIT:** CLIP ViT-L-14
- **Qwen License:** Qwen2.5-VL (allows commercial use)
