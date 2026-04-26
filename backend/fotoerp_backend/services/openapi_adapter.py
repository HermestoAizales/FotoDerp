"""FotoDerp — OpenAPI Adapter

Universeller Adapter für OpenAI-kompatible Endpunkte.
Unterstützt: llama.cpp, Ollama, vLLM, LM Studio, Jan.ai, etc.

Verwendung:
    adapter = OpenAPIAdapter(endpoint="http://127.0.0.1:11434/v1", model="llava")
    result = await adapter.chat(messages)
    embedding = await adapter.embedding(image_path)
"""

import base64
import json
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import httpx


@dataclass
class ModelInfo:
    """Modell-Informationen"""
    id: str
    name: str
    type: str = "vision"       # vision | text | embedding | multimodal
    context_length: int = 4096
    max_image_size: tuple = (1536, 1536)
    supported_tasks: List[str] = field(default_factory=lambda: [
        "chat", "embedding", "image_analysis"
    ])
    quantization: Optional[str] = None
    size_mb: Optional[int] = None


@dataclass
class AdapterConfig:
    """Adapter-Konfiguration"""
    endpoint: str = "http://127.0.0.1:8080/v1"
    model: str = "llava-1.5-7b-q4"
    api_key: Optional[str] = None
    timeout: float = 120.0
    max_retries: int = 3
    temperature: float = 0.1
    max_tokens: int = 1024
    # Prompt für Bildanalyse
    analysis_prompt: str = (
        "Analyze this photo comprehensively. Return valid JSON only, no markdown, "
        "no explanations. Format:\n"
        "{\n"
        '  "tags": [{"name": "...", "category": "...", "confidence": 0.95}],\n'
        '  "faces": [{"person_id": "...", "x": 0.3, "y": 0.2, "width": 0.15, "height": 0.25, "confidence": 0.9}],\n'
        '  "aesthetic_score": 0.75,\n'
        '  "ocr_text": "...",\n'
        '  "scene_description": "..."\n'
        "}\n"
        "Tags should include: objects, scene type, colors, season, lighting, mood."
    )


