"""Model registry per PROJECT_GUIDE.md Section 7.

Stores per-capability model configuration for:
  - vision   : multimodal OCR / scanned document understanding
  - reasoning: SOP grounding, findings synthesis, knowledge Q&A
  - coding   : deterministic code generation & sandboxed calculation

All models must be served by the LOCAL Ollama runtime (http://localhost:11434).
No cloud or remote inference endpoints are permitted.

Final production model names are NOT hardcoded here — they are controlled
entirely through environment variables so hardware/VRAM-appropriate models
can be selected without touching application code.

Configurable via .env:
    OLLAMA_URL              - Ollama generate endpoint (default: http://localhost:11434/api/generate)
    OLLAMA_VISION_MODEL     - Multimodal model for scanned PDFs / images
    OLLAMA_REASONING_MODEL  - Text reasoning / instruction-following model
    OLLAMA_CODING_MODEL     - Code-generation model
    OLLAMA_MODEL            - Generic fallback (used only if a capability var is unset)
"""

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("sovereign.registry")


# ---------------------------------------------------------------------------
# Documented default models (development/prototype only).
# Override all three via environment variables before running in production.
# ---------------------------------------------------------------------------
_DEFAULT_FALLBACK = "qwen2.5vl:3b"          # last-resort generic fallback
_DEFAULT_VISION = "qwen2.5vl:3b"            # multimodal; supports images
_DEFAULT_REASONING = "qwen2.5:7b"           # instruction-following, text-only
_DEFAULT_CODING = "qwen2.5-coder:7b"        # code-specialist


class ModelRegistry:
    """
    Central registry that maps capability names to local model configurations.

    Capability keys: "vision", "reasoning", "coding"

    Usage:
        cfg = registry.get_model_for_capability("vision")
        response = local_client.generate(prompt=..., model=cfg["model"],
                                         endpoint=cfg["endpoint"])
    """

    def __init__(self) -> None:
        ollama_endpoint: str = os.getenv(
            "OLLAMA_URL", "http://localhost:11434/api/generate"
        )
        # Generic fallback — used only when a capability-specific var is absent.
        base_model: str = os.getenv("OLLAMA_MODEL", _DEFAULT_FALLBACK)

        self.models: Dict[str, Dict[str, Any]] = {
            # ------------------------------------------------------------------
            # VISION — multimodal OCR for scanned PDFs, photos, drawings
            # Must support Ollama's "images" payload field.
            # ------------------------------------------------------------------
            "vision": {
                "model": os.getenv("OLLAMA_VISION_MODEL", _DEFAULT_VISION),
                "endpoint": ollama_endpoint,
                "runtime": "ollama",
                "capability": "multimodal_ocr_vision",
                "description": (
                    "Local open-weight multimodal model for scanned PDFs, "
                    "visual telemetry and engineering diagrams."
                ),
                "supports_vision": True,
                "supports_code": False,
                "supports_reasoning": False,
                "context_window": 4096,
                "hardware_note": (
                    "Requires a multimodal-capable model (e.g. qwen2.5vl). "
                    "Min ~4 GB VRAM for 3b variant."
                ),
                "fallback_priority": 1,
            },
            # ------------------------------------------------------------------
            # REASONING — SOP compliance, findings synthesis, Q&A grounding
            # Text-only; does NOT need image input capability.
            # ------------------------------------------------------------------
            "reasoning": {
                "model": os.getenv("OLLAMA_REASONING_MODEL", _DEFAULT_REASONING),
                "endpoint": ollama_endpoint,
                "runtime": "ollama",
                "capability": "industrial_reasoning_sops",
                "description": (
                    "Local open-weight reasoning model for SOP compliance, "
                    "findings synthesis and grounded knowledge Q&A."
                ),
                "supports_vision": False,
                "supports_code": False,
                "supports_reasoning": True,
                "context_window": 8192,
                "hardware_note": (
                    "Text-only model. 7b variant recommended for quality; "
                    "3b variant usable on low-VRAM hardware (~4 GB)."
                ),
                "fallback_priority": 2,
            },
            # ------------------------------------------------------------------
            # CODING — deterministic Python scripts & sandboxed calculations
            # Code-specialist model preferred.
            # ------------------------------------------------------------------
            "coding": {
                "model": os.getenv("OLLAMA_CODING_MODEL", _DEFAULT_CODING),
                "endpoint": ollama_endpoint,
                "runtime": "ollama",
                "capability": "sandboxed_code_generation",
                "description": (
                    "Local open-weight code-specialist model for deterministic "
                    "Python scripts and telemetry calculation."
                ),
                "supports_vision": False,
                "supports_code": True,
                "supports_reasoning": False,
                "context_window": 8192,
                "hardware_note": (
                    "Code-specialist model preferred (e.g. qwen2.5-coder). "
                    "3b variant usable on low-VRAM hardware (~4 GB)."
                ),
                "fallback_priority": 3,
            },
        }

        self._log_differentiation_status()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get_model_for_capability(self, capability: str) -> Dict[str, Any]:
        """
        Return the full model configuration dict for the requested capability.

        Falls back to 'reasoning' if an unknown capability is requested so
        callers always receive a usable config rather than crashing.
        """
        config = self.models.get(capability)
        if config is None:
            logger.warning(
                "Unknown capability '%s' requested; falling back to 'reasoning'.",
                capability,
            )
            config = self.models["reasoning"]
        return config

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Return all capability configs (used by /health endpoint)."""
        return dict(self.models)

    def list_models(self) -> Dict[str, Any]:
        """Return all capability configs. Alias kept for backward compatibility."""
        return self.models

    def are_models_differentiated(self) -> bool:
        """
        Return True when at least two capability roles use different model names.
        Returns False when all three resolve to the same model (the P0 problem).
        """
        model_names = {cfg["model"] for cfg in self.models.values()}
        return len(model_names) > 1

    def get_capability_names(self) -> List[str]:
        """Return the list of registered capability keys."""
        return list(self.models.keys())

    def summary(self) -> Dict[str, str]:
        """Return a compact {capability: model_name} mapping for logging."""
        return {cap: cfg["model"] for cap, cfg in self.models.items()}

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _log_differentiation_status(self) -> None:
        """
        Log the resolved model configuration at startup so the team can
        immediately see whether true model separation is active.
        """
        s = self.summary()
        logger.info(
            "Model registry loaded — vision=%s | reasoning=%s | coding=%s",
            s.get("vision"),
            s.get("reasoning"),
            s.get("coding"),
        )
        if not self.are_models_differentiated():
            logger.warning(
                "P0 WARNING: All three capability roles resolve to the same model "
                "('%s'). True multi-model separation requires distinct models. "
                "Set OLLAMA_VISION_MODEL, OLLAMA_REASONING_MODEL, and "
                "OLLAMA_CODING_MODEL in your .env file.",
                s.get("vision"),
            )


# Module-level singleton — import this throughout the codebase.
registry = ModelRegistry()
