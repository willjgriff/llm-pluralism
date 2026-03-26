"""Model client wrappers and configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from openai import OpenAI

import config


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    temperature: float = 0.2
    timeout_seconds: float = 20.0
    max_retries: int = 0


def _get_client(model: ModelConfig) -> OpenAI:
    if model.provider == "openai":
        api_key = config.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing.")
        return OpenAI(
            api_key=api_key,
            timeout=model.timeout_seconds,
            max_retries=model.max_retries,
        )

    if model.provider == "openrouter":
        api_key = config.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is missing.")
        return OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=model.timeout_seconds,
            max_retries=model.max_retries,
        )

    raise ValueError(f"Unsupported provider '{model.provider}'.")


def generate_answer(*, instruction: str, question: str, config: ModelConfig) -> str:
    """Call OpenAI chat completions and return the assistant text."""
    client = _get_client(config)

    responses = client.chat.completions.create(
        model=config.model,
        temperature=config.temperature,
        timeout=config.timeout_seconds,
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": question},
        ],
    )

    content = responses.choices[0].message.content
    return (content or "").strip()


def parse_model_specs(model_specs: Iterable[str]) -> list[ModelConfig]:
    """Parse model specs like 'openai:gpt-4.1-mini'."""
    parsed_configs: list[ModelConfig] = []
    for raw_spec in model_specs:
        spec_value = raw_spec.strip()
        if not spec_value:
            continue
        if ":" not in spec_value:
            raise ValueError(
                f"Invalid model spec '{spec_value}'. Expected format 'provider:model'."
            )
        provider, model = spec_value.split(":", 1)
        provider = provider.strip().lower()
        model = model.strip()
        parsed_configs.append(ModelConfig(provider=provider, model=model))
    if not parsed_configs:
        raise ValueError("No valid model specs were provided.")
    return parsed_configs


def default_model_configs() -> list[ModelConfig]:
    model_specs = [
        model_spec for model_spec in config.EVALUATION_MODELS.split(",") if model_spec.strip()
    ]
    return parse_model_specs(model_specs)