class OpenAPIAdapter:
    """Universeller OpenAI-kompatibler Adapter"""

    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._models: List[ModelInfo] = []
        self._model_cache: Dict[str, ModelInfo] = {}

    async def ensure_client(self) -> httpx.AsyncClient:
        """HTTP-Client initialisieren"""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint,
                headers=headers,
                timeout=httpx.Timeout(self.config.timeout),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=10),
            )
        return self._client

    async def close(self):
        """Client schließen"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """Chat-Completion aufrufen"""
        client = await self.ensure_client()

        response = await client.post(
            "/chat/completions",
            json={
                "model": model or self.config.model,
                "messages": messages,
                "temperature": temperature if temperature is not None else self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "stream": stream,
            },
        )
        response.raise_for_status()
        return response.json()

    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
    ):
        """Streaming Chat-Completion (Server-Sent Events)"""
        client = await self.ensure_client()

        async with client.stream(
            "POST", "/chat/completions",
            json={
                "model": model or self.config.model,
                "messages": messages,
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

    async def image_analysis(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Bild mit einem Vision-Modell analysieren"""
        image_b64 = self._encode_image(image_path)
        p = prompt or self.config.analysis_prompt

        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": p},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                },
            ],
        }]

        result = await self.chat(messages, model=model)
        content = result["choices"][0]["message"]["content"]
        return self._parse_analysis_response(content)

    async def embedding(self, text: str | List[str], model: Optional[str] = None) -> Dict[str, Any]:
        """Embeddings generieren"""
        client = await self.ensure_client()

        response = await client.post(
            "/embeddings",
            json={
                "model": model or self.config.model,
                "input": text,
            },
        )
        response.raise_for_status()
        return response.json()

    async def detect_models(self) -> List[ModelInfo]:
        """Verfügbare Modelle detektieren"""
        client = await self.ensure_client()

        try:
            resp = await client.get("/models")
            if resp.status_code == 200:
                data = resp.json()
                models_data = data.get("data", [])

                self._models = []
                for m in models_data:
                    model_id = m.get("id", "")
                    info = ModelInfo(
                        id=model_id,
                        name=self._infer_model_name(model_id),
                        type=self._classify_model_type(model_id),
                        context_length=self._detect_context_length(model_id),
                    )
                    self._models.append(info)
                    self._model_cache[model_id] = info

                return self._models
        except Exception:
            pass

        # Fallback: Standard-Modelle
        return [
            ModelInfo(
                id=self.config.model,
                name=self._infer_model_name(self.config.model),
                type="vision",
            )
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Adapter-Health prüfen"""
        try:
            client = await self.ensure_client()
            resp = await client.get("/health", timeout=5)
            return {
                "status": "ok" if resp.status_code == 200 else "error",
                "endpoint": self.config.endpoint,
                "model": self.config.model,
            }
        except Exception as e:
            return {
                "status": "error",
                "endpoint": self.config.endpoint,
                "model": self.config.model,
                "detail": str(e),
            }

    @staticmethod
    def _encode_image(path: str) -> str:
        """Bild als Base64 kodieren"""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    @staticmethod
    def _parse_analysis_response(content: str) -> Dict[str, Any]:
        """Antwort-Text in Analyse-JSON parsen"""
        # Versuche JSON zu extrahieren
        content = content.strip()

        # Entferne markdown code blocks
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: Finde erstes JSON-Objekt
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    data = {"raw_response": content, "tags": [], "faces": []}
            else:
                data = {"raw_response": content, "tags": [], "faces": []}

        # Normalisiere die Struktur
        tags = data.get("tags", [])
        if tags and isinstance(tags[0], str):
            tags = [{"name": t, "category": "auto", "confidence": 0.9} for t in tags]

        return {
            "tags": tags,
            "faces": data.get("faces", []),
            "aesthetic_score": data.get("aesthetic_score"),
            "ocr_text": data.get("ocr_text"),
            "scene_description": data.get("scene_description", ""),
            "raw_response": content[:500],
        }

    @staticmethod
    def _infer_model_name(model_id: str) -> str:
        """Modell-ID in lesbaren Namen umwandeln"""
        name = model_id.replace("-", " ").replace("_", " ")
        # Entferne Quantisierungssuffixe
        name = re.sub(r"-q[0-9]_[a-z]", "", name)
        name = re.sub(r"-[qQ][0-9]", "", name)
        return name.strip().title()

    @staticmethod
    def _classify_model_type(model_id: str) -> str:
        """Modell-Typ klassifizieren"""
        mid = model_id.lower()
        if any(k in mid for k in ["llava", "moondream", "bakllava", "llama-3.2-vision", "qwen2-vl"]):
            return "vision"
        elif any(k in mid for k in ["embed", "text-embedding", "nomic"]):
            return "embedding"
        elif any(k in mid for k in ["llava", "moondream", "qwen2-vl"]):
            return "multimodal"
        return "text"

    @staticmethod
    def _detect_context_length(model_id: str) -> int:
        """Kontext-Länge aus Modell-ID erkennen"""
        import re
        match = re.search(r"(4k|8k|16k|32k|128k|\b(4096|8192|16384|32768|131072)\b)", model_id, re.IGNORECASE)
        if match:
            text = match.group(1).lower()
            multipliers = {"4k": 4096, "8k": 8192, "16k": 16384, "32k": 32768, "128k": 131072}
            if text in multipliers:
                return multipliers[text]
            return int(text)
        return 4096


# --- Factory: Adapter aus Config erstellen ---

def create_adapter_from_config(config_dict: dict) -> OpenAPIAdapter:
    """Erstelle einen Adapter aus einem Konfigurations-Dict"""
    cfg = AdapterConfig(**{k: v for k, v in config_dict.items() if hasattr(AdapterConfig(), k)})
    return OpenAPIAdapter(cfg)
