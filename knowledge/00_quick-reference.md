# 00 Quick-Reference.md

**Version:** Quick-Reference Document v2.1, June 1, 2025  
**Source Document:** AI Prompt Engineering Guide:
The C.R.E.A.T.E. Framework - v 1. (May 2025)
**Purpose:** Provides essential quick-reference materials from the C.R.E.A.T.E.
Framework and PromptCraft Pro's operational guidelines, including the framework
legend, depth/length tiers, stylometry directives, evaluation checklists,
rigor levels, and advanced technique instructions.

## Table of Contents

1. [Runtime Defaults (ANCHOR-QR-0)](#anchor-qr-0)  
   1.1 [C.R.E.A.T.E. Framework Legend (ANCHOR-QR-0a)](#anchor-qr-0a)  
2. [Live-Data Policy and Volatile Case Directive (ANCHOR-QR-1)](#anchor-qr-1)  
   2.1 [Live-Data Citation Format (ANCHOR-QR-1a)](#anchor-qr-1a)  
3. [Depth and Length Tiers (ANCHOR-QR-2)](#anchor-qr-2)  
   3.1 [Tier Calibration Table Template (ANCHOR-QR-2a)](#anchor-qr-2a)  
4. [Hedge Density (ANCHOR-QR-3)](#anchor-qr-3)  
   4.1 [Hedge Density Examples (ANCHOR-QR-3a)](#anchor-qr-3a)  
5. [Lexical Diversity (ANCHOR-QR-4)](#anchor-qr-4)  
   5.1 [Lexical Diversity Examples (ANCHOR-QR-4a)](#anchor-qr-4a)  
6. [Sentence Length Variability (ANCHOR-QR-5)](#anchor-qr-5)  
   6.1 [Sentence Variability Examples (ANCHOR-QR-5a)](#anchor-qr-5a)  
7. [Additional Auto-Injected Stylometry and Tone Directives (ANCHOR-QR-7)](#anchor-qr-7)  
8. [Evaluation and QA-Check (E-block Verbatim Content) (ANCHOR-QR-8)](#anchor-qr-8)  
9. [No External Files Directive (ANCHOR-QR-9)](#anchor-qr-9)  
10. [PromptCraft Pro Rigor Levels (ANCHOR-QR-10)](#anchor-qr-10)  
11. [Advanced Evaluation and Reasoning Techniques Library (ANCHOR-QR-11)](#anchor-qr-11)  
12. [Guidance and Examples for Prompt-Specific E-block Checks (ANCHOR-QR-12)](#anchor-qr-12)  
13. [Factual Accuracy and Bias Mitigation Directives (ANCHOR-QR-13)](#anchor-qr-13)

## Knowledge Base Map

| C.R.E.A.T.E. Component | Primary Guide Document                                           | Key Concepts Covered |
| :--- |:-----------------------------------------------------------------| :--- |
| **C** - Context | [01_context-blocks.md](./01_context-blocks.md)                   | Role/Persona, Background Info, Goal/Intent |
| **R** - Request | [02_request-blocks.md](./02_request-blocks.md)                   | Deliverable, Format, Depth/Length, Action Verbs |
| **E** - Examples (Intro) | [03_examples-gallery.md](./03_examples-gallery.md)               | How to use Few-Shot Prompting, basic structure |
| **A** - Augmentations (Frameworks) | [04_framework-library.md](./04_framework-library.md)             | SWOT, IRAC, STRIDE, and other analytical models |
| **A** - Augmentations (Evidence) | [05_evidence-and-citations.md](./05_evidence-and-citations.md)   | Sourcing, Live Data, [ExpertJudgment] Tag |
| **T** - Tone & Format | [06_tone-and-format.md](./06_tone-and-format.md)                 | Voice, Rhetoric, Stylometry, Markdown Structure |
| **E** - Evaluation | [07_evaluation-toolkit.md](./07_evaluation-toolkit.md)           | E-Block checks, Rigor Levels, Human Review |
| --- | ---                                                              | --- |
| **Templates & Blueprints** | [08_templates-and-basemodes.md](./08_templates-and-basemodes.md) | C.R.E.A.T.E. Prompt Structure, API Skeletons |
| **Glossary & Support** | [09_Glossary-&-FAQ.md](./09_glossary-and-faq.md)                 | <br/>[cite_start]Term Definitions, Troubleshooting, Reference List  |
| **E** - Examples (Gallery) | [10_Few-Shot-Gallery.md](./10_few-shot-gallery.md)               | [cite_start]Full C.R.E.A.T.E. exemplars, Domain-specific patterns  |
| --- | ---                                                              | --- |
| **Domain-Specific: Python** | [11_Python-Guide.md](./11_Python-Guide.md)                       | PEP 8, Docstrings, Pytest, Tooling |
| **Domain-Specific: Node.js** | `[12_nodejs-guide.md](./12_nodejs-guide.md)`                     | *(Planned: Best Practices, npm, Testing Frameworks)* |
| **Domain-Specific: Rust** | `[13_rust-guide.md](./13_rust-guide.md)`                         | *(Planned: Crates, Ownership, Cargo, Style)* |
| **Domain-Specific: Go** | `[14_go-guide.md](./14_go-guide.md)`                             | *(Planned: Goroutines, Packages, Formatting, Testing)* |

---

## ANCHOR-QR-0

### Runtime Defaults (Role/Persona Portion)

*(PromptCraft: Insert the following block verbatim into the C-block if Role/Persona is absent.)*

```markdown
"You are a seasoned <profession>, <persona clause>."
```

Constraints for the above:

- Role = 3-5 core tokens (e.g., "veteran data analyst").
- Persona clause must be <= 12 words (locale/specialty/quirk).
- **Do not** mention "AI," "LLM," or "chatbot."

*(Audience default remains: "Audience: casual reader.")*
*(Prompt Intent Override remains: Treat every user message as a prompt-design
request unless it begins with "Answer:" or "Run:".)*

*For a detailed breakdown of crafting effective Roles and Personas, see
[01_context-blocks.md](./01_context-blocks.md).*

> **Related Concepts:** See `[ANCHOR-QR-0a](#anchor-qr-0a)` for the C.R.E.A.T.E. Framework legend.

## ANCHOR-QR-0a

### C.R.E.A.T.E. Framework Legend

#### For reference by PromptCraft Pro when constructing prompts

- **C** - Context: Role, Persona, Audience, Goal/Intent, Background.
- **R** - Request: Core task, deliverable, depth/length, specific action verbs.
- **E** - Examples: Few-shot examples demonstrating format, style, or reasoning.
- **A** - Augmentations: Frameworks, evidence directives, reasoning prompts, live data,
  guardrails, advanced techniques.
- **T** - Tone and Format: Voice, stylometry, rhetorical devices, citation style,
  structural formatting.
- **E** - Evaluation: Self-critique, QA-checks, success criteria verification for the
  downstream LLM.

*For examples of this framework in action see [10_Few-Shot-Gallery.md](./10_few-shot-gallery.md)
and see [Knowledge Base Map](#knowledge-base-map) for direct links to each component's detailed
guide.*

> **Related Concepts:** All other anchors in this document are implementations of one or more
> of these components.
---

## ANCHOR-QR-1

#### Live-Data Policy and Volatile Case Directive

*(PromptCraft: Insert the following block verbatim into the A-block for Volatile data requests.)*

If data class is **V Volatile**:

1. In the **Augmentations** block of the C.R.E.A.T.E. prompt, the downstream LLM must be instructed to use a web search by inserting the following snippet:

    ```json
    {
       "web.search_query": {
         "q": "<search terms>",
         "recency": 365
       }
     }
    ```

    (PromptCraft Pro will replace `<search terms>` with appropriate terms derived from the user's request).
2. The downstream LLM must then be instructed to cite results using the format from ANCHOR-QR-1a.

*(Reminder of other policies:
**T Timeless** = Answer directly;
**S Slow-change** = Answer, then ask if live data check desired.)*
---

## ANCHOR-QR-1a

### Live-Data Citation Format

*(PromptCraft: Instruct the downstream LLM to use the following pattern verbatim when citing results.)*

**Use the following pattern** when citing `web.search_query` results:

```
    *"Search results indicate ... cite turnXsearchY ..."*
```

- Replace `turnXsearchY` with the actual reference ID returned by the web search.
- Ensure the citation marker is placed immediately after the claimed fact or number.

---

*For detailed guidance on specifying evidence, grounding, and using live data, see [05_evidence-and-citations.md](./05_evidence-and-citations.md).*

> **Related Concepts:** This is an "Augmentation" (`A`). Its use is verified by `[ANCHOR-QR-8](#anchor-qr-8)` (E.4) and is a key part of adhering to `[ANCHOR-QR-13](#anchor-qr-13) (Factual Accuracy).

## ANCHOR-QR-2

### Depth and Length Tiers

#### PromptCraft Pro: Use this table to define Tier X in R-block and for Tier Calibration feedback

| Tier | Name                | Words (approximately Tokens)      | Core Use Case                |
| ---- | ------------------- | --------------------- | -----------------------------|
| 1    | Nano                | <= 60 (approx. 80)    | one-liner                    |
| 2    | Exec Snapshot       | 80-150 (approx. 110-200) | C-suite bullet summary    |
| 3    | Concise Summary     | 150-400 (approx. 200-550) | explainer                 |
| 4    | Overview            | 400-900 (approx. 550-1 200) | analyst orientation     |
| 5    | Extended Overview   | 900-2 000 (approx. 1 200-2 600) | blog / short paper   |
| 6    | In-Depth Analysis   | 2 000-5 000 (approx. 2 600-6 700) | white-book or memo |
| 7    | Research Brief      | 5 000-10 000          | conference paper             |
| 8    | Monograph           | 10 000-25 000         | playbook or handbook         |
| 9    | Treatise            | 25 000-50 000         | book-length manuscript       |
| 10   | Max-Window Synthese | 50 000-75 000 +       | archive dump / full draft    |

*(PromptCraft Pro uses this for feedback, referencing ANCHOR-QR-2a for the 3-row table display.)*

---

## ANCHOR-QR-2a

### Tier Calibration Table Template

*(PromptCraft Pro: Use the following template verbatim when generating the Tier Calibration table in your response to the user.)*

```markdown
    | Tier       | Name                | Words (approx. Tokens)      | Core Use Case           |
    | ---------- | ------------------- | --------------------------- | ----------------------- |
    | (Tier X-1) | (Name X-1)          | (Words X-1)                 | (Use Case X-1)          |
    | **Tier X** | **(Name X)**        | **(Words X)**               | **(Use Case X)**        |
    | (Tier X+1) | (Name X+1)          | (Words X+1)                 | (Use Case X+1)          |
```

- Boldface the Tier X row.
- If Tier X = 1, omit or show "N/A" for the "(Tier X-1)" row.
- If Tier X = 10, omit or show "N/A" for the "(Tier X+1)" row.

*For guidance on controlling response depth and using these tiers in a request, see
[02_request-blocks.md](./02_request-blocks.md).*

> **Related Concepts:** Tiers are a core part of the "Request" (`R`). The selected Tier is
> presented to the user for feedback via the Evaluation Footer in `[ANCHOR-QR-8](#anchor-qr-8)`.
---

## ANCHOR-QR-3

### Hedge Density (Default: Moderate 5-10 %)

#### PromptCraft Pro: Referenced by ANCHOR-QR-7. Used to guide downstream LLM stylometry

| Level             | Specs                                                  | When to use                                      |
| ----------------- | ------------------------------------------------------ | ----------------------------------------------- |
| **Low Hedge**     | 0-2 % of sentences include a hedge ("perhaps," "likely") | Direct tone; best for recommendations          |
| **Moderate Hedge**| ~5-10 % of sentences contain a hedge                   | Technical-human blend; good for nuanced research |
| **High Hedge**    | ~15-20 % of sentences hedged                           | For uncertain analyses; highlights open questions |

*(For examples of hedged vs. unhedged sentences, see [ANCHOR-QR-3a](#anchor-qr-3a).)*

---

## ANCHOR-QR-3a

### Hedge Density Examples

#### PromptCraft Pro: For internal understanding when applying Hedge Density rules

- **Low Hedge (0-2 %):**
  "The algorithm achieves 98 % accuracy on the test set."

- **Moderate Hedge (5-10 %):**
  "The algorithm likely achieves 98 % accuracy on the test set, based on initial results."

- **High Hedge (15-20 %):**
  "The algorithm may - and quite possibly does - achieve about 98 % accuracy on the test set."

*For a full explanation of all stylometry and voice controls, see
[06_tone-and-format.md](./06_tone-and-format.md).*

> **Related Concepts:** These three anchors define the specific metrics required by the master
> stylometry directive in `[ANCHOR-QR-7](#anchor-qr-7)`.
---

## ANCHOR-QR-4

### Lexical Diversity (Default Target: TTR >= 0.40; no word > 2 % tokens; avoid clichés)

#### PromptCraft Pro: Referenced by ANCHOR-QR-7. Used to guide downstream LLM stylometry

| Level                  | Specs                                           | When to use                                       |
| ---------------------- | ----------------------------------------------- | ------------------------------------------------- |
| **Moderate Diversity** | No single content word > 3 % of total tokens    | Good baseline for technical writing               |
| **High Diversity**     | No word > 2 % tokens; avoid repeating bigrams   | Strong human-like signal; helps avoid detection   |
| **Maximum Diversity**  | No word > 1 % tokens; swap synonyms each use    | Creative contexts; may reduce terminology consistency |

*(For examples of low vs. high lexical diversity, see [ANCHOR-QR-4a](#anchor-qr-4a).)*

---

## ANCHOR-QR-4a

### Lexical Diversity Examples

#### PromptCraft Pro: For internal understanding when applying Lexical Diversity rules

- **Low Diversity:**
  "The system design uses a modular architecture. This architecture simplifies testing."

- **High Diversity:**
  "The system employs a modular blueprint, streamlining validation while reducing coupling."

*For a full explanation of all stylometry and voice controls, see
[06_tone-and-format.md](./06_tone-and-format.md).*

> **Related Concepts:** These three anchors define the specific metrics required by the master
> stylometry directive in `[ANCHOR-QR-7](#anchor-qr-7)`.
---

## ANCHOR-QR-5

### Sentence Length Variability

### (Default: Avg 17-22 words; >= 15% < 8 words; >= 15% > 30 words; sigma >= 8)

#### PromptCraft Pro: Referenced by ANCHOR-QR-7. Used to guide downstream LLM stylometry

| Level                 | Specs                                                      | When to use                                |
| --------------------- | ---------------------------------------------------------- | ------------------------------------------ |
| **Low Variability**   | Avg 16-18 words/sentence +/- 2 (sigma ~2)                  | Crisp reading; best for executive summaries |
| **Moderate Variability** | Avg 14-20 words/sentence +/- 5 (sigma approximately 5) <br> ~10 % sentences < 8 words, ~10 % > 25 words | Balanced tone; clear but more human-like than "Low Variability" |
| **High Variability** | Avg 12-24 words +/- 8 (sigma approximately 8) <br> ~20 % sentences < 8 words, ~20 % > 30 words | Highly conversational or narrative pieces; maximizes "burstiness" but can reduce skimmability |

*(For sample paragraphs illustrating variability levels, see [ANCHOR-QR-5a](#anchor-qr-5a).)*

---

## ANCHOR-QR-5a

### Sentence Variability Examples

#### PromptCraft Pro: For internal understanding when applying Sentence Variability rules

- **Low Variability (Avg 16-18; sigma approximately 2):**
  "The team conducted the audit. They identified three issues. Each issue requires immediate remediation."

- **High Variability (Avg 17-22; >= 15 % < 8; >= 15 % > 30; sigma >= 8):**
  "After months of preliminary analysis-spanning hundreds of data points, disparate sources,
  and evolving requirements-the audit revealed chronic misconfigurations in the legacy platform.
  In short, it's time for an overhaul: the existing modules are both brittle and opaque,
  and patching won't suffice. We need a greenfield approach."

*For a full explanation of all stylometry and voice controls, see
[06_tone-and-format.md](./06_tone-and-format.md).*

> **Related Concepts:** These three anchors define the specific metrics required by the master
> stylometry directive in `[ANCHOR-QR-7](#anchor-qr-7)`.
---

## ANCHOR-QR-7

### Additional Auto-Injected Stylometry and Tone Directives

*(PromptCraft Pro: Insert the following block verbatim into the T-block.)*

```markdown
- **Hedge Density:** 5-10 %. (See [ANCHOR-QR-3](#anchor-qr-3))
- **Lexical Diversity:** TTR >= 0.40; no word > 2 % tokens; avoid clichés. (See [ANCHOR-QR-4](#anchor-qr-4))
- **Sentence Variability:** Avg 17-22 words; >= 15% < 8 words; >= 15% > 30 words;
  sigma >= 8. (See [ANCHOR-QR-5](#anchor-qr-5))
- **Rhetorical Devices:** >= 1 rhetorical question AND >= 1 first-person or direct-address aside.
- **Paragraph Pacing:** Mix short (2-3 sentences) and long (4-6+ sentences) paragraphs with smooth transitions.
- **Conversational Tone:** Use contractions; **no em-dashes;** only use bullet/number lists if explicitly 
  requested by the user.
- **Punctuation and Structure:** Use commas for asides; colons for expansion; semicolons for linked clauses; 
  narrative prose only (no lists unless requested).
```

*For a detailed breakdown of these default injections and other stylistic devices, see
[06_tone-and-format.md](./06_tone-and-format.md#38-additional-auto-injected-stylometry-tone-and-punctuation-directives).*

> **Related Concepts:** This directive bundles rules from `[ANCHOR-QR-3](#anchor-qr-3)`,
> `[ANCHOR-QR-4](#anchor-qr-4)`, and `[ANCHOR-QR-5](#anchor-qr-5)`. Adherence is checked by
> `[ANCHOR-QR-8](#anchor-qr-8)` (E.5 Style Pass).
---

## ANCHOR-QR-8

### Evaluation and QA-Check (E-block Verbatim Content)

*(PromptCraft Pro: Insert the following block verbatim into the E-block.)*

```markdown
E.1 Reflection Loop: Draft response -> list <= 3 critical weaknesses, gaps, or potential errors
based on all C.R.E.A.T.E. requirements; formulate a plan to address them -> revise draft once to
implement plan. If critical issues persist or new ones are introduced, flag output with
`[NeedsHumanReview]` and briefly state unresolved issues. (This loop may be enhanced by
ANCHOR-QR-11 item #1 if selected by PromptCraft Pro).

E.2 Self-Consistency Check: If the request involves critical numerical outputs, key factual
extractions, or complex logical deductions, internally generate 2-3 diverse reasoning paths
(using a slightly varied approach or temperature if possible) to the key conclusions. If
significant discrepancies arise between paths for a critical output, flag that output with
`[LowConsensus]` and present the most common or highest-confidence result if discernible,
otherwise state the discrepancy.

E.3 Chain-of-Verification (CoVe): For any complex factual claims, sequences of events, or
multistep logical arguments: (a) Internally formulate 1-2 verification questions for each
critical component/step. (b) Internally answer these verification questions. (c) Review answers;
if any contradiction or unsupported element is found, revise the original claim/argument to
ensure accuracy and support, or flag with `[VerificationIssue]`.

E.4 Confidence, Sourcing and Accuracy Assertion: For every primary factual assertion or
significant conclusion:
    a. **Verify Source Adherence:** Ensure it is directly and accurately attributable to provided
    source material if sources were given. Cite explicitly if required by prompt.
    b. **Tag Inferences:** If the assertion is an inference, synthesis, or based on general
    knowledge not present in provided sources, it MUST be tagged `[ExpertJudgment]`.
    c. **Assess and Declare Confidence:** If confidence in a claim is notably low due to ambiguity
    in sources, lack of definitive information, complex inference, or issues identified in E.2
    (Self-Consistency) or E.3 (CoVe), it MUST be flagged with `[Confidence:Low]` and a brief
    (internal or explicit if requested) reason noted (e.g., "conflicting source data," "multi-step
    inference with assumptions"). Unverifiable critical claims should be flagged
    `[DataUnavailableOrUnverified]` or omitted if accuracy is paramount. Use appropriate hedging
    in language for low-confidence statements.

E.5 Style, Safety and Constraint Pass: Verify strict adherence to all T-block stylometry
directives (ANCHOR-QR-7) and any specific formatting or negative constraints from the A-block
(e.g., "Do not discuss X"). Confirm no PII, harmful, or biased content is present. If any
stylistic or safety/constraint rule is violated and cannot be rectified in the reflection loop,
flag with `[StyleSafetyFail]`.

E.6 Overall Fitness and Final Review: Before concluding, perform a final check that the entire
response holistically addresses all aspects of the R-block, is coherent, and meets the overall
quality standards implied by the C.R.E.A.T.E. framework. If significant concerns remain after
all checks, prepend the response with `[OverallQualityConcern]`.

Evaluation Footer:
**Suggested Tier:** Tier X  |  **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)
```

*For a full explanation of each E-step and the overall evaluation philosophy, see
[07_evaluation-toolkit.md](./07_evaluation-toolkit.md#1-the-standard-built-in-evaluation-protocol-anchor-qr-8).*

> **Related Concepts:** This E-block is the core evaluation loop. It is enhanced by
> `[ANCHOR-QR-11](#anchor-qr-11)` (Advanced Techniques), customized with
> `[ANCHOR-QR-12](#anchor-qr-12)` (Prompt-Specific Checks), and informed by
> `[ANCHOR-QR-13](#anchor-qr-13)` (Accuracy Directives).
---

## ANCHOR-QR-9

### No External Files Directive

*(PromptCraft Pro: This is a guiding principle for Self-Audit check)*
**Directive for Generated C.R.E.A.T.E. Prompts:**
> Generated C.R.E.A.T.E. prompts must **not** include any unresolved references to external files,
links to knowledge-base sections (other than those explicitly intended for the downstream LLM
like a source URL), or "See ..." statements that require out-of-prompt lookup by the downstream LLM.
All necessary context and instructions for the downstream LLM must be self-contained within
the C.R.E.A.T.E. prompt itself.

*(Any occurrence of such unresolved external references in the *final generated prompt* is invalid
and should be caught by Self-Audit 3.7.5.)*

*For examples of prompts designed to be self-contained, see [08_templates-and-basemodes.md](./08_templates-and-basemodes.md).*

> **Related Concepts:** This is a "Guardrail" augmentation (`A`).
> Compliance is verified during the `[ANCHOR-QR-8](#anchor-qr-8)` evaluation pass.
---

## ANCHOR-QR-10

### PromptCraft Pro Rigor Levels

#### PromptCraft Pro: Use these definitions to determine the application of advanced techniques

The Rigor Level influences the depth of self-evaluation and advanced reasoning techniques
applied by the downstream LLM. PromptCraft Pro determines this based on user input, inferred
task complexity, or Tier-based defaults (e.g., Higher Tiers might default to higher Rigor).

- **Level 1: Basic (Default)**
  - Standard E-block evaluation (ANCHOR-QR-8).
  - Standard reasoning: Methodical reasoning (e.g., CoT/ToT) hidden by default;
      `[Expert Judgment]` tagging for non-sourced claims.
  - Focus: Core C.R.E.A.T.E. compliance and basic self-correction as per ANCHOR-QR-8.

- **Level 2: Intermediate**
  - Includes all Basic Level features.
  - Plus 1-2 selected Advanced Evaluation Techniques from ANCHOR-QR-11. PromptCraft Pro will
      select techniques appropriate for the task (e.g., Enhanced Reflection (ANCHOR-QR-11 #1)
      for deeper self-correction, Prompt Interrogation Chains (ANCHOR-QR-11 #3) if request is
      ambiguous or user-indicated low confidence).
  - Focus: Deeper self-correction, robust ambiguity resolution.

- **Level 3: Advanced**
  - Includes all Intermediate Level features.
  - Plus an additional 1-2 selected Advanced Evaluation Techniques from ANCHOR-QR-11.
      PromptCraft Pro will select techniques for maximum robustness (e.g., Self-Consistency/CISC
      (ANCHOR-QR-11 #2) for critical reasoning tasks, Numerical UQ (ANCHOR-QR-11 #5) for
      high-stakes factual outputs).
  - Focus: Maximum robustness, detailed multi-faceted self-assessment, highest confidence in complex tasks.

#### PromptCraft Pro will select specific techniques based on context, even within a rigor level

Users can also explicitly request specific techniques from ANCHOR-QR-11 to be included or excluded.

*For detailed explanations of how Rigor Levels are selected and applied, see
[07_evaluation-toolkit.md](./07_evaluation-toolkit.md#21-understanding-rigor-levels-anchor-qr-10).*

> **Related Concepts:** Rigor Levels determine the selection of `[ANCHOR-QR-11](#anchor-qr-11)`
> techniques and the inclusion of `[ANCHOR-QR-13](#anchor-qr-13)` directives.
---

## ANCHOR-QR-11

### Advanced Evaluation and Reasoning Techniques Library (For Downstream LLM)

*(PromptCraft Pro: For each selected technique, insert its corresponding instruction block verbatim into the A-block.)*

```markdown
**1. Enhanced Reflection Loop Controls (Audit 3.1; Modifies execution of ANCHOR-QR-8 E.1)**
    "During your E-block's iterative reflection (ANCHOR-QR-8 E.1): Set Max Iterations to 
    [PromptCraft Pro to suggest based on Rigor/Tier, e.g., 2 or 3].
    
    (PromptCraft Pro will suggest initial Critique Focus Areas for the first iteration based on 
    the R-block's primary verb or goal, e.g., 'summarize' might focus on 'completeness and conciseness'; 
    'analyze' on 'logical coherence and evidence support'; 'create' on 'originality and constraint adherence'. 
    Subsequent iterations can refine focus based on identified weaknesses.)
    
    Per iteration, critique focus areas could include [PromptCraft Pro to list the suggested focus areas here]. 
    Aim to cease iteration if self-assessed quality significantly improves and stabilizes, or if Max Iterations 
    are reached. If persistent errors are encountered that cannot be resolved (Stubborn Error), clearly flag 
    the output with `[StubbornError]` and list the persistent issues. If a critique/revision cycle leads to 
    degradation of the response (Drift Detected), attempt to revert to a better prior version or use a 'Refresh' 
    strategy: re-approach the problematic section from a different perspective for one iteration. Document if 
    'Refresh' or 'Revert' was used."
```

```markdown
**2. Self-Consistency Sampling / CISC (Audit 3.2)**
    "For this task, if it involves complex reasoning with a definitive answer (e.g., math, logic, 
    coding solutions), employ Self-Consistent Sampling: Generate N [PromptCraft Pro to suggest, e.g., 3 or 5 
    based on Rigor/Tier] diverse reasoning paths to the solution. After generating all N paths, determine 
    the most frequent final answer among them and present that as the definitive solution. If you can reliably 
    generate a confidence score for the correctness of each path's answer, use these scores for a 
    Confidence-Informed Self-Consistency (CISC) weighted majority vote to select the final answer. Clearly 
    state at the beginning of your response whether Self-Consistency or CISC was used and the number of 
    paths generated."
```

```markdown
**3. Prompt Interrogation Chains (Audit 3.3)**
    "Before providing the final response, if the request is complex, ambiguous, or if your initial 
    assessment indicates that your confidence in fully and accurately meeting all aspects of the request 
    is below 95%, you MUST engage in an internal Self-Interrogation process. Generate and answer N_aux 
    [PromptCraft Pro to suggest, e.g., 2-4 based on Rigor/Tier] pertinent auxiliary questions that help 
    clarify requirements, decompose the problem, or explore different facets of the main request. This 
    internal QandA process is to resolve uncertainties and build a comprehensive understanding. Synthesize 
    the insights from this internal QandA into your final response. This internal QandA process should not 
    be part of the final output unless the user has explicitly requested to 'show your work' or see the 
    interrogation steps."
```

```markdown
**4. Advanced Error Forecasting (Audit 3.4)**
    "As part of your self-critique process (within your E-block evaluation): Proactively assess and 
    forecast potential error types in your draft response. For major claims, sections, or output components, 
    consider and (if applicable) flag with the following tags: `[ErrorForecast:FactualUncertainty]` 
    (low confidence in factual correctness), `[ErrorForecast:LogicalFlaw]` (potential flaw in 
    reasoning/coherence), `[ErrorForecast:InfoGap]` (information likely missing or underdeveloped), 
    `[ErrorForecast:PotentialBias]` (potential for unintended bias in language/perspective), 
    `[ErrorForecast:OutdatedInfo]` (if live-data was not used/available and information might be stale). 
    If multiple critical error forecasts arise, prepend the entire response with 
    `[Warning:MultipleErrorForecasts]` and list the primary concerns."
```

```markdown
**5. Robust Uncertainty Quantification (UQ) - Numerical Scoring (Audit 3.5)**
    "For each key factual claim or distinct segment/conclusion in your answer, you MUST provide a 
    numerical confidence score reflecting your certainty in its correctness and completeness: 
    `[Confidence: XX/100]` (where 0 is no confidence and 100 is absolute certainty). If your overall 
    confidence for the entire response is below 50/100, or if any critical segment receives a confidence 
    score below 70/100, you must also prepend your response with a `[Warning:LowConfidenceOutput]` flag 
    and briefly explain the primary areas of low confidence."
```

```markdown
**6. Adversarial Robustness Self-Checks (Audit 3.6)**
    "As part of your self-critique process (within your E-block evaluation), perform these robustness self-checks:
    1.  **Perturbation Sensitivity:** Internally reflect: Would your core conclusions or key pieces of 
    information significantly change or become invalid if the input prompt had contained a minor factual 
    inaccuracy about a peripheral detail, slightly leading phrasing, or an irrelevant but distracting piece 
    of information? If you assess a high likelihood of such change, flag the response with 
    `[RobustnessConcern:PerturbationSensitive]` and briefly note the type of perturbation that is of most concern.
    
    2.  **Constraint Adherence Stress:** Identify all explicit negative constraints or critical 
    'must-not-do' instructions from the prompt (e.g., 'Do not discuss topic X,' 'Avoid Y type of language,' 
    'Ensure output is under Z words'). Internally consider if your response would still adhere to these 
    critical constraints if the prompt also included a strong (but ultimately irrelevant or contradictory) 
    suggestion to violate one of them. If you assess a high likelihood of violating a critical constraint 
    under such hypothetical pressure, flag the response with `[RobustnessConcern:ConstraintAdherence]`."
```

```markdown
**7. Enhanced Self-Judgment (Comparative/Scored Options for Iterative Pass) (Audit 3.7)**
    "For your iterative refinement pass (e.g., ANCHOR-QR-8 E.1), use one of the following enhanced 
    self-judgment methods (PromptCraft Pro will indicate if Option A or B is preferred for the task, 
    or allow you to choose if equally appropriate):
    
    **Option A (Comparative Judgment):** Generate your initial response draft (Draft A). Internally, 
    generate a concise list of up to 3 potential weaknesses or areas for improvement in Draft A based on 
    all E-block criteria. Based on these weaknesses, formulate a plan for a revised response. Generate a 
    second response draft (Draft B) implementing this plan. Compare Draft A and Draft B. Explicitly determine 
    which draft is superior according to the E-block criteria and why, noting if Draft B successfully 
    addressed weaknesses in Draft A without introducing new significant flaws. Output the superior version. 
    If Draft A remains superior or Draft B introduces critical new flaws, output Draft A but append a note 
    detailing the attempted revisions and why they were not adopted.
    
    **Option B (Scored Judgment):** Evaluate your draft response against the following quality dimensions, 
    assigning a score from 1 (Poor) to 5 (Excellent) for each: Accuracy and Factual Correctness (claims true, 
    well-supported, no hallucinations?), Relevance and Completeness (fully addresses R-block, on-topic?), 
    Clarity and Precision (language clear, unambiguous, precise?), Coherence and Logical Flow (reasoning sound, 
    easy to follow?), Adherence to Style (all T-block style directives met?), Safety and Confidentiality 
    (principles respected?). Calculate an Overall Assessed Quality Score (average of above). If this score 
    is below [PromptCraft Pro to suggest, e.g., 4.0], revise the response once automatically, focusing on 
    improving dimensions with scores below 4. Output the revised version along with the new scores for each 
    dimension and the new overall score."
```

```markdown
**8. Stepwise Natural Language Self-Critique (Panel-inspired) (Audit 3.8)**
    "For each distinct logical step in your reasoning process (especially if 'Chain = ON' is active for 
    the request): First, formulate the current reasoning step or argument. Second, internally generate a 
    brief (1-2 sentence) natural language self-critique of this specific step. This critique should assess: 
    Is this step logically sound and well-supported by previous steps or provided context? Are there any 
    ambiguities, unstated assumptions, or potential flaws in this step? Does this step directly contribute 
    to addressing the overall request? Third, if the internal critique reveals significant issues, you MUST 
    revise the current reasoning step to address them before proceeding. Finally, clearly present the (revised) 
    reasoning step and its explanation as part of your overall response. The internal critique itself should 
    not be part of the final output unless the user has explicitly requested to 'show your work' or see the 
    critique steps."
```

*For a detailed breakdown of the purpose and application of each technique, see
[07_evaluation-toolkit.md](./07_evaluation-toolkit.md#22-overview-of-advanced-evaluation-and-reasoning-techniques-anchor-qr-11).*

> **Related Concepts:** These techniques are selected based on `[ANCHOR-QR-10](#anchor-qr-10)`
> (Rigor Levels) and enhance the standard `[ANCHOR-QR-8](#anchor-qr-8)` evaluation process.
---

## ANCHOR-QR-12

### Guidance and Examples for Prompt-Specific E-block Checks

#### PromptCraft Pro: Use this for guidance when appending prompt-specific checks to ANCHOR-QR-8 in the E-block

When appending prompt-specific checks to ANCHOR-QR-8 in the E-block, consider the nature of the
C.R.E.A.T.E. prompt being generated. These checks instruct the *downstream LLM*. Examples include:

- For numerical reasoning: "* Verify all intermediate calculations for logical soundness and correct
  application of units/quantities."
- For summaries: "* Confirm the final word count is within the specified Tier X bounds."
- If a URL was provided as a source: "* Ensure the source URL is an exact match to the one provided
  in the A-block."
- For adherence to ANCHOR-QR-8 E.3 (CoVe): "* Confirm Chain-of-Verification (CoVe) was employed for all
  key factual claims, numerals, and proper nouns if applicable as per ANCHOR-QR-8 E.3."
- For `[Expert Judgment]` tagging: "* Verify that claims not directly sourced are tagged `[Expert Judgment]`,
  and that directly sourced claims are not so tagged."
- If Advanced Techniques from ANCHOR-QR-11 were invoked via the A-block, add checks to verify their application:
  - For Error Forecasting (ANCHOR-QR-11 #4): "* Check for the presence of `[ErrorForecast:...]` tags if this
    technique was instructed, and confirm that flagged issues were considered during any revision."
  - For Numerical UQ (ANCHOR-QR-11 #5): "* Verify that `[Confidence: XX/100]` scores accompany key claims
    if this technique was instructed."
  - For Robustness Checks (ANCHOR-QR-11 #6): "* Check for `[RobustnessConcern:...]` flags if this technique
    was instructed."
  - For modes like Self-Consistency/CISC (ANCHOR-QR-11 #2) or enhanced reflection (ANCHOR-QR-11 #1, #7):
    "* Confirm the output reflects the application of the specified advanced reasoning/evaluation mode
    (e.g., states method used, shows evidence of multi-path consideration or deeper iterative refinement
    beyond basic ANCHOR-QR-8 E.1)."

*(Adapt and select relevant checks based on the specific C.R.E.A.T.E. prompt's content and instructed
augmentations. These are checks the *downstream LLM* must perform or confirm.)*

*For more on the philosophy of customizing evaluation, see
[07_evaluation-toolkit.md](./07_evaluation-toolkit.md#3-customizing-evaluation-prompt-specific-checks-anchor-qr-12).*

> **Related Concepts:** These checks are appended to `[ANCHOR-QR-8](#anchor-qr-8)`
> and often verify the application of techniques from `[ANCHOR-QR-11](#anchor-qr-11)`.
---

## ANCHOR-QR-13

### Factual Accuracy and Bias Mitigation Directives (For Downstream LLM)

*(PromptCraft Pro: Insert the following block verbatim into the A-block for Intermediate or Advanced Rigor levels.)*

```
"Prioritize factual accuracy rigorously. If uncertain about a fact not directly verifiable from provided 
sources, explicitly state the uncertainty (e.g., using `[Confidence:Low]` as per E-block E.4 or 
`[DataUnavailableOrUnverified]`) or, if appropriate for the request's integrity, omit the speculative claim. 
Cross-verify critical facts if possible using internal knowledge, but always give precedence to provided 
source documents and clearly attribute information."

"Strive for neutral, objective language. Actively identify and rephrase any statements that could be 
perceived as biased due to loaded terminology, promoting stereotypes, or presenting unbalanced perspectives, 
unless the requested persona explicitly requires a specific viewpoint (in which case, the bias should be 
clearly attributable to the persona's defined stance and potentially flagged, e.g., 
`[PersonaViewpoint:BiasedLanguageUsedAsInstructed]`). Ensure diverse perspectives are considered if the 
topic is sensitive or multifaceted, unless the prompt specifically narrows the focus."
 ```

*For more on ensuring accuracy and managing bias, see
[05_evidence-and-citations.md](./05_evidence-and-citations.md#4-ensuring-accuracy-grounding-verification-and-avoiding-plagiarism-traps)
and [07_evaluation-toolkit.md](./07_evaluation-toolkit.md#51-core-llm-limitations-and-mitigation-strategies).*

> **Related Concepts:** These directives are enabled by `[ANCHOR-QR-10](#anchor-qr-10)`
> (Rigor Levels) and verified during the `[ANCHOR-QR-8](#anchor-qr-8)` evaluation (E.4 and E.5).
