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

DATA_DIR = Path("data")
RESULTS_DIR = Path("results")

# Step: collect evaluation responses (prompted by shared system prompt).
# Comma-separated model specs `provider:model`.
EVALUATION_MODELS = (
    "openai:gpt-4.1-mini,"
    "openrouter:anthropic/claude-3.5-haiku,"
    "openrouter:x-ai/grok-4-fast,"
    "openrouter:meta-llama/llama-3.3-70b-instruct,"
    "openrouter:mistralai/mistral-large,"
    "openrouter:qwen/qwen-2.5-72b-instruct"
)
EVALUATION_PROMPTS_PATH = DATA_DIR / "evaluation_prompts.csv"
EVALUATION_SYSTEM_PROMPT_PATH = DATA_DIR / "evaluation_system_prompt.txt"
QUERY_OUTPUT_PATH = RESULTS_DIR / "evaluation_responses.csv"

# Runtime behavior for evaluation/persona query calls.
# If True, failed API calls become `[ERROR] ...` rows instead of aborting the run.
SKIP_ERRORS = True
# If True, models are queried one after another; if False, parallel threads (one pool per model).
SEQUENTIAL = False

# Step: collect persona ratings over evaluation responses.
PERSONA_SYSTEM_PROMPTS_PATH = DATA_DIR / "persona_system_prompts.csv"
PERSONA_QUERY_INPUT_PATH = RESULTS_DIR / "evaluation_responses.csv"
PERSONA_QUERY_OUTPUT_PATH = RESULTS_DIR / "persona_responses.csv"
# Single model used for persona_query mode.
PERSONA_QUERY_MODEL = "openrouter:mistralai/mistral-large"
# Max concurrent requests for persona_query mode.
PERSONA_QUERY_MAX_THREADS = 4

# --- Analysis Configuration ---

# Persona IDs included in bridging scores, pairwise correlations, and persona distribution charts.
ANALYSIS_PERSONA_IDS: tuple[int, ...] = (1, 2, 5, 6, 7, 8)

ANALYSIS_OUTPUT_DIR = RESULTS_DIR / "analysis"

# If True, after ``analyse`` completes, copy ``DATA_DIR`` and ``RESULTS_DIR`` into
# ``DOCS_RUN_DIR``/``data`` and ``DOCS_RUN_DIR``/``results`` (overwrites on repeat runs).
COPY_RESULTS_TO_DOCS = False
DOCS_RUN_DIR = Path("docs/run_2")

# Step: bridging score analysis from persona responses.
BRIDGING_SCORE_INPUT_PATH = RESULTS_DIR / "persona_responses.csv"
BRIDGING_SCORE_OUTPUT_PATH = ANALYSIS_OUTPUT_DIR / "bridging_scores.csv"
BRIDGING_SCORE_LAMBDA = 0.5

# Step: persona-correlation analysis from persona responses.
PERSONA_CORRELATIONS_INPUT_PATH = RESULTS_DIR / "persona_responses.csv"
PERSONA_CORRELATIONS_OUTPUT_PATH = ANALYSIS_OUTPUT_DIR / "persona_correlations.csv"
