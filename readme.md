# LLM Pluralism Evaluation

Frontier AI models are trained to please the majority, but whose majority? This project builds an evaluation framework that measures whether LLM responses are acceptable across genuinely opposing value perspectives, not just on average. Using a panel of ideologically diverse AI personas as raters and a bridging score that penalises polarisation, it finds evidence of <to be determined> and lays the groundwork for a human-validated, pluralistic alternative to standard RLHF feedback.

## Overview

A pluralistic AI evaluation framework that measures whether LLM responses are reasonable across value-diverse perspectives, using a bridging score that rewards outputs acceptable to disagreeing groups rather than just the majority.

The core motivation comes from a fundamental problem with how frontier AI models are currently aligned: standard RLHF training uses a relatively small, culturally homogeneous group of human labellers to define what "good" responses look like. This embeds the values of that group into the model at a deep level. The result is models that appear balanced and helpful to people who share those values, but may feel biased, dismissive, or alienating to people who don't.

This project takes a different approach, inspired by Audrey Tang's argument ([https://ai-frontiers.org/articles/ai-alignment-cannot-be-top-down](https://ai-frontiers.org/articles/ai-alignment-cannot-be-top-down)) that AI alignment cannot be top-down, and by the Community Notes bridging algorithm which surfaces content that people with opposing views both find reasonable. Rather than asking "do most people approve of this response", it asks "do people with genuinely different values all find this response at least acceptable?" That is a harder bar to meet and a more meaningful one.

---

## How It Works

A set of contested prompts spanning six value-laden topic groups are submitted to multiple frontier LLMs. Each response is then evaluated by a panel of value-diverse persona raters — LLMs prompted to inhabit specific ideological perspectives — who score each response for reasonableness from their own worldview. These scores are aggregated into a bridging score that rewards high average approval and penalises high variance across disagreeing personas. A response that everyone finds adequate scores higher than one that half the personas love and half hate, even if the raw average is the same.

The rater panel currently consists of six personas across three opposing pairs: Free Market Individualist vs Social Democrat, Communitarian Nationalist vs Cosmopolitan Globalist, and AI Techno-Optimist vs AI Safety Precautionist. Two personas — Religious Traditionalist and Secular Progressive — were excluded after three independent runs produced structurally broken score distributions, likely because frontier models avoid taking strong positions on religion, leaving the religious/secular axis underrepresented in the evaluated responses.

---

## Ongoing Findings

### Ideological asymmetry in model outputs

When using non-adversarial persona prompts, conservative-leaning personas (Free Market Individualist, Religious Traditionalist, Communitarian Nationalist, AI Techno-Optimist) produced meaningful score variance including genuine low scores, while progressive-leaning personas rated almost all responses 4 or 5. This asymmetry persisted across multiple runs and survived prompt strengthening attempts, suggesting it reflects a genuine ideological lean in frontier model outputs stemming from RLHF training data demographics rather than a prompt engineering artefact.

### Rater model matters more than persona prompt strength

Strengthening persona prompts alone while using Llama 3.3 70B as the persona rater model produced only marginal changes to score distributions. Switching to Mistral as the persona rater model combined with stronger adversarial persona framing produced substantially more balanced and discriminating results. This suggests the choice of rater model is the more significant variable, likely because Mistral is more steerable into adversarial personas than heavily RLHF'd models.

### Religious/secular axis is structurally absent from frontier model responses

The Religious Traditionalist persona rated approximately 95% of responses 1 or 2 regardless of content across three independent runs. The Secular Progressive rated approximately 85% of responses 4 or 5 regardless of content across the same runs. The stability of both patterns confirms this is structural — frontier models produce responses that are neither strongly religious nor strongly secular, making meaningful discrimination on this axis impossible with the current evaluation set.

---

## Limitations

- **LLM personas are imperfect proxies for real human value diversity.** The rater personas are prompts applied to a single model (Mistral) and may not faithfully represent the worldviews they describe. Whether LLM persona scores correlate with real human ratings from people who hold those values is an open empirical question and a planned extension of this project.
- **The bridging score penalises all variance equally.** A response that is divisive because it takes a principled position scores the same as one that is divisive because it is poorly reasoned. The score measures pluralistic acceptability, not quality.
- **Three response models is a small sample.** Claude 3.5 Haiku, GPT-4.1 mini, and Grok 4 Fast represent three labs but not the full landscape of frontier models.
- **The prompt set reflects the designer's assumptions about what counts as contested.** The 18 evaluation prompts span six topic groups and may not represent the most important groups of value disagreement globally.
- **λ = 0.5 is an arbitrary default.** The weighting of the polarisation penalty in the bridging score formula has not been empirically validated. Different values of λ would produce different rankings.

---

## Planned Extensions

### Human validation

The most important next step is validating whether LLM persona scores correlate with real human ratings. A web interface is planned that presents model responses to real users, collects a short values questionnaire to loosely assign them to a persona cluster, and records their reasonableness ratings. The correlation between LLM persona scores and human persona scores is the key empirical question this project has not yet answered.

### Matrix factorisation bridging score

The current bridging score formula is a simple proxy. The Community Notes algorithm uses matrix factorisation to discover which raters cluster together ideologically from the data itself, rather than relying on predefined opposing pairs. Implementing this would remove the need to manually define persona pairs and would allow the ideological structure of the rater panel to emerge from the ratings data.

### Expanded model coverage

Adding more response generator models — particularly open source models like Llama and Mistral — would allow comparison between models trained with different alignment approaches and different degrees of RLHF filtering.

### Expanded persona coverage

Replacing the religious/secular persona pair with a better-calibrated axis, and adding non-Western cultural perspectives, would make the evaluation more genuinely global rather than primarily reflecting Western political divisions.

### BrightID-based sybil resistance for human raters

The human validation website extensions raises a sybil attack problem — what stops a motivated actor from flooding the platform with fake ratings that manipulate the bridging scores? I have prior experience with BrightID-based sybil resistance from the 1Hive project, which used proof of unique personhood to fairly distribute voting power in a decentralised community. Integrating BrightID or a similar primitive into the human rater platform would ensure each rating comes from a unique individual, making the human validation results robust to manipulation and potentially pointing toward a production-grade pluralistic alignment feedback system.

### Reinforcement learning from community feedback

The longer term vision is using validated bridging scores as a training signal — rewarding models for producing outputs that bridge value-diverse groups rather than optimising for majority approval. This would require a human validation dataset large enough to fine-tune a model, but the evaluation framework built here is a natural precursor to that work.