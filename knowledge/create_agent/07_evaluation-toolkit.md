# [](#07-evaluation-toolkitmd)07 Evaluation-Toolkit.md

**Version:** Evaluation-Toolkit Document v2.0, June 1, 2025
**Source Document:** AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework - v 1. (May 2025)
**Purpose:** This document details the 'E' (Evaluation) component of the C.R.E.A.T.E. framework as
implemented by PromptCraft Pro. It explains the standard built-in evaluation protocol (`ANCHOR-QR-8`),
how this can be augmented by Rigor Levels (`ANCHOR-QR-10`) and Advanced Evaluation Techniques
(`ANCHOR-QR-11`), the role of prompt-specific checks (`ANCHOR-QR-12`), guidance for post-hoc human
review, and principles for safety and success criteria.

## [](#table-of-contents)Table of Contents

1. [Introduction to Evaluation in PromptCraft Pro](#introduction-to-evaluation-in-promptcraft-pro)
2. [1. The Standard Built-in Evaluation Protocol (ANCHOR-QR-8)](#1-the-standard-built-in-evaluation-protocol-anchor-qr-8)
3. [# 1.1. Overview of ANCHOR-QR-8](#-11-overview-of-anchor-qr-8)
4. [# 1.2. Detailed Breakdown of ANCHOR-QR-8 Steps (E.1-E.6)](#-12-detailed-breakdown-of-anchor-qr-8-steps-e1-e6)
   1. [# 1.2.1. E.1 Reflection Loop](#-121-e1-reflection-loop)
   2. [# 1.2.2. E.2 Self-Consistency Check](#-122-e2-self-consistency-check)
   3. [# 1.2.3. E.3 Chain-of-Verification (CoVe)](#-123-e3-chain-of-verification-cove)
   4. [# 1.2.4. E.4 Confidence, Sourcing and Accuracy Assertion](#-124-e4-confidence-sourcing-and-accuracy-assertion)
   5. [# 1.2.5. E.5 Style, Safety and Constraint Pass](#-125-e5-style-safety-and-constraint-pass)
   6. [# 1.2.6. E.6 Overall Fitness and Final Review](#-126-e6-overall-fitness-and-final-review)
5. [# 1.3. The Standard Evaluation Footer (User Interaction)](#-13-the-standard-evaluation-footer-user-interaction)
6. [2. Augmenting Evaluation: Rigor Levels and Advanced Techniques](#2-augmenting-evaluation-rigor-levels-and-advanced-techniques)
7. [# 2.1. Understanding Rigor Levels (ANCHOR-QR-10)](#-21-understanding-rigor-levels-anchor-qr-10)
8. [# 2.2. Overview of Advanced Evaluation and Reasoning Techniques (ANCHOR-QR-11)](#-22-overview-of-advanced-evaluation-and-reasoning-techniques-anchor-qr-11)
   1. [# 2.2.1. Enhanced Reflection Loop Controls (ANCHOR-QR-11 #1)](#-221-enhanced-reflection-loop-controls-anchor-qr-11-1)
   2. [# 2.2.2. Self-Consistency Sampling / CISC (ANCHOR-QR-11 #2)](#-222-self-consistency-sampling--cisc-anchor-qr-11-2)
   3. [# 2.2.3. Prompt Interrogation Chains (ANCHOR-QR-11 #3)](#-223-prompt-interrogation-chains-anchor-qr-11-3)
   4. [# 2.2.4. Advanced Error Forecasting (ANCHOR-QR-11 #4)](#-224-advanced-error-forecasting-anchor-qr-11-4)
   5. [# 2.2.5. Robust Uncertainty Quantification (UQ) - Numerical Scoring (ANCHOR-QR-11 #5)](#-225-robust-uncertainty-quantification-uq---numerical-scoring-anchor-qr-11-5)
   6. [# 2.2.6. Adversarial Robustness Self-Checks (ANCHOR-QR-11 #6)](#-226-adversarial-robustness-self-checks-anchor-qr-11-6)
   7. [# 2.2.7. Enhanced Self-Judgment (Comparative/Scored) (ANCHOR-QR-11 #7)](#-227-enhanced-self-judgment-comparativescored-anchor-qr-11-7)
   8. [# 2.2.8. Stepwise Natural Language Self-Critique (ANCHOR-QR-11 #8)](#-228-stepwise-natural-language-self-critique-anchor-qr-11-8)
9. [# 2.3. How PromptCraft Pro Selects and Applies Advanced Techniques](#-23-how-promptcraft-pro-selects-and-applies-advanced-techniques)
10. [3. Customizing Evaluation: Prompt-Specific Checks (ANCHOR-QR-12)](#3-customizing-evaluation-prompt-specific-checks-anchor-qr-12)
11. [# 3.1. Purpose of Prompt-Specific Checks](#-31-purpose-of-prompt-specific-checks)
12. [# 3.2. Guidance on Crafting Prompt-Specific Checks (referencing ANCHOR-QR-12)](#-32-guidance-on-crafting-prompt-specific-checks-referencing-anchor-qr-12)
13. [# 3.3. Stylistic and Readability Metrics as Prompt-Specific Checks](#-33-stylistic-and-readability-metrics-as-prompt-specific-checks)
14. [4. The Role of Human Review](#4-the-role-of-human-review)
15. [# 4.1. Why Human Review Remains Crucial](#-41-why-human-review-remains-crucial)
16. [# 4.2. Key Areas for Human Review (Hallucination and Quality Checklist)](#-42-key-areas-for-human-review-hallucination-and-quality-checklist)
17. [5. Safety, Guardrails, and Ethical Considerations](#5-safety-guardrails-and-ethical-considerations)
18. [# 5.1. Core LLM Limitations and Mitigation Strategies](#-51-core-llm-limitations-and-mitigation-strategies)
    1. [# 5.1.1. Addressing Hallucinations](#-511-addressing-hallucinations)
    2. [# 5.1.2. Mitigating Bias](#-512-mitigating-bias)
    3. [# 5.1.3. Managing Knowledge Cutoff Dates](#-513-managing-knowledge-cutoff-dates)
19. [# 5.2. Data Protection (PII, Secrets)](#-52-data-protection-pii-secrets)
20. [# 5.3. Negative Constraints and Content Suppression](#-53-negative-constraints-and-content-suppression)
21. [# 5.4. Transparency in Uncertainty and Neutrality](#-54-transparency-in-uncertainty-and-neutrality)
22. [6. Defining and Verifying Success Criteria](#6-defining-and-verifying-success-criteria)
23. [# 6.1. Importance and Method](#-61-importance-and-method)
24. [# 6.2. Examples and Best Practices](#-62-examples-and-best-practices)

## [](#introduction-to-evaluation-in-promptcraft-pro)Introduction to Evaluation in PromptCraft Pro

You've meticulously built your prompt through Context (C), Request (R), Examples (E), Augmentations (A),
and Tone and Format (T). The final step in the C.R.E.A.T.E. process is Evaluation (E). Large Language
Models (LLMs) are incredibly capable, but they are not infallible. They can misunderstand, 'hallucinate'
facts, miss constraints, or make logical errors.

Within the PromptCraft Pro ecosystem, Evaluation encompasses several layers designed to ensure the
downstream LLM produces high-quality, reliable outputs:

1. A **Standard Built-in Evaluation Protocol** (`ANCHOR-QR-8`) that is embedded in every C.R.E.A.T.E.
   prompt. This protocol instructs the downstream LLM to perform a series of self-checks before finalizing
   its response.
2. **Augmented Evaluation** capabilities through selectable Rigor Levels (`ANCHOR-QR-10`) and Advanced
   Evaluation and Reasoning Techniques (`ANCHOR-QR-11`). These allow for more intensive and specialized
   self-correction by the downstream LLM.
3. **Customizable Prompt-Specific Checks** tailored to the unique requirements of the task, guided by
   `ANCHOR-QR-12`.
4. Essential **Post-Hoc Human Review** to verify final quality and accuracy, especially for high-stakes
   applications.

This multi-faceted approach is critical for building trust and ensuring that outputs generated from
PromptCraft Pro prompts meet the highest standards of reliability and fitness for purpose.

***

## [](#1-the-standard-built-in-evaluation-protocol-anchor-qr-8)1. The Standard Built-in Evaluation Protocol (ANCHOR-QR-8)

## [](#-11-overview-of-anchor-qr-8)# 1.1. Overview of ANCHOR-QR-8

The cornerstone of built-in evaluation for C.R.E.A.T.E. prompts generated by PromptCraft Pro is
`ANCHOR-QR-8`, as defined in `00 Quick-Reference.md`.
This entire anchor, including its six core evaluation steps (E.1-E.6) and the standard Evaluation Footer,
is copied **verbatim** into the 'E - Evaluation' block of every generated prompt.
This ensures a consistent and rigorous self-evaluation process that the downstream LLM must perform
before finalizing its response.

## [](#-12-detailed-breakdown-of-anchor-qr-8-steps-e1-e6)# 1.2. Detailed Breakdown of ANCHOR-QR-8 Steps (E.1-E.6)

The following details each step of the `ANCHOR-QR-8` protocol, which instructs the downstream LLM's
self-evaluation process.
(The full text of these E-steps is found in `ANCHOR-QR-8` in `00 Quick-Reference.md`).

### [](#-121-e1-reflection-loop)# 1.2.1. E.1 Reflection Loop

* **`ANCHOR-QR-8` E.1 Text:** `E.1 Reflection Loop: Draft response -> list <= 3 critical
  weaknesses, gaps, or potential errors based on all C.R.E.A.T.E. requirements; formulate a plan
  to address them -> revise draft once to implement plan. If critical issues persist or new ones
  are introduced, flag output with [NeedsHumanReview] and briefly state unresolved issues. (This
  loop may be enhanced by ANCHOR-QR-11 item #1 if selected by PromptCraft Pro).`
* **Purpose:** This initial step mandates a self-critique and at least one iterative revision
  by the downstream LLM. The LLM must identify its own potential errors, weaknesses, or gaps
  against all C.R.E.A.T.E. prompt requirements, formulate a plan to address these issues, and
  then implement the plan by revising its draft. It also includes a mechanism to flag
  persistent issues for human attention. The note explicitly states that the execution of this
  loop can be made more dynamic and controlled if PromptCraft Pro selects "Enhanced Reflection
  Loop Controls" (from `ANCHOR-QR-11` #1) for the task.

### [](#-122-e2-self-consistency-check)# 1.2.2. E.2 Self-Consistency Check

* **`ANCHOR-QR-8` E.2 Text:** `E.2 Self-Consistency Check: If the request involves critical numerical
  outputs, key factual extractions, or complex logical deductions, internally generate 2-3 diverse
  reasoning paths (using a slightly varied approach or temperature if possible) to the key
  conclusions. If significant discrepancies arise between paths for a critical output, flag that
  output with [LowConsensus] and present the most common or highest-confidence result if discernible,
  otherwise state the discrepancy.`
* **Purpose:** For tasks demanding high precision in reasoning or the extraction of specific facts or
  numbers, this step instructs the downstream LLM to internally explore multiple solution paths (if
  feasible within its processing). This helps identify and flag outputs where the LLM's own reasoning
  is not stable or consistent across these internal paths-a common indicator of potential error or
  hallucination. It aims to present the most robust conclusion or transparently state the
  inconsistency. This is a simplified, built-in version; more comprehensive Self-Consistency
  techniques are available via `ANCHOR-QR-11` #2.

### [](#-123-e3-chain-of-verification-cove)# 1.2.3. E.3 Chain-of-Verification (CoVe)

* **`ANCHOR-QR-8` E.3 Text:** `E.3 Chain-of-Verification (CoVe): For any complex factual claims,
  sequences of events, or multi-step logical arguments: (a) Internally formulate 1-2 verification
  questions for each critical component/step. (b) Internally answer these verification questions.
  (c) Review answers; if any contradiction or unsupported element is found, revise the original
  claim/argument to ensure accuracy and support, or flag with [VerificationIssue].`
* **Purpose:** This step forces the downstream LLM to deconstruct and internally verify its own
  complex factual claims, sequences of events, or multi-step logical arguments. By generating and
  answering its own internal verification questions for each critical component, it can proactively
  catch logical fallacies, unsupported statements, or internal contradictions before the output is
  finalized.

### [](#-124-e4-confidence-sourcing-and-accuracy-assertion)# 1.2.4. E.4 Confidence, Sourcing and Accuracy Assertion

* **`ANCHOR-QR-8` E.4 Text (incorporating latest refinements):** `E.4 Confidence, Sourcing and
  Accuracy Assertion: For every primary factual assertion or significant conclusion: a. **Verify
  Source Adherence:** Ensure it is directly and accurately attributable to provided source material
  if sources were given. Cite explicitly if required by prompt. b. **Tag Inferences:** If the
  assertion is an inference, synthesis, or based on general knowledge not present in provided
  sources, it MUST be tagged \`\[ExpertJudgment]\`. c. **Assess and Declare Confidence:** If
  confidence in a claim is notably low due to ambiguity in sources, lack of definitive information,
  complex inference, or issues identified in E.2 (Self-Consistency) or E.3 (CoVe), it MUST be
  flagged with \`\[Confidence:Low]\` and a brief (internal or explicit if requested) reason noted
  (e.g., "conflicting source data," "multi-step inference with assumptions"). Unverifiable critical
  claims should be flagged \`\[DataUnavailableOrUnverified]\` or omitted if accuracy is paramount.
  Use appropriate hedging in language for low-confidence statements.\`
* **Purpose:** This multi-faceted step is crucial for responsible information presentation. It mandates that the
  downstream LLM:
  * Ensures claims are accurately tied to provided sources.
  * Explicitly tags non-sourced inferences or synthesized statements with `[ExpertJudgment]`.
  * Assesses its confidence in its assertions, especially if other checks (E.2, E.3) revealed issues, and uses
    flags like `[Confidence:Low]` or `[DataUnavailableOrUnverified]` for transparency, along with appropriate
    hedging.

### [](#-125-e5-style-safety-and-constraint-pass)# 1.2.5. E.5 Style, Safety and Constraint Pass

* **`ANCHOR-QR-8` E.5 Text:** `E.5 Style, Safety and Constraint Pass: Verify strict adherence to all T-block
  stylometry directives (ANCHOR-QR-7) and any specific formatting or negative constraints from the A-block
  (e.g., "Do not discuss X"). Confirm no PII, harmful, or biased content is present. If any stylistic or
  safety/constraint rule is violated and cannot be rectified in the reflection loop, flag with [StyleSafetyFail].`
* **Purpose:** This step ensures the downstream LLM's output complies with all specified
  stylistic rules from `ANCHOR-QR-7` (which PromptCraft Pro injects into the T-block), any custom formatting
  requirements, critical safety constraints (like PII avoidance), and any explicit negative constraints (topic
  exclusions, etc.) provided in the Augmentations block.

### [](#-126-e6-overall-fitness-and-final-review)# 1.2.6. E.6 Overall Fitness and Final Review

* **`ANCHOR-QR-8` E.6 Text:** `E.6 Overall Fitness and Final Review: Before concluding, perform a
  final check that the entire response holistically addresses all aspects of the R-block, is
  coherent, and meets the overall quality standards implied by the C.R.E.A.T.E. framework. If
  significant concerns remain after all checks, prepend the response with [OverallQualityConcern].`
* **Purpose:** This serves as a final, holistic self-review by the downstream LLM. It checks if the
  output, as a whole, is fit for purpose, comprehensively addresses the user's core request
  (R-block), maintains internal coherence, and generally meets the high-quality standards expected
  from a C.R.E.A.T.E.-structured prompt.

## [](#-13-the-standard-evaluation-footer-user-interaction)# 1.3. The Standard Evaluation Footer (User Interaction)

The `ANCHOR-QR-8` E-block definition in `00 Quick-Reference.md` concludes with the following standard footer:

```markdown
Evaluation Footer:
**Suggested Tier:** Tier X  |  **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A.T.E block before we finalise)
```

It's important to note that while this footer is part of the verbatim `ANCHOR-QR-8` copied into the
E-block of the generated prompt, its interactive function (`OK?`, `Other changes?`) is primarily for
the user's interaction *with PromptCraft Pro itself*, after PromptCraft Pro has generated the full
C.R.E.A.T.E. prompt. PromptCraft Pro presents this Tier and Rigor feedback to the user. Its
inclusion in `ANCHOR-QR-8` ensures the template is complete.

***

## [](#2-augmenting-evaluation-rigor-levels-and-advanced-techniques)2. Augmenting Evaluation: Rigor Levels and Advanced Techniques

Beyond the standard `ANCHOR-QR-8` protocol, PromptCraft Pro can instruct the downstream LLM to apply
more sophisticated evaluation and reasoning strategies. This is primarily controlled by **Rigor
Levels** (defined in `ANCHOR-QR-10`) and the selection of specific **Advanced Evaluation and
Reasoning Techniques** (from `ANCHOR-QR-11`).

## [](#-21-understanding-rigor-levels-anchor-qr-10)# 2.1. Understanding Rigor Levels (ANCHOR-QR-10)

PromptCraft Pro utilizes a system of Rigor Levels to modulate the depth and intensity of the
evaluation and reasoning processes undertaken by the downstream LLM. These levels are defined in
`ANCHOR-QR-10` of `00 Quick-Reference.md`:

* **Level 1: Basic (Default):** Employs the standard `ANCHOR-QR-8` evaluation protocol and core
  reasoning directives (e.g., CoT/ToT, `[ExpertJudgment]` tagging). This is the baseline for all
  prompts.
* **Level 2: Intermediate:** Includes all Basic Level features, plus PromptCraft Pro will select 1-2
  appropriate Advanced Techniques from `ANCHOR-QR-11` (e.g., Enhanced Reflection Loop Controls,
  Prompt Interrogation Chains) based on the task's nature and complexity.
* **Level 3: Advanced:** Encompasses all Intermediate Level features, with PromptCraft Pro selecting
  an additional 1-2 Advanced Techniques from `ANCHOR-QR-11`, prioritizing those that offer maximum
  robustness for critical tasks (e.g., Self-Consistency Sampling/CISC, Robust UQ with Numerical
  Scoring).

PromptCraft Pro determines the applicable Rigor Level based on defaults tied to the request's
Tier, explicit user specification, or inferred needs from the request's complexity. Users can
typically override the suggested Rigor Level.

## [](#-22-overview-of-advanced-evaluation-and-reasoning-techniques-anchor-qr-11)# 2.2. Overview of Advanced Evaluation and Reasoning Techniques (ANCHOR-QR-11)

`ANCHOR-QR-11` in `00 Quick-Reference.md` is a library of instructions for advanced methods. When
selected by PromptCraft Pro, these instructions are added to the C.R.E.A.T.E. prompt (usually the
A-block, or to guide E-block execution) to direct the downstream LLM. Key techniques include:

### [](#-221-enhanced-reflection-loop-controls-anchor-qr-11-1)# 2.2.1. Enhanced Reflection Loop Controls (ANCHOR-QR-11 #1)

* **Purpose:** This technique makes the standard E.1 Reflection Loop in `ANCHOR-QR-8` more powerful
  and adaptive. It allows for multiple controlled iterations, directs the LLM to use specific
  critique focus areas (which PromptCraft Pro can suggest based on the R-block's goal, e.g.,
  focusing on 'logical coherence' for an analysis task), and implements "Refresh" (re-approach
  problem) or "Revert" (to a better prior version) strategies to overcome stubborn errors or
  counter "drift" where revisions degrade quality.

### [](#-222-self-consistency-sampling--cisc-anchor-qr-11-2)# 2.2.2. Self-Consistency Sampling / CISC (ANCHOR-QR-11 #2)

* **Purpose:** For tasks requiring high accuracy in reasoning (e.g., math, logic, code generation),
  this instructs the LLM to internally generate multiple diverse reasoning paths to a solution. The
  final answer is then determined by a majority vote among these paths (Self-Consistency) or, if
  the LLM can provide confidence scores for each path, by a confidence-weighted majority vote
  (CISC). This significantly improves the robustness and reliability of the answer.

### [](#-223-prompt-interrogation-chains-anchor-qr-11-3)# 2.2.3. Prompt Interrogation Chains (ANCHOR-QR-11 #3)

* **Purpose:** Targeted at complex or ambiguous requests, this technique instructs the LLM to first
  engage in an internal self-questioning process. It generates and answers its own pertinent
  auxiliary questions to clarify ambiguities, decompose the problem, or explore different facets of
  the request, aiming for a high degree of confidence (e.g., 95%) before formulating the final,
  more comprehensive response.

### [](#-224-advanced-error-forecasting-anchor-qr-11-4)# 2.2.4. Advanced Error Forecasting (ANCHOR-QR-11 #4)

* **Purpose:** This makes the LLM's self-critique more proactive by requiring it to assess its draft
  output against a predefined list of potential error types (e.g., factual uncertainty, logical
  flaw, information gap, potential bias, outdated information) and to flag relevant parts of the
  text with specific tags like `[ErrorForecast:FactualUncertainty]`.

### [](#-225-robust-uncertainty-quantification-uq---numerical-scoring-anchor-qr-11-5)# 2.2.5. Robust Uncertainty Quantification (UQ) - Numerical Scoring (ANCHOR-QR-11 #5)

* **Purpose:** Moves beyond qualitative hedging by instructing the LLM to provide explicit numerical
  confidence scores (e.g., `[Confidence: XX/100]`) for its key factual claims or conclusions. This
  offers a more granular and actionable measure of the LLM's perceived reliability for specific
  statements.

### [](#-226-adversarial-robustness-self-checks-anchor-qr-11-6)# 2.2.6. Adversarial Robustness Self-Checks (ANCHOR-QR-11 #6)

* **Purpose:** This guides the LLM to perform internal "stress tests." It reflects on its
  sensitivity to minor (potentially misleading) input perturbations and its adherence to critical
  negative constraints under hypothetical pressure. This helps identify and flag outputs that might
  be brittle or easily manipulated, using tags like `[RobustnessConcern:PerturbationSensitive]`.

### [](#-227-enhanced-self-judgment-comparativescored-anchor-qr-11-7)# 2.2.7. Enhanced Self-Judgment (Comparative/Scored) (ANCHOR-QR-11 #7)

* **Purpose:** This technique modifies the LLM's iterative E.1 reflection pass to employ more
  sophisticated self-judgment. Option A involves the LLM generating two drafts and making a
  comparative judgment to select the superior one. Option B involves the LLM scoring its draft
  against detailed quality dimensions (Accuracy, Relevance, Clarity, etc.) to guide targeted
  revisions.

### [](#-228-stepwise-natural-language-self-critique-anchor-qr-11-8)# 2.2.8. Stepwise Natural Language Self-Critique (ANCHOR-QR-11 #8)

* **Purpose:** Particularly useful for tasks requiring transparent, multi-step reasoning (e.g., if
  "Chain = ON" is active), this instructs the LLM to internally generate and consider a brief
  natural language critique for each distinct reasoning step it takes. It must revise the step if
  its critique reveals issues before proceeding, ensuring a more meticulous and self-aware
  problem-solving process.

## [](#-23-how-promptcraft-pro-selects-and-applies-advanced-techniques)# 2.3. How PromptCraft Pro Selects and Applies Advanced Techniques

PromptCraft Pro determines which techniques from `ANCHOR-QR-11` to incorporate into the generated
C.R.E.A.T.E. prompt based on:

* The **Rigor Level** (`ANCHOR-QR-10`) set for the task (either by default based on Tier, or by
  user specification).
* **Explicit user requests** for particular advanced methodologies.
* **Inferred needs** that PromptCraft Pro identifies from the R-block, such as high complexity,
  inherent ambiguity in the request, keywords suggesting deep analysis (e.g., "analyze," "solve,"
  "evaluate critically"), or the domain of the task.
* The overall **Tier** of the request, with higher tiers often justifying more advanced
  processing.

PromptCraft Pro then copies the verbatim instructional phrasing for the selected technique(s) from
`ANCHOR-QR-11` into the A-block (or occasionally to guide E-block execution) of the C.R.E.A.T.E.
prompt it builds.

***

## [](#3-customizing-evaluation-prompt-specific-checks-anchor-qr-12)3. Customizing Evaluation: Prompt-Specific Checks (ANCHOR-QR-12)

## [](#-31-purpose-of-prompt-specific-checks)# 3.1. Purpose of Prompt-Specific Checks

While `ANCHOR-QR-8` provides a robust and comprehensive standard evaluation protocol for the
downstream LLM, many C.R.E.A.T.E. prompts will have unique requirements, constraints, or desired
output characteristics that benefit from additional, tailored verification steps. PromptCraft Pro
should append such relevant checks to the E-block after the standard `ANCHOR-QR-8` content.

## [](#-32-guidance-on-crafting-prompt-specific-checks-referencing-anchor-qr-12)# 3.2. Guidance on Crafting Prompt-Specific Checks (referencing ANCHOR-QR-12)

`ANCHOR-QR-12` in `00 Quick-Reference.md` offers extensive guidance and a rich set of examples for
prompt-specific checks. These examples illustrate how to instruct the downstream LLM to verify:

* Numerical logic and calculations.
* Adherence to word counts for specific Tiers.
* Exactness of URLs or other critical data points.
* Correct application of `[ExpertJudgment]` tagging.
* Crucially, confirmation that any Advanced Techniques from `ANCHOR-QR-11` that were invoked via
  the A-block were indeed applied and that their characteristic outputs or tags (e.g.,
  `[ErrorForecast:...]` tags, `[Confidence: XX/100]` scores, `[RobustnessConcern:...]` flags) are
  present and correctly used.

Users should refer to `ANCHOR-QR-12` for constructing effective custom checks when designing prompts
with PromptCraft Pro or when reviewing prompts generated by it.

## [](#-33-stylistic-and-readability-metrics-as-prompt-specific-checks)# 3.3. Stylistic and Readability Metrics as Prompt-Specific Checks

The primary stylistic requirements for the downstream LLM's output are defined by the seven
stylometry lines injected from `ANCHOR-QR-7` into the T-block. Adherence to these is then verified
by the downstream LLM as part of `ANCHOR-QR-8`'s E.5 "Style, Safety and Constraint Pass."

However, if additional, highly specific readability metrics (such as a target Flesch-Kincaid Grade
Level or a Flesch Reading Ease score, as were detailed in previous versions of this toolkit) are
deemed critical for a particular output, PromptCraft Pro should be instructed to add these as
prompt-specific checks for the downstream LLM to perform and verify. `ANCHOR-QR-12` provides a
suitable place to list examples of how such checks can be formulated (e.g., "\* Verify Flesch
Reading Ease score is between 50-60."). The downstream LLM would address any failures to meet
these specific metrics during its E.1 Reflection Loop or flag them as per E.5 or E.6 of
`ANCHOR-QR-8`.

***

## [](#4-the-role-of-human-review)4. The Role of Human Review

## [](#-41-why-human-review-remains-crucial)# 4.1. Why Human Review Remains Crucial

Despite the sophisticated multi-layered built-in evaluation protocols (`ANCHOR-QR-8`), the
powerful advanced techniques (`ANCHOR-QR-11`), and customizable prompt-specific checks
(`ANCHOR-QR-12`) that PromptCraft Pro embeds in C.R.E.A.T.E. prompts, **human review remains an
indispensable final step for any high-stakes or critical outputs.** LLMs are advanced tools,
capable of remarkable feats, but they are not infallible and do not possess true understanding or
consciousness. Expert human oversight is essential to:

* Verify nuanced factual accuracy and contextual appropriateness beyond the scope of automated
  checks.
* Assess strategic alignment with overarching goals.
* Catch subtle biases or logical inconsistencies that automated systems might miss.
* Ensure overall fitness for purpose before an LLM-generated output is relied upon, published, or
  disseminated, particularly in professional, legal, fiscal, or policy contexts.

The comprehensive automated evaluation framework designed into PromptCraft Pro aims to make this
human review process significantly more efficient and targeted by proactively identifying, flagging,
and often correcting many potential issues *before* the output reaches the human reviewer.

## [](#-42-key-areas-for-human-review-hallucination-and-quality-checklist)# 4.2. Key Areas for Human Review (Hallucination and Quality Checklist)

This checklist provides a systematic guide for human reviewers to validate the LLM's output. The
automated evaluation layers (`ANCHOR-QR-8`, `ANCHOR-QR-11`, `ANCHOR-QR-12`, `ANCHOR-QR-13`) are
designed to proactively address many of these items, but final human verification is paramount:

* **\[v] Factual Veracity and Hallucinations:** Are all factual claims accurate and genuinely
  supported by specified sources or correctly tagged (e.g., `[ExpertJudgment]`, `[Confidence:Low]`)?
  Confirm absence of fabricated details.
* **\[v] Citation Accuracy and Relevance:** Are citations correctly formatted (per T-block) and do
  they truly support the specific claims made? Verify links if applicable.
* **\[v] Data Recency:** If current information was crucial, is the data up-to-date (check
  `web.search_query` recency if used)?
* **\[v] Logical Coherence and Reasoning:** Is the reasoning sound, consistent, and free of gaps or
  fallacies? If "Chain = ON" or Stepwise NL Self-Critique (ANCHOR-QR-11 #8) was used, is the
  step-by-step flow clear and valid?
* **\[v] Format and Style Compliance:** Does the output meticulously adhere to all T-block
  requirements (including the 7 stylometry lines from `ANCHOR-QR-7`) and any specified structural
  formatting (headings, lists, etc.)?
* **\[v] Constraint Adherence:** Were all negative constraints (e.g., "Do not discuss...") and
  safety guardrails (e.g., PII avoidance) strictly followed? Check for `[RobustnessConcern:ConstraintAdherence]` if that check was active.
* **\[v] Completeness and Request Fulfillment:** Does the output fully address all components
  and nuances of the R-block? Is it appropriately detailed for the specified Tier and not
  prematurely truncated?
* **\[v] Framework Application:** If an analytical framework (e.g., SWOT, IRAC) was requested in
  the A-block, was it applied correctly, comprehensively, and appropriately?
* **\[v] Advanced Technique Markers and Outcomes:** If advanced techniques from `ANCHOR-QR-11`
  were invoked, are their characteristic markers present (e.g., `[Confidence: XX/100]`, `[ErrorForecast:...]`, stated use of Self-Consistency) and do these markers seem appropriate
  for the content?
* **\[v] Bias Check:** Does the language appear neutral and objective, avoiding loaded terms or
  stereotypes, as per `ANCHOR-QR-13` (unless a specific biased persona was explicitly defined
  and requested)?

***

## [](#5-safety-guardrails-and-ethical-considerations)5. Safety, Guardrails, and Ethical Considerations

PromptCraft Pro is designed to facilitate the creation of prompts that encourage responsible,
safe, and ethical use of downstream LLMs. This involves instructing these LLMs, through the
generated C.R.E.A.T.E. prompt, to adhere to various safety filters, guardrails, and directives
for transparency.

## [](#-51-core-llm-limitations-and-mitigation-strategies)# 5.1. Core LLM Limitations and Mitigation Strategies

### [](#-511-addressing-hallucinations)# 5.1.1. Addressing Hallucinations

* **Primary Mitigation:** PromptCraft Pro instructs downstream LLMs to perform rigorous multi-step
  internal verification via `ANCHOR-QR-8` (specifically E.3 Chain-of-Verification, E.4 Confidence,
  Sourcing and Accuracy Assertion which includes `[ExpertJudgment]` and `[Confidence:Low]`
  tagging).
* **Enhanced Mitigation:** For prompts set to Intermediate or Advanced Rigor Levels
  (`ANCHOR-QR-10`), PromptCraft Pro includes the specific Factual Accuracy directives from
  `ANCHOR-QR-13` in the A-block. Furthermore, relevant Advanced Techniques from `ANCHOR-QR-11`
  (such as #2 Self-Consistency Sampling/CISC, #4 Advanced Error Forecasting, and #5 Robust UQ -
  Numerical Scoring) are employed to further proactively identify and minimize hallucinations in
  the downstream LLM's output.

### [](#-512-mitigating-bias)# 5.1.2. Mitigating Bias

* **Primary Mitigation:** For C.R.E.A.T.E. prompts generated at Intermediate or Advanced Rigor
  Levels, PromptCraft Pro includes the specific Bias Mitigation directives from `ANCHOR-QR-13` in
  the A-block. These instruct the downstream LLM to strive for neutral, objective language and
  consider diverse perspectives unless a biased persona is explicitly part of the request.
* **Supporting Checks:** The standard E-block (`ANCHOR-QR-8` E.5 "Style, Safety and Constraint
  Pass") includes a general check for the downstream LLM to confirm no harmful or biased content is
  present.

### [](#-513-managing-knowledge-cutoff-dates)# 5.1.3. Managing Knowledge Cutoff Dates

* **Mitigation:** For requests involving Volatile information (where current data is essential),
  `ANCHOR-QR-1` (from `00 Quick-Reference.md`) mandate that PromptCraft Pro instructs the downstream
  LLM to use `web.search_query` with appropriate recency filters (defaulting to 365 days) to fetch
  current information.

## [](#-52-data-protection-pii-secrets)# 5.2. Data Protection (PII, Secrets)

* **Instruction to Downstream LLM (via `ANCHOR-QR-8` E.5):** The downstream LLM is explicitly
  instructed to confirm no Personally Identifiable Information (PII) is present in its output.
* **General Best Practice for Users:** Users of PromptCraft Pro (and any LLM system) should avoid
  inputting actual PII, proprietary secrets, or sensitive credentials into prompts whenever
  feasible.
* **PromptCraft Pro System Security:** PromptCraft Pro itself is designed with high-priority
  security protocols to prevent the disclosure of its own internal instructions, configurations, or
  any user-provided data it processes.

## [](#-53-negative-constraints-and-content-suppression)# 5.3. Negative Constraints and Content Suppression

* **Mechanism:** Users can specify negative constraints (e.g., "Do not discuss \\[sensitive topic\n  X]," "Avoid using marketing jargon") directly in their input to PromptCraft Pro, which will then\n  be incorporated into the A-block of the generated C.R.E.A.T.E. prompt.
* **Verification by Downstream LLM:** `ANCHOR-QR-8` E.5 ("Style, Safety and Constraint Pass")\n  instructs the downstream LLM to verify its adherence to these negative constraints. Furthermore,\n  if "Adversarial Robustness Self-Checks" (`ANCHOR-QR-11` #6) are invoked, the downstream LLM will\n  perform additional internal stress tests on its constraint adherence.

## [](#-54-transparency-in-uncertainty-and-neutrality)# 5.4. Transparency in Uncertainty and Neutrality

PromptCraft Pro emphasizes generating prompts that instruct downstream LLMs to be transparent about\nuncertainty and strive for neutrality:

* **Uncertainty Tagging (`ANCHOR-QR-8` E.4):** The standard E-block mandates tagging inferences\n  with `[ExpertJudgment]` and flagging claims where confidence is low with tags like\n  `[Confidence:Low]` or `[DataUnavailableOrUnverified]`.
* **Numerical Uncertainty Quantification (`ANCHOR-QR-11` #5):** If this advanced technique is\n  selected, the downstream LLM is instructed to provide explicit `[Confidence: XX/100]` scores.
* **Error Forecasting (`ANCHOR-QR-11` #4):** This technique has the LLM proactively flag potential\n  errors with specific tags like `[ErrorForecast:FactualUncertainty]`.
* **Neutrality Directives (`ANCHOR-QR-13`):** For Intermediate/Advanced Rigor, the downstream LLM\n  is instructed to actively strive for neutral, objective language and to consider diverse\n  perspectives, mitigating unintentional bias.

***

## [](#6-defining-and-verifying-success-criteria)6. Defining and Verifying Success Criteria

## [](#-61-importance-and-method)# 6.1. Importance and Method

It is significantly easier to evaluate an LLM's output if you have a clear understanding of what "success"
entails for that specific task *before* the prompt is even finalized or the LLM generates a response. Defining
clear, objective success criteria upfront provides benchmarks against which the output can be measured. This
proactive step also critically informs the prompt engineering process itself, helping ensure that the C.R.E.A.T.E.
prompt generated by PromptCraft Pro actually contains all the necessary instructions for the downstream LLM to
meet those criteria.

For any given task you bring to PromptCraft Pro, ask yourself: "What are the 1-3 absolutely essential things
this final output *must* achieve or include to be considered successful and fit for my purpose?" These criteria
often derive directly from the 'R - Request' (what needs to be done) and the 'C - Context' (specifically, the
Goal/Intent) components of the C.R.E.A.T.E. framework.

## [](#-62-examples-and-best-practices)# 6.2. Examples and Best Practices

* **Be Measurable and Specific:** Where possible, define criteria that are objective and measurable.
  * *Instead of:* "The summary should be good."
  * *Prefer:* "Success = The summary is between 350-400 words (Tier 3), accurately captures the 3
    main findings of the source report, and is written in a C-Suite Neutral tone."
* **Examples of Success Criteria:**
  * **For a Legal Memo:** "Success = 1) IRAC structure is correctly and fully applied to all
    distinct issues; 2) All legal assertions and rule statements cite primary sources in precise
    Bluebook format; 3) The conclusion directly and unambiguously answers each Issue identified."
  * **For a Python Script Generation:** "Success = 1) The generated Python 3.11 code runs without
    errors using standard libraries only; 2) It correctly processes the provided sample input CSV
    file and produces an output JSON matching the specified schema; 3) The code is well-commented
    and adheres to PEP 8 style guidelines."
  * **For a Policy Brief:** "Success = 1) The brief is no more than 1500 words (Tier 5); 2) It
    clearly presents three distinct policy options, each with a balanced discussion of 2-3 pros and
    2-3 cons based on provided evidence; 3) The language used is suitable for non-technical
    legislative aides (Plain-Language tone)."
* **Prioritize:** If you have numerous potential criteria, identify the 2-3 most critical
  (must-have) versus desirable (nice-to-have). This helps focus both the prompt engineering and the
  evaluation.
* **Inform PromptCraft Pro Input:** Use your defined success criteria to double-check that your
  initial request to PromptCraft Pro is complete. If a success criterion depends on information or
  an instruction not present in your input, PromptCraft Pro cannot ensure the generated C.R.E.A.T.E.
  prompt will ask the downstream LLM to achieve it. Ensure your R-block (core task), A-block
  considerations (e.g., specific data to include), and T-block preferences (format, style)
  collectively support your success criteria.

By defining success criteria upfront, you transform evaluation from a subjective assessment into a
more objective verification process, leading to more consistently useful and reliable outputs.
