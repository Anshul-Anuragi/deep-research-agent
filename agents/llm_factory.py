"""
LLM Factory - Initializes Chat models for OpenRouter or Google Gemini
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def normalize_model_name(model_name: str) -> str:
    """Normalize user-friendly model names (e.g., 'DeepSeek V4.1 Flash 1017') to provider slugs."""
    trimmed = model_name.strip()
    if "/" in trimmed:
        return trimmed

    clean = trimmed.lower()
    if "deepseek" in clean and "flash" in clean and "1017" in clean:
        return "deepseek/deepseek-v4.1-flash-1017"
    if "deepseek" in clean and "flash" in clean:
        return "deepseek/deepseek-v4.1-flash"
    if "deepseek" in clean and "v3" in clean:
        return "deepseek/deepseek-chat"
    if "deepseek" in clean and "r1" in clean:
        return "deepseek/deepseek-r1"
    if "gemma" in clean:
        return "google/gemma-4-26b-a4b-it:free"

    return trimmed


def get_llm(model: Optional[str] = None, temperature: float = 0.2):
    """
    Returns an initialized LangChain Chat model.
    Prioritizes OpenRouter if OPENROUTER_API_KEY is present,
    or falls back to Google Gemini if GOOGLE_API_KEY is present.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    raw_model = (model or os.getenv("DR_MODEL", "")).strip()
    norm_model = normalize_model_name(raw_model)

    # Use OpenRouter if key exists and (model has slash / deepseek or no gemini prefix, or no google key)
    if openrouter_api_key and (
        "/" in norm_model
        or "deepseek" in norm_model.lower()
        or not google_api_key
        or not norm_model.startswith("gemini-")
    ):
        from langchain_openai import ChatOpenAI
        final_model = norm_model if norm_model else "deepseek/deepseek-v4.1-flash-1017"
        return ChatOpenAI(
            model=final_model,
            openai_api_key=openrouter_api_key,
            openai_api_base=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/deep-research-agents",
                "X-Title": "Deep Research Agents"
            },
            temperature=temperature
        )

    # Google Gemini client
    from langchain_google_genai import ChatGoogleGenerativeAI
    final_model = norm_model if norm_model else "gemini-3.5-flash"
    return ChatGoogleGenerativeAI(
        model=final_model,
        temperature=temperature,
        google_api_key=google_api_key
    )

