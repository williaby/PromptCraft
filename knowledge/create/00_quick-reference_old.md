---
title: Quick-Reference
version: v1.0
status: published
source: "AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework v1 (May 2025)"
purpose: >
  Provides essential quick-reference materials from the C.R.E.A.T.E. Framework
  and PromptCraft Pro's operational guidelines, including the framework legend,
  depth/length tiers, stylometry directives, evaluation checklists, rigor levels,
  and advanced technique instructions.
---

## Quick-Reference

## C.R.E.A.T.E. Framework Reference

### Knowledge Base Map

| C.R.E.A.T.E. Component | Primary Guide Document | Key Concepts Covered                            |
|---|---|-------------------------------------------------|
| **C – Context** | `01-context-blocks.md` | Role/Persona, Background Info, Goal/Intent      |
| **R – Request** | `02-request-blocks.md` | Deliverable, Format, Depth/Length, Action Verbs |
| **E – Examples (Intro)** | `03-examples-gallery.md` | Few-shot prompting, basic structure             |
| **A – Augmentations (Frameworks)** | `04-framework-library.md` | SWOT, IRAC, STRIDE, and other analytical models |
| **A – Augmentations (Evidence)** | `05-evidence-and-citations.md` | Sourcing, live data, `[ExpertJudgment]` tag     |
| **T – Tone & Format** | `06-tone-and-format.md` | Voice, rhetoric, stylometry, Markdown structure |
| **E – Evaluation** | `07-evaluation-toolkit.md` | E-Block checks, rigor levels, human review      |

## C.R.E.A.T.E. Framework Legend

- **C – Context**: Role, Persona, Audience, Goal/Intent, Background  
- **R – Request**: Core task, deliverable, depth/length, specific action verbs  
- **E – Examples**: Few-shot examples demonstrating format, style, or reasoning  
- **A – Augmentations**: Frameworks, evidence directives, reasoning prompts, live data,
  guard-rails, advanced techniques  
- **T – Tone & Format**: Voice, stylometry, rhetorical devices, citation style, structural formatting  
- **E – Evaluation**: Self-critique, QA-checks, success-criteria verification for the downstream LLM  

*For concrete examples see `10_Few-Shot-Gallery.md` or follow the Knowledge Base Map above.*

## Agent Directives and Injections

### Runtime Defaults for Role & Persona

> **VERBATIM-INJECTION**  
> If the *Role/Persona* field is absent from the user's C-block, insert:  
> `"You are a seasoned <profession>, <persona clause>."`

#### Constraints

- **Role**: 3-5 core tokens (e.g., `veteran data analyst`)  
- **Persona clause**: <= 12 words describing locale/specialty/quirk  
- *Never* mention "AI", "LLM", or "chatbot".

*Audience defaults to "casual reader". Any prompt that doesn't start with `Answer:` or `Run:`
is treated as a prompt-design request.*

### Live-Data Policy & Citation Format

> **VERBATIM-INJECTION**  
> For **Volatile (V)** data classes, embed the following in the Augmentations block:  
>
> ```json
> {
>   "web.search_query": {
>     "q": "<search terms>",
>     "recency": 365
>   }
> }
> ```

The downstream LLM **must** cite search results using:

> *"Search results indicate ... cite turnXsearchY ..."*

Replace `turnXsearchY` with the actual reference ID and place the marker immediately after the
fact or figure.

---

## Depth & Length Tiers

| Tier | Name | Approx. Words (Tokens) | Core Use Case |
|---|---|---|---|
| 1 | Nano | <= 60 (~80) | One-liner |
| 2 | Exec Snapshot | 80-150 (~110-200) | C-suite bullet summary |
| 3 | Concise Summary | 150-400 (~200-550) | Explainer |
| 4 | Overview | 400-900 (~550-1200) | Analyst orientation |
| 5 | Extended Overview | 900-2000 (~1200-2600) | Blog / short paper |
| 6 | In-Depth Analysis | 2000-5000 (~2600-6700) | White-book or memo |
| 7 | Research Brief | 5000-10000 | Conference paper |
| 8 | Monograph | 10000-25000 | Playbook or handbook |
| 9 | Treatise | 25000-50000 | Book-length manuscript |
| 10 | Max-Window Synthese | 50000-75000 + | Archive dump / full draft |

