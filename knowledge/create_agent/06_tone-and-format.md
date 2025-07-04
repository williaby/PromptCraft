# [](#06-tone-and-formatmd)06 Tone-and-Format.md

**Version:** Tone-Format Document v1.0, May 31, 2025
**Source Document:** AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework - v 1. (May 2025)
**Purpose:** This document details the 'T' (Tone and Format) component of the C.R.E.A.T.E. framework.
It explains how to shape the AI's output by selecting appropriate tones and voices (style palettes),
employing rhetorical devices (including PromptCraft Pro defaults), defining how citations should be
styled for presentation, and controlling overall structural formatting (including Markdown best
practices consistent with PromptCraft Pro's rules).

## [](#table-of-contents)Table of Contents

1. [Introduction to Tone and Format in Prompting](#introduction-to-tone-and-format-in-prompting)
2. [ANCHOR-TF-1](#anchor-tf-1)
3. [1. Selecting Tone and Voice (Style Palettes)](#1-selecting-tone-and-voice-style-palettes)
   1. [1.1. Why Selecting Tone and Voice Matters](#11-why-selecting-tone-and-voice-matters)
   2. [1.2. How to Select Tone and Voice](#12-how-to-select-tone-and-voice)
   3. [1.3. Tone and Voice Descriptors (Table)](#13-tone-and-voice-descriptors-table)
   4. [1.4. Specific Guidance and Best Practices for Tone and Voice](#14-specific-guidance-and-best-practices-for-tone-and-voice)
4. [ANCHOR-TF-2](#anchor-tf-2)
5. [2. Defining Citation Styles and Format (Presentation)](#2-defining-citation-styles-and-format-presentation)
   1. [2.1. Why Defining Citation Presentation Matters](#21-why-defining-citation-presentation-matters)
   2. [2.2. How to Define Citation Style and Format in Prompts](#22-how-to-define-citation-style-and-format-in-prompts)
   3. [2.3. Example Triggers for Citation Presentation](#23-example-triggers-for-citation-presentation)
   4. [2.4. Specific Guidance for Citation Presentation](#24-specific-guidance-for-citation-presentation)
6. [ANCHOR-TF-3](#anchor-tf-3)
7. [3. Employing Rhetorical and Stylistic Devices](#3-employing-rhetorical-and-stylistic-devices)
   1. [3.1. Why Employing Rhetorical Devices Matters](#31-why-employing-rhetorical-devices-matters)
   2. [3.2. How to Employ Rhetorical Devices](#32-how-to-employ-rhetorical-devices)
   3. [3.3. Rhetorical and Stylistic Devices (Table)](#33-rhetorical-and-stylistic-devices-table)
   4. [3.4. Specific Guidance and Best Practices for Rhetorical Devices](#34-specific-guidance-and-best-practices-for-rhetorical-devices)
   5. [3.5 Hedge Density](#35-hedge-density)
   6. [3.6 Lexical Diversity (Type-Token Ratio)](#36-lexical-diversity-type-token-ratio)
   7. [3.7 Sentence Length Variability](#37-sentence-length-variability)
   8. [3.8 Additional Auto-Injected Stylometry, Tone, and Punctuation Directives (PromptCraft Pro Defaults)](#38-additional-auto-injected-stylometry-tone-and-punctuation-directives-promptcraft-pro-defaults)
8. [ANCHOR-TF-4](#anchor-tf-4)
9. [4. Controlling Structural Formatting (Markdown Guidance)](#4-controlling-structural-formatting-markdown-guidance)
   1. [4.1. Why Controlling Structural Formatting Matters](#41-why-controlling-structural-formatting-matters)
   2. [4.2. How to Control Structural Formatting](#42-how-to-control-structural-formatting)
   3. [4.3. Example Formatting Triggers and Commands](#43-example-formatting-triggers-and-commands)
   4. [4.4. Specific Guidance and Best Practices for Structural Formatting](#44-specific-guidance-and-best-practices-for-structural-formatting)

## [](#introduction-to-tone-and-format-in-prompting)Introduction to Tone and Format in Prompting

You've set the Context (C), defined the Request (R), provided Examples (E), and added Augmentations (A).
Now, you need to define the *presentation* - how the final output should look and feel. Tone and Format
(T) covers everything from the voice and stylistic flair of the language to the structural layout,
including headings, lists, and citation formatting. Getting this right is crucial for ensuring the
output is not only accurate but also readable, appropriate for its audience, and compliant with any
relevant standards.

***

## [](#anchor-tf-1)ANCHOR-TF-1

## [](#1-selecting-tone-and-voice-style-palettes)1. Selecting Tone and Voice (Style Palettes)

### [](#11-why-selecting-tone-and-voice-matters)1.1. Why Selecting Tone and Voice Matters

The 'voice' of the output dramatically affects how it's received. A Formal / Scholarly tone lends
authority to a legal brief, while a Warm / Conversational tone is better for client letters. Choosing
the right tone ensures your message resonates correctly with its intended audience.

### [](#12-how-to-select-tone-and-voice)1.2. How to Select Tone and Voice

Use domain-aware style descriptors to shape diction, cadence, and formality. Select one or more
triggers (see table below), and if combining potentially conflicting tones, specify a priority
(see Tone Hierarchy in Rhetorical Devices).

### [](#13-tone-and-voice-descriptors-table)1.3. Tone and Voice Descriptors (Table)

| Descriptor                   | Domain             | Signals                                                | Trigger Snippet                                          |
|------------------------------|--------------------|--------------------------------------------------------|----------------------------------------------------------|
| Formal / Scholarly           | General, Legal     | Latinate vocabulary; passive constructions; footnotes  | “Use a formal scholarly tone with citations.”            |
| Warm / Conversational        | Client Letters     | Contractions; second-person (“you”); plain language    | “Explain in plain English, suitable for clients.”        |
| RFC-style                    | IT Documentation   | Numbered MUST/SHOULD; requirement language             | “Respond in RFC-style prose with MUST/SHOULD.”           |
| Authoritative Practitioner   | Tax                | Inline statute/reg citations; directive language       | “Write as an authoritative practitioner.”                |
| C-Suite Neutral              | Fiscal, Policy     | Executive summary; bullet lists; no jargon             | “Provide a C-suite brief with key bullets.”              |
| Exam-Style QandA               | Tax, Compliance    | Question headers; IRC Section citations; concise answers       | “Answer in exam-style, cite IRC Section 61(a)(1).”             |
| Plain-Language               | Public-Policy      | Minimal jargon; analogies; simple sentences            | “Use plain-language suitable for non-technical readers.” |
| Peer-Code-Review             | Software Dev       | Comment tags; style checks; inline suggestions         | “Provide peer-code-review comments per Google standard.” |

### [](#14-specific-guidance-and-best-practices-for-tone-and-voice)1.4. Specific Guidance and Best Practices for Tone and Voice

* **Combine Carefully:** You can mix tones (e.g., Formal + Analogies), but if there's a risk of clashing,
  use a Tone Hierarchy directive (see Section 3.3) like: "Maintain formal tone; allow conversational
  analogies only."

***

## [](#anchor-tf-2)ANCHOR-TF-2

## [](#2-defining-citation-styles-and-format-presentation)2. Defining Citation Styles and Format (Presentation)

### [](#21-why-defining-citation-presentation-matters)2.1. Why Defining Citation Presentation Matters

While *what* evidence to cite is covered under Augmentations, *how* those citations are presented is a
key aspect of Tone and Format. Consistent and accurate citation formatting is non-negotiable in many
professional fields for credibility and traceability. Simply asking for "citations" isn't enough for
presentation; you must specify the *style guide* and desired *visual format*.

### [](#22-how-to-define-citation-style-and-format-in-prompts)2.2. How to Define Citation Style and Format in Prompts

* **Name the Guide:** Explicitly state the citation manual to enforce its specific formatting rules
  (e.g., Bluebook, Chicago Manual of Style, APA 7th). This tells the LLM which set of presentation rules
  to follow.
* **Specify Format:** Indicate whether you prefer inline parenthetical citations, superscript numbers
  for footnotes/endnotes, or another specific visual layout for the citations within the text.

### [](#23-example-triggers-for-citation-presentation)2.3. Example Triggers for Citation Presentation

* “Cite 26 U.S.C. Section 61... in Bluebook format using inline parenthetical citations.”
* “Use superscript footnotes following the Chicago Manual of Style for all references.”
* “Format all citations as APA 7th style, with a full reference list at the end.”

### [](#24-specific-guidance-for-citation-presentation)2.4. Specific Guidance for Citation Presentation

* **Placement of Instruction:** Like other formatting instructions, place citation style directives
  clearly, often before word-count limits, to ensure they are applied.
* **Clarity on End Product:** If a full bibliography or reference list is required in addition to in-text
  citations, state this explicitly.

***

## [](#anchor-tf-3)ANCHOR-TF-3

## [](#3-employing-rhetorical-and-stylistic-devices)3. Employing Rhetorical and Stylistic Devices

### [](#31-why-employing-rhetorical-devices-matters)3.1. Why Employing Rhetorical Devices Matters

Beyond the base tone, specific rhetorical devices can enhance engagement, improve clarity for certain
audiences, and add a layer of polish to the output. These are stylistic nuances that can make the
content more effective.

### [](#32-how-to-employ-rhetorical-devices)3.2. How to Employ Rhetorical Devices

Embed trigger snippets (usually after depth/framework commands) to adjust only the style. For
PromptCraft Pro, specific directives are auto-injected as detailed below.

### [](#33-rhetorical-and-stylistic-devices-table)3.3. Rhetorical and Stylistic Devices (Table)

*Note: PromptCraft Pro defaults to injecting a specific combination of rhetorical devices for human-like
cadence. See Section 3.8 for these default auto-injected directives.*

| Device                       | Effect                                                              | Trigger Snippet                                                      |
|------------------------------|---------------------------------------------------------------------|----------------------------------------------------------------------|
| Analogies for Lay Readers    | Generates clear metaphors linking complex concepts to familiar ideas| “Incorporate analogies for non-technical readers.”                   |
| Rhetorical Questions         | Introduces Socratic hooks to engage the reader                      | “Use rhetorical questions to prompt reflection.”                     |
| Sentence-Length Burstiness   | Varies sentence cadence (mix of short and long)                       | “Encourage sentence-length burstiness (12-24 words avg).”            |
| Dry Wit / Mild Humour        | Inserts light humour without informal tone                          | “Add a touch of dry wit, no more than one quip per section.”         |
| Negative Constraints         | Suppresses unwanted patterns (e.g., bigrams, emojis)                | “Avoid bigrams and limit exclamation marks.”                         |
| Voice Perspective            | Switches between first/second/third person                          | “Write in second person, addressing the reader as ‘you.’”             |
| Tone Hierarchy               | Resolves conflicting tone descriptors by priority                   | “Maintain formal tone; allow conversational analogies only.”         |

### [](#34-specific-guidance-and-best-practices-for-rhetorical-devices)3.4. Specific Guidance and Best Practices for Rhetorical Devices

* **Subtlety is Key:** Combine only one or two devices for a subtle effect, rather than overwhelming
  the output.
* **Example:** "Draft a policy memo. Encourage sentence-length burstiness and incorporate analogies for
  lay readers, but avoid emojis."
* Analogy v / Case v if helps clarity.

### [](#35-hedge-density)3.5 Hedge Density

*PromptCraft Pro Default Injection: **Moderate Hedge***

| Level              | Specs                                                      | When to use                                                                             |
| ------------------ | ---------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Low Hedge** | \* 0-2 % of sentences include a hedge (“perhaps,” “likely”) | Direct, authoritative tone; best for final recommendations or strict guidelines         |
| **Moderate Hedge** | \* ~5-10 % of sentences contain a hedge                     | Balanced technical-human blend; suitable for research summaries where nuance is key. **(PCP Default: Moderate 5-10%)** |
| **High Hedge** | \* ~15-20 % sentences hedged                               | Exploratory or uncertain analyses; highlights open questions or calls for further study |

### [](#36-lexical-diversity-type-token-ratio)3.6 Lexical Diversity (Type-Token Ratio)

*PromptCraft Pro Default Injection: **High Diversity equivalent with specific directives***

| Level                  | Specs                                                      | When to use                                                                              |
| ---------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Moderate Diversity** | \* No single content word > 3 % of total tokens             | Good baseline for technical writing-avoids repetition without compromising cohesion      |
| **High Diversity** | \* No word > 2 % of tokens; avoid repeating exact bigrams   | Strong human-like signal; ideal when you really need to dodge detector flags. **(PCP Default Target: TTR >= 0.40; no word > 2 % tokens; avoid clichés like “delve into”, “crucial”)** |
| **Maximum Diversity** | \* No word > 1 % of tokens; actively swap synonyms each use | Very creative or narrative contexts; may hamper terminology consistency in dense reports |

### [](#37-sentence-length-variability)3.7 Sentence Length Variability

*PromptCraft Pro Default Injection: **High Variability equivalent with specific directives***

| Level                    | Specs                                                                                         | When to use                                                                                       |
| ------------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Low Variability** | \* Avg 16-18 words/sentence +/- 2 words (std dev approximately 2)                                            | Crisp, easy reading; best for executive summaries or very formal legal text                       |
| **Moderate Variability** | *Avg 14-20 words +/- 5 words (std dev approximately 5) <br>* ~10 % sentences < 8 words, ~10 % > 25 words | Balanced human-like feel; suits most technical reports where clarity and natural tone both matter |
| **High Variability** | *Avg 12-24 words +/- 8 words (std dev approximately 8) <br>* ~20 % < 8 words, ~20 % > 30 words           | Highly conversational or narrative pieces; maximizes burstiness but can reduce skimmability. **(PCP Default Target: Avg 17-22 w; >= 15 % < 8 w and >= 15 % > 30 w; sigma >= 8)** |

### [](#38-additional-auto-injected-stylometry-tone-and-punctuation-directives-promptcraft-pro-defaults)3.8 Additional Auto-Injected Stylometry, Tone, and Punctuation Directives (PromptCraft Pro Defaults)

The following directives are auto-injected by PromptCraft Pro into the target prompt’s **T - Tone and Format** block.
These are applied by default unless Style-Seed Analysis provides overriding metrics or the user specifies differently.

* **Rhetorical Devices (Specific Default):**
  * **Directive:** >= 1 rhetorical Q **and** >= 1 first-person or direct-address aside.
  * **Why:** To achieve a human-like cadence in the output.
* **Paragraph Pacing:**
  * **Directive:** Mix short (2-3 sent) and long (4-6 +) paras with smooth transitions.
  * **Why:** To enhance reader flow and engagement.
* **Conversational Tone Elements:**
  * **Directive:** Use contractions (e.g., "it's", "don't"); **no em-dashes;** lists only if user asked for them.
  * **Why:** To ensure a natural yet rule-compliant output, avoiding overly formal or stiff language unless specifically requested.
* **Overall Punctuation and Structure Guidance (for target LLM output):**
  * **Directive:** Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.** Output should be narrative prose; avoid bullet/number lists unless the user explicitly requests steps or lists.
  * **Why:** To enforce a consistent, clean, and readable punctuation style aligned with PromptCraft Pro's guard-rails.

***

## [](#anchor-tf-4)ANCHOR-TF-4

## [](#4-controlling-structural-formatting-markdown-guidance)4. Controlling Structural Formatting (Markdown Guidance)

### [](#41-why-controlling-structural-formatting-matters)4.1. Why Controlling Structural Formatting Matters

A well-structured document is easier to read, understand, and use. Clear headings, lists, and code
blocks guide the reader's eye and organize complex information. Failing to specify format can lead to
errors or an unreadable "wall of text". PromptCraft Pro enforces certain structural rules by default
(e.g., avoidance of em-dashes and unsolicited lists).

### [](#42-how-to-control-structural-formatting)4.2. How to Control Structural Formatting

* **Use Formatting Commands:** Explicitly tell the AI how to structure the document using Markdown or
  other formatting cues, especially if you need to override PromptCraft Pro's defaults (e.g., if you
  *do* want lists).
* **Leverage Templates:** Base-Mode Blocks and Domain-Specific Templates (from the main guide) often
  include implicit or explicit formatting rules.

### [](#43-example-formatting-triggers-and-commands)4.3. Example Formatting Triggers and Commands

* “Use H2/H3 headings for main sections and sub-sections, respectively.”
* “Present the steps as a numbered list.” (Explicitly asking for a list)
* “Wrap code in triple backticks using Python syntax highlighting.”
* “Format as 5 x 5 rule (<=5 bullets of <=5 words per slide).” (For presentation slide content)
* “Use inline CSV / Markdown tables (definitions adjacent).”
* “Ensure all Markdown is valid.”

### [](#44-specific-guidance-and-best-practices-for-structural-formatting)4.4. Specific Guidance and Best Practices for Structural Formatting

* **Be Explicit for Overrides:** Don't assume the model knows what "a standard report format" means if
  it differs from PromptCraft Pro's defaults (e.g., regarding lists or em-dashes). Specify heading
  levels (H1, H2, H3, etc.), list types (bulleted, numbered), table formats, and code block conventions.
* **Semantic Heading Hierarchy:** Maintain a logical heading hierarchy (H1 -> H2 -> H3 -> H4 -> H5 -> H6).
  This is crucial so screen readers and automated converters (e.g., to HTML, PDF/UA) can navigate the
  document effectively. This complies with accessibility standards like WCAG 2.2 and Section 508 of the
  Rehabilitation Act.
* **QA Check for Formatting:** For critical documents, consider adding a step in your prompt's
  Evaluation component (or as a post-generation check) to: "Ensure markdown validity (headers, lists,
  code blocks properly rendered)."
