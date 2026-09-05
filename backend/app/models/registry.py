"""Model registry and configuration per Section 12."""

import os
from typing import Dict, Any


class ModelRegistry:
    def __init__(self):
        ollama_endpoint = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        base_model = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")

        self.models: Dict[str, Dict[str, Any]] = {
            "vision": {
                "endpoint": ollama_endpoint,
                "model": os.getenv("OLLAMA_VISION_MODEL", base_model),
                "capability": "multimodal_ocr_vision",
                "description": "Local Open-Weight Multimodal Model for scanned PDFs, visual telemetry & diagrams",
            },
            "reasoning": {
                "endpoint": ollama_endpoint,
                "model": os.getenv("OLLAMA_REASONING_MODEL", base_model),
                "capability": "industrial_reasoning_sops",
                "description": "Local Open-Weight Reasoning Model for SOP compliance and findings synthesis",
            },
            "coding": {
                "endpoint": ollama_endpoint,
                "model": os.getenv("OLLAMA_CODING_MODEL", base_model),
                "capability": "sandboxed_code_generation",
                "description": "Local Open-Weight Code Model for deterministic scripts & telemetry calculation",
            },
        }

    def get_model_for_capability(self, capability: str) -> Dict[str, Any]:
        return self.models.get(capability, self.models["reasoning"])

    def list_models(self) -> Dict[str, Any]:
        return self.models


registry = ModelRegistry()
