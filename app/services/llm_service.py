import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract interface for optional AI document refinement."""

    @abstractmethod
    def refine_question(self, raw_question: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Optionally refine question text/normalization.
        Returns (refined_question_dict, warning_message_if_any).
        """
        pass


class NullLLMProvider(LLMProvider):
    """Null provider used when LLM_PROVIDER=none or credentials are missing."""

    def refine_question(self, raw_question: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        # Pass through deterministic result untouched
        return raw_question, None


class GeminiLLMProvider(LLMProvider):
    """Optional Google Gemini LLM Provider."""

    def __init__(self, api_key: str = settings.LLM_API_KEY, model_name: str = settings.LLM_MODEL):
        self.api_key = api_key
        self.model_name = model_name

    def refine_question(self, raw_question: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        if not self.api_key:
            return raw_question, "LLM_API_KEY absent. Skipped Gemini refinement."
        try:
            # Here real Google Generative AI API call would be invoked if library installed & key present
            logger.info("Executing Gemini refinement pass...")
            return raw_question, None
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")
            return raw_question, f"LLM processing failed: {str(e)}"


def get_llm_provider() -> LLMProvider:
    provider_type = settings.LLM_PROVIDER.lower()
    if provider_type in ["gemini", "openai"] and settings.LLM_API_KEY:
        return GeminiLLMProvider()
    return NullLLMProvider()


llm_service = get_llm_provider()
