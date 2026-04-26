"""FotoDerp — llama.cpp Server Manager

Startet, stoppt und überwacht einen eingebauten llama.cpp Server.
Unterstützt CPU und GPU (CUDA/Metal).

Verwendung:
    manager = LlamaServerManager(model_path="/path/to/model.gguf")
    await manager.start()
    endpoint = manager.endpoint  # "http://127.0.0.1:8080/v1"
    await manager.stop()
"""

import asyncio
import os
import platform
import shutil
import subprocess
import tempfile
import hashlib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

import httpx


class GpuLayer(Enum):
    """GPU-Offload-Modi für llama.cpp"""
    NONE = "none"          # CPU only
    AUTO = "auto"          # Auto-detect optimal
    MAX = "max"            # Full GPU offload
    LAYERS = "layers"      # Custom layer count


@dataclass
class ServerConfig:
    """Konfiguration für den llama.cpp Server"""
    model_path: str = ""
    host: str = "127.0.0.1"
    port: int = 8080
    gpu_layers: int = -1          # -1 = all layers, 0 = CPU only
    n_ctx: int = 4096             # Kontext-Fenster
    n_batch: int = 512            # Batch-Größe
    n_threads: int = 0            # 0 = auto (CPU cores)
    n_threads_batch: int = 0      # 0 = auto
    flash_attn: bool = True       # Flash Attention aktivieren
    mmap: bool = True             # Memory-mapped I/O
    embedding: bool = True        # Embedding-Modus aktivieren
    log_level: str = "warn"       # debug, info, warn, error
    rope_freq_scale: float = 0.0  # RoPE frequency scaling (0 = auto)
    tensor_split: Optional[str] = None  # GPU-Split für Multi-GPU
    prompt_template: Optional[str] = None  # Custom Prompt-Template


