# LLM Pluralism Evaluation

A pluralistic AI evaluation framework that measures whether LLM responses are reasonable across value-diverse perspectives, using a bridging score that rewards outputs acceptable to disagreeing groups rather than just the majority. 

Similar to Community Notes on X.

Influenced by this article: https://ai-frontiers.org/articles/ai-alignment-cannot-be-top-down

Using llm-honesty repository as a base, more to come...

## Ongoing Findings

> Observations noted during development for future documentation/analysis.

- **Ideological asymmetry in rater scores:** Conservative-leaning personas (Free Market Individualist, Religious Traditionalist, Communitarian Nationalist, AI Techno-Optimist) show meaningful score variance including low scores of 1-2, while progressive-leaning personas (Social Democrat, Secular Progressive, Cosmopolitan Globalist, AI Safety Precautionist) rate almost all responses 4-5. This likely reflects a genuine ideological lean in frontier model outputs stemming from RLHF training data demographics. Needs formal analysis and visualisation. This result is from using the initial persona set (found in `docs/personas_weak.csv`). The weak personas will be highlighted separately in the final analysis as evidence of ideological lean before any prompt strengthening was applied.

- **Rater model matters more than persona prompt strength:** Strengthening the persona prompts alone (using Llama as the rater model) produced only marginal changes to score distributions. Switching to Mistral as the rater model — combined with stronger personas — produced substantially more balanced and discriminating results. This suggests the choice of rater model is the more significant variable, likely because Mistral is more steerable into adversarial personas than Llama.

- **Religious/secular axis excluded:** Personas 3 (Religious Traditionalist) and 4 (Secular Progressive) were excluded from bridging score analysis after three independent runs produced consistent but unusable distributions. Religious Traditionalist rated ~95% of responses 1 or 2 regardless of content — too hostile to discriminate meaningfully. Secular Progressive rated ~85% of responses 4 or 5 regardless of content — too approving to discriminate meaningfully. Both patterns were stable across all three runs confirming the issue is structural rather than random. Frontier models appear to avoid taking strong positions on religion, leaving the religious/secular groups underrepresented in the evaluated responses. The remaining six personas across three opposing pairs were used for all bridging score analysis.