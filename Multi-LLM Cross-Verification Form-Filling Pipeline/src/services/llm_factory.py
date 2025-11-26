"""LLM factory using OpenAI or local Ollama via LangChain."""
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from config.settings import ModelConfig, Settings, get_settings


def resolve_llm(model_cfg: ModelConfig, settings: Settings | None = None):
    settings = settings or get_settings()
    if settings.openai_api_key:
        return ChatOpenAI(
            model=model_cfg.name,
            temperature=model_cfg.temperature,
            max_tokens=model_cfg.max_tokens,
            api_key=settings.openai_api_key,
        )
    return ChatOllama(
        model=model_cfg.name,
        temperature=model_cfg.temperature,
        base_url=settings.ollama_endpoint,
    )
