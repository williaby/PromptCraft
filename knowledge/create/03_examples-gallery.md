# [](#03-examples-gallerymd)03 Examples-Gallery.md

**Version:** Examples-Gallery Document v1.0, May 29, 2025
**Source Document:** AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework - v 1. (May 2025)
**ApproxTokens:** approximately 150 k
**Purpose:** This document explains the 'E' (Examples) component of the C.R.E.A.T.E. framework.
It details the importance of Few-Shot Prompting (In-Context Learning), guides users on when and how to
incorporate effective examples into their prompts, discusses potential pitfalls, and provides 
illustrative examples of how to structure such example-driven prompts. The examples provided 
herein are to show users *how to create good examples for their own prompts*.

## [](#table-of-contents)Table of Contents

1. [Introduction to Using Examples in Prompts (The "E" in C.R.E.A.T.E.)](#introduction-to-using-examples-in-prompts-the-e-in-create)
   1. [ANCHOR-EG-1](#anchor-eg-1)
2. [1. Why Examples Matter: The Power of Few-Shot Prompting](#1-why-examples-matter-the-power-of-few-shot-prompting)
   1. [ANCHOR-EG-2](#anchor-eg-2)
3. [2. When to Use Examples in Your Prompt](#2-when-to-use-examples-in-your-prompt)
   1. [ANCHOR-EG-3](#anchor-eg-3)
4. [3. How to Structure Effective Examples in Your Prompt](#3-how-to-structure-effective-examples-in-your-prompt)
   1. [ANCHOR-EG-4](#anchor-eg-4)
5. [4. Illustrative Examples of How to Construct In-Prompt Examples](#4-illustrative-examples-of-how-to-construct-in-prompt-examples)
   1. [4.1. Example Type: Tax (Exam-Style QandA)](#41-example-type-tax-exam-style-qanda)
      1. [The LLM would then complete the answer for the second question, following the demonstrated style and format](#the-llm-would-then-complete-the-answer-for-the-second-question-following-the-demonstrated-style-and-format)
   2. [4.2. Example Type: IT (RFC-Style Requirement)](#42-example-type-it-rfc-style-requirement)
      1. [The LLM would then generate the RFC-style output for the second input](#the-llm-would-then-generate-the-rfc-style-output-for-the-second-input)
   3. [4.3. Example Type: Legal (Simple IRAC Snippet)](#43-example-type-legal-simple-irac-snippet)
      1. [The LLM would then attempt to generate the Issue, Rule, Application, and Conclusion for the new facts provided](#the-llm-would-then-attempt-to-generate-the-issue-rule-application-and-conclusion-for-the-new-facts-provided)
   4. [ANCHOR-EG-5](#anchor-eg-5)
6. [5. Potential Pitfalls When Using Examples in Prompts](#5-potential-pitfalls-when-using-examples-in-prompts)
7. [Anchor Index of Example Types](#anchor-index-of-example-types)

## [](#introduction-to-using-examples-in-prompts-the-e-in-create)Introduction to Using Examples in Prompts (The "E" in C.R.E.A.T.E.)

**Purpose:** While Context (C) sets the scene and Request (R) defines the task, Examples (E) provide concrete
demonstrations of *how* you want that task executed. Often, *showing* the LLM what you want, through one or
more well-chosen examples (known as "Few-Shot Prompting" or "In-Context Learning"), is significantly more
effective than relying solely on instructions, especially for tasks involving specific formats, nuanced
styles, or complex reasoning patterns. It's the "Show, Don't Just Tell" principle applied to AI.

***

### [](#anchor-eg-1)ANCHOR-EG-1

## [](#1-why-examples-matter-the-power-of-few-shot-prompting)1. Why Examples Matter: The Power of Few-Shot Prompting

LLMs learn by identifying patterns. When you provide examples within your prompt, you give the model a
powerful, immediate pattern to latch onto. This helps to:

* **Reduce Ambiguity:** Instructions can sometimes be interpreted in multiple ways. An example provides a
  single, clear interpretation.
* **Enforce Formatting:** It's often easier to *show* a desired JSON structure, citation style, or report
  layout than to describe it in words.
* **Guide Style and Tone:** Demonstrating a specific voice (like "Exam-Style QandA") or a complex tone is
  more direct than just naming it.
* **Improve Novel Task Performance:** If your task is unusual or highly specific, examples give the model a
  crucial starting point.
* **Set Quality Standards:** High-quality examples encourage high-quality outputs.

Few-Shot Prompting (providing 1 to 5+ examples) leverages the "In-Context Learning" ability of LLMs,
allowing them to adapt their behaviour for the current task without needing retraining. It's a powerful way
to "program" the model on the fly.

***

### [](#anchor-eg-2)ANCHOR-EG-2

## [](#2-when-to-use-examples-in-your-prompt)2. When to Use Examples in Your Prompt

While not *every* prompt needs examples (simple, zero-shot requests can work well), they are particularly
beneficial when:

* **The Format is Critical:** You need output in a strict JSON, XML, Markdown table, specific code style, or
  a defined report structure.
* **The Style is Nuanced:** You require a very specific tone, voice, or linguistic pattern (e.g., RFC-style,
  Exam-Style QandA, or a specific Citation Style).
* **The Task is Complex or Novel:** The LLM might struggle to understand a complex set of instructions
  without a concrete demonstration.
* **Instructions are Ambiguous:** If you find your text-only prompts aren't yielding the right results,
  adding examples is a great next step.
* **You Need Consistency:** Providing examples helps ensure more consistent outputs across multiple runs.
* **Demonstrating Reasoning (Carefully):** While Chain-of-Thought (covered in Augmentations) is often better
  for *explicit* reasoning, examples can demonstrate a *pattern* of analysis (like a mini-IRAC).

***

### [](#anchor-eg-3)ANCHOR-EG-3

## [](#3-how-to-structure-effective-examples-in-your-prompt)3. How to Structure Effective Examples in Your Prompt

Crafting good examples to include in your prompt is key to their success:

* **Be Consistent:** Ensure your examples *perfectly* match the format, style, and quality you desire in the
  final output from the LLM. Any errors or inconsistencies in your examples may be replicated by the model.

* **Use Clear Delimiters:** Separate your examples from each other and from the rest of the prompt. Use clear
  labels like `Input:`, `Output:`, `Q:`, `A:`, or structured markers such as:

  ```markdown
  ### Example 1 ###
  Input: [Your Input Here]
  Output: [Your Desired Output Here]
  ### End Example 1 ###
  ```

* **Keep it Relevant:** Choose examples that are as close as possible to the *actual* task you want the AI
  to perform. Irrelevant examples can confuse the model.

* **Start Small (1-3 Examples):** Often, one to three well-chosen examples are sufficient. More examples
  consume valuable context window space and don't always lead to better results. Experiment to find the
  sweet spot.

* **Placement Matters:** Typically, examples should come *after* your main Context and Request, but *before*
  your final instruction (the one you want the AI to act upon).

* **Note for PromptCraft Pro Users:** When you provide such structured examples in your input to PromptCraft
  Pro, they will be placed into the 'E - Examples' section of the C.R.E.A.T.E. prompt that PromptCraft Pro
  generates. PromptCraft Pro is designed to handle this placement. If you do not provide an example for a
  task where one might be beneficial, PromptCraft Pro will populate the 'E - Examples' block according to
  its standard procedure, which is:
  * It will insert: `(N/A: R and T specify format.)` if the Request and Tone/Format blocks are deemed
    sufficient to guide the output format.
  * It may use a generic placeholder like `1. <Item> - <1-2 sentence description>` if some structural
    illustration is needed by the downstream LLM and you haven't provided a specific example.

***

### [](#anchor-eg-4)ANCHOR-EG-4

## [](#4-illustrative-examples-of-how-to-construct-in-prompt-examples)4. Illustrative Examples of How to Construct In-Prompt Examples

The following sections demonstrate how you, the user, might structure few-shot examples when providing
your initial input *to PromptCraft Pro*. PromptCraft Pro will then take these examples and incorporate them
into the 'E - Examples' section of the full C.R.E.A.T.E. prompt it generates. This generated C.R.E.A.T.E.
prompt, with your examples embedded, is then used to guide the downstream LLM.

The key is to show PromptCraft Pro the desired input/output pattern or style you expect from the downstream
LLM.

### [](#41-example-type-tax-exam-style-qanda)4.1. Example Type: Tax (Exam-Style QandA)

If you want the LLM to answer tax questions in a specific QandA format, citing relevant IRC sections, you
could include an example like this in your prompt:

```markdown
## # Example ###
Q: Is a gift received from an employer taxable income under IRC Section 61?
A: Generally, yes. While IRC Section 102 excludes gifts from gross income, transfers from an employer to an 
   employee are typically not considered excludable gifts due to the employer-employee relationship and are 
   included under IRC Section 61(a)(1) as compensation for services. See Treas. Reg. Section 1.61-2(a)(1) 
   and Comm'r v. Duberstein, 363 U.S. 278 (1960).
## # End Example ###

Q: Is interest received on State bonds taxable income under IRC Section 61?
A: 
```

#### [](#the-llm-would-then-complete-the-answer-for-the-second-question-following-the-demonstrated-style-and-format)The LLM would then complete the answer for the second question, following the demonstrated style and format

### [](#42-example-type-it-rfc-style-requirement)4.2. Example Type: IT (RFC-Style Requirement)

If you need the LLM to rephrase system requirements into a formal, RFC-style, you could show it an example:

```markdown
## # Example ###
Input: The system must authenticate users before granting access.
Output: 1.1. User Authentication
         The system MUST authenticate all users via the central IDP (Identity Provider) before granting 
         access to any non-public resource.
## # End Example ###

Input: The system should log all failed login attempts.
Output:
```

#### [](#the-llm-would-then-generate-the-rfc-style-output-for-the-second-input)The LLM would then generate the RFC-style output for the second input

### [](#43-example-type-legal-simple-irac-snippet)4.3. Example Type: Legal (Simple IRAC Snippet)

To guide an LLM to produce a concise IRAC analysis for a given set of facts, you might include:

```markdown
## # Example ###
Facts: A person finds a lost wallet on a public sidewalk.
Issue: Is the finder legally entitled to keep the wallet?
Rule: Under property law, the finder of lost property generally has a right superior to all except the true 
      owner. However, this varies by jurisdiction.
Application: The person found the wallet, which appears lost, not abandoned. They must typically take 
             reasonable steps to locate the true owner.
Conclusion: The finder has a conditional right, subordinate to the true owner, and must act responsibly.
## # End Example ###

Facts: [Provide your new facts here for the LLM to analyze]
Issue:
```

#### [](#the-llm-would-then-attempt-to-generate-the-issue-rule-application-and-conclusion-for-the-new-facts-provided)The LLM would then attempt to generate the Issue, Rule, Application, and Conclusion for the new facts provided

***

### [](#anchor-eg-5)ANCHOR-EG-5

## [](#5-potential-pitfalls-when-using-examples-in-prompts)5. Potential Pitfalls When Using Examples in Prompts

Be aware of potential challenges when embedding examples in your prompts:

* **Bias:** Your examples might inadvertently introduce or amplify biases if not carefully constructed.
* **Overfitting:** The model might just mimic the *surface structure* of your examples without understanding
  the underlying principle you're trying to teach. Vary your examples if this becomes an issue.
* **Context Cost:** Examples use up tokens in the prompt, which can be a concern with models that have
  smaller context windows or when using APIs where token count affects cost. Be concise.
* **Order Sensitivity:** Some models can be sensitive to the order in which examples are presented. If
  results are inconsistent, try reordering your examples.

***

## [](#anchor-index-of-example-types)Anchor Index of Example Types

* [Tax (Exam-Style QandA)](#41-example-type-tax-exam-style-qanda)
* [IT (RFC-Style Requirement)](#42-example-type-it-rfc-style-requirement)
* [Legal (Simple IRAC Snippet)](#43-example-type-legal-simple-irac-snippet)
