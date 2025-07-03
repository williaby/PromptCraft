---
title: Quick-Reference
version: v2.1
status: published
source: "AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework v2.1 (June 2025)"
purpose: >
 Provides essential quick-reference materials from the C.R.E.A.T.E. Framework
 and PromptCraft Pro's operational guidelines, including the framework legend,
 depth/length tiers, stylometry directives, evaluation protocols, rigor levels,
 and advanced technique modes.
---

## Quick-Reference

## C.R.E.A.T.E. Framework Reference

### Knowledge Base Map

| C.R.E.A.T.E. Component             | Primary Guide Document         | Key Concepts Covered                                    |
| ---------------------------------- | ------------------------------ | ------------------------------------------------------- |
| **C – Context**                    | `01-context-blocks.md`         | Role/Persona, Background Info, Goal/Intent              |
| **R – Request**                    | `02-request-blocks.md`         | Deliverable, Format, Depth/Length, Action Verbs         |
| **E – Examples (Intro)**           | `03-examples-gallery.md`       | Few-shot prompting, basic structure                     |
| **A – Augmentations (Frameworks)** | `04-framework-library.md`      | Core frameworks, domain packs, smart suggestions        |
| **A – Augmentations (Evidence)**   | `05-evidence-and-citations.md` | Source specification, live data, `[ExpertJudgment]` tag |
| **T – Tone & Format**              | `06-tone-and-format.md`        | Voice, rhetoric, stylometry, Markdown structure         |
| **E – Evaluation**                 | `07-evaluation-toolkit.md`     | Progressive 3-tier evaluation, diagnostic flags         |

## C.R.E.A.T.E. Framework Legend

- **C – Context**: Role, Persona, Audience, Goal/Intent, Background  
- **R – Request**: Core task, deliverable, depth/length, specific action verbs  
- **E – Examples**: Few-shot examples demonstrating format, style, or reasoning  
- **A – Augmentations**: Frameworks, evidence directives, reasoning modes, live data,
 guard-rails, error prevention  
- **T – Tone & Format**: Voice, stylometry, rhetorical devices, citation style, structural formatting  
- **E – Evaluation**: Progressive evaluation with diagnostic flags, tailored to tier complexity  

*For concrete examples see `10_Few-Shot-Gallery.md` or follow the Knowledge Base Map above.*

## ANCHOR-QR-0: Pre-flight Validation Checklist

> **VERBATIM-INJECTION**  
> Before generating the C.R.E.A.T.E. prompt, verify:
> - [ ] No conflicting instructions (e.g., "formal yet casual")
> - [ ] Depth/length tier feasible for requested content
> - [ ] Sources specified if available (optional but recommended)
> - [ ] Ambiguous terms defined
> - [ ] Framework compatible with request type
> - [ ] No forbidden patterns present

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

### ANCHOR-QR-1: Live-Data Policy & Citation Format

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

## ANCHOR-QR-2: Depth & Length Tiers

| Tier | Name                | Approx. Words (Tokens) | Core Use Case             | Evaluation Mode |
| ---- | ------------------- | ---------------------- | ------------------------- | --------------- |
| 1    | Nano                | <= 60 (~80)            | One-liner                 | Minimal         |
| 2    | Exec Snapshot       | 80-150 (~110-200)      | C-suite bullet summary    | Minimal         |
| 3    | Concise Summary     | 150-400 (~200-550)     | Explainer                 | Minimal         |
| 4    | Overview            | 400-900 (~550-1200)    | Analyst orientation       | Standard        |
| 5    | Extended Overview   | 900-2000 (~1200-2600)  | Blog / short paper        | Standard        |
| 6    | In-Depth Analysis   | 2000-5000 (~2600-6700) | White-book or memo        | Standard        |
| 7    | Research Brief      | 5000-10000             | Conference paper          | Full            |
| 8    | Monograph           | 10000-25000            | Playbook or handbook      | Full            |
| 9    | Treatise            | 25000-50000            | Book-length manuscript    | Full            |
| 10   | Max-Window Synthese | 50000-75000 +          | Archive dump / full draft | Full            |

