"""P0 Multi-Model Architecture Tests.

Covers the 10 tests defined in the P0 implementation task.

Tests 1-9 are STATIC (no Ollama runtime required).
Test 10 verifies no cloud endpoints exist in the codebase.

Run:
    cd backend
    python -m pytest tests/test_p0_multimodel.py -v
"""

import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Make sure the backend package is importable from tests/
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


# ===========================================================================
# TEST 1: Registry loads successfully
# ===========================================================================
class TestRegistryLoads:
    def test_registry_import(self):
        """Registry module must import without errors."""
        from app.models.registry import ModelRegistry, registry

        assert registry is not None, "Module-level registry singleton must not be None"
        assert isinstance(registry, ModelRegistry)

    def test_registry_has_all_capabilities(self):
        """Registry must expose vision, reasoning, and coding capabilities."""
        from app.models.registry import registry

        for cap in ("vision", "reasoning", "coding"):
            cfg = registry.get_model_for_capability(cap)
            assert cfg is not None, f"Capability '{cap}' must return a config dict"
            assert "model" in cfg, f"Config for '{cap}' must contain 'model' key"
            assert "endpoint" in cfg, f"Config for '{cap}' must contain 'endpoint' key"

    def test_registry_required_metadata_fields(self):
        """Per PROJECT_GUIDE.md Section 7, registry must store rich metadata."""
        from app.models.registry import registry

        required_keys = {
            "model", "endpoint", "runtime", "capability", "description",
            "supports_vision", "supports_code", "supports_reasoning",
            "context_window", "hardware_note", "fallback_priority",
        }
        for cap in ("vision", "reasoning", "coding"):
            cfg = registry.get_model_for_capability(cap)
            missing = required_keys - set(cfg.keys())
            assert not missing, (
                f"Capability '{cap}' config is missing keys: {missing}"
            )

    def test_registry_all_endpoints_are_local(self):
        """All configured endpoints must point to localhost (sovereignty rule)."""
        from app.models.registry import registry

        for cap, cfg in registry.get_all_configs().items():
            endpoint = cfg["endpoint"]
            assert "localhost" in endpoint or "127.0.0.1" in endpoint, (
                f"Capability '{cap}' has non-local endpoint: {endpoint}. "
                "All inference must stay local (PROJECT_GUIDE.md Section 3)."
            )

    def test_list_models_backward_compat(self):
        """list_models() must still return the same data as get_all_configs()."""
        from app.models.registry import registry

        assert registry.list_models() == registry.get_all_configs()


# ===========================================================================
# TEST 2: Vision capability returns the configured vision model
# ===========================================================================
class TestVisionCapability:
    def test_vision_returns_vision_model(self):
        """get_model_for_capability('vision') must return the vision model."""
        from app.models.registry import registry

        cfg = registry.get_model_for_capability("vision")
        expected = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
        assert cfg["model"] == expected, (
            f"Vision capability returned '{cfg['model']}', expected '{expected}'"
        )

    def test_vision_supports_vision_flag(self):
        """Vision config must have supports_vision=True."""
        from app.models.registry import registry

        cfg = registry.get_model_for_capability("vision")
        assert cfg["supports_vision"] is True


# ===========================================================================
# TEST 3: Reasoning capability returns the configured reasoning model
# ===========================================================================
class TestReasoningCapability:
    def test_reasoning_returns_reasoning_model(self):
        """get_model_for_capability('reasoning') must return the reasoning model."""
        from app.models.registry import registry

        cfg = registry.get_model_for_capability("reasoning")
        expected = os.getenv("OLLAMA_REASONING_MODEL", "qwen2.5:7b")
        assert cfg["model"] == expected, (
            f"Reasoning capability returned '{cfg['model']}', expected '{expected}'"
        )

    def test_reasoning_supports_reasoning_flag(self):
        """Reasoning config must have supports_reasoning=True."""
        from app.models.registry import registry

        cfg = registry.get_model_for_capability("reasoning")
        assert cfg["supports_reasoning"] is True


# ===========================================================================
# TEST 4: Coding capability returns the configured coding model
# ===========================================================================
class TestCodingCapability:
    def test_coding_returns_coding_model(self):
        """get_model_for_capability('coding') must return the coding model."""
        from app.models.registry import registry

        cfg = registry.get_model_for_capability("coding")
        expected = os.getenv("OLLAMA_CODING_MODEL", "qwen2.5-coder:7b")
        assert cfg["model"] == expected, (
            f"Coding capability returned '{cfg['model']}', expected '{expected}'"
        )

    def test_coding_supports_code_flag(self):
        """Coding config must have supports_code=True."""
        from app.models.registry import registry

        cfg = registry.get_model_for_capability("coding")
        assert cfg["supports_code"] is True