class LlamaServerManager:
    """Manager für den eingebauten llama.cpp Server-Prozess"""

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self._process: Optional[subprocess.Popen] = None
        self._startup_task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        self._server_ready: asyncio.Event = asyncio.Event()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def endpoint(self) -> str:
        return f"http://{self.config.host}:{self.config.port}/v1"

    @property
    def health_url(self) -> str:
        return f"http://{self.config.host}:{self.config.port}/health"

    async def start(self, timeout: int = 60) -> bool:
        """llama.cpp Server starten und auf readiness warten"""
        if self._is_running:
            return True

        if not os.path.exists(self.config.model_path):
            raise FileNotFoundError(f"Model not found: {self.config.model_path}")

        llama_cpp_bin = self._locate_llama_cpp_server()
        if not llama_cpp_bin:
            raise RuntimeError(
                "llama.cpp server binary not found. "
                "Install via: git clone https://github.com/ggml-org/llama.cpp "
                "and build with CUDA=1 or METAL=1"
            )

        cmd = self._build_command(llama_cpp_bin)
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._build_env(),
        )

        # Warte auf Server-Start
        try:
            await asyncio.wait_for(self._wait_for_ready(timeout), timeout=timeout)
            self._is_running = True
            self._client = httpx.AsyncClient(base_url=self.endpoint, timeout=120)
            return True
        except (asyncio.TimeoutError, httpx.ConnectError):
            await self.stop()
            raise RuntimeError(
                f"llama.cpp server failed to start on port {self.config.port}"
            )

    async def stop(self) -> None:
        """Server-Prozess beenden"""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(self._process.wait), timeout=10
                )
            except asyncio.TimeoutError:
                self._process.kill()

        if self._client:
            await self._client.aclose()
            self._client = None

        self._is_running = False
        self._server_ready.clear()

    async def health_check(self) -> dict:
        """Server-Health prüfen"""
        if not self._client:
            return {"status": "stopped"}

        try:
            resp = await self._client.get("/health")
            return resp.json()
        except Exception:
            return {"status": "error", "detail": "connection failed"}

    async def chat_completion(self, messages: list, **kwargs) -> dict:
        """Chat-Completion über den eingebauten Server aufrufen"""
        if not self._client:
            raise RuntimeError("Server not running")

        return await self._client.post(
            "/chat/completions",
            json={"model": "", "messages": messages, **kwargs},
        ).json()

    async def embeddings(self, input: str | list, **kwargs) -> dict:
        """Embeddings über den eingebauten Server generieren"""
        if not self._client:
            raise RuntimeError("Server not running")

        return await self._client.post(
            "/embeddings",
            json={"model": "", "input": input, **kwargs},
        ).json()

    def _locate_llama_cpp_server(self) -> Optional[str]:
        """llama.cpp server binary finden"""
        # 1. Suche im PATH
        bin_name = "llama-server"
        if platform.system() == "Windows":
            bin_name += ".exe"

        found = shutil.which(bin_name)
        if found:
            return found

        # 2. Suche im Projekt-Verzeichnis (llama.cpp fork)
        project_root = Path(__file__).parents[3]  # FotoDerp root
        build_dirs = [
            "llama.cpp/build/bin",
            "llama.cpp/build/release/bin",
            "llama.cpp/out/release/bin",
        ]

        for build_dir in build_dirs:
            candidate = project_root / build_dir / bin_name
            if candidate.exists():
                return str(candidate)

        # 3. Suche im HOME-Verzeichnis (typischer llama.cpp Pfad)
        home_llama = Path.home() / "llama.cpp"
        for build_dir in ["build/bin", "build/release/bin"]:
            candidate = home_llama / build_dir / bin_name
            if candidate.exists():
                return str(candidate)

        return None

    def _build_command(self, binary: str) -> list[str]:
        """Befehlszeile für llama-server zusammenstellen"""
        cmd = [
            binary,
            "--model", self.config.model_path,
            "--host", self.config.host,
            "--port", str(self.config.port),
            "--log-level", self.config.log_level,
            "--ctx-size", str(self.config.n_ctx),
            "--batch-size", str(self.config.n_batch),
            "--embedding",
        ]

        # CPU/GPU Threads
        n_threads = self.config.n_threads or os.cpu_count() or 4
        cmd.extend(["--threads", str(n_threads)])
        threads_batch = self.config.n_threads_batch or n_threads
        cmd.extend(["--threads-batch", str(threads_batch)])

        # GPU Offload
        if self.config.gpu_layers > 0:
            cmd.extend(["--gpu-layers", str(self.config.gpu_layers)])
        elif self.config.gpu_layers == -1:
            cmd.extend(["--gpu-layers", "999"])  # All layers to GPU

        # Optional: Flash Attention
        if self.config.flash_attn:
            cmd.append("--flash-attn")

        # Memory mapping
        if not self.config.mmap:
            cmd.append("--no-mmap")

        # RoPE frequency scaling
        if self.config.rope_freq_scale > 0:
            cmd.extend(["--rope-freq-scale", str(self.config.rope_freq_scale)])

        # Tensor split (Multi-GPU)
        if self.config.tensor_split:
            cmd.extend(["--tensor-split", self.config.tensor_split])

        # Prompt Template
        if self.config.prompt_template:
            cmd.extend(["--prompt-template", self.config.prompt_template])

        return cmd

    def _build_env(self) -> dict:
        """Environment-Variablen für den Server-Prozess"""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parents[2])

        # GPU-spezifische Env-Vars
        gpu_layers = self.config.gpu_layers
        if gpu_layers and gpu_layers > 0:
            env["CUDA_VISIBLE_DEVICES"] = env.get("CUDA_VISIBLE_DEVICES", "0")

        return env

    async def _wait_for_ready(self, timeout: int) -> None:
        """Warte bis der Server bereit ist"""
        import time
        start = time.monotonic()

        while time.monotonic() - start < timeout:
            try:
                async with httpx.AsyncClient(timeout=2) as client:
                    resp = await client.get(self.health_url)
                    if resp.status_code == 200:
                        self._server_ready.set()
                        return
            except Exception:
                pass
            await asyncio.sleep(0.5)

        raise asyncio.TimeoutError("Server did not become ready in time")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *exc):
        await self.stop()


# --- Model Downloader ---

class ModelDownloader:
    """Lädt Modelle von Hugging Face oder lokalen Quellen"""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else (
            Path.home() / ".cache" / "fotoderp" / "models"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download(
        self,
        repo_id: str,
        filename: str,
        quantization: str = "q4_k_m",
    ) -> Path:
        """Modell von Hugging Face herunterladen"""
        target = self.cache_dir / repo_id.replace("/", "--") / filename
        if target.exists():
            return target

        target.parent.mkdir(parents=True, exist_ok=True)

        import httpx
        url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
        print(f"Downloading {url} -> {target}")

        with httpx.stream("GET", url, follow_redirects=True) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(target, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        print(f"\r  {pct:.0f}% ({downloaded}/{total} bytes)", end="")

        print(f"\nDownloaded: {target}")
        return target

    def find_local_models(self, search_dirs: Optional[list[str]] = None) -> list[dict]:
        """Finde GGUF-Modelle in gegebenen Verzeichnissen"""
        dirs = search_dirs or [
            str(Path.home() / "LLMs"),
            str(Path.home() / ".cache" / "fotoderp" / "models"),
        ]

        models = []
        for d in dirs:
            path = Path(d)
            if not path.exists():
                continue
            for gguf in path.rglob("*.gguf"):
                size_mb = gguf.stat().st_size / (1024 * 1024)
                models.append({
                    "path": str(gguf),
                    "filename": gguf.name,
                    "size_mb": round(size_mb, 1),
                    "directory": str(gguf.parent),
                })

        return models