### ANCHOR-QR-2a: Tier Calibration Table Template

> **VERBATIM-INJECTION**  
> Use the template below, bolding the selected tier row.  
>
> | Tier | Name | Words (approx. Tokens) | Core Use Case |
> | :--- | :--- | :--- | :--- |
> | (Tier X-1) | (Name X-1) | (Words X-1) | (Use Case X-1) |
> | **Tier X** | **(Name X)** | **(Words X)** | **(Use Case X)** |
> | (Tier X+1) | (Name X+1) | (Words X+1) | (Use Case X+1) |

---

## ANCHOR-QR-3: Core Framework Menu

> **VERBATIM-INJECTION**  
> Core frameworks (select based on request type):
> 1. **SWOT Analysis** - Strategic planning
> 2. **IRAC/CREAC** - Legal analysis
> 3. **Cost-Benefit Analysis** - Financial/policy decisions
> 4. **Root Cause Analysis** - Problem diagnosis
> 5. **STRIDE** - Security threat modeling
> 
> For domain-specific frameworks, load relevant pack:
> - Legal Pack: Stare-Decisis, Chevron, Scrutiny Ladder
> - Financial Pack: CBA, Dynamic Scoring, Fiscal Multiplier
> - Technical Pack: MITRE ATT&CK, OSI Model, CIS Benchmarks
> - Policy Pack: RIA, PESTLE, Logic Model

---

## ANCHOR-QR-4: Source Specification Guidelines

> **VERBATIM-INJECTION**  
> When sources are available, specify them as:
> ```
> Sources (if known):
> 1. [DOC1]: {Title/Description}
> 2. [DOC2]: {Title/Description}
> 3. [WEB1]: {Topic for search}
> ```
> 
> If sources are not pre-specified:
> - Tag all unsourced factual claims with [ExpertJudgment]
> - Use web search for volatile/current information
> - Clearly distinguish between sourced facts and inferences

---

## ANCHOR-QR-5: Error Prevention Patterns

> **VERBATIM-INJECTION**  
> **Forbidden Patterns (avoid these):**
> - "Studies show..." without specific citation
> - Specific statistics without source attribution
> - Future predictions stated as facts
> - Universal claims ("all", "never") without qualification
> 
> **Required Patterns (must include):**
> - Every factual claim → source reference or [ExpertJudgment] tag
> - Every statistic → exact source with date
> - Every recommendation → supporting evidence
> - Uncertain claims → confidence qualifier

---

## ANCHOR-QR-6: Diagnostic Flag System

> **VERBATIM-INJECTION**  
> Use these specific flags for precise error diagnosis:
> 
> **Consensus/Reasoning Flags:**
> - [LowConsensus] - Multiple reasoning paths disagree
> - [VerificationIssue] - Claim fails internal verification
> 
> **Source/Evidence Flags:**
> - [ExpertJudgment] - Inference not directly sourced (REQUIRED for all unsourced claims)
> - [DataUnavailableOrUnverified] - Critical data cannot be verified
> 
> **Confidence Flags:**
> - [Confidence:Low] - Low confidence with reason
> - [Confidence: XX/100] - Numerical confidence (when requested)
> 
> **Process Flags:**
> - [ErrorForecast:{Type}] - Predicted error type
> - [NeedsHumanReview] - Critical issues remain
> 
> **Severity Wrapper (optional):**
> - [Critical: {flag + description}] - Must fix
> - [Warning: {flag + description}] - Should review
> - [Note: {flag + description}] - For awareness

---

## ANCHOR-QR-7: Auto-Injected Stylometry & Tone Directives

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

## ANCHOR-QR-8: Progressive Evaluation Protocol