# ===========================================================================
# TEST 5: Router sends a pure coding request to coding capability
# ===========================================================================
class TestRouterCodingRoute:
    def test_pure_coding_task(self):
        """A coding-only task (no files, coding keywords) must route to coding."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        task_type, model, metadata = r.route(
            task_prompt="Write a Python script to calculate vibration deviation.",
            files=[],
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        assert "coding" in caps, (
            f"Expected 'coding' in required_capabilities, got: {caps}"
        )
        assert task_type == "coding", f"Expected task_type='coding', got '{task_type}'"

    def test_explicit_coding_agent_override(self):
        """Explicit coding_agent mode must route to coding regardless of prompt."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        task_type, model, metadata = r.route(
            task_prompt="What does SOP section 4 require?",
            files=[],
            requested_mode="coding_agent",
        )
        assert metadata["required_capabilities"] == ["coding"]
        assert task_type == "coding"


# ===========================================================================
# TEST 6: Router sends SOP/knowledge question to reasoning
# ===========================================================================
class TestRouterReasoningRoute:
    def test_sop_question_routes_to_reasoning(self):
        """A SOP/knowledge question with no files must route to reasoning."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        task_type, model, metadata = r.route(
            task_prompt="What does SOP section 4.2 require for pump seal inspection?",
            files=[],
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        assert "reasoning" in caps, (
            f"Expected 'reasoning' in required_capabilities, got: {caps}"
        )
        # Should NOT include vision (no files, no visual keywords)
        assert "vision" not in caps, (
            f"Unexpected 'vision' in caps for text-only SOP question: {caps}"
        )

    def test_explicit_knowledge_assistant_override(self):
        """Explicit knowledge_assistant mode must route to reasoning only."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        task_type, model, metadata = r.route(
            task_prompt="Write Python code.",
            files=[],
            requested_mode="knowledge_assistant",
        )
        assert metadata["required_capabilities"] == ["reasoning"]
        assert task_type == "knowledge_reasoning"


