# Run Notes: run_3

## Overview
- **Date:** 2026-03-28
- **Response models:** openai:gpt-4.1-mini, openrouter:anthropic/claude-3.5-haiku,
  openrouter:meta-llama/llama-3.3-70b-instruct, openrouter:mistralai/mistral-large,
  openrouter:qwen/qwen-2.5-72b-instruct, openrouter:x-ai/grok-4-fast
- **Evaluation prompts:** 36 prompts across 6 topic groups
- **Persona rater model:** mistralai/mistral-large (via OpenRouter)
- **Personas used:** 6 (persona_ids 1, 2, 5, 6, 7, 8)
- **Personas excluded from bridging scores:** 3 (Religious), 4 (Secularist)
  — kept in data for reference, excluded from analysis
- **Lambda default:** 0.5
- **Total responses:** 216 (36 prompts × 6 models)
- **Total persona ratings:** 1296 (216 responses × 6 personas)

## Changes from run_1

- Added 3 response models: Llama 3.3 70B, Mistral Large, Qwen 2.5 72B
- Doubled evaluation prompts from 18 to 36 (3 new prompts per topic group)

## Key Findings

- **Model ranking is compressed** — all six models score between 2.50 and 2.86 with
  overlapping error bars. Llama scores marginally highest (~2.86) and Grok lowest
  (~2.50). The Claude > GPT > Grok ranking from run_1 holds within the six-model
  field, with Llama inserted above and Mistral and Qwen between GPT and Grok.
- **Llama leads on AI and values (3.32), Economic redistribution (3.12), and
  Individual vs collective rights (2.99)** — the highest single cell in the dataset
  and consistent top performance on institutional authority questions.
- **Grok consistently lowest on Global vs national identity (2.12)** — confirmed
  across run_1 and run_3 with different prompt sets and model counts. Most robust
  finding in the dataset.
- **Qwen appears at both extremes** — among the highest on individual rights questions
  and lowest on Technology and progress (2.04). Takes stronger positions than other
  models, sometimes bridging well and sometimes polarising badly.
- **Progressive lean confirmed and strengthened across all 6 models** — Libertarian
  scores range 1.94–2.36, the tightest and coolest row in the Mean Persona Scores
  heatmap. Globalist scores range 3.69–4.28, the warmest row. All frontier models
  produce similarly progressive-leaning content regardless of training approach or
  origin.
- **GPT scores lowest from Libertarian (1.94)** — consistent with run_1.
- **Persona correlation structure holds but weakens** — Libertarian vs Collectivist
  drops from -0.66 to -0.48, Collectivist vs Globalist stable at 0.74. Technology
  axis remains weakest at -0.24.

## Persona Notes

- Nationalist: IQR compressed around 3, correlation with Globalist -0.16.
  Confirmed as structural content limitation rather than prompt engineering problem.
- Personas 3 and 4 excluded — consistent with run_1. See readme for full details.
- All other personas consistent with run_1 distributions.

## Potential Conflicts of Interest

- Mistral Large is used as both a response model and the persona rater model. Its
  bridging scores may be affected by the rater having seen similar training data to
  the responses it is rating. Worth noting as a methodological limitation.

## TODOs Before Next Run

- Qualitative inspection of Qwen's highest and lowest scoring responses to understand
  what drives the extreme variance
- Consider whether Mistral should be excluded as a response model given its dual role
  as rater model
- Human validation website — next major development priority