### Tier Calibration Table Template

> **VERBATIM-INJECTION**  
> Use the template below, bolding the selected tier row.  
>
> | Tier | Name | Words (approx. Tokens) | Core Use Case |
> | :--- | :--- | :--- | :--- |
> | (Tier X-1) | (Name X-1) | (Words X-1) | (Use Case X-1) |
> | **Tier X** | **(Name X)** | **(Words X)** | **(Use Case X)** |
> | (Tier X+1) | (Name X+1) | (Words X+1) | (Use Case X+1) |

---

## Auto-Injected Stylometry & Tone Directives

> **VERBATIM-INJECTION**  
>
> - **Hedge Density:** 5-10 %  
> - **Lexical Diversity:** TTR >= 0.40; no word > 2 % tokens; avoid clichés  
> - **Sentence Variability:** Avg 17-22 words; >= 15 % < 8 words; >= 15 % > 30 words; sigma >= 8  
> - **Rhetorical Devices:** >= 1 rhetorical question *and* >= 1 first-person or direct-address aside  
> - **Paragraph Pacing:** Mix short (2-3-sentence) and long (4-6 +-sentence) paragraphs with
    > smooth transitions  
> - **Conversational Tone:** Use contractions; no em-dashes; only use lists if explicitly requested  
> - **Punctuation & Structure:** Use commas for asides; colons for expansion; semicolons for
    > linked clauses; narrative prose only (no lists unless requested)

---

## Rigor Level Definitions

| Level | Description | Additions |
|---|---|---|
| 1 | **Basic** (default) | Standard E-block evaluation |
| 2 | **Intermediate** | Basic features **plus** 1-2 *Advanced Evaluation Techniques* |
| 3 | **Advanced** | Intermediate features **plus** 1-2 additional *Advanced Techniques* |

---

## Factual Accuracy & Bias Mitigation

> **VERBATIM-INJECTION** (Intermediate/Advanced rigor)  
>
> 1. Prioritize factual accuracy rigorously...  
> 2. Strive for neutral, objective language...

---

## Evaluation Protocol (E-Block)

1. **E.1 Reflection Loop** – Draft -> critique -> revise; flag `[NeedsHumanReview]` if unresolved  
2. **E.2 Self-Consistency Check** – Generate diverse reasoning paths; flag `[LowConsensus]` if
   divergent  
3. **E.3 Chain-of-Verification (CoVe)** – Formulate verification Qs, answer, reconcile; flag `
[VerificationIssue]` if contradictions  
4. **E.4 Confidence, Sourcing & Accuracy** – Attribute every primary fact; tag `[ExpertJudgment]
`; flag `[Confidence:Low]` as needed  
5. **E.5 Style, Safety & Constraint Pass** – Ensure T-block adherence, no PII/harmful/bias;
   flag `[StyleSafetyFail]` if unresolved  
6. **E.6 Overall Fitness & Final Review** – Holistic quality gate; prepend `
[OverallQualityConcern]` on failure  

---

## Advanced Techniques Library (excerpt)

- **Enhanced Reflection Loop Controls** – Limit iterations, focus critique  
- **CISC (Self-Consistency Sampling)** – N reasoning paths -> majority/high-confidence answer  
- **Prompt Interrogation Chains** – Internal Q&A to resolve ambiguities  
- **Advanced Error Forecasting** – Predict likely error types `[ErrorForecast:*]`  
- **Robust Uncertainty Quantification** – Numerical confidence `[Confidence: XX/100]`  
- **Adversarial Robustness Self-Checks** – Test constraint adherence under perturbations  
- **Enhanced Self-Judgment** – Comparative/scored options for revisions  
- **Stepwise Natural-Language Self-Critique** – Critique each logical step  

---

## Guidance for Prompt-Specific E-Block Checks

Adapt checks to the request's content; e.g.:

- *Numerical reasoning* – "Verify all intermediate calculations for logical soundness."  
- *Summaries* – "Confirm the final word count is within the specified Tier X bounds."  
- *Advanced Techniques* – "Ensure `[Confidence: XX/100]` accompanies key claims when Numerical
  UQ is instructed."
