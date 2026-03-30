# Run Notes: run_2_3models_18prompts_LlamaRater

## Overview
- **Date:** 2026-03-27
- **Response models:** openai:gpt-4.1-mini, openrouter:anthropic/claude-3.5-haiku, openrouter:x-ai/grok-4-fast
- **Evaluation prompts:** 18 prompts across 6 topic groups
- **Persona rater model:** meta-llama/llama-3.3-70b-instruct (via OpenRouter)
- **Personas used:** All 8 (persona_ids 1-8, including Religious and Secularist for comparison)
- **Personas excluded from bridging scores:** None — all 8 included to observe Llama behaviour across full panel
- **Lambda default:** 0.5
- **Total responses:** 54 (18 prompts × 3 models)
- **Total persona ratings:** 432 (54 responses × 8 personas)

## Purpose
This run was conducted as a direct comparison to run_1 (Mistral rater) using identical 
prompts, personas, and response models. The only variable changed was the persona rater 
model, from Mistral Large to Llama 3.3 70B. The purpose was to test whether rater model 
choice meaningfully affects results.

## Key Observations
- Llama produces strongly approval-biased ratings — most personas cluster 4-5 regardless 
  of content, making bridging scores artificially inflated and unreliable
- Persona correlation structure collapses almost entirely — most pairs show near-zero 
  correlation compared to meaningful opposition in the Mistral run
- Exception: Free Market vs Collectivist correlation holds at -0.71, 
  consistent with Mistral run (-0.70), confirming the economic axis is robust across 
  rater models
- Grok remains the most polarising model in the mean vs std scatter plot, consistent 
  with Mistral run
- Religious behaves differently with Llama — produces reasonable 
  distribution (median ~2, box spanning 2-4) vs broken distribution with Mistral 
  (95% scores of 1-2)
- Nationalist breaks in opposite direction with Llama — rates almost 
  everything 4, vs compressed around 3 with Mistral

## Conclusion
Llama is unsuitable as a persona rater model for this framework due to approval bias. 
Mistral Large is the preferred rater model. This run is archived for reference and 
comparison only. See Ongoing Findings in readme for full analysis.

## Robust Findings (consistent across both rater models)
- Free Market vs Collectivist opposition: -0.70 to -0.71
- Grok is the most polarising response model by std deviation

## Notes
- Bridging scores from this run should not be used for model comparison conclusions
- Persona correlation data is useful only for the economic axis pair
- All 8 personas were included specifically to observe Religious and 
  Secularist behaviour with a different rater model