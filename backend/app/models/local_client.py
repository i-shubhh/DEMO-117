"""Local model client for communicating exclusively with local inference runtimes (Ollama/vLLM)."""

import json
import logging
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("sovereign.local_client")


class LocalModelClient:
    def __init__(self, default_url: str = "http://localhost:11434/api/generate"):
        self.default_url = default_url

    def generate(
        self,
        prompt: str,
        model: str = "qwen2.5vl:3b",
        endpoint: Optional[str] = None,
        images: Optional[List[str]] = None,
        temperature: float = 0.2,
        json_format: bool = False,
        timeout: int = 180,
    ) -> str:
        url = endpoint or self.default_url
        options = {"temperature": temperature}
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if images:
            payload["images"] = images
        if json_format:
            payload["format"] = "json"

        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.RequestException as error:
            logger.error(f"Local inference call failed on {url}: {error}")
            raise RuntimeError(f"Local AI runtime error at {url}: {error}") from error


local_client = LocalModelClient()
