# Setup and run

How to install dependencies, configure keys, and run `[src/run.py](src/run.py)` from the **project root** (so `import config` and paths resolve).

## Requirements

- **Python** 3.10+ recommended.
- **Packages:** `pip install -r requirements.txt` (includes `openai`, `requests`, `pandas`, `matplotlib`, `scipy`, etc.).
- `**.env`** in the repo root (copy from `.env.example`):
  - `**OPENAI_API_KEY`** / `**OPENROUTER_API_KEY**` — needed when any configured model uses that provider (`openai` or `openrouter` only; see `src/model_query/models.py`).
  - `**EXPORT_PASSWORD**` — only for `**survey_query**` (HTTP Basic user `admin`).

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in the keys you need, then edit defaults in `**src/config.py**` (models, paths, toggles). There is no separate CLI for configuration.

## Run

```bash
python src/run.py [--mode MODE [MODE ...]]
```


| Mode                       | What it does                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| `evaluation_query`         | Prompts → LLMs → `output/evaluation_responses.csv`                                                       |
| `persona_query`            | Persona ratings over those responses → `output/persona_responses.csv`                                    |
| `survey_query`             | Fetches survey export → `output/survey_responses_sessions.csv` and `output/survey_responses_ratings.csv` |
| `persona_response_analyse` | Bridging scores, correlations, charts under `output/analysis/`                                           |
| `survey_response_analyse`  | Human-vs-AI charts + summary under `output/analysis/survey/`                                             |


**Default** (no `--mode`): all five modes, in the order above.

Useful one-liners:

```bash
python src/run.py                                          # full pipeline
python src/run.py --mode persona_response_analyse          # charts from existing persona CSV
python src/run.py --mode survey_query                      # refresh survey CSVs only
python src/run.py --mode survey_response_analyse           # needs survey CSVs + bridging_scores.csv
```

**There are dependencies between stages and with a blank project the different modes need to be run in order.**

## Troubleshooting

- Missing API key errors come from `model_query` when a model uses that provider.
- `**survey_query` fails (401 / network)** — check `EXPORT_PASSWORD` and `SURVEY_EXPORT_URL` in `config.py`.
- `**SKIP_ERRORS = True`** — failed calls become `[ERROR] ...` in CSVs; downstream numbers may be meaningless.

Debug: `**.vscode/launch.json`** has launch configs that call `src/run.py` with different `--mode` values.

## Outputs (where to look)


| Path                                                               | Role                                             |
| ------------------------------------------------------------------ | ------------------------------------------------ |
| `output/evaluation_responses.csv`                                  | Raw model answers                                |
| `output/persona_responses.csv`                                     | Persona scores per response                      |
| `output/analysis/bridging_scores.csv` / `persona_correlations.csv` | Computed metrics                                 |
| `output/analysis/*.png`                                            | Model-persona charts                             |
| `output/analysis/survey/`                                          | Human survey charts + `what_transfers_summary.*` |


Column names match the writers in `src/model_query/query_pipeline.py`. Extra λ columns on bridging scores are documented in `src/result_analysis/model_personas/scoring/bridging_score.py` (`LAMBDA_VALUES`).

## Archiving a run

Set `COPY_RESULTS_TO_DOCS = True` and `DOCS_RUN_DIR = Path("docs/run_N")` in `config.py`, then run an analysis mode so `data/` and `output/` copy into `docs/run_N/`. Or copy those two folders manually into the same layout.