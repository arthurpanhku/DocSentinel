"""
LLM abstraction: unified interface for OpenAI and Ollama.
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
    if settings.LLM_PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama

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
