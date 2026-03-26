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

# --- Edit in this file (not read from the environment) ---

# Comma-separated model specs `provider:model`.
EVALUATION_MODELS = (
    "openai:gpt-4.1-mini,"
    "openrouter:anthropic/claude-3.5-haiku,"
    "openrouter:x-ai/grok-4-fast"
)

# Single model used for persona_query mode.
PERSONA_QUERY_MODEL = "openrouter:mistralai/mistral-large"

# Max concurrent requests for persona_query mode.
PERSONA_QUERY_MAX_THREADS = 4

# CSV of evaluation prompts (columns include question_id, group_id, group_name, prompt text).
EVALUATION_PROMPTS_PATH = Path("data/evaluation_prompts.csv")

# Shared system/instruction text prepended for every model call during querying.
EVALUATION_SYSTEM_PROMPT_PATH = Path("data/evaluation_system_prompt.txt")

# Where querying writes the responses CSV.
QUERY_OUTPUT_PATH = Path("results/evaluation_responses.csv")

# Persona-system prompts used in persona_query mode.
PERSONA_SYSTEM_PROMPTS_PATH = Path("data/persona_system_prompts.csv")

# Input CSV for persona_query mode (typically output from evaluation_query).
PERSONA_QUERY_INPUT_PATH = Path("results/evaluation_responses.csv")

# Where persona_query writes outputs.
PERSONA_QUERY_OUTPUT_PATH = Path("results/persona_responses.csv")

# When running `run.py --mode analyse`, this CSV is read (typically the last query output).
ANALYSIS_INPUT_CSV = Path("results/evaluation_responses.csv")

# Directory for analysis outputs (figures, derived CSVs, etc.).
ANALYSIS_OUTPUT_DIR = Path("results")

# If True, failed API calls become `[ERROR] ...` rows instead of aborting the run.
SKIP_ERRORS = False

# If True, models are queried one after another; if False, parallel threads (one pool per model).
SEQUENTIAL = False

# If True, after analysis, copy chart PNGs from the results tree into `docs/images/` for the README.
COPY_README_IMAGES = False
