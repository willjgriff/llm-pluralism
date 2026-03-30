# Run Notes: run_3_36prompts_6models_MistralRater

## Overview
- **Date:** 2026-03-28
- **Response models:** openai:gpt-4.1-mini, openrouter:anthropic/claude-3.5-haiku, 
  openrouter:meta-llama/llama-3.3-70b-instruct, openrouter:mistralai/mistral-large, 
  openrouter:qwen/qwen-2.5-72b-instruct, openrouter:x-ai/grok-4-fast
- **Evaluation prompts:** 36 prompts across 6 topic groups
- **Persona rater model:** mistralai/mistral-large (via OpenRouter)
- **Personas used:** 6 (persona_ids 1, 2, 5, 6, 7, 8)
- **Personas excluded from bridging scores:** 3 (Religious), 4 (Secular 
  Progressive) — kept in data for reference, excluded from analysis
- **Lambda default:** 0.5
- **Total responses:** 216 (36 prompts × 6 models)
- **Total persona ratings:** 1296 (216 responses × 6 personas)

## Changes from run_1

- Added 3 response models: Llama 3.3 70B, Mistral Large, Qwen 2.5 72B
- Doubled evaluation prompts from 18 to 36 (3 new prompts per topic group)

## Key Findings

- **Model ranking by bridging score is compressed** — all six models score between 
  2.44 and 2.65, with Llama marginally highest and Grok lowest. No model can be said 
  to definitively outperform another at this sample size. Claude's run_1 lead does 
  not hold with 6 models.
- **Qwen appears at both extremes** — highest single response (AI refusal, 4.8+) and 
  lowest single response (autonomous weapons, ~1.1). Takes stronger positions than 
  other models, sometimes bridging well and sometimes polarising badly.
- **Grok consistently lowest on Global vs national identity (1.94)** — confirmed across 
  run_1 and run_3 with different prompt sets and model counts. Most robust finding 
  in the dataset.
- **Progressive lean confirmed across all 6 models** — Libertarian scores 
  all models between 1.94 and 2.19, the tightest row in the Mean Persona Scores by 
  Model heatmap. All frontier models produce similarly progressive-leaning economic 
  content regardless of training approach.
- **Mistral scores lowest from Libertarian (1.94)** — even more 
  economically progressive than GPT in run_1.
- **Claude clusters in the middle range** — rarely appears at the top or bottom of the 
  ranked chart. Most consistently moderate model rather than highest bridging model 
  as suggested by run_1.
- **Nationalist still shows IQR compression** — Correlation with
  Globalist unchanged at -0.08. Confirmed as structural content limitation rather than 
  prompt engineering problem.

## Persona Notes

- Nationalist: unstrengthened prompt — IQR compressed around 3, 
  correlation with Globalist -0.08. Confirmed as structural limitation 
  regardless of prompt strength (tested separately).
- Secularist: unstrengthened prompt — skewed toward 4-5, correlation with 
  Religious -0.31 when tested with strengthened prompt. Kept in data, 
  excluded from analysis alongside Religious.
- All other personas consistent with run_1 distributions.

## Potential Conflicts of Interest

- Mistral Large is used as both a response model and the persona rater model. Its 
  bridging scores may be affected by the rater model having seen similar training 
  data to the responses it is rating. Worth noting as a methodological limitation.

## TODOs Before Next Run

- Qualitative inspection of Qwen's highest and lowest scoring responses to understand 
  what drives the extreme variance
- Qualitative inspection of Mistral on "Should citizenship be replaced with a universal 
  global identity" — appears near bottom of ranked chart, worth understanding why
- Consider whether Mistral should be excluded as a response model given its dual role 
  as rater model
- Human validation website — next major development priority