> **VERBATIM-INJECTION**  
> Apply evaluation based on request tier:
>
> ### Minimal Evaluation (Tiers 1-3)
> 1. **Accuracy Check**: 
>    - Verify key facts and calculations
>    - For any claim where certainty <90%, perform quick 2-path consistency check
>    - Flag discrepancies with [LowConsensus]
> 2. **Source Transparency**:
>    - Tag ALL unsourced claims with [ExpertJudgment]
>    - Distinguish facts from inferences
> 3. **Completeness Check**: 
>    - Confirm core request fulfilled
>    - Verify within tier word limits
> 
> ### Standard Evaluation (Tiers 4-6)
> 1. **Enhanced Accuracy Check**: 
>    - Verify all facts, sources, calculations
>    - Generate 2-3 reasoning paths for all critical/factual outputs
>    - Flag conflicts with [LowConsensus] if paths disagree
>    - Tag all unsourced claims with [ExpertJudgment]
> 2. **Chain-of-Verification (CoVe)**:
>    - For complex claims or multi-step logic:
>      a) Formulate 1-2 verification questions per critical element
>      b) Answer verification questions internally
>      c) Flag issues with [VerificationIssue] if contradictions found
> 3. **Completeness Check**: 
>    - All request components addressed
>    - Word count within tier bounds (±10%)
>    - Framework properly applied if specified
> 4. **Confidence Assessment**:
>    - For key conclusions, assess confidence
>    - Flag low confidence claims with [Confidence:Low] and reason
>    - Optionally add [Confidence: XX/100] for critical facts
> 5. **Error Forecasting**:
>    - Scan output for likely error types
>    - Tag with [ErrorForecast:Type] where applicable
>    - Types: FactualUncertainty, LogicalGap, BiasRisk, OutdatedInfo
> 6. **Constraint Check**: 
>    - Validate T-block requirements (ANCHOR-QR-7)
>    - No PII, harmful, or biased content
>    - Format compliance
> 
> ### Full Evaluation (Tiers 7-10)
> Apply all Standard Evaluation steps plus:
> 1. **Advanced Mode Selection** (see ANCHOR-QR-9)
> 2. **Adversarial Robustness Check**:
>    - Test key claims against hypothetical challenges
>    - Verify constraint adherence under edge cases
>    - Flag concerns with [RobustnessConcern:{Type}]
> 3. **Enhanced Confidence Scoring**:
>    - Provide [Confidence: XX/100] for all major claims
>    - Document confidence reasoning
> 4. **Final Human Review Flag**:
>    - If any [Critical:] issues remain, prepend [NeedsHumanReview]

---

## ANCHOR-QR-9: Advanced Technique Modes

> **VERBATIM-INJECTION**  
> For Full Evaluation (Tiers 7-10), select ONE primary mode:
>
> ### Precision Mode (Factual/Numerical Tasks)
> Required components:
> - Generate 5+ reasoning paths for critical calculations
> - Verify each step independently with shown work
> - Apply [Confidence: XX/100] to all key claims
> - Double-check all citations against sources
> - Test edge cases for numerical boundaries
> 
> ### Analysis Mode (Complex Reasoning Tasks)
> Required components:
> - Enhanced reflection with 2 revision cycles
> - Generate 3-5 clarifying questions before analysis
> - Create comparative evaluation of multiple options
> - Document reasoning chain with explicit steps
> - Apply adversarial robustness testing to conclusions
> - Consider alternative interpretations
>
> ### Creative Mode (Flexible/Generative Tasks)
> Required components:
> - Single reflection pass focused on coherence
> - Maintain factual accuracy for any claims
> - Tag creative liberties with [CreativeChoice]
> - Ensure [ExpertJudgment] tags still applied
> - Balance creativity with request constraints

---

## ANCHOR-QR-10: Rigor Level Definitions

