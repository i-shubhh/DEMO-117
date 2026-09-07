"""Task Router — routes incoming tasks to local model capabilities.

Per PROJECT_GUIDE.md Sections 7, 8, and 37:
  - Routing must be REAL backend behaviour, not a UI label.
  - The router must produce structured metadata that the agent graph consumes.
  - Multiple capability stages are supported for compound industrial tasks.

Return contract (P0.5)
----------------------
router.route() returns a 3-tuple:

    (primary_task_type, primary_model_name, metadata_dict)

``metadata_dict`` now includes a ``required_capabilities`` key — an ordered
list of capability names reflecting the full pipeline this task should traverse.

Examples
--------
"Summarize this inspection PDF and calculate the vibration deviation."
    required_capabilities = ["vision", "reasoning", "coding"]

"Summarize this scanned inspection report."
    required_capabilities = ["vision", "reasoning"]

"What does SOP section 4 require?"
    required_capabilities = ["reasoning"]

"Write a Python script to calculate pump degradation."
    required_capabilities = ["coding"]

Routing is DETERMINISTIC — it uses scored keyword/file-type patterns, not an
external AI classifier.  This keeps the router fully offline and auditable.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.models.registry import registry

logger = logging.getLogger("sovereign.router")


class TaskRouter:
    """
    Routes tasks to one or more local model capabilities based on:
      1. Explicit mode selected by the user (overrides auto-detection).
      2. Attached file types (PDF / image → likely vision stage required).
      3. Scored keyword patterns for vision, reasoning, and coding signals.

    The router does NOT execute inference.  It produces a routing plan that
    the AgentWorkflowEngine (graph.py) consumes to select the right model at
    each pipeline stage.
    """

    def __init__(self) -> None:
        # ---------------------------------------------------------------
        # Keyword pattern sets — each produces a 0/1 score per pattern.
        # Designed to be additive: higher score = stronger signal.
        # ---------------------------------------------------------------

        # Signals that the task involves code generation or deterministic
        # calculation that must run in the sandbox.
        self._coding_patterns: List[str] = [
            r"\b(write|generate|create)\s+(a\s+)?(python|script|code|function|program)\b",
            r"\b(calculate|compute|compute the|run the)\b",
            r"\b(sandbox|execute|algorithm|benchmark|numpy|pandas|matplotlib)\b",
            r"\b(vibration analysis|outlier detection|formula|tolerance limit test|telemetry calc)\b",
            r"\b(deviation|degradation index|rms|fft|regression)\b",
        ]

        # Signals that the task requires visual / multimodal understanding.
        self._visual_patterns: List[str] = [
            r"\b(scanned|scan|image|photo|photograph|diagram|drawing|gauge|visual|ocr)\b",
            r"\b(pdf report|inspection report|inspection image|report page|page from)\b",
            r"\b(handwritten|stamp|signoff|signature|printed form)\b",
            r"\b(p&id|piping and instrumentation|engineering drawing|blueprint)\b",
            r"\b(extract text|read the (image|page|form|document))\b",
        ]

        # Signals for knowledge/SOP/reasoning tasks (text-in, text-out).
        self._reasoning_patterns: List[str] = [
            r"\b(sop|standard operating procedure|section\s+\d+|iso\s+\d+)\b",
            r"\b(compliance|approve|authoriz|safety requirement|protocol|policy)\b",
            r"\b(what does|what is the|explain|summarize|describe|analyze findings)\b",
            r"\b(recommendation|risk assessment|inspection finding|maintenance note)\b",
            r"\b(causes?|symptom|diagnos|troubleshoot|root cause)\b",
        ]

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def route(
        self,
        task_prompt: str,
        files: List[Dict[str, Any]],
        requested_mode: str = "auto",
    ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Determine the routing plan for a task.

        Parameters
        ----------
        task_prompt : str
            The user's natural-language request.
        files : list of dict
            Attached file descriptors with keys ``filename`` and ``mime_type``.
        requested_mode : str
            Explicit mode override from the frontend.
            Accepted values: "auto" | "coding_agent" | "knowledge_assistant" |
            "document_agent".

        Returns
        -------
        tuple
            (primary_task_type, primary_model_name, metadata)

            ``metadata`` contains:
              - ``capability``             : primary capability string
              - ``required_capabilities``  : ordered list, e.g. ["vision","reasoning"]
              - ``reason``                 : human-readable routing rationale
              - ``endpoint``               : primary model's Ollama endpoint
              - ``model_configs``          : full config dict per capability
        """
        # ------------------------------------------------------------------
        # 1. Explicit mode overrides — user knows what they want.
        # ------------------------------------------------------------------
        if requested_mode == "coding_agent":
            return self._build_result(
                primary_capability="coding",
                required_capabilities=["coding"],
                reason="User selected Coding Agent mode explicitly.",
            )

        if requested_mode == "knowledge_assistant":
            return self._build_result(
                primary_capability="reasoning",
                required_capabilities=["reasoning"],
                reason="User selected Knowledge Assistant mode explicitly.",
            )

        if requested_mode == "document_agent":
            # Document agent always does vision first, then reasoning for synthesis.
            return self._build_result(
                primary_capability="vision",
                required_capabilities=["vision", "reasoning"],
                reason="User selected Document Agent mode explicitly.",
            )

        # ------------------------------------------------------------------
        # 2. Auto-detect from file types and prompt signals.
        # ------------------------------------------------------------------
        prompt_lower = task_prompt.lower()

        has_visual_files = self._has_visual_attachments(files)
        has_pdf_files = self._has_pdf_attachments(files)

        coding_score = self._score(prompt_lower, self._coding_patterns)
        visual_score = self._score(prompt_lower, self._visual_patterns)
        reasoning_score = self._score(prompt_lower, self._reasoning_patterns)

        logger.debug(
            "Router scores — visual=%d reasoning=%d coding=%d | "
            "has_visual_files=%s has_pdf_files=%s",
            visual_score, reasoning_score, coding_score,
            has_visual_files, has_pdf_files,
        )

        # ------------------------------------------------------------------
        # 3. Build required_capabilities list — ORDER MATTERS (pipeline seq).
        # ------------------------------------------------------------------
        required: List[str] = []

        # Vision is required when: visual files attached OR strong visual keywords.
        needs_vision = has_visual_files or has_pdf_files or visual_score >= 1

        # Reasoning is required when: knowledge/SOP keywords OR after vision
        # extraction (findings need interpretation).
        needs_reasoning = reasoning_score >= 1 or (needs_vision and reasoning_score >= 0)

        # Coding is required when: calculation/script keywords present.
        needs_coding = coding_score >= 1

        if needs_vision:
            required.append("vision")
        # Reasoning almost always follows vision in industrial workflows.
        # Only skip reasoning if it is a pure visual extraction (no analysis keywords).
        if needs_reasoning or (needs_vision and (reasoning_score > 0 or len(task_prompt) > 40)):
            if "reasoning" not in required:
                required.append("reasoning")
        if needs_coding:
            required.append("coding")

        # Pure reasoning — no files, no visual signals, no coding signals.
        if not required:
            required = ["reasoning"]

        # If only reasoning (no vision, no coding), ensure that's the result.
        primary_capability = required[0]

        # Build human-readable reason.
        reason_parts = []
        if has_visual_files or has_pdf_files:
            reason_parts.append(
                f"Visual/PDF file(s) attached ({len(files)} file(s))"
            )
        if visual_score:
            reason_parts.append(f"visual keyword signals (score={visual_score})")
        if reasoning_score:
            reason_parts.append(f"reasoning/SOP keyword signals (score={reasoning_score})")
        if coding_score:
            reason_parts.append(f"code/calculation keyword signals (score={coding_score})")
        if not reason_parts:
            reason_parts.append("no specific signals — defaulting to knowledge reasoning")

        reason = (
            f"Pipeline stages: {' → '.join(required).upper()}. "
            f"Detected: {'; '.join(reason_parts)}."
        )

        return self._build_result(
            primary_capability=primary_capability,
            required_capabilities=required,
            reason=reason,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _build_result(
        self,
        primary_capability: str,
        required_capabilities: List[str],
        reason: str,
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Assemble the return tuple with full model configs for all capabilities."""
        primary_cfg = registry.get_model_for_capability(primary_capability)

        # Resolve configs for every required capability so the graph can use
        # them directly without additional registry lookups.
        model_configs: Dict[str, Dict[str, Any]] = {}
        for cap in required_capabilities:
            model_configs[cap] = registry.get_model_for_capability(cap)

        # Map primary capability to the legacy task_type strings that graph.py
        # already branches on (backward compatibility).
        _capability_to_task_type = {
            "vision": "visual_document",
            "reasoning": "knowledge_reasoning",
            "coding": "coding",
        }
        task_type = _capability_to_task_type.get(primary_capability, "knowledge_reasoning")

        metadata: Dict[str, Any] = {
            "capability": primary_cfg["capability"],
            "required_capabilities": required_capabilities,
            "reason": reason,
            "endpoint": primary_cfg["endpoint"],
            "model_configs": model_configs,
        }

        logger.info(
            "Router decision — task_type=%s model=%s pipeline=%s",
            task_type,
            primary_cfg["model"],
            required_capabilities,
        )

        return task_type, primary_cfg["model"], metadata

    @staticmethod
    def _score(text: str, patterns: List[str]) -> int:
        """Return count of patterns that match in text."""
        return sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))

    @staticmethod
    def _has_visual_attachments(files: List[Dict[str, Any]]) -> bool:
        """True when any attached file is an image (non-PDF visual)."""
        return any(
            f.get("filename", "").lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"))
            or f.get("mime_type", "").startswith("image/")
            for f in files
        )

    @staticmethod
    def _has_pdf_attachments(files: List[Dict[str, Any]]) -> bool:
        """True when any attached file is a PDF."""
        return any(
            f.get("filename", "").lower().endswith(".pdf")
            or f.get("mime_type", "") == "application/pdf"
            for f in files
        )


# Module-level singleton.
router = TaskRouter()
