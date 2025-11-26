"""Configuration and defaults for the form-filling workflow."""
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
    mismatch_escalation_threshold: int = 2


class Settings(BaseSettings):
    # LLM backends
    openai_api_key: str | None = None
    ollama_endpoint: str | None = None

    # Model choices
    form_analysis_model: ModelConfig = Field(
        default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.0)
    )
    bill_parser_model_a: ModelConfig = Field(
        default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.1)
    )
    bill_parser_model_b: ModelConfig = Field(
        default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.2)
    )
    reconciler_model: ModelConfig = Field(
        default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.0)
    )
    writer_model: ModelConfig = Field(
        default_factory=lambda: ModelConfig(name="gpt-4o-mini", temperature=0.0)
    )

    consensus: ConsensusConfig = Field(default_factory=ConsensusConfig)

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"


def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