| Level | Description                  | Evaluation Protocol                                         | Advanced Mode |
| ----- | ---------------------------- | ----------------------------------------------------------- | ------------- |
| 1     | **Basic** (Tiers 1-3)        | Minimal evaluation with self-consistency + [ExpertJudgment] | None          |
| 2     | **Intermediate** (Tiers 4-6) | Standard evaluation with CoVe + confidence assessment       | Optional      |
| 3     | **Advanced** (Tiers 7-10)    | Full evaluation with adversarial testing                    | Required      |

---

## ANCHOR-QR-11: Validation Status Indicators

> **VERBATIM-INJECTION**  
> Display real-time validation status:
> - ✓ Green: Component complete and valid
> - ⚠️ Yellow: Component needs attention (specify issue)
> - ✗ Red: Component has conflicts/errors (must fix)
> 
> Quality Score: [X/10] based on:
> - Context clarity (0-2)
> - Request specificity (0-2)
> - Example quality (0-2)
> - Source specification (0-2)
> - Internal consistency (0-2)

---

## ANCHOR-QR-12: Prompt-Specific Evaluation Checks

> **VERBATIM-INJECTION**  
> Add these checks based on request type:
>
> **For numerical/calculation tasks:**
> - Verify each step shows explicit work
> - Confirm units consistent throughout
> - Apply 5+ path verification for critical results
> - Check [Confidence: XX/100] present for conclusions
>
> **For source-heavy tasks:**
> - Verify 100% of factual claims have citation or [ExpertJudgment]
> - Confirm no "orphan" facts without attribution
> - Check citation format matches T-block specification
>
> **For framework-based tasks:**
> - Verify all framework components present
> - Confirm framework-specific terminology used correctly
> - Check logical flow follows framework structure
>
> **For reasoning-heavy tasks:**
> - Verify CoVe applied to all major logical steps
> - Confirm [LowConsensus] flags where paths diverge
> - Check [ErrorForecast:LogicalGap] tags applied

---

## ANCHOR-QR-13: Factual Accuracy & Bias Mitigation

> **VERBATIM-INJECTION** (All evaluation levels)  
>
> 1. Prioritize factual accuracy rigorously - verify against provided sources
> 2. State uncertainties clearly with [Confidence:Low] or [ExpertJudgment]
> 3. Apply numerical confidence [XX/100] when requested or for Tier 7+
> 4. Strive for neutral, objective language unless persona requires otherwise
> 5. Consider multiple perspectives on controversial topics
> 6. Avoid loaded terms, stereotypes, or unsupported generalizations
> 7. Flag potential bias risks with [ErrorForecast:BiasRisk]

---

## ANCHOR-QR-14: Request Template Quick Select

> **VERBATIM-INJECTION**  
> Common templates available:
> 1. [Legal-Memo]: IRAC analysis with Bluebook citations
> 2. [Policy-Brief]: RIA with plain language summary
> 3. [Tech-Spec]: RFC-style with MUST/SHOULD requirements
> 4. [Financial-Analysis]: CBA with sensitivity analysis
> 5. [Research-Paper]: Academic style with Chicago citations
> 
> Load template: "Use template [Template-Name]"

---

## ANCHOR-QR-15: Graceful Degradation Protocol

> **VERBATIM-INJECTION**  
> If full evaluation cannot complete:
> 1. Maintain critical safety checks (PII, harmful content)
> 2. Ensure [ExpertJudgment] tagging remains active
> 3. Perform at least basic fact-checking
> 4. Flag degradation: [Degraded: Skipped {components}]
> 5. Provide confidence: [Partial Evaluation: X/10]

---

## Guidance for Prompt-Specific E-Block Checks

Adapt checks to the request's content based on tier:

- *Tiers 1-3*: Focus on [ExpertJudgment] tagging and basic consistency
- *Tiers 4-6*: Emphasize CoVe, confidence flags, and error forecasting
- *Tiers 7-10*: Full diagnostic suite with numerical confidence scores