# ===========================================================================
# TEST 7: Router recognizes a visual/scanned document task
# ===========================================================================
class TestRouterVisionRoute:
    def test_image_file_triggers_vision(self):
        """An attached image file must trigger vision in required_capabilities."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        files = [{"filename": "scan_page1.png", "mime_type": "image/png"}]
        _, _, metadata = r.route(
            task_prompt="Extract the readings from this inspection image.",
            files=files,
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        assert "vision" in caps, f"Expected 'vision' for image file, got: {caps}"

    def test_pdf_file_triggers_vision(self):
        """An attached PDF must trigger vision in required_capabilities."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        files = [{"filename": "report.pdf", "mime_type": "application/pdf"}]
        _, _, metadata = r.route(
            task_prompt="Summarize this inspection report.",
            files=files,
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        assert "vision" in caps, f"Expected 'vision' for PDF file, got: {caps}"

    def test_visual_keywords_trigger_vision(self):
        """Strong visual keywords in prompt must trigger vision even without files."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        _, _, metadata = r.route(
            task_prompt="Analyze this scanned inspection page and extract all readings.",
            files=[],
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        assert "vision" in caps, f"Expected 'vision' for scanned keyword, got: {caps}"


# ===========================================================================
# TEST 8: Multi-capability task produces structured routing metadata
# ===========================================================================
class TestMultiCapabilityRouting:
    def test_pdf_plus_calculation_gives_three_stage_pipeline(self):
        """PDF + calculation keywords should produce vision→reasoning→coding pipeline."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        files = [{"filename": "inspection.pdf", "mime_type": "application/pdf"}]
        _, _, metadata = r.route(
            task_prompt=(
                "Analyze this inspection PDF, compare the findings against the SOP, "
                "calculate the vibration deviation, and generate the result."
            ),
            files=files,
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        assert "vision" in caps, f"Missing 'vision' in pipeline: {caps}"
        assert "reasoning" in caps, f"Missing 'reasoning' in pipeline: {caps}"
        assert "coding" in caps, f"Missing 'coding' in pipeline: {caps}"
        # Vision must come first
        assert caps.index("vision") < caps.index("reasoning"), (
            "Vision must precede reasoning in pipeline"
        )
        assert caps.index("reasoning") < caps.index("coding"), (
            "Reasoning must precede coding in pipeline"
        )

    def test_pdf_plus_sop_gives_two_stage_pipeline(self):
        """PDF + SOP question should produce vision→reasoning pipeline (no coding)."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        files = [{"filename": "report.pdf", "mime_type": "application/pdf"}]
        _, _, metadata = r.route(
            task_prompt="Summarize this scanned inspection report and check SOP compliance.",
            files=files,
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        assert "vision" in caps
        assert "reasoning" in caps
        # coding should NOT appear for a pure summarise+compliance task
        assert "coding" not in caps, (
            f"Unexpected 'coding' in pipeline for summarise task: {caps}"
        )

    def test_metadata_contains_model_configs_for_all_required_caps(self):
        """metadata['model_configs'] must contain configs for every required cap."""
        from app.agent.router import TaskRouter

        r = TaskRouter()
        files = [{"filename": "report.pdf", "mime_type": "application/pdf"}]
        _, _, metadata = r.route(
            task_prompt="Analyze this PDF and calculate the tolerance deviation.",
            files=files,
            requested_mode="auto",
        )
        caps = metadata["required_capabilities"]
        model_configs = metadata.get("model_configs", {})
        for cap in caps:
            assert cap in model_configs, (
                f"model_configs missing entry for required capability '{cap}'"
            )
            assert "model" in model_configs[cap]


# ===========================================================================
# TEST 9: LocalModelClient receives the selected model explicitly
# ===========================================================================
class TestLocalClientExplicitModel:
    def test_generate_requires_model_kwarg(self):
        """generate() must accept model as explicit keyword argument."""
        import inspect
        from app.models.local_client import LocalModelClient

        sig = inspect.signature(LocalModelClient.generate)
        assert "model" in sig.parameters, "generate() must have a 'model' parameter"

    def test_generate_no_hardcoded_cloud_url_in_source(self):
        """The client source must not contain any cloud API URL."""
        client_source = Path(BACKEND_DIR / "app/models/local_client.py").read_text()
        forbidden_patterns = [
            r"api\.openai\.com",
            r"generativelanguage\.googleapis\.com",
            r"api\.anthropic\.com",
            r"huggingface\.co/api",
            r"azure\.openai",
        ]
        for pattern in forbidden_patterns:
            assert not re.search(pattern, client_source, re.IGNORECASE), (
                f"Cloud API URL pattern '{pattern}' found in local_client.py! "
                "This violates the sovereignty requirement."
            )

    def test_generate_raises_on_bad_endpoint(self):
        """generate() must raise RuntimeError (not return empty string) on connection failure."""
        from app.models.local_client import LocalModelClient

        client = LocalModelClient(default_url="http://localhost:1")  # nothing on port 1
        with pytest.raises(RuntimeError) as exc_info:
            client.generate(
                prompt="test",
                model="dummy-model",
                endpoint="http://localhost:1/api/generate",
                timeout=2,
            )
        assert "Local AI runtime error" in str(exc_info.value), (
            "RuntimeError message should explain the local inference failure"
        )

    def test_generate_passes_model_to_payload(self):
        """generate() must include the exact model name in the Ollama payload."""
        from app.models.local_client import LocalModelClient
        import requests

        captured_payload = {}

        def fake_post(url, json=None, timeout=None):
            captured_payload.update(json or {})
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {"response": "ok"}
            return mock_resp

        client = LocalModelClient()
        with patch.object(requests, "post", side_effect=fake_post):
            client.generate(
                prompt="hello",
                model="qwen2.5-coder:7b",
            )
        assert captured_payload.get("model") == "qwen2.5-coder:7b", (
            f"Expected model='qwen2.5-coder:7b' in payload, got: {captured_payload.get('model')}"
        )


# ===========================================================================
# TEST 10: No cloud/external LLM endpoint has been introduced
# ===========================================================================
class TestNoCloudEndpoints:
    """Sovereignty compliance: scan source files for forbidden external endpoints."""

    FORBIDDEN_PATTERNS = [
        r"api\.openai\.com",
        r"generativelanguage\.googleapis\.com",
        r"api\.anthropic\.com",
        r"huggingface\.co/api",
        r"azure\.openai",
        r"openai\.azure\.com",
        r"bedrock\.amazonaws\.com",
        r"vertexai\.googleapis\.com",
        r"cohere\.ai",
        r"together\.ai/v1",
        r"replicate\.com/v1",
    ]

    SOURCE_DIRS = ["app", "main.py"]

    def _collect_python_sources(self) -> List[Path]:
        sources = []
        for target in self.SOURCE_DIRS:
            p = BACKEND_DIR / target
            if p.is_file():
                sources.append(p)
            elif p.is_dir():
                sources.extend(p.rglob("*.py"))
        return sources

    def test_no_cloud_ai_urls_in_source(self):
        """No source file must contain a cloud inference API URL."""
        violations = []
        for src_file in self._collect_python_sources():
            try:
                text = src_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pattern in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append(f"{src_file.relative_to(BACKEND_DIR)}: matched '{pattern}'")

        assert not violations, (
            "SOVEREIGNTY VIOLATION — cloud API URLs found in source:\n"
            + "\n".join(violations)
        )

    def test_no_cloud_sdk_imports(self):
        """No source file must import cloud AI SDKs."""
        forbidden_imports = [
            r"import openai",
            r"from openai",
            r"import anthropic",
            r"from anthropic",
            r"import google\.generativeai",
            r"from google\.generativeai",
            r"import boto3.*bedrock",
        ]
        violations = []
        for src_file in self._collect_python_sources():
            try:
                text = src_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pattern in forbidden_imports:
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append(f"{src_file.relative_to(BACKEND_DIR)}: '{pattern}'")

        assert not violations, (
            "SOVEREIGNTY VIOLATION — cloud AI SDK imports found:\n"
            + "\n".join(violations)
        )
