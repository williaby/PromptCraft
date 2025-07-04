# [](#05-evidence-and-citationsmd)05 Evidence-and-Citations.md

**Version:** Evidence-Citations Document v1.0, May 29, 2025
**Source Document:** AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework - v 1. (May 2025)
**ApproxTokens:** approximately 60 k
**Purpose:** This document focuses on critical 'Augmentations' (A) and 'Tone and Format' (T)
aspects of the C.R.E.A.T.E. framework related to evidence, data sources, and citations.
It covers specifying evidence, using citation guides, understanding the authority ladder,
incorporating live data with recency filters, and best practices to ensure factual accuracy
and avoid issues like hallucinations and plagiarism traps.

## [](#table-of-contents)Table of Contents

1. [Introduction to Evidence and Citations in Prompts](#introduction-to-evidence-and-citations-in-prompts)
2. [1. Specifying Evidence and Data Sources (Augmentation)](#1-specifying-evidence-and-data-sources-augmentation)
   1. [1.1. Why Specifying Evidence Matters](#11-why-specifying-evidence-matters)
   2. [1.2. How to Specify Evidence and Data Sources](#12-how-to-specify-evidence-and-data-sources)
   3. [1.3. Domain-Tailored Evidence Directives (Table)](#13-domain-tailored-evidence-directives-table)
   4. [1.4. Best Practices for Evidence Specification](#14-best-practices-for-evidence-specification)
3. [2. Defining Citation Styles and Format (Tone and Format)](#2-defining-citation-styles-and-format-tone-and-format)
   1. [2.1. Why Defining Citation Styles Matters](#21-why-defining-citation-styles-matters)
   2. [2.2. How to Define Citation Styles and Format](#22-how-to-define-citation-styles-and-format)
   3. [2.3. Example Triggers for Citation Styles](#23-example-triggers-for-citation-styles)
   4. [2.4. Specific Guidance and Best Practices for Citations](#24-specific-guidance-and-best-practices-for-citations)
4. [3. Using Live Data and Recency Filters (Augmentation)](#3-using-live-data-and-recency-filters-augmentation)
   1. [3.1. Why Live Data and Recency Filters Matter](#31-why-live-data-and-recency-filters-matter)
   2. [3.2. How to Use Live Data and Recency Filters](#32-how-to-use-live-data-and-recency-filters)
   3. [3.3. Example Triggers for Live Data](#33-example-triggers-for-live-data)
   4. [3.4 Live-Data Decision Matrix (T-S-V)](#34-live-data-decision-matrix-t-s-v)
5. [*Timeless* -> answer;
   *Slow-changing* -> answer + offer search;
   *Volatile* -> PromptCraft Pro instructs the downstream LLM to auto-search by applying `ANCHOR-QR-1`
   from `00 Quick-Reference.md`. This anchor details the use of `web.search_query` with a default
   `recency: 365` and citation instructions via `ANCHOR-QR-1a`.
   **T-S-V = Tell, Suggest, Verify live**](#timeless---answerslow-changing---answer--offer-searchvolatile---promptcraft-pro-instructs-the-downstream-llm-to-auto-search-by-applying-anchor-qr-1from-00-quick-referencemd-this-anchor-details-the-use-of-websearch_query-with-a-defaultrecency-365-and-citation-instructions-via-anchor-qr-1at-s-v--tell-suggest-verify-live)
6. [4. Ensuring Accuracy: Grounding, Verification, and Avoiding "Plagiarism Traps"](#4-ensuring-accuracy-grounding-verification-and-avoiding-plagiarism-traps)
7. [5. Tagging Unsourced Claims - \[Expert Judgment\]](#5-tagging-unsourced-claims---expert-judgment)

## [](#introduction-to-evidence-and-citations-in-prompts)Introduction to Evidence and Citations in Prompts

Incorporating robust evidence specification, proper citation formatting, and current data are
crucial for producing high-quality, reliable outputs from Large Language Models (LLMs). These
elements fall under the 'Augmentations' and 'Tone and Format' components of the C.R.E.A.T.E.
framework. Failing to address these can lead to hallucinations, inaccuracies, and outputs that
lack credibility or are unfit for professional use. This document outlines how to effectively
manage evidence, citations, and data recency in your prompts.

***

<!-- ANCHOR-EC-1 -->

## [](#1-specifying-evidence-and-data-sources-augmentation)1. Specifying Evidence and Data Sources (Augmentation)

### [](#11-why-specifying-evidence-matters)1.1. Why Specifying Evidence Matters

This is perhaps the *most critical* augmentation for preventing hallucinations and ensuring factual
accuracy in high-stakes legal, fiscal, or policy work. LLMs can fabricate facts or references when
they lack concrete grounding. By explicitly naming *which* sources the AI must use and *how* it must
cite them, you anchor its responses in verifiable reality. Without explicit citation directives or
source constraints, an LLM may present plausible sounding but incorrect information.

### [](#12-how-to-specify-evidence-and-data-sources)1.2. How to Specify Evidence and Data Sources

* Name the specific citation style guide to be used.
* List the primary authorities (statutes, regulations, cases, reports) that the LLM should use.
* Specify the preferred order or ranking of authority if multiple source types are relevant.
* Place these directives *before* length or other style instructions in your prompt to prevent
  them from being inadvertently dropped or overlooked by the model when it processes complex
  instructions.

### [](#13-domain-tailored-evidence-directives-table)1.3. Domain-Tailored Evidence Directives (Table)

| Domain        | Citation Guide(s)                             | Primary Authorities and Cue Words                     | Example Trigger Snippet                                |
|---------------|-----------------------------------------------|----------------------------------------------------|--------------------------------------------------------|
| General       | Chicago Manual of Style (17th ed.)            | Superscript footnotes; References section           | "Use superscript footnotes following Chicago style     |
|               |                                               |                                                    | and include a References section."                      |
| Legal         | Bluebook (21st ed.)                           | U.S. Code; Code of Federal Regulations;             | "Cite 26 U.S.C. Section 61, 17 C.F.R. Section 1.61-1,  |
|               |                                               | Tax Ct., Fed Cir., SCOTUS                          | Tax Ct. opinions in Bluebook format."                   |
| Fiscal        | GAO Cost Guide (GAO-20-195G); OMB A-4         | GAO reports; OMB Circular A-4 RIAs; CBO estimates   | "Reference GAO-20-195G and OMB Circular A-4 for cost   |
|               |                                               |                                                    | models."                                                |
| IT/Security   | NIST SP 800-53 Rev. 5; CIS Controls v8;       | NIST control IDs (e.g., AC-3); CIS Safeguard       | "Use NIST SP 800-53 controls and CIS v8 mappings;      |
|               | RFC 2119                                      | numbers; RFC normative terms                       | format MUST/SHOULD per RFC 2119."                       |
| Tax           | IRC and Treasury Regs; Rev. Rul.;             | 26 U.S.C. Section; 26 C.F.R. Section;              | "Cite IRC Section 162, Treas. Reg. Section 1.162-1,    |
|               | PLRs; Circular 230                           | Rev. Rul. numbers; Tax Ct. cases                   | Rev. Rul. 2023-2, and Tax Ct. Memos."                   |

### [](#14-best-practices-for-evidence-specification)1.4. Best Practices for Evidence Specification

* **Order of Authority:** Always rank sources if applicable (e.g., "Statute > Regulation > Court
  Opinion > Ruling"). This helps the LLM prioritize when information might conflict or when
  constructing an argument.
* **Style Compliance:** Enforce formatting consistency by explicitly naming the style manual
  (e.g., Bluebook, APA 7th, Chicago Manual of Style).
* **Inline vs. Footnote:** Indicate your preference for citation placement (e.g., "use inline
  parenthetical citations" or "use superscript footnotes").

***

<!-- ANCHOR-EC-2 -->

## [](#2-defining-citation-styles-and-format-tone-and-format)2. Defining Citation Styles and Format (Tone and Format)

### [](#21-why-defining-citation-styles-matters)2.1. Why Defining Citation Styles Matters

Consistent and accurate citation formatting is non-negotiable in legal, fiscal, policy, and academic
work. It ensures credibility, traceability, and adherence to professional standards. Simply asking
for "citations" isn't enough; you must specify the *style guide* and *format* to achieve the desired
professionalism and utility in the LLM's output.

### [](#22-how-to-define-citation-styles-and-format)2.2. How to Define Citation Styles and Format

* **Name the Guide:** Explicitly state the citation manual to enforce its specific formatting rules.
  Examples include:
  * General: Chicago Manual of Style
  * Legal: Bluebook (21st ed.)
  * Fiscal: GAO Cost Guide (GAO-20-195G)
  * IT and Security: NIST SP 800-53 Rev. 5, RFC 2119
  * Policy: OMB Circular A-4, APA 7th
  * Tax: IRC and Treasury Regs
* **Specify Format:** Indicate whether you prefer inline parenthetical citations or superscript
  footnotes (e.g., "Use superscript Chicago footnotes"). You can also refer to specific template
  requirements if applicable.

### [](#23-example-triggers-for-citation-styles)2.3. Example Triggers for Citation Styles

* "Cite 26 U.S.C. Section 61... in Bluebook format."
* "Use superscript footnotes following the Chicago Manual of Style and include a References section."

### [](#24-specific-guidance-and-best-practices-for-citations)2.4. Specific Guidance and Best Practices for Citations

* **Prevent Drift:** Place evidence *and* citation style directives *before* word-count limits or
  other stylistic instructions. This helps prevent the model from dropping these critical formatting
  rules when it edits for length or other constraints.
* **Verify:** Always double-check generated citations, especially for less common sources or complex
  styles. LLMs can sometimes make errors in citation formatting or cite irrelevant parts of a source.
* **Tag Uncited Claims:** For statements where a direct verifiable source might not be provided by
  the LLM (or if it's generating heuristic opinions based on its training), instruct the LLM to tag
  such statements (e.g., with `[Expert Judgment]`). This allows reviewers to distinguish between
  fact-based, cited information and model-generated insights that require further scrutiny.

***

<!-- ANCHOR-EC-3 -->

## [](#3-using-live-data-and-recency-filters-augmentation)3. Using Live Data and Recency Filters (Augmentation)

### [](#31-why-live-data-and-recency-filters-matter)3.1. Why Live Data and Recency Filters Matter

LLM training data is not a live feed of the internet; it has a knowledge cutoff date. For tasks
requiring current information (e.g., recent events, new legislation, evolving terminology), you must
augment the prompt by directing the AI to use tools that can access live data and by filtering that
data for recency.

### [](#32-how-to-use-live-data-and-recency-filters)3.2. How to Use Live Data and Recency Filters

* **Invoke Live Tools:** Explicitly call tools like `web.search_query` or `image_query` when current
  information or visuals are needed.
  * For visuals, you can use: `image_query q="CoreDistAccess diagram"` (which typically returns 1-4
    images).
* **Apply Recency Filters:** Constrain live data searches by date to avoid outdated information
  (e.g., "last 180 days," "from 2023-2025").
* PromptCraft Pro, when instructing the use of `web.search_query` for Volatile data (as per
  `ANCHOR-QR-1` in `00 Quick-Reference.md`), defaults to a recency of 365 days. Users can request
  different recency periods in their input to PromptCraft Pro.
* **Specify Python Usage:** Detail when to use `python` for backend analysis versus
  `python_user_visible` for outputs like tables or plots intended for the user to see directly.

### [](#33-example-triggers-for-live-data)3.3. Example Triggers for Live Data

* PromptCraft Pro defaults to `recency: 365` for `web.search_query` (see `ANCHOR-QR-1`). A user might
  request: "`For current market trends, use web.search_query with recency = 90 days.`"
* `Pull data from the last 30 days via web.search_query.`
* `Use peer-reviewed journals (2023-2025).`
* `Use python_user_visible for tables/plots.`

### [](#34-live-data-decision-matrix-t-s-v)3.4 Live-Data Decision Matrix (T-S-V)

[](#timeless---answerslow-changing---answer--offer-searchvolatile---promptcraft-pro-instructs-the-downstream-llm-to-auto-search-by-applying-anchor-qr-1from-00-quick-referencemd-this-anchor-details-the-use-of-websearch_query-with-a-defaultrecency-365-and-citation-instructions-via-anchor-qr-1at-s-v--tell-suggest-verify-live)*Timeless* -> answer;
*Slow-changing* -> answer + offer search;
*Volatile* -> PromptCraft Pro instructs the downstream LLM to auto-search by applying `ANCHOR-QR-1`
from `00 Quick-Reference.md`. This anchor details the use of `web.search_query` with a default
`recency: 365` and citation instructions via `ANCHOR-QR-1a`.
**T-S-V = Tell, Suggest, Verify live**
--------------------------------------

<!-- ANCHOR-EC-4 -->

## [](#4-ensuring-accuracy-grounding-verification-and-avoiding-plagiarism-traps)4. Ensuring Accuracy: Grounding, Verification, and Avoiding "Plagiarism Traps"

A "plagiarism trap" in the context of LLM usage often refers to the unintentional presentation of
ungrounded, misattributed, or hallucinated information as factual or properly sourced. This can happen
if prompts do not adequately constrain the LLM to specific evidence or if outputs are not rigorously
verified.

Key principles to avoid these traps and ensure accuracy include:

* **Emphasize Source Grounding:** As detailed in Section 1, always instruct the LLM to base its
  responses on specified, verifiable sources, especially for factual claims, legal interpretations,
  or policy details. This is the primary defense against hallucinated content.
* **Beware of Hallucinations:** LLMs can fabricate facts, references, or entire sections of text if
  they lack concrete grounding or misunderstand a query. The C.R.E.A.T.E. guide introduction warns:
  "Without explicit citation directives or source constraints, an LLM may present plausible sounding
  but incorrect information."
* **Mandate Citations:** For any task requiring factual support, make citation to primary authorities
  or provided documents a non-negotiable part of the prompt (see Sections 1 and 2 above).
* **Leveraging PromptCraft Pro's Enhanced Evaluation Framework:**
  The C.R.E.A.T.E. prompts generated by PromptCraft Pro are designed to significantly bolster
  accuracy and minimize issues like hallucinations. Key mechanisms include:
  * **Rigorous Default E-Block (`ANCHOR-QR-8`):** The standard Evaluation block copied verbatim into
    every C.R.E.A.T.E. prompt includes multiple steps for the downstream LLM, such as a Reflection
    Loop (E.1), Self-Consistency Check (E.2), Chain-of-Verification (CoVe) (E.3), and specific
    checks for Confidence, Sourcing and Accuracy Assertion (E.4). These are designed to proactively
    identify and correct errors.
  * **Selectable Advanced Evaluation and Reasoning Techniques (`ANCHOR-QR-11`):** Based on the
    determined Rigor Level or user request, PromptCraft Pro can instruct the downstream LLM to
    employ advanced techniques like more dynamic reflection, formal self-consistency sampling
    (including CISC), prompt interrogation chains, advanced error forecasting, numerical uncertainty
    quantification, adversarial robustness self-checks, enhanced self-judgment methods, and stepwise
    natural language self-critique. Each of these contributes to a more thorough and reliable output.
  * **Factual Accuracy and Bias Mitigation Directives (`ANCHOR-QR-13`):** For prompts at
    Intermediate or Advanced Rigor Levels, PromptCraft Pro includes specific directives in the
    A-block for the downstream LLM to prioritize factual accuracy, state uncertainties clearly, and
    strive for neutral, objective language, further reducing the risk of hallucinations and bias.
* **Implement Verification Steps:**
  * Always critically review LLM-generated content that relies on factual accuracy or specific
    citations.
  * Cross-reference generated citations with the actual source documents to ensure relevance and
    correctness.
  * For complex information, consider asking the LLM to provide quotes or direct excerpts from its
    sources to aid verification.
* **Use "Tag Uncited Claims" Strategy:** As mentioned in Best Practices for Citations (Section 2.4),
  instruct the LLM to flag any statements it makes that are not directly supported by the provided
  sources (e.g., using `[Expert Judgment]` or `[Model Inference]`). This creates transparency.
* **Iterative Refinement:** If an LLM output contains unverified claims or poor citations, refine
  the prompt to be more specific about evidence requirements, or use a follow-up prompt to challenge
  the LLM on specific points and ask for supporting evidence.
* **Understand LLM Limitations:** Remember that LLMs are not databases of perfect fact; they are
  language predictors. Their "knowledge" is based on patterns in their training data and can be
  outdated or contain biases. Live data tools help, but verification remains essential.
* PromptCraft Pro's systematic inclusion of these evaluation layers aims to embed best practices for
  accuracy directly into the prompts it generates.

By diligently applying these practices for specifying evidence, defining citation styles, using
current data appropriately, and critically evaluating outputs, you can significantly improve the
reliability and trustworthiness of LLM-generated content and avoid the pitfalls of presenting
unverified information.

<!-- ANCHOR-EC-5 -->

## [](#5-tagging-unsourced-claims---expert-judgment)5. Tagging Unsourced Claims - \[Expert Judgment]

When the LLM must rely on its own model knowledge rather than a verifiable source, instruct it to
append **`[Expert Judgment]`** at the sentence end.

1. **When to use:**
   * No primary source exists or is readily accessible.
   * The statement synthesises multiple cited facts into a new inference.
2. **Formatting examples**
   * *Cited fact* -> "Regulation S-K was first adopted in 1933.¹"
   * *Model inference* -> "A phased rollout minimises regulatory risk. **\[Expert Judgment]**"
3. **Evaluation tie-in**
   * The QA-Check (Evaluation block) must confirm that every uncited assertion is tagged and that
     tags are **not** used where a citation *is* available.
4. **User transparency**
   * Tagging lets reviewers quickly spot which parts need human vetting or additional sourcing.
