"""Local model client — communicates exclusively with the local Ollama runtime.

IMPORTANT DESIGN CONSTRAINT:
    This client ONLY targets http://localhost:11434 (or whatever OLLAMA_URL is
    set to in the environment).  It has NO cloud fallback, NO external API
    integration, and NO silent rerouting to remote services.

    If the local Ollama server is unavailable, this client raises RuntimeError
    with a clear diagnostic message rather than silently failing or calling an
    external API.

Runtime compatibility:
    Ollama (/api/generate endpoint — non-streaming).

    vLLM is NOT currently implemented.  If vLLM support is added in the future,
    it must target a local vLLM endpoint only (e.g. http://localhost:8000/v1).
    A docstring reference to vLLM was previously present in this file; it has
    been removed to avoid misleading documentation.

Usage pattern (per P0.5 model-selection contract):
    # Always resolve the model from the registry; never use a hardcoded name.
    model_cfg = registry.get_model_for_capability("vision")
    result = local_client.generate(
        prompt=my_prompt,
        model=model_cfg["model"],        # explicit — not a default
        endpoint=model_cfg["endpoint"],  # explicit — not a default
        images=[base64_image],           # only for vision capability
    )
"""

import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("sovereign.local_client")


class LocalModelClient:
    """
    Thin HTTP client for the local Ollama /api/generate endpoint.

    Parameters
    ----------
    default_url : str
        The Ollama generate endpoint to use when no ``endpoint`` is passed to
        :meth:`generate`.  Should always be a localhost URL.
    """

    def __init__(self, default_url: str = "http://localhost:11434/api/generate") -> None:
        self.default_url = default_url

    def generate(
        self,
        prompt: str,
        *,
        model: str,                          # now REQUIRED — no hardcoded default
        endpoint: Optional[str] = None,
        images: Optional[List[str]] = None,  # base64-encoded strings for vision
        temperature: float = 0.2,
        json_format: bool = False,
        timeout: int = 180,
    ) -> str:
        """
        Send a prompt to the local Ollama inference server.

        Parameters
        ----------
        prompt : str
            The text prompt to send.
        model : str
            Model identifier as registered in Ollama (e.g. ``"qwen2.5vl:3b"``).
            Always obtain this from :func:`registry.get_model_for_capability`
            rather than hardcoding a model name.
        endpoint : str, optional
            Override the Ollama endpoint URL.  Defaults to ``self.default_url``.
            Must be a localhost URL — never a remote API.
        images : list of str, optional
            Base64-encoded image strings.  Only pass for vision-capable models.
            Non-vision models will likely ignore or error on this field.
        temperature : float
            Sampling temperature (default 0.2 for industrial factual tasks).
        json_format : bool
            When True, instructs Ollama to return a JSON-parseable response.
        timeout : int
            Request timeout in seconds.  Default 180 s for large model inference.

        Returns
        -------
        str
            The model's text response, stripped of leading/trailing whitespace.

        Raises
        ------
        RuntimeError
            If the local Ollama server is unreachable or returns an error.
            The error message includes the endpoint URL and the underlying
            exception to aid diagnosis.  No cloud fallback is attempted.
        """
        url = endpoint or self.default_url
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
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
            logger.error(
                "Local Ollama inference failed | endpoint=%s model=%s error=%s",
                url,
                model,
                error,
            )
            raise RuntimeError(
                f"Local AI runtime error at {url} (model={model}): {error}. "
                "Ensure Ollama is running and the model is installed locally."
            ) from error


# Module-level singleton.
# All application code should import and use this instance so that the
# default_url configuration is consistent.
local_client = LocalModelClient()
