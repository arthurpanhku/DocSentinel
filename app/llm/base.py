"""
LLM abstraction: unified interface for hosted and local LLM providers.
PRD §5.2.6; switch provider via config without changing Agent logic.
"""

from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings


@lru_cache(maxsize=1)
def get_llm() -> BaseChatModel:
    """Return a cached LLM client instance (one per process lifetime)."""
    if settings.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY or None,
            base_url=settings.OPENAI_BASE_URL or None,
            temperature=0.2,
        )
    if settings.LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY or None,
            base_url=settings.ANTHROPIC_BASE_URL or None,
            temperature=0.2,
        )
    if settings.LLM_PROVIDER in {
        "qwen",
        "deepseek",
        "openai_compatible",
        "local_openai",
    }:
        from langchain_openai import ChatOpenAI

        provider_config = {
            "qwen": (
                settings.QWEN_MODEL,
                settings.QWEN_API_KEY,
                settings.QWEN_BASE_URL,
            ),
            "deepseek": (
                settings.DEEPSEEK_MODEL,
                settings.DEEPSEEK_API_KEY,
                settings.DEEPSEEK_BASE_URL,
            ),
            "openai_compatible": (
                settings.COMPAT_MODEL,
                settings.COMPAT_API_KEY,
                settings.COMPAT_BASE_URL,
            ),
            "local_openai": (
                settings.LOCAL_MODEL,
                settings.LOCAL_API_KEY,
                settings.LOCAL_BASE_URL,
            ),
        }
        model, api_key, base_url = provider_config[settings.LLM_PROVIDER]
        return ChatOpenAI(
            model=model,
            api_key=api_key or None,
            base_url=base_url or None,
            temperature=0.2,
        )
    if settings.LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.2,
        )
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}")


async def invoke_llm(system_prompt: str, user_prompt: str) -> str:
    """Invoke LLM with system + user message; return content string."""
    llm = get_llm()
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    result = await llm.ainvoke(messages)
    return result.content if hasattr(result, "content") else str(result)
