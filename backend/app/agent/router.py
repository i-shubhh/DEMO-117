"""Task Router per Section 12 of master plan."""

import re
from typing import Any, Dict, List, Tuple
from app.models.registry import registry


class TaskRouter:
    """Routes incoming tasks to appropriate open-weight models based on multimodal input and intent."""

    def __init__(self):
        self.code_patterns = [
            r"\b(code|script|python|execute|sandbox|calculate|compute|algorithm|benchmark|run|vibration analysis|outlier)\b",
            r"\b(write a function|plot|pandas|numpy|formula|tolerance limit test)\b",
        ]
        self.visual_patterns = [
            r"\b(scanned|inspection|image|photo|diagram|drawing|gauge|visual|ocr|pdf report|signoff|stamp)\b",
        ]

    def route(self, task_prompt: str, files: List[Dict[str, Any]], requested_mode: str = "auto") -> Tuple[str, str, Dict[str, Any]]:
        """
        Determines:
        1. task_type: 'visual_document' | 'knowledge_reasoning' | 'coding'
        2. selected_model: model identifier
        3. decision_metadata: reasons and model config
        """
        # Explicit override if requested
        if requested_mode == "coding_agent":
            model_info = registry.get_model_for_capability("coding")
            return "coding", model_info["model"], {
                "capability": "sandboxed_code_generation",
                "reason": "User selected Coding Agent mode explicitly",
                "endpoint": model_info["endpoint"],
            }
        elif requested_mode == "knowledge_assistant":
            model_info = registry.get_model_for_capability("reasoning")
            return "knowledge_reasoning", model_info["model"], {
                "capability": "industrial_reasoning_sops",
                "reason": "User selected Knowledge Assistant mode explicitly",
                "endpoint": model_info["endpoint"],
            }
        elif requested_mode == "document_agent":
            model_info = registry.get_model_for_capability("vision")
            return "visual_document", model_info["model"], {
                "capability": "multimodal_ocr_vision",
                "reason": "User selected Document Agent mode explicitly",
                "endpoint": model_info["endpoint"],
            }

        prompt_lower = task_prompt.lower()

        # Check if files contain image or pdf
        has_visual_files = any(
            f.get("filename", "").lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".webp"))
            or f.get("mime_type", "").startswith(("image/", "application/pdf"))
            for f in files
        )

        # Code detection score
        code_score = sum(1 for p in self.code_patterns if re.search(p, prompt_lower))
        visual_score = sum(1 for p in self.visual_patterns if re.search(p, prompt_lower))

        if has_visual_files or visual_score > 0:
            task_type = "visual_document"
            model_info = registry.get_model_for_capability("vision")
            reason = f"Visual input detected ({len(files)} files present, visual matching score {visual_score})"
        elif code_score > 0:
            task_type = "coding"
            model_info = registry.get_model_for_capability("coding")
            reason = f"Code/computational intent identified (score: {code_score})"
        else:
            task_type = "knowledge_reasoning"
            model_info = registry.get_model_for_capability("reasoning")
            reason = "Industrial inquiry requiring local SOP grounding and structured reasoning"

        return task_type, model_info["model"], {
            "capability": model_info["capability"],
            "reason": reason,
            "endpoint": model_info["endpoint"],
        }


router = TaskRouter()
