# [](#02-request-blocksmd)02 Request-Blocks.md

**Version:** Request-Blocks Document v1.0, May 29, 2025
**Source Document:** AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework - v 1. (May 2025)
**ApproxTokens:** ~90k
**Purpose:** This document provides detailed explanations, guidance, and exemplars for formulating
effective 'Request' statements (the 'R' in C.R.E.A.T.E.) in AI prompts. It covers stating the
deliverable and format, controlling depth and length (including depth nouns and word-count mapping),
and using specific action verbs (deliverable verbs) with examples of good versus bad requests.

## [](#table-of-contents)Table of Contents

1. [Introduction to the Request in Prompting](#introduction-to-the-request-in-prompting)
   1. [ANCHOR-RB-1](#anchor-rb-1)
   2. [1. Stating the Deliverable and Format](#1-stating-the-deliverable-and-format)
      1. [1.1. Why It Matters](#11-why-it-matters)
      2. [1.2. How to Do It](#12-how-to-do-it)
      3. [1.3. Examples](#13-examples)
      4. [1.4. Specific Guidance and Best Practices](#14-specific-guidance-and-best-practices)
   3. [ANCHOR-RB-2](#anchor-rb-2)
   4. [2. Controlling Depth and Length](#2-controlling-depth-and-length)
      1. [2.1. Why It Matters](#21-why-it-matters)
      2. [2.2. How to Do It](#22-how-to-do-it)
      3. [2.3. Depth and Length Tiers (Table)](#23-depth-and-length-tiers-table)
      4. [2.4. IT-Specific Modes (Table)](#24-it-specific-modes-table)
      5. [2.5. Specific Guidance and Best Practices for Depth and Length](#25-specific-guidance-and-best-practices-for-depth-and-length)
   5. [ANCHOR-RB-3](#anchor-rb-3)
   6. [3. Using Action Verbs and Specificity](#3-using-action-verbs-and-specificity)
      1. [3.1. Why It Matters](#31-why-it-matters)
      2. [3.2. How to Do It](#32-how-to-do-it)
      3. [3.3. Examples of Strong Action Verbs](#33-examples-of-strong-action-verbs)
      4. [3.4. Examples of Improving Specificity (Good vs. Bad Requests)](#34-examples-of-improving-specificity-good-vs-bad-requests)
      5. [3.5. Specific Guidance and Best Practices for Action Verbs and Specificity](#35-specific-guidance-and-best-practices-for-action-verbs-and-specificity)
   7. [ANCHOR-RB-4](#anchor-rb-4)
   8. [4. White-Paper Deliverable Template](#4-white-paper-deliverable-template)

# [](#introduction-to-the-request-in-prompting)Introduction to the Request in Prompting

**Purpose:** Having set the stage with Context (C), the Request (R) is where you articulate the core
mission. This is the heart of your prompt - the direct instruction telling the LLM precisely *what*
you want it to *do*, *what deliverable* it should produce, and *how much* content is required.
Clarity and precision here are paramount; any ambiguity in the request can lead the AI astray, no
matter how good the context.

***

## [](#anchor-rb-1)ANCHOR-RB-1

## [](#1-stating-the-deliverable-and-format)1. Stating the Deliverable and Format

### [](#11-why-it-matters)1.1. Why It Matters

The LLM needs to know the *shape* of the answer you expect. Are you asking for a legal brief, a
code snippet, a bulleted list, a comprehensive report, or something else entirely? Specifying the
*deliverable* and its *format* upfront helps the model select the appropriate structure, sectioning,
and presentation style from the outset.

### [](#12-how-to-do-it)1.2. How to Do It

* Be explicit about the final product.
* Combine the deliverable with its format or standard where applicable.
* Refer to the Task component of the foundational checklist (from the main C.R.E.A.T.E. guide).

### [](#13-examples)1.3. Examples

* Draft an OMB A-4 compliant RIA (~5000 words) on \[rule].
* Prepare an RIA per Circular A-4 Section 5 for the emissions rule.
* Perform a comparative statutory analysis of ORS Section 170 vs WA Ch. 82.
* Build a STRIDE threat model for the new API.
* Map findings to the MITRE ATTandCK framework.
* Provide a <= 40-line Bash script to set up VLANs on Mikrotik.
* Draft an ASC 740 analysis for the COVID-relief credits.
* Generate a Fishbone Diagram for \[Defect].

### [](#14-specific-guidance-and-best-practices)1.4. Specific Guidance and Best Practices

* **Link to Frameworks:** Often, your chosen analytical framework (covered in Augmentations) will
  heavily imply the deliverable and format (e.g., IRAC analysis implies a legal memo structure).
  Stating it explicitly reinforces this.
* **Be Specific on Format:** If you need a specific output like JSON, Markdown, or a table, state it
  clearly. (Expert Judgment).

***

## [](#anchor-rb-2)ANCHOR-RB-2

## [](#2-controlling-depth-and-length)2. Controlling Depth and Length

### [](#21-why-it-matters)2.1. Why It Matters

A "Nano Answer" is useless when you need a "Monograph", and vice-versa. Controlling the depth and
length of the response is critical for:

* **Usability:** Ensuring the output matches the need (e.g., a C-suite brief must be concise).
* **Focus:** Preventing the AI from rambling or providing insufficient detail.
* **Cost/Token Management:** Keeping outputs within manageable limits, especially when using APIs.

### [](#22-how-to-do-it)2.2. How to Do It

* Use the established 'Depth Noun' tiers (see table below).
* Pair the noun with a specific word or token count for precision.
* Consider IT-specific length controls when applicable (see IT-Specific Modes table).

### [](#23-depth-and-length-tiers-table)2.3. Depth and Length Tiers (Table)

The canonical "Depth and Length Tiers" used by PromptCraft Pro are defined in **ANCHOR-QR-2** of the
`00 Quick-Reference.md` document. This table provides ten distinct tiers, from "Tier 1: Nano Answer"
to "Tier 10: Max-Window Synthese," with associated names, word/token counts, core use-cases, and
example triggers. Please refer to `ANCHOR-QR-2` for the definitive and most up-to-date information
on these tiers.

When PromptCraft Pro suggests a tier for your request, it will present a 3-row calibration table
derived from `ANCHOR-QR-2a`).

### [](#24-it-specific-modes-table)2.4. IT-Specific Modes (Table)

| Mode                    | Length and Format                      | Core Use-Case                                    | Example Trigger                                                |
|-------------------------|---------------------------------------|------------------------------------------------|----------------------------------------------------------------|
| Short Form CLI Snippet  | <= 40 lines of code or instructions    | Quick command-line examples or config snippets | Provide a <= 40-line Bash script to set up VLANs on Mikrotik. |
| Architecture Whitepaper | ~6000 words + ASCII/diagram           | Detailed network or system design with diagrams | Draft a ~6000-word network architecture paper with ASCII diagrams of Core-Dist-Access layers. |
| API-Walkthrough         | 800-1200 words                        | Integration tutorial with code blocks + sample JSON | Create an API walkthrough for integrating with the new payment gateway, including code examples and sample JSON responses. |
| Design-Doc              | 2000-3000 words                       | RFC-style architecture decision record (ADR)   | Write a design document outlining the architecture decisions for the new microservices platform. |

### [](#25-specific-guidance-and-best-practices-for-depth-and-length)2.5. Specific Guidance and Best Practices for Depth and Length

* **Prioritize Depth:** Place your depth/length selection *early* in the prompt, often right after the
  role or core task, to ensure it takes precedence over potentially conflicting style cues.
* **Plan for Limits:** For very long requests (Treatise, Max-Window), anticipate token limits and
  instruct the model on how to handle them using continuation markers: "If token limit reached, insert
  \===CONTINUE=== and resume."
* For multi-phase analyses, set the flag **Chain ON** to break the generation into numbered passes.

***

## [](#anchor-rb-3)ANCHOR-RB-3

## [](#3-using-action-verbs-and-specificity)3. Using Action Verbs and Specificity

### [](#31-why-it-matters)3.1. Why It Matters

While the *deliverable* defines the *what*, strong *action verbs* define the *how*, and *specificity*
ensures the *how* is applied correctly. Vague verbs ("Discuss...") or non-specific requests
("...about the new rule") invite the AI to make choices you might not intend. Clear verbs and high
specificity narrow the AI's focus, leading to more targeted and relevant outputs.

### [](#32-how-to-do-it)3.2. How to Do It

* **Choose Strong Verbs:** Select verbs that accurately reflect the cognitive task you want the AI to
  perform.
* **Be Hyper-Specific:** Don't assume the AI knows implied details. Spell out the exact focus areas,
  comparisons, or elements to include or exclude.
* **Break down complex requests** into smaller, specific sub-tasks if necessary. (Expert Judgment).

### [](#33-examples-of-strong-action-verbs)3.3. Examples of Strong Action Verbs

* **Information Retrieval/Generation:** List, Define, Summarize, Explain, Draft, Generate
* **Analysis/Comparison:** Analyze, Compare, Contrast, Evaluate, Map, Juxtapose
* **Problem Solving/Design:** Troubleshoot, Design, Model, Refactor, Optimize
* **Synthesis/Creation:** Synthesize, Create, Develop, Propose

### [](#34-examples-of-improving-specificity-good-vs-bad-requests)3.4. Examples of Improving Specificity (Good vs. Bad Requests)

**Example 1:**

* **Before (Vague/Bad):** Write about the Chevron doctrine.
* **After (Specific/Good):** Explain the Chevron two-step framework for judicial deference to agency
  interpretations. Analyze its current status, noting recent challenges and the potential impact of the
  Major-Questions doctrine, and provide one example of its application in an environmental law case.

**Example 2:**

* **Before (Vague/Bad):** Give me a Python script.
* **After (Specific/Good):** Generate a Python 3.11 script using Poetry. It should take a CSV file
  path as input, read the 'Revenue' column, calculate the total and average revenue, and output the
  results as a JSON object, following PEP 8 style with full type hints.

### [](#35-specific-guidance-and-best-practices-for-action-verbs-and-specificity)3.5. Specific Guidance and Best Practices for Action Verbs and Specificity

* **Avoid Ambiguity:** Reread your request. Could any word be interpreted in multiple ways? If so,
  clarify or define it.
* **Think Like a Task Manager:** If you were assigning this to a human analyst, what specific
  instructions would you give them? Provide that level of detail to the AI.
* **Influencing Advanced Processing:** Be aware that the nature, specificity, and complexity of your
  request (e.g., using action verbs that imply deep analysis, synthesis, multi-step problem-solving, or
  addressing ambiguous topics) can be key factors for PromptCraft Pro. These elements may lead it to:
  * Suggest or default to a higher **Rigor Level** (e.g., "Intermediate" or "Advanced" as defined in
    `ANCHOR-QR-10` of `00 Quick-Reference.md`).
  * Infer the need for and incorporate specific **Advanced Evaluation and Reasoning Techniques** (from
    `ANCHOR-QR-11` of `00 Quick-Reference.md`) into the C.R.E.A.T.E. prompt it generates for the
    downstream LLM.
  * For requests involving multiple distinct logical steps, PromptCraft Pro is instructed
    to prepend "Chain = ON" to the R-block and ensure the
    downstream LLM adds mini-state summaries, structuring the output for clarity.

## [](#anchor-rb-4)ANCHOR-RB-4

## [](#4-white-paper-deliverable-template)4. White-Paper Deliverable Template

Use this scaffold whenever a *white-paper-level* deliverable (>= 5000 words) is requested or inferred.

| Section | Target Share | Key Content | Word Guideline |
|---------|--------------|-------------|----------------|
| **Executive Summary** | ~10% | Problem, objectives, 3-5 takeaway bullets | 500-800 |
| **Analysis and Discussion** | ~70% | Background, evidence, reasoning, diagrams | 3500-4000 |
| **Next Steps / Recommendations** | ~10% | Action items, risk-impact grid | 500-800 |
| **References** | ~10% | Chicago-style footnotes + full citations | 500-800 |

> **Guidance for Requesting a White Paper:** When formulating an R-block request for a *White-Paper*
> deliverable, it's highly recommended to suggest or embed the four H2 section headers (Executive
> Summary, Analysis and Discussion, Next Steps/Recommendations, References) from the table above. You
> might also include the table itself as guidance for the desired structure and request confirmation
> or adjustment of each section's depth before full content generation. This level of detail will help
> PromptCraft Pro construct a more effective C.R.E.A.T.E. prompt for the downstream LLM.
