# Setup and run reference

Developer-oriented notes for cloning, configuring, and running the LLM pluralism evaluation pipeline (`src/run.py`).

## Requirements

- **Python** 3.10+ (uses `pathlib`, type hints, and patterns common in 3.10+; no formal `pyproject.toml` pin—use a recent 3.x).
- **API keys** (loaded via `python-dotenv` from a `.env` file in the project root):
  - **`OPENAI_API_KEY`** — Required if any evaluation or persona model uses provider `openai`. Create at [OpenAI API keys](https://platform.openai.com/api-keys).
  - **`OPENROUTER_API_KEY`** — Required if any model uses provider `openrouter`. Create at [OpenRouter](https://openrouter.ai/) (Settings → Keys). Billing and model access are managed there.
- **Python packages** — See `requirements.txt`: `openai`, `matplotlib`, `python-dotenv`, `numpy`. The OpenAI SDK is used for both OpenAI and OpenRouter (OpenRouter uses the OpenAI-compatible endpoint `https://openrouter.ai/api/v1`).

Supported **providers** are only `openai` and `openrouter` (`src/model_query/models.py`). Anything else raises `ValueError` at client creation.

## Installation

Clone this repository, then from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip3 install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set real values for `OPENAI_API_KEY` and `OPENROUTER_API_KEY` (see `.env.example`).

## Configuration

All defaults live in **`src/config.py`** (paths are relative to the **project root**; run **`python src/run.py`** from the project root so imports resolve).

### Evaluation models (response generators)

- **`EVALUATION_MODELS`** — A comma-separated string of specs `provider:model` (e.g. `openai:gpt-4.1-mini,openrouter:anthropic/claude-3.5-haiku`). The file may break the string across lines using implicit string concatenation; the runtime value is still one comma-separated string parsed in `model_query.models.default_model_configs()`.

### Persona rater (single model)

- **`PERSONA_QUERY_MODEL`** — One `provider:model` string used for all persona ratings in `persona_query` mode (e.g. `openrouter:meta-llama/llama-3.3-70b-instruct`).
- **`PERSONA_QUERY_MAX_THREADS`** — Concurrency for persona API calls.
- **`PERSONA_QUERY_INPUT_PATH`** — Defaults to `RESULTS_DIR / "evaluation_responses.csv"`; must exist before `persona_query`.
- **`PERSONA_QUERY_OUTPUT_PATH`** — `persona_responses.csv` output.

### Bridging score λ (polarisation penalty)

- **`BRIDGING_SCORE_LAMBDA`** — Weight used for the primary **`bridging_score`** column in `results/analysis/bridging_scores.csv`: `mean_score - λ * std_score` (population std across included personas per response).
- Additional columns for λ ∈ `{0.25, 0.50, 0.75}` are always written for the **λ comparison chart**; those values are defined in `src/result_analysis/scoring/bridging_score.py` as **`LAMBDA_VALUES`** (not the config file).

### Which personas enter analysis

- **`ANALYSIS_PERSONA_IDS`** — Tuple of persona IDs included in bridging scores, pairwise correlations, and persona distribution charts. Rows whose `persona_id` is not listed are dropped from scoring.

### Prompts and data files

Point these at different files to swap prompts or personas without code changes:

| Setting | Purpose |
|--------|---------|
| **`EVALUATION_PROMPTS_PATH`** | `data/evaluation_prompts.csv` — evaluation prompt rows |
| **`EVALUATION_SYSTEM_PROMPT_PATH`** | `data/evaluation_system_prompt.txt` — shared system prompt for response models |
| **`PERSONA_SYSTEM_PROMPTS_PATH`** | `data/persona_system_prompts.csv` — persona definitions for the rater |
| **`DATA_DIR`** / **`RESULTS_DIR`** | Roots for `data/` and `results/` trees |

### Optional: copy a run into `docs/`

- **`COPY_RESULTS_TO_DOCS`** — If `True`, after `analyse` finishes, copies **`DATA_DIR`** → **`DOCS_RUN_DIR/data`** and **`RESULTS_DIR`** → **`DOCS_RUN_DIR/results`** (`src/run.py` uses `shutil.copytree(..., dirs_exist_ok=True)`).
- **`DOCS_RUN_DIR`** — Example: `Path("docs/run_1")`.

### Runtime toggles

- **`SKIP_ERRORS`** — If `True`, failed API calls produce `[ERROR] ...` text in CSV rows instead of aborting.
- **`SEQUENTIAL`** — If `True`, evaluation models are queried one after another; if `False`, parallel execution per model.

## Running the pipeline

Entrypoint: **`src/run.py`**. Run from the **project root**:

```bash
python3 src/run.py [--mode MODE [MODE ...]]
```

### CLI

| Flag | Description |
|------|-------------|
| **`--mode`** | One or more of: `evaluation_query`, `persona_query`, `analyse`. Default: all three in order. |

There are no other CLI flags; models, paths, and λ are configured in **`src/config.py`**.

### Stages (actual order in `run.py`)

1. **`evaluation_query`** — Reads `EVALUATION_PROMPTS_PATH` and `EVALUATION_SYSTEM_PROMPT_PATH`, calls each model in `EVALUATION_MODELS`, writes **`QUERY_OUTPUT_PATH`** (`results/evaluation_responses.csv`).
2. **`persona_query`** — Reads `PERSONA_QUERY_INPUT_PATH` (evaluation responses) and `PERSONA_SYSTEM_PROMPTS_PATH`, calls **`PERSONA_QUERY_MODEL`** for each (prompt × response × persona) cell, writes **`PERSONA_QUERY_OUTPUT_PATH`** (`results/persona_responses.csv`).
3. **`analyse`** — Reads persona ratings, writes **`BRIDGING_SCORE_OUTPUT_PATH`**, **`PERSONA_CORRELATIONS_OUTPUT_PATH`**, generates charts under **`ANALYSIS_OUTPUT_DIR`**, then optionally copies to **`DOCS_RUN_DIR`** if **`COPY_RESULTS_TO_DOCS`** is `True`.

### Example commands

Full pipeline (default):

```bash
python3 src/run.py
```

Equivalent explicit modes:

```bash
python3 src/run.py --mode evaluation_query persona_query analyse
```

Query only (no scoring or charts):

```bash
python3 src/run.py --mode evaluation_query
```

Both query steps, no analysis:

```bash
python3 src/run.py --mode evaluation_query persona_query
```

Analyse only (requires existing `results/persona_responses.csv` and any inputs those steps need):

```bash
python3 src/run.py --mode analyse
```

### Gotchas and common errors

- **`OPENAI_API_KEY is missing.`** / **`OPENROUTER_API_KEY is missing.`** — Raised from `model_query.models._get_client` if a configured model uses that provider and the env var is empty.
- **`persona_query` before evaluation output** — `PERSONA_QUERY_INPUT_PATH` must point to a populated `evaluation_responses.csv` (run `evaluation_query` first or supply your own CSV with the expected columns).
- **`analyse` without persona data** — Bridging and correlations read **`BRIDGING_SCORE_INPUT_PATH`** / **`PERSONA_CORRELATIONS_INPUT_PATH`** (`persona_responses.csv` by default). Missing or empty files will yield empty or useless outputs.
- **`SKIP_ERRORS: True`** — Failures appear as `[ERROR] ...` in `response` / model output fields; downstream analysis may still run but scores can be invalid—inspect CSVs before trusting charts.

VS Code / Cursor: see **`.vscode/launch.json`** for debug configurations that pass `--mode` (e.g. `evaluation_query`, `persona_query`, `analyse`, or combined).

## Interpreting outputs

### `results/evaluation_responses.csv`

One row per (prompt × evaluation model). Columns: `question_id`, `group_id`, `group_name`, `model`, `question`, `response` (`src/model_query/query_pipeline.py` — `EVALUATION_RESPONSES_CSV_FIELD_NAMES`).

### `results/persona_responses.csv`

One row per (evaluation row × persona). Columns: `question_id`, `group_id`, `group_name`, `source_model`, `question`, `source_response`, `persona_id`, `persona_name`, `score`, `response` (`PERSONA_RESPONSES_CSV_FIELD_NAMES`). Analysis code also accepts `response_model` as an alias for `source_model` where noted in chart code.

### `results/analysis/bridging_scores.csv`

Per aggregated response (question / group / prompt / response model): `mean_score`, `std_score`, `bridging_score` (uses **`BRIDGING_SCORE_LAMBDA`**), plus `bridging_score_0.25`, `bridging_score_0.50`, `bridging_score_0.75` for the λ comparison chart.

### `results/analysis/persona_correlations.csv`

Pairwise Pearson correlations between persona rating vectors (`persona_a_id`, `persona_a_name`, `persona_b_id`, `persona_b_name`, `correlation`).

### Charts (`results/analysis/*.png`)

Generated by `result_analysis.charts.pipeline.generate_analysis_charts`:

| File | Content |
|------|---------|
| `bridging_scores_by_model.png` | Mean bridging score by response model |
| `bridging_scores_by_group.png` | Mean bridging score by topic group |
| `bridging_scores_by_model_and_group.png` | Heatmap model × group |
| `persona_correlations.png` | Persona × persona correlation heatmap |
| `mean_vs_std_scatter.png` | Mean vs std of persona scores per response |
| `persona_score_distributions.png` | Boxplots of scores by persona |
| `persona_scores_by_model.png` | Mean persona score × model heatmap |
| `bridging_scores_ranked.png` | Responses ranked by bridging score |
| `bridging_scores_lambda_comparison.png` | Mean bridging score by model for λ ∈ {0.25, 0.5, 0.75} |

## Archiving a run (`docs/run_N/`)

Convention:

1. Create a dedicated directory for the run, e.g. **`docs/run_1/`**, **`docs/run_2/`**, …
2. Set **`DOCS_RUN_DIR`** in `src/config.py` to that path (e.g. `Path("docs/run_1")`).
3. Set **`COPY_RESULTS_TO_DOCS = True`** and run **`analyse`** (or the full pipeline so results exist). The code copies:
   - **`data/`** → **`docs/run_N/data/`**
   - **`results/`** → **`docs/run_N/results/`**

So archived charts and CSVs live under **`docs/run_N/results/analysis/`**; prompts and personas under **`docs/run_N/data/`**.

To archive manually without re-running, copy the same two trees:

```bash
mkdir -p docs/run_1
cp -R data docs/run_1/data
cp -R results docs/run_1/results
```

Adjust `run_N` and use the same layout so it matches what `copy_data_and_results_to_docs` produces.
