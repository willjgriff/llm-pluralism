"""Central configuration: edit values here; API keys come from ``.env``."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- From `.env` only (see `.env.example`) ---

# OpenAI API key for models with provider `openai` (e.g. `openai:gpt-4.1-mini`).
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# OpenRouter API key for models with provider `openrouter`.
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# --- Evaluation Configuration ---

# Step: collect evaluation responses (prompted by shared system prompt).
# Comma-separated model specs `provider:model`.
EVALUATION_MODELS = (
    "openai:gpt-4.1-mini,"
    "openrouter:anthropic/claude-3.5-haiku,"
    "openrouter:x-ai/grok-4-fast"
)
EVALUATION_PROMPTS_PATH = Path("data/evaluation_prompts.csv")
EVALUATION_SYSTEM_PROMPT_PATH = Path("data/evaluation_system_prompt.txt")
QUERY_OUTPUT_PATH = Path("results/evaluation_responses.csv")

# Runtime behavior for evaluation/persona query calls.
# If True, failed API calls become `[ERROR] ...` rows instead of aborting the run.
SKIP_ERRORS = False
# If True, models are queried one after another; if False, parallel threads (one pool per model).
SEQUENTIAL = False

# Step: collect persona ratings over evaluation responses.
PERSONA_SYSTEM_PROMPTS_PATH = Path("data/persona_system_prompts.csv")
PERSONA_QUERY_INPUT_PATH = Path("results/evaluation_responses.csv")
PERSONA_QUERY_OUTPUT_PATH = Path("results/persona_responses.csv")
# Single model used for persona_query mode.
PERSONA_QUERY_MODEL = "openrouter:mistralai/mistral-large"
# Max concurrent requests for persona_query mode.
PERSONA_QUERY_MAX_THREADS = 4

# --- Analysis Configuration ---

ANALYSIS_OUTPUT_DIR = Path("results/analysis")

# Step: bridging score analysis from persona responses.
BRIDGING_SCORE_INPUT_PATH = Path("results/persona_responses.csv")
BRIDGING_SCORE_OUTPUT_PATH = ANALYSIS_OUTPUT_DIR / "bridging_scores.csv"
BRIDGING_SCORE_LAMBDA = 0.5

# Step: persona-correlation analysis from persona responses.
PERSONA_CORRELATIONS_INPUT_PATH = Path("results/persona_responses.csv")
PERSONA_CORRELATIONS_OUTPUT_PATH = ANALYSIS_OUTPUT_DIR / "persona_correlations.csv"
