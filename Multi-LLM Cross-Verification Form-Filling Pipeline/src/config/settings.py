"""Configuration for multi-LLM cross-verification pipeline."""
from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    name: str
    temperature: float = 0.0
    max_tokens: int | None = None


class ConsensusConfig(BaseModel):
    numeric_tolerance: float = 0.01
    max_retries: int = 2


class Settings(BaseSettings):
    openai_api_key: str | None = None
    ollama_endpoint: str | None = None

    missing_field_model: ModelConfig = Field(default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.0))
    extractor_model_a: ModelConfig = Field(default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.1))
    extractor_model_b: ModelConfig = Field(default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.2))
    checker_model: ModelConfig = Field(default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.0))
    writer_model: ModelConfig = Field(default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.0))

    consensus: ConsensusConfig = Field(default_factory=ConsensusConfig)

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
