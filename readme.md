# LLM Pluralism Evaluation

A pluralistic AI evaluation framework that measures whether LLM responses are reasonable across value-diverse perspectives, using a bridging score that rewards outputs acceptable to disagreeing groups rather than just the majority. 

Similar to Community Notes on X.

Influenced by this article: https://ai-frontiers.org/articles/ai-alignment-cannot-be-top-down

Using llm-honesty repository as a base, more to come...


## Ongoing Findings

> These are observations noted during development that need to be properly analysed and documented.

- **Ideological asymmetry in rater scores:** Conservative-leaning personas (Free Market Individualist, Religious Traditionalist, Communitarian Nationalist, AI Techno-Optimist) show meaningful score variance including low scores of 1-2, while progressive-leaning personas (Social Democrat, Secular Progressive, Cosmopolitan Globalist, AI Safety Precautionist) rate almost all responses 4-5. This likely reflects a genuine ideological lean in frontier model outputs stemming from RLHF training data demographics. Needs formal analysis and visualisation. This result is from using my initial persona set (found in data/persona_system_prompts_weak.csv). I will strengthen the progressive personas (encorage them to be more decisive etc) for future evaluation but will highlight the above in my final analysis.