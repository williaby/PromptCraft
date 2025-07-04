# [](#10-few-shot-gallerymd)10 Few-Shot-Gallery.md

**Version**: Few-Shot Gallery v1.2, May 30, 2025
**Source Document**: AI Prompt Engineering Guide - The C.R.E.A.T.E. Framework v1 (May 2025)
**ApproxTokens**: approximately 50k (Note: This will increase as more examples are added)
**Purpose**: Curated collection of extended C.R.E.A.T.E. prompt exemplars that are too large for the
main instruction block. Each example demonstrates how PromptCraft Pro(TM) should transform user input
into a high-quality C.R.E.A.T.E. prompt. These examples sit under unique
`## ANCHOR-FS-[DOMAIN_CODE]-[ID]` headings so the Custom GPT can potentially vector-retrieve and
imitate detailed patterns without bloating its core instructions.

## [](#table-of-contents)Table of Contents

1. 1. [ANCHOR-FS-GENERAL](#anchor-fs-general)
   2. [1. General Analysis](#1-general-analysis)
   3. [ANCHOR-FS-GENERAL-1.1](#anchor-fs-general-11)
   4. [1.1. Ethical Implications of AI in Hiring - Tier 6](#11-ethical-implications-of-ai-in-hiring---tier-6)
      1. 1. [User Input](#user-input)
         2. [PromptCraft Pro Output](#promptcraft-pro-output)
   5. [ANCHOR-FS-GENERAL-1.2](#anchor-fs-general-12)
   6. [1.2. Chemical Symbol Lookup - Tier 1](#12-chemical-symbol-lookup---tier-1)
      1. 1. [USER PROMPT](#user-prompt)
         2. [PromptCraft Pro Output](#promptcraft-pro-output-1)
   7. [ANCHOR-FS-GENERAL-1.3](#anchor-fs-general-13)
   8. [1.3. Meeting Takeaways Snapshot - Tier 2](#13-meeting-takeaways-snapshot---tier-2)
      1. 1. [User Input](#user-input-1)
         2. [PromptCraft Pro Output](#promptcraft-pro-output-2)
   9. [ANCHOR-FS-GENERAL-1.4](#anchor-fs-general-14)
   10. [1.4. Product Description to JSON Extraction (with In-Prompt Examples) - Tier 1 (for JSON Output)](#14-product-description-to-json-extraction-with-in-prompt-examples---tier-1-for-json-output)
       1. 1. [User Input](#user-input-2)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-3)
   11. [ANCHOR-FS-LEGAL](#anchor-fs-legal)
   12. [2. Legal](#2-legal)
   13. [ANCHOR-FS-LEGAL-2.1](#anchor-fs-legal-21)
   14. [2.1. Cease and Desist Letter (Copyright Infringement) - Tier 3](#21-cease-and-desist-letter-copyright-infringement---tier-3)
       1. 1. [User Input](#user-input-3)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-4)
   15. [ANCHOR-FS-LEGAL-2.2](#anchor-fs-legal-22)
   16. [2.2. Oregon Travel Ethics: Research Brief and Advice Letter - Tier 7 (Brief) / Tier 3 (Letter)](#22-oregon-travel-ethics-research-brief-and-advice-letter---tier-7-brief--tier-3-letter)
       1. 1. [User Input](#user-input-4)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-5)
   17. [ANCHOR-FS-FISCAL](#anchor-fs-fiscal)
   18. [3. Fiscal](#3-fiscal)
   19. [ANCHOR-FS-FISCAL-3.1](#anchor-fs-fiscal-31)
   20. [3.1. UBI Pilot Program Fiscal Impact Analysis - Tier 7](#31-ubi-pilot-program-fiscal-impact-analysis---tier-7)
       1. 1. [User Input](#user-input-5)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-6)
   21. [ANCHOR-FS-POLICY](#anchor-fs-policy)
   22. [4. Policy and Program](#4-policy-and-program)
   23. [ANCHOR-FS-POLICY-4.1](#anchor-fs-policy-41)
   24. [4.1. National Parks Plastic Waste Reduction Policy Monograph - Tier 8](#41-national-parks-plastic-waste-reduction-policy-monograph---tier-8)
       1. 1. [User Input](#user-input-6)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-7)
   25. [ANCHOR-FS-ITSEC](#anchor-fs-itsec)
   26. [5. IT and Security](#5-it-and-security)
   27. [ANCHOR-FS-ITSEC-5.1](#anchor-fs-itsec-51)
   28. [5.1. Zero Trust Architecture Report - Tier 5](#51-zero-trust-architecture-report---tier-5)
       1. 1. [User Input](#user-input-7)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-8)
   29. [ANCHOR-FS-ITSEC-5.2](#anchor-fs-itsec-52)
   30. [5.2. SSO Definition One-Liner - Tier 1](#52-sso-definition-one-liner---tier-1)
       1. 1. [User Input](#user-input-8)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-9)
   31. [ANCHOR-FS-ITSEC-5.3](#anchor-fs-itsec-53)
   32. [5.3. Future Today Strategy Group 2025 Tech Trends Report Highlights - Tier 2](#53-future-today-strategy-group-2025-tech-trends-report-highlights---tier-2)
       1. 1. [User Input](#user-input-9)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-10)
   33. [ANCHOR-FS-TAXACC](#anchor-fs-taxacc)
   34. [6. Tax and Accounting](#6-tax-and-accounting)
   35. [ANCHOR-FS-TAXACC-6.1](#anchor-fs-taxacc-61)
   36. [6.1. Earned Income Credit Overview - Tier 4](#61-earned-income-credit-overview---tier-4)
       1. 1. [User Input](#user-input-10)
          2. [PromptCraft Pro Output](#promptcraft-pro-output-11)
   37. [ANCHOR-FS-COMPGLOB](#anchor-fs-compglob)
2. [7. Comparative / Global](#7-comparative--global)
   1. [ANCHOR-FS-COMPGLOB-7.1](#anchor-fs-compglob-71)
   2. [7.1. Renewable Energy Strategies (Germany vs. Japan) - Tier 9](#71-renewable-energy-strategies-germany-vs-japan---tier-9)
      1. 1. [User Input](#user-input-11)
         2. [PromptCraft Pro Output](#promptcraft-pro-output-12)

## [](#anchor-fs-general)ANCHOR-FS-GENERAL

## [](#1-general-analysis)1. General Analysis

## [](#anchor-fs-general-11)ANCHOR-FS-GENERAL-1.1

## [](#11-ethical-implications-of-ai-in-hiring---tier-6)1.1. Ethical Implications of AI in Hiring - Tier 6

#### [](#user-input)User Input

> "I need a thorough analysis of the ethical problems when companies use AI for hiring."

#### [](#promptcraft-pro-output)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are a seasoned AI-ethics researcher, deeply examining hiring algorithms' impact on workplace fairness.

**2. Background Information**:
The use of Artificial Intelligence (AI) in recruitment and hiring processes (e.g., resume screening, candidate sourcing, interview analysis, predictive performance modeling) is rapidly increasing. While promising efficiency and objectivity, these AI tools also raise significant ethical concerns regarding fairness, bias, transparency, accountability, and potential discriminatory outcomes. There's a growing need for a comprehensive understanding of these ethical challenges to inform policy, regulation, and responsible AI development and deployment in the HR sector.

**3. Goal / Intent**:
The primary goal is to produce an **in-depth analytical report that thoroughly explores the spectrum of ethical issues associated with using AI in hiring processes.** The output should enable HR professionals, policymakers, AI developers, and ethicists to:
    a. Identify and understand the key ethical risks and dilemmas.
    b. Appreciate the potential harms to individuals and societal groups.
    c. Consider the challenges in ensuring fairness, accountability, and transparency.
    d. Begin formulating strategies for mitigation and responsible governance.
The ultimate impact is to contribute to a more ethical and equitable application of AI in the employment lifecycle.

---

# R - Request

**1. Deliverable and Format**:
Produce an **In-Depth Analysis** of the ethical implications of using AI in hiring.
The output should be a comprehensive, well-structured analytical report suitable for an informed audience interested in AI ethics and HR practices.

**2. Depth and Length**:
The target length is approximately **3500 words**. This aligns with **Tier 6: In-Depth Analysis (technical note / detailed report)** from the C.R.E.A.T.E. guide's depth scale. The analysis should be substantial and well-supported.

**3. Core Content Requirements**:
The "In-Depth Analysis" must comprehensively address:
    1.  **Introduction**: Overview of AI in hiring and statement of ethical concerns.
    2.  **Bias and Discrimination**: Detailed exploration of how biases (algorithmic, data-driven, human-like) can manifest in AI hiring tools and lead to discriminatory outcomes against protected groups (based on race, gender, age, disability, etc.). Include examples.
    3.  **Transparency and Explainability (XAI)**: Discuss the challenges of "black box" AI algorithms in hiring, the difficulty in understanding how decisions are made, and the implications for accountability and due process for candidates.
    4.  **Privacy Concerns**: Analyze issues related to data collection, candidate surveillance, consent, and the security of sensitive personal information processed by AI hiring systems.
    5.  **Accountability and Oversight**: Examine who is responsible when AI hiring tools cause harm or make errors (developers, vendors, employers). Discuss the need for robust human oversight and appeal mechanisms.
    6.  **Impact on Human Agency and Candidate Experience**: Consider how AI-driven processes affect the candidate experience, potential for dehumanization, and the role of human judgment in hiring.
    7.  **Potential Solutions and Mitigation Strategies**: Explore proposed solutions, including technical approaches (e.g., fairness-aware algorithms), regulatory frameworks, ethical guidelines, auditing practices, and the importance of diverse development teams.
    8.  **Conclusion**: Summarize key findings and offer forward-looking perspectives on achieving more ethical AI in hiring.

---

## # E - Examples

*(N/A for providing a full output example of the entire report. The detailed Core Content Requirements in R and the Augmentations guide the structure and specific elements.)*

---

# A - Augmentations

**1. Evidence and Data Source Guidance**:

- The analysis should be grounded in **established AI ethics literature, research papers, reports from reputable organizations** (e.g., AI ethics institutes, academic centers, governmental advisory bodies like those from the EU or NIST if applicable), and relevant legal/regulatory discussions where available.
- Cite sources using **Chicago Manual of Style (superscript footnotes and a bibliography/references section at the end)**.
- If discussing specific types of AI tools (e.g., facial recognition, sentiment analysis in interviews), refer to common understandings of their capabilities and ethical discussions surrounding them.

**2. Recency and Current Discourse**:

- While foundational ethical principles are timeless, aim to incorporate understanding of the current discourse (last 2-3 years) on AI in hiring.
- Use `web.search_query` (recency <= 365 days) to find 1-2 recent high-quality overview articles, conference proceedings, or major reports on "AI ethics in hiring" or "algorithmic bias in recruitment" to ensure current perspectives are considered. Synthesize key themes or examples.

**3. Illustrative Content Requirement**:

- Include **hypothetical (but plausible) scenarios or brief case study summaries (1-2 examples)** to illustrate how specific ethical issues (e.g., algorithmic bias leading to a skewed candidate pool, lack of transparency in an AI-driven rejection) can manifest in practice. Ensure these are presented as illustrative examples.

**4. Analytical Framework (Optional Suggestion)**:

- Consider structuring parts of the analysis using a relevant ethical framework (e.g., a principle-based approach discussing autonomy, justice, non-maleficence, beneficence; or a rights-based approach). If used, briefly introduce the framework.

**5. Content Guardrails and Constraints**:

- Maintain an **objective and critical, yet constructive** tone. Avoid overly alarmist or purely dystopian views; focus on identifying issues and exploring potential pathways towards responsible AI.
- Clearly distinguish between documented issues, potential risks, and speculative concerns.
- Tag any significant analytical conclusions or novel syntheses not directly supported by a cited source as `[Expert Judgment]`.

---

# T - Tone and Format

1. Tone and Voice:

- Adopt a **"Formal / Scholarly"** tone, supported by **"Plain-Language"** for accessibility to an informed, non-specialist audience. Language must be **"precise."**
- The voice should be authoritative, thoughtful, and critically engaged.
- Minimize jargon; define essential technical AI or ethical terms upon first use.
- Use contractions sparingly if they enhance readability within the formal/plain-language blend; otherwise, avoid.

2. Stylometry and Stylistic Directives (Auto-Injected Defaults):

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés (e.g., “delve into”, “crucial”).
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; standard deviation sigma >= 8. Ensure varied sentence openings and types (simple, compound, complex).
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside, integrated naturally and maintaining the formal tone.
- **Paragraph Pacing**: Mix short (2-3 sentence) and longer (4-6+ sentence) paragraphs, ensuring smooth transitions.

3. Structural Formatting and Punctuation:

- Organize the report logically (per R.3 Core Content) using H2 for main sections, H3 for sub-sections.
- Employ well-structured paragraphs with clear topic sentences.
- Use bullet points or numbered lists sparingly, only if user specifically asked or if essential for clarity (e.g., listing principles) and adhering to "narrative prose first" principle.
- Include a References/Bibliography section (Chicago style).
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid..

---

# E - Evaluation

Before finalizing your "In-Depth Analysis" on AI ethics in hiring, perform these critical self-checks. Document any major deviations or uncertainties, and revise to meet all checks:

**1. Core Requirements and Content (vs. R and A)**:
    ***Comprehensive Coverage**: Does the report thoroughly address all 8 core content areas specified in the Request?
    * **Augmentations Met**: Is analysis grounded in AI ethics literature? Are Chicago citations (footnotes + bibliography) used? Is recent discourse incorporated? Are 1-2 illustrative scenarios included? Is `[Expert Judgment]` tag used appropriately?
    * **Length Adherence**: Does the report meet the ~3500-word target (Tier 6)?

**2. Accuracy, Grounding and Neutrality (Anti-Hallucination/Bias)**:
    ***Factual and Conceptual Integrity**: Is all information regarding AI tools, ethical principles, and potential impacts accurate and aligned with credible sources and established ethical discourse? Any fabricated details/claims?
    * **Objectivity and Balanced View**: Is content objective, critical yet constructive?

**3. Clarity, Tone and Formatting (vs. T and C.Goal)**:
    ***Accessibility and Precision**: Is the report's language clear, precise, and accessible to an informed audience? Are terms defined?
    * **Tone Consistency**: Is the "Formal / Scholarly" yet "Plain-Language" and "precise" tone maintained? Is sentence-length variability effective?
    * **Structural Integrity**: Is the report well-organized (H2/H3)? Are paragraphs/lists effective? Bibliography correct? Markdown valid?

**4. Overall Goal Achievement and Impact (vs. C.Goal)**:
    *Does the report provide comprehensive understanding of ethical issues in AI hiring?
    * Does it equip readers to identify risks and consider responsible governance?

*After these checks, briefly summarize your confidence in meeting each major category and note any significant assumptions made or areas where further refinement by a human expert in AI ethics would be beneficial given the report's depth.*

# Length Check

| Tier | Name and Synonyms                    | Words                   | Core Use-Case                       |
|------|------------------------------------|-------------------------|-------------------------------------|
| 5    | Extended Overview (mini-report)    | 900 - 2000 words        | Blog posts, press briefings         |
| **6**| **In-Depth Analysis (technical note)** | **2000 - 5000 words** | **Internal white memos, policy briefs** |
| 7    | Research Brief / Whitepaper        | 5000 - 10000 words      | Investor decks, conference papers   |

**Suggested tier**: **6** | **OK?** (yes / choose another)
**Other changes?**(add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-general-12)ANCHOR-FS-GENERAL-1.2

## [](#12-chemical-symbol-lookup---tier-1)1.2. Chemical Symbol Lookup - Tier 1

#### [](#user-prompt)USER PROMPT

> "I just need a prompt to find out the official chemical symbol for gold."

#### [](#promptcraft-pro-output-1)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are a meticulous science reference librarian, providing precise chemical data with instant accuracy.

**2. Background Information**:
The user requires a single, standardized piece of scientific data: the chemical symbol for the element gold. This is a straightforward lookup task.

**3. Goal / Intent**:
To retrieve and provide **only the official chemical symbol for gold**, without any additional explanatory text or context.

---

# R - Request

**1. Deliverable and Format**:
State the **official chemical symbol for gold**.

**2. Depth and Length**:
The output must be a **Nano Answer (Tier 1: typically 1-2 words for this type of data)**.

**3. Core Content Requirements**:

- Provide the single, correct chemical symbol.

---

# E - Examples

*(N/A for this type of direct data point retrieval.)*

---

# A - Augmentations

**1. Evidence and Data Source Guidance**:

- The symbol provided must be the internationally recognized chemical symbol for gold, as per IUPAC (International Union of Pure and Applied Chemistry) or a standard Periodic Table of Elements.
- No external citation needed in the output string itself, but the information must be from an authoritative source.

**2. Content Guardrails**:

- **Strictly output only the chemical symbol.** Do not include phrases like "The chemical symbol for gold is..." or any other descriptive text.
- Ensure 100% accuracy.

---

# T - Tone and Format

1. Tone and Voice:

- "Neutral / Factual / Data-Point." No conversational or stylistic language elements.

1. Structural Formatting:

- The output must be **solely the chemical symbol itself** (e.g., "Au").
- No stylometry directives (hedge, lexical, sentence variability, rhetoric, pacing, contractions, complex punctuation) are applicable due to the atomic data output format.

---

# E - Evaluation

Before finalizing the response, perform these self-checks:

**1. Core Requirement (vs. R and A)**:
    *Does the output consist *only* of the correct chemical symbol for gold?
    * Is it based on authoritative chemical data (e.g., IUPAC)?

**2. Length and Format (vs. R and T)**:
    *Is the output a Nano Answer (Tier 1 - just the symbol)?
    * Is the formatting strictly the symbol itself, with no extra text?

**3. Goal Achievement (vs. C.Goal)**:
    * Does the output directly provide the specific factual data point requested?

*After these checks, confirm suitability.*

# Length Check

| Tier | Name and Synonyms                    | Words                 | Core Use-Case                       |
|------|------------------------------------|-----------------------|-------------------------------------|
| **1**| **Nano Answer (blurb, micro-reply)** | **<= 60 words approximately 80 tokens** | **One-line definitions or fact checks** |
| 2    | Executive Snapshot (headline)      | 80 - 150 words        | C-suite bullet-point summary        |
| 3    | Concise Summary (abstract, précis) | 150 - 400 words       | Board memo abstracts, article abstracts |

**Suggested tier**: **1** | **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-general-13)ANCHOR-FS-GENERAL-1.3

## [](#13-meeting-takeaways-snapshot---tier-2)1.3. Meeting Takeaways Snapshot - Tier 2

#### [](#user-input-1)User Input

> "Can you build a prompt to get a summary of the key decisions and action items from today's
> two-hour strategy meeting for Sarah who was out sick? She just needs the essentials to catch up quickly."

#### [](#promptcraft-pro-output-2)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are an efficiency-minded project coordinator, skilled at distilling meetings into crisp action snapshots.

**2. Background Information**:
A team member ("Sarah") was absent from a significant two-hour strategy meeting. She requires a very brief summary focusing *only* on key decisions made and specific action items assigned to get up to speed efficiently. Lengthy minutes or detailed discussion points are not needed for this immediate purpose.

**3. Goal / Intent**:
To generate a **highly condensed "executive snapshot" of the strategy meeting's crucial decisions and clearly assigned action items** for Sarah, enabling her to quickly understand the primary outcomes without reviewing extensive notes.

---

# R - Request

**1. Deliverable and Format**:
Produce an **Executive Snapshot** of the key decisions made and action items assigned during the strategy meeting.
The output should be a concise bulleted list.

**2. Depth and Length**:
The target length is an **Executive Snapshot (Tier 2: 80-150 words)**. Clarity and conciseness are paramount.

**3. Core Content Requirements**:
The snapshot must clearly and briefly state:
    *1-2 Major Decisions Made (if any explicitly stated).
    * 2-3 Key Action Items Assigned (clearly indicating who is responsible, what the task is, and by when, if specified in the source meeting information).
    * (Optional, if central) 1 overarching next step for the strategy discussed.

---

# E - Examples

N/A. The requested output is a simple, concise bulleted list guided by R and T.

---

# A - Augmentations

**1. Evidence and Data Source Guidance**:

- The summary must be based on **information provided by the user about the meeting's outcomes** (e.g., from their notes, official minutes, or direct recollection, which they would hypothetically provide to the target LLM).
- Focus strictly on explicitly stated decisions and clearly assigned action items.

**2. Content Guardrails**:

- **Exclude** general discussion points, unresolved debates, opinions, or background conversation not leading to a decision or action.
- Ensure action items are presented as actionable.
- Be extremely concise; every word should count.

---

# T - Tone and Format

1. Tone and Voice:

- Adopt an **"Informative," "Clear," "Action-Oriented,"** and **"Precise"** tone.
- Language should be direct and factual. Use contractions.

1. Stylometry and Stylistic Directives (Applied to framing text and bullet content):

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: For any sentences used, aim for Avg 17-22 words; >= 15 % < 8 w and >= 15 % > 30 w; sigma >= 8. Use varied openings/types.
- **Rhetorical Devices**: If framing text allows, include >= 1 rhetorical Q AND >= 1 first-person or direct-address aside, integrated naturally.
- **Paragraph Pacing**: (Applicable to framing text if used) Mix short (2-3 sent) and long (4-6 +) paras.

1. Structural Formatting and Punctuation:

- Output as a **bulleted list (3 to 5 points maximum)** as requested by user.
- Each bullet point: direct. Action items: start with a verb, denote responsibility/task.
- Minimal introductory/concluding paragraphs framing the list (e.g., "Key Outcomes from Strategy Meeting:").
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid.

---

# E - Evaluation

Before finalizing the meeting snapshot, perform these self-checks:

**1. Core Requirements (vs. R and A)**:
    *Does the snapshot accurately capture 1-2 key decisions and 2-3 specific action items (with owner/task/timeline details if available in source info)?
    * Is it strictly based on outcomes, excluding general discussion?

**2. Brevity and Impact (Tier 2 Length vs. R)**:
    *Is the entire output within the 80-150 word limit (Tier 2)?
    * Is each point concise and essential for a quick catch-up?

**3. Clarity and Tone (vs. T and C.Goal)**:
    *Is the language clear, unambiguous, action-oriented, and precise?
    * Does it directly provide Sarah with the essential outcomes?

*After these checks, confirm the summary is fit for its purpose.*

# Length Check

| Tier | Name and Synonyms                    | Words                 | Core Use-Case                       |
|------|------------------------------------|-----------------------|-------------------------------------|
| 1    | Nano Answer (blurb, micro-reply)   | <= 60 words            | One-line definitions or fact checks |
| **2**| **Executive Snapshot (headline)** | **80 - 150 words** | **C-suite bullet-point summary** |
| 3    | Concise Summary (abstract, précis) | 150 - 400 words       | Board memo abstracts, article abstracts |

**Suggested tier**: **2** | **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-general-14)ANCHOR-FS-GENERAL-1.4

## [](#14-product-description-to-json-extraction-with-in-prompt-examples---tier-1-for-json-output)1.4. Product Description to JSON Extraction (with In-Prompt Examples) - Tier 1 (for JSON Output)

#### [](#user-input-2)User Input

> "I have a bunch of messy product descriptions. I need a C.R.E.A.T.E. prompt that will instruct
> an LLM to pull out specific details like product name, key feature, price, and stock status, and put it all into a clean JSON format. It's crucial that the JSON structure is consistent, so the C.R.E.A.T.E. prompt itself needs to show the LLM exactly what I mean with a couple of examples."

#### [](#promptcraft-pro-output-3)PromptCraft Pro Output

`````markdown
# C - Context

**1. Role**:
You are a detail-oriented data wrangler, adept at transforming messy blurbs into perfect JSON.

**2. Background Information**:
A dataset consisting of unstructured product descriptions needs to be processed to extract key attributes for cataloging, inventory management, and e-commerce platforms. The primary challenge is the variability in the input descriptions. Therefore, ensuring strict consistency in the output JSON structure and data types for each extracted item is paramount for downstream data processing. This C.R.E.A.T.E. prompt will guide a target LLM to perform this extraction task.

**3. Goal / Intent**:
The primary goal is to **enable a target LLM to reliably extract specified product information from unstructured text descriptions and output this information as a valid, consistently structured JSON object.** This process needs to be repeatable for numerous product descriptions. The generated JSON must adhere precisely to the demonstrated schema and examples.

---

# R - Request

**1. Deliverable and Format**:
For each input product description, produce a **single, valid JSON object** containing the extracted information. The output must be *only* the JSON object, with no extraneous text, explanations, or Markdown fencing.

**2. Depth and Length (of JSON output per input item)**:
The JSON output for each processed product description will be concise, typically a **Nano Answer (Tier 1)** in terms of its raw text length, though its complexity is defined by the number of fields.

**3. Core Task and Fields to Extract**:
For each `[INPUT_PRODUCT_DESCRIPTION]` provided to you (the target LLM), you must:
Extract the following fields and structure them into a JSON object:
    *`product_name`: (string) The main name of the product.
    * `key_feature`: (string) A concise description of the primary feature or selling point.
    *`price`: (number) The numerical price if mentioned (e.g., 79.99, 129.00). If no price is found, this field should be `null`.
    * `in_stock`: (boolean) `true` if availability or "in stock" is mentioned or clearly implied; `false` if "out of stock" or similar is mentioned. If availability is not mentioned, this field should be `null`.

---

# E - Examples

Below are two examples demonstrating the exact input/output transformation expected. Adhere strictly to this pattern, including field names, data types, and handling of missing information (using `null`).

**Example 1**:
Input: "The new AquaSplash X1000 is a fantastic waterproof speaker with 12-hour battery life. Get it now for $79.99! Currently available."
Output:

```json
{
  "product_name": "AquaSplash X1000",
  "key_feature": "waterproof speaker with 12-hour battery life",
  "price": 79.99,
  "in_stock": true
}
````json

**Example 2**:
Input: "Introducing the CozyNook E-Reader. Features an anti-glare screen perfect for reading outdoors. Price: $129. Unfortunately, this popular item is temporarily out of stock."
Output:

```json
{
  "product_name": "CozyNook E-Reader",
  "key_feature": "anti-glare screen perfect for reading outdoors",
  "price": 129.00,
  "in_stock": false
}
```json

---

# A - Augmentations

**1. Extraction Rules and Logic**:

- If multiple features are listed, select the most prominent or first-mentioned as the `key_feature`.
- For `price`, extract only the numeric value. Do not include currency symbols in the JSON value.
- For `in_stock`, infer `true` from phrases like "currently available," "ships now." Infer `false` from "out of stock," "unavailable." If no direct statement or clear implication of stock status is present, use `null`.
- If a field cannot be reliably extracted from the input text, its value in the JSON should be `null`.

**2. Schema Adherence**:

- The output JSON object **must** strictly adhere to the field names: `product_name`, `key_feature`, `price`, `in_stock`.
- Data types must be consistent with the examples: `product_name` (String), `key_feature` (String), `price` (Number or Null), `in_stock` (Boolean or Null).

**3. Content Guardrails**:

- Do not infer information not present in the input text.
- If the input text is entirely unrelated to a product description or too ambiguous to extract any meaningful data for the schema, output a JSON object with all field values set to `null`.

---

# T - Tone and Format

1. Tone and Voice (of target LLM's output):

- N/A. The output is exclusively a JSON data object. No natural language tone or stylometry is applicable.

1. Structural Formatting (of target LLM's output):

- Output must be **strictly valid JSON.**
- No extraneous characters, text, explanations, or Markdown fencing before or after the JSON object. Output begins with `{` and ends with `}`.
- Use standard JSON indentation (e.g., 2 spaces) for readability, as shown in examples.
- Stylometry directives (hedge, lexical, sentence variability, rhetoric, pacing, contractions, complex punctuation) are N/A.

---

# E - Evaluation

Before finalizing any JSON output for a given input description, perform these critical self-checks:

**1. JSON Validity and Schema (vs. R and A)**:

- **Valid JSON**: Is the entire output a perfectly valid JSON object that can be parsed without errors?
- **Schema Adherence**: Does the JSON object contain *only* the specified fields (`product_name`, `key_feature`, `price`, `in_stock`) and no others?
- **Data Types**: Are the data types for each field correct (string, number/null, boolean/null) as demonstrated in the examples and specified in Augmentations?

**2. Extraction Accuracy and Logic (vs. A and Examples)**:

- **Content Accuracy**: Do the values for each field accurately reflect the information present in the input product description?
- **Null Handling**: Is `null` correctly used for missing prices or ambiguous stock status as per the rules?
- **Rule Application**: Were the specific extraction rules for `key_feature`, `price`, and `in_stock` correctly applied?

**3. Format and Purity (vs. T)**:

- **JSON Only**: Is the output *exclusively* the JSON object, with absolutely no preceding or succeeding text, comments, or explanations?
- **Formatting Consistency**: Does the JSON formatting (indentation, quotes) match the style shown in the provided examples?

**4. Overall Task Adherence (vs. C.Goal)**:

- Does the output reliably provide the structured data needed for cataloging/database ingestion, accurately reflecting the input description according to the defined schema and examples?

*After these checks, ensure the output is solely the generated JSON object.*

# Length Check

| Tier | Name and Synonyms                    | Words                 | Core Use-Case                       |
|------|------------------------------------|-----------------------|-------------------------------------|
| **1**| **Nano Answer (JSON Output)** | **(Varies, but textually brief)** | **Structured data object per input** |
| 2    | Executive Snapshot (headline)      | 80 - 150 words        | C-suite bullet-point summary        |
| 3    | Concise Summary (abstract, précis) | 150 - 400 words       | Board memo abstracts, article abstracts |

**Suggested tier**: **1 (for the JSON output per description)** | **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

`````

## [](#anchor-fs-legal)ANCHOR-FS-LEGAL

## [](#2-legal)2. Legal

## [](#anchor-fs-legal-21)ANCHOR-FS-LEGAL-2.1

## [](#21-cease-and-desist-letter-copyright-infringement---tier-3)2.1. Cease and Desist Letter (Copyright Infringement) - Tier 3

#### [](#user-input-3)User Input

> "Someone is using my copyrighted photos on their website without my permission! Help me create
> a C.R.E.A.T.E. prompt to get a strong Cease and Desist letter drafted that I can send them."

#### [](#promptcraft-pro-output-4)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are an experienced intellectual-property attorney, fiercely protecting creative works from online infringement.

**2. Background Information**:
A client (the 'Rights Holder') has discovered specific copyrighted visual works (e.g., photographs, illustrations) they own are being displayed and used on a third-party website (the 'Infringing Website') without any license, permission, or authorization. This unauthorized use constitutes copyright infringement. The Rights Holder wishes to formally demand the immediate removal of all infringing content and explicitly reserve all legal rights and remedies available to them. This Cease and Desist letter serves as the initial formal communication to the operator of the Infringing Website.

**3. Goal / Intent**:
The primary goal is to **generate a legally sound, professionally toned, and effective Cease and Desist letter** addressed to the owner/operator of the Infringing Website. This letter must:
    a. Clearly identify the Rights Holder and the specific copyrighted work(s) being infringed.
    b. Unequivocally state the Rights Holder's ownership of the copyright.
    c. Precisely identify the Infringing Website and the exact location(s) (URLs) of the infringing content.
    d. Formally demand the immediate cessation of all infringing activities and removal of the content within a specified, reasonable timeframe.
    e. Request written confirmation of compliance.
    f. Explicitly reserve all of the Rights Holder's legal rights and remedies, including the right to pursue legal action for damages, injunctive relief, and attorney's fees.
The ultimate impact is to achieve swift removal of the infringing content and deter future infringement, while formally preserving all legal options for the Rights Holder.

---

# R - Request

**1. Deliverable and Format**:
Draft a **formal Cease and Desist Letter** concerning copyright infringement of visual works. The letter should be suitable for sending via registered mail or email with delivery confirmation.

**2. Depth and Length**:
The letter should be a **Concise Summary (Tier 3: approximately 250-400 words)**. It must be comprehensive enough to include all necessary legal elements but remain direct and to the point.

**3. Core Content Requirements**:
The Cease and Desist Letter must systematically include the following sections/information, using placeholders for user-specific details:
    1.  **Sender Information**: `[Rights Holder Name/Company Name]`, `[Rights Holder Address]`, `[Date]`
    2.  **Recipient Information**: `[Infringing Website Owner/Operator Name, if known, or "To Whom It May Concern"]`, `[Infringing Website Domain/Company Address, if known]`
    3.  **Subject Line**: e.g., "URGENT: Cease and Desist - Unauthorized Use of Copyrighted Material"
    4.  **Identification of Rights Holder and Copyrighted Work(s)**: Clear statement identifying the Rights Holder and a description of the copyrighted work(s) (e.g., "the photograph titled '[Photo Title]' taken on [Date], Copyright Registration No. [Number, if applicable], a copy of which is available at [Link to Rights Holder's Original Work, if any, or attached as Exhibit A]"). Use placeholders `[Description of Copyrighted Work(s) and evidence of ownership]`.
    5.  **Identification of Infringement**: Precise identification of the Infringing Website (`[Infringing Website URL]`) and the specific page(s)/URL(s) where the infringing content is located (`[Specific URLs of Infringing Content on their site]`). State that this use is unauthorized.
    6.  **Demand to Cease and Desist**: A clear and unequivocal demand that the recipient immediately (within `[e.g., 7 or 10] calendar days` from the date of the letter) cease and desist from any further use, reproduction, distribution, or display of the copyrighted work(s) and remove all instances from the Infringing Website and any other platforms under their control.
    7.  **Demand for Confirmation**: A request for written confirmation (email acceptable) within the specified timeframe that all infringing activities have ceased and the content has been removed.
    8.  **Reservation of Rights**: A statement such as: "This letter is without prejudice to any and all rights and remedies available to [Rights Holder Name], all of which are expressly reserved. Failure to comply with this demand within the specified timeframe will leave [Rights Holder Name] with no alternative but to pursue all available legal remedies, including but not limited to, seeking injunctive relief, statutory damages, actual damages, and recovery of attorney's fees."
    9.  **Good Faith Contact Attempt**: (Optional but good practice) "We hope to resolve this matter amicably and without the need for further legal action."
    10. **Closing and Signature**: Formal closing (e.g., "Sincerely,") and placeholder for `[Rights Holder Name/Authorized Representative Signature]` and `[Printed Name]`.
    11. **Disclaimer (Crucial - to be included by the LLM in the letter body or footer)**: "This letter is generated for informational purposes based on the details provided and does not constitute legal advice, nor does it create an attorney-client relationship. The Rights Holder should consult with a qualified attorney regarding their specific situation before sending this letter or taking any legal action."

---

# E - Examples

*(N/A for providing a full output example of the Cease and Desist letter itself. The detailed Core Content Requirements in R, combined with the Persona and Augmentations, guide the LLM in structuring and phrasing the letter. The persona's expertise implies knowledge of standard legal letter formats.)*

---

# A - Augmentations

**1. Legal Framework Adherence**:

- The letter must adhere to the standard components, tone, and legal implications of a **U.S. Copyright Cease and Desist Letter**. It should clearly assert rights, provide notice of infringement, demand specific remedial action, and state the potential consequences of non-compliance.

**2. Evidence and Data Source (User-Provided)**:

- The LLM will draft the letter based on the assumption that the user (Rights Holder) will replace placeholders with their specific factual details (e.g., their name, description of work, URLs of infringement). No external legal research beyond general U.S. copyright principles is required from the LLM for this drafting task.

**3. Content Guardrails**:

- **Include the critical disclaimer** (as specified in R.3.11) about the letter not being legal advice and the recommendation to consult an attorney. This must be part of the letter's text.
- The tone must be **firm and formal but not unduly aggressive, threatening, or inflammatory.** The goal is compliance, and an overly hostile tone can be counterproductive.
- Do not make specific monetary demands or detail specific damages amounts in this initial letter, beyond generally stating that remedies include damages.

---

# T - Tone and Format

**1. Tone and Voice**:

- Adopt a **"Formal / Legal"** tone. Language must be precise, unambiguous, clearly articulating the legal basis for demand.
- Voice: professional, measured, firm. Avoid emotional language and contractions.

**2. Stylometry and Stylistic Directives (Auto-Injected Defaults)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; sigma >= 8. Ensure varied sentence openings and types.
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside, integrated formally and judiciously.
- **Paragraph Pacing**: Mix short (2-3 sentence) and longer (4-6+ sentence) paragraphs with smooth, logical transitions.

**3. Structural Formatting and Punctuation**:

- Follow standard professional business letter format (Sender/Recipient Info, Date, Subject, Salutation, logical body paragraphs per R.3, Formal Closing, Signature placeholder).
- Use clear, complete sentences; focused paragraphs. No unsolicited lists.
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid.

---

# E - Evaluation

Before finalizing the Cease and Desist letter, perform these critical self-checks. List any major deviations or uncertainties, and revise if possible:

**1. Core Requirements and Legal Sufficiency (vs. R and A)**:
    ***All Components Present**: Does the letter include all 11 specified core content requirements from R.3 (Sender/Recipient Info, Subject, Work ID, Infringement ID, Demand, Confirmation Request, Rights Reservation, Good Faith, Closing, Disclaimer)?
    * **Legal Assertions**: Are copyright ownership and infringement clearly and correctly asserted based on standard U.S. copyright principles?
    ***Demand Clarity**: Are the demands (cease use, remove content, confirm compliance) and the timeframe for action unambiguous?
    * **Disclaimer**: Is the "not legal advice" disclaimer included as specified?

**2. Accuracy, Grounding and Guardrails (vs. A)**:
    ***Factual Placeholders**: Are placeholders for user-specific facts clear and appropriate?
    * **No External Research Assumed**: Does the letter correctly rely on user-provided facts for specifics, without fabricating details?
    * **Guardrails Adhered To**: Is the tone firm but not overly aggressive? Are specific monetary demands avoided?

**3. Clarity, Tone and Formatting (vs. T and C.Goal)**:
    ***Professionalism**: Is the language precise, formal, and unambiguous, suitable for legal correspondence?
    * **Tone Consistency**: Does the response consistently maintain the "Formal / Legal" and professional tone of "IPGuard AI"?
    * **Formatting**: Does the letter adhere to standard business letter format? Are paragraphs focused and sentences clear?

**4. Overall Goal Achievement (vs. C.Goal)**:
    *Does the drafted letter effectively serve as a formal Cease and Desist notice?
    * Is it likely to achieve the goal of prompting removal of infringing content while preserving the Rights Holder's legal options?

*After these checks, briefly note confidence in meeting requirements and any assumptions made (e.g., assuming user will correctly fill placeholders).*

# Length Check

| Tier | Label                      | Words                   | Core Use-Case                       |
|------|----------------------------|-------------------------|-------------------------------------|
| 2    | Executive Snapshot         | 80 - 150 words          | C-suite bullet-point summary        |
| **3**| **Concise Summary** | **150 - 400 words** | **Board memo abstracts, legal letter draft** |
| 4    | Overview                   | 400 - 900 words         | First-pass orientation for analysts |

**Suggested tier**: **3** | **OK?** (yes / choose another)
**Other changes?**(add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-legal-22)ANCHOR-FS-LEGAL-2.2

## [](#22-oregon-travel-ethics-research-brief-and-advice-letter---tier-7-brief--tier-3-letter)2.2. Oregon Travel Ethics: Research Brief and Advice Letter - Tier 7 (Brief) / Tier 3 (Letter)

#### [](#user-input-4)User Input

> "I'm helping a state agency prepare a briefing on ethics and travel. I need a C.R.E.A.T.E.
> prompt to get an LLM to produce a detailed research brief (at least 5000 words) covering potential
> penalties, what counts as personal vs. business travel, and how to handle mixed trips under Oregon
> ethics law, citing ORS 244, cases, and OGEC advice. After that, it should draft an official-style
> advice letter based on some OGEC examples I have links for. The research brief needs CRRACC and CoT;
> the letter needs to be direct."
> OGEC Advice follows a standard format. Below are three examples of requests for advice
> submitted and then the OGEC response to use as examples of the level of details and type of response.

> \###Sample Advice Letter

> Sample Request #1 <<https://apps.oregon.gov/OGEC/CMS/File/GetFile>?
> filekey=82cb55af-5889-4083-8090-8a45103d7cf6>
> Sample Advice # 1<<https://apps.oregon.gov/OGEC/CMS/File/GetFile>?
> filekey=03dfc4fa-9652-4ca4-8064-5bb04a9bb39d>

> Sample Request #2 <<https://apps.oregon.gov/OGEC/CMS/File/GetFile>?
> filekey=d0b74b3a-5f60-4740-9ddc-277876e4e78b>
> Sample Advice #2 <<https://apps.oregon.gov/OGEC/CMS/File/GetFile>?
> filekey=e106e176-7721-453e-a6ae-dd4339a518d2>

> Sample Request #3 <<https://apps.oregon.gov/OGEC/CMS/File/GetFile>?
> filekey=bccc886c-d0b6-456f-9044-689dba7ae032>
> Sample Advice #3 <<https://apps.oregon.gov/OGEC/CMS/File/GetFile>?
> filekey=1e3c0b32-38d8-426c-b4af-89894b1788bc>

#### [](#promptcraft-pro-output-5)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are a veteran Oregon government-ethics lawyer, intimately familiar with ORS 244 travel compliance.

**2. Background Information**:
A State of Oregon agency requires a definitive internal guidance document for its staff concerning the ethical and potential legal (including criminal, if applicable) ramifications associated with travel reimbursements and activities during official state business. Specifically, clarity is needed on distinguishing personal travel from official duties, managing mixed-purpose trips to avoid improper personal gain, and understanding potential penalties for non-compliance with state travel policies and Oregon ethics laws. The provided "Request for Advice" (see "User-Provided Scenario and Materials" below) outlines key questions that need to be addressed.

**3. Goal / Intent**:
The primary goal is twofold:
    a. To produce a **comprehensive Research Brief** serving as a technical legal guide for agency staff. This brief will thoroughly analyze relevant Oregon ethics statutes (ORS Chapter 244), administrative rules, OGEC opinions, and pertinent case law concerning state employee travel, focusing on the questions in the "Request for Advice."
    b. To draft a model **Advice Letter**, styled after official OGEC communications, that directly answers the questions posed in the "Request for Advice," providing clear, actionable guidance.
The ultimate impact is to enhance ethical awareness, ensure legal compliance, and minimize risks associated with official travel for all agency personnel.

---

# R - Request

**1. Deliverable 1: Research Brief**

- Draft a **Research Brief** of at least **5000 words (Tier 7: Research Brief / Whitepaper)**.
- This brief must analyze potential criminal and ethics law issues, key legal concepts, relevant Oregon court cases, and OGEC cases/advice pertaining to:
    1. Potential ethics and criminal penalties for submitting, approving, or receiving non-compliant travel reimbursements.
    2. The definition and distinction between personal travel and official/business travel under Oregon law/policy.
    3. Permissible methods and best practices for accounting for and managing trips that combine personal and business travel to prevent personal gain and ensure compliance.
- The voice should be scholarly yet understandable for agency staff who may not be legal experts.

**2. Deliverable 2: Advice Letter**

- Following the Research Brief, draft an **Advice Letter** directly responding to the three questions posed in the "Request for Advice" (see "User-Provided Scenario and Materials" below).
- The style, structure, and tone must meticulously emulate those of actual advice letters issued by the Oregon Government Ethics Commission, based on the samples provided.
- The target length is a **Concise Summary / Overview (Tier 3: approx. 400-900 words)**.

---

# E - Examples

- **For Deliverable 2 (Advice Letter)**: The style, tone, structure, and method of analysis **must closely emulate** the official advice letters issued by the Oregon Government Ethics Commission. Refer to and analyze the patterns in the following actual examples:

- Sample Request #1 <https://apps.oregon.gov/OGEC/CMS/File/GetFile?filekey=82cb55af-5889-4083-8090-8a45103d7cf6>
- Sample Advice # 1<https://apps.oregon.gov/OGEC/CMS/File/GetFile?filekey=03dfc4fa-9652-4ca4-8064-5bb04a9bb39d>

- Sample Request #2 <https://apps.oregon.gov/OGEC/CMS/File/GetFile?filekey=d0b74b3a-5f60-4740-9ddc-277876e4e78b>
- Sample Advice #2 <https://apps.oregon.gov/OGEC/CMS/File/GetFile?filekey=e106e176-7721-453e-a6ae-dd4339a518d2>

- Sample Request #3 <https://apps.oregon.gov/OGEC/CMS/File/GetFile?filekey=bccc886c-d0b6-456f-9044-689dba7ae032>
- Sample Advice #3 <https://apps.oregon.gov/OGEC/CMS/File/GetFile?filekey=1e3c0b32-38d8-426c-b4af-89894b1788bc>

- **For Deliverable 1 (Research Brief)**: No full output example is provided. The "scholarly but understandable voice," CRRACC structure, Bluebook citation requirements, and other augmentations will define the expected standard.

---

# A - Augmentations

**1. Analytical Framework (CRRACC)**:

- For the **Research Brief (Deliverable 1)**, each distinct legal issue or question analyzed must be structured using the **"CRRACC" paradigm**: Conclusion - Rule statement - Rule explanation - Application of rules to the facts/scenario - Counterarguments/Alternative interpretations - Conclusion restated.

**2. Reasoning Process (Chain of Thought)**:

- For the **Research Brief (Deliverable 1)**, explicitly **use and articulate your Chain-of-Thought (CoT) reasoning process** for each CRRACC element. Explain your analytical steps, statutory interpretation, and how you connect legal principles to the travel scenarios.
- For the **Advice Letter (Deliverable 2)**, the conclusions must be based on the Research Brief's CoT. However, the letter itself should be direct, presenting the reasoned advice without detailing the full CoT, consistent with OGEC's style.

**3. Evidence, Citation and Authority Hierarchy**:

- **Primary Legal Sources**: Base all analysis primarily on **ORS Chapter 244 (Ethics)**, relevant Oregon Administrative Rules (OARs, especially Chapter 199 - OGEC rules), and official OGEC guidance (e.g., Public Official's Guide, published formal/informal advice, training materials).
- **Secondary and Supporting Sources**: Incorporate relevant Oregon court cases and other secondary authorities as appropriate. Utilize all URLs provided in the "Known References" section (see "User-Provided Scenario and Materials").
- **Citation Format**: All sources in both deliverables must be cited using **Bluebook citation format (latest edition)**. Footnotes are preferred for the Research Brief. For the Advice Letter, follow the citation style observed in the OGEC samples.
- **Authority Prioritization**: Strictly prioritize sources in this order: Oregon Constitution -> Oregon Revised Statutes -> Oregon Administrative Rules -> Official OGEC Policy/Guides -> Formal OGEC Advisory Opinions -> Informal OGEC Advice Letters -> Oregon Court Cases -> Persuasive Secondary Sources.
- **Tagging**: Tag any significant conclusions or analytical points not directly supported by a citable primary or secondary authority as `[Expert Judgment]`.

**4. Recency and Data Verification**:

- Ensure all legal references are to the **latest versions** of statutes, rules, and guidance.
- Use `web.search_query` with appropriate date filters (e.g., "last 1-3 years" for OGEC advice/cases, "current official ORS Chapter 244") to verify the currency of provided links and to find any more recent, relevant OGEC materials or court decisions related to travel, gifts, or personal gain for public officials. Focus on "Oregon.gov" domains.

**5. Illustrative Content (Research Brief)**:

- In the Research Brief, use analogies or reference relevant (hypothetical or actual, if citable) case examples from OGEC or Oregon courts to clarify complex points.

---

# T - Tone and Format

**For Deliverable 1: Research Brief**

**1.1. Tone and Voice**:

- Adopt a **"Formal / Scholarly"** tone, ensuring legal rigor and precision. Explanations must be **"Understandable"** to agency staff (non-legal experts).
- Avoid contractions.

**1.2. Stylometry and Stylistic Directives (Auto-Injected Defaults)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés. Avoid unnecessary bigrams.
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; sigma >= 8. Use varied sentence openings/types.
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside, integrated with scholarly subtlety.
- **Paragraph Pacing**: Mix short (2-3 sentence) and longer (4-6+ sentence) paragraphs with smooth, logical transitions.

**1.3. Structural Formatting and Punctuation (Research Brief)**:

- Use clear H2, H3, H4 headings for CRRACC analyses. Utilize bullet points for lists sparingly (narrative prose first).
- Bluebook footnotes for citations.
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid.

**For Deliverable 2: Advice Letter**

**2.1. Tone and Voice**:

- Precisely **mirror the authoritative, formal, clear, direct, and helpful tone** evident in the provided OGEC 'Sample Advice Letter' examples. This mimicry overrides general stylistic defaults where there's conflict (e.g., if OGEC samples use em-dashes or lack contractions, follow the samples).

**2.2. Stylometry and Stylistic Directives (Applied if consistent with OGEC Samples)**:

- Default stylometry (Hedge, Lexical, Sentence Variability, Rhetoric, Pacing, Contractions, Punctuation rules including **no em-dashes**) should be applied *only if consistent with, or not contradicted by, the OGEC sample letters*. The primary directive is to emulate the samples.

**2.3. Structural Formatting and Punctuation (Advice Letter)**:

- Adhere strictly to the structural and punctuation conventions of the OGEC samples (e.g., sections for Facts, Question, Applicable Law, Analysis, Conclusion/Advice).
- Ensure all Markdown is valid.

---

# E - Evaluation

Before finalizing EACH deliverable, perform these critical self-checks. Document any major deviations or uncertainties and revise to meet all checks:

**1. Core Requirements and Content (vs. R and A)**:
    ***Research Brief**: Are all aspects of the "Request for Advice" questions thoroughly analyzed using CRRACC? Is ORS 244 central? Are penalties, business/personal distinctions, and mixed-travel solutions covered? Is CoT demonstrated? Is the ~5000-word (Tier 7) target met?
    * **Advice Letter**: Does it directly answer the 3 questions from the "Request for Advice"? Is the style, structure, and tone exceptionally consistent with the provided OGEC sample letter URLs? Is it concise (Tier 3) and based on the Brief's findings?
    * **Both**: Are all "Known References" considered and relevant ones integrated? Are analogies/case examples used effectively in the Brief?

**2. Accuracy, Citations and Authority (Anti-Hallucination/Bias)**:
    ***Legal Accuracy**: Is all legal analysis (statute/rule interpretation, application) accurate and current for Oregon ethics law?
    * **Citations**: Are all legal assertions meticulously cited in Bluebook format (footnotes for Brief, style per samples for Letter)? Is the authority ladder respected? Is `[Expert Judgment]` used appropriately?
    ***No Fabrications**: Are there *any* fabricated statutes, rules, OGEC opinions, cases, or unsupported claims (hallucinations)?
    * **Objectivity**: Is the analysis impartial and unbiased?

**3. Tone, Style, Clarity and Formatting (vs. T and C.Goal)**:
    ***Research Brief**: Is it 'Scholarly but understandable'? Is sentence-length variability/bigram guidance met?
    * **Advice Letter**: Does it precisely match OGEC sample style?
    * **Clarity**: Is the language in both documents precise, unambiguous, and suitable for their respective intended audiences?

**4. Overall Goal Achievement (vs. C.Goal)**:
    * Does the Research Brief serve as a robust technical guide? Does the Advice Letter provide clear, actionable, OGEC-style guidance?

*After these checks for EACH deliverable, explicitly state confidence and note any assumptions or limitations.*

*(PromptCraft Pro(TM) will then embed the user's full "Request for Advice" scenario, "Known References" URLs, and "Sample Advice Letter" URLs here under a heading like "### User-Provided Scenario and Materials")*

# Length Check

| Tier | Name and Synonyms                    | Words                   | Core Use-Case                       |
|------|------------------------------------|-------------------------|-------------------------------------|
| 6    | In-Depth Analysis (technical note) | 2000 - 5000 words       | Internal white memos, policy briefs |
| **7**| **Research Brief / Whitepaper** | **5000 - 10000 words** | **Investor decks, conference papers** |
| 8    | Monograph (comprehensive report)   | 10000 - 25000 words     | Strategy bluebooks, agency playbooks|

*(For the Advice Letter component, a separate Tier 3 'Concise Summary' of 400-900 words is implied by the instructions.)*

**Suggested tier**: **7 (for Research Brief)** | **OK?** (yes / choose another tier for primary deliverable)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-fiscal)ANCHOR-FS-FISCAL

## [](#3-fiscal)3. Fiscal

## [](#anchor-fs-fiscal-31)ANCHOR-FS-FISCAL-3.1

## [](#31-ubi-pilot-program-fiscal-impact-analysis---tier-7)3.1. UBI Pilot Program Fiscal Impact Analysis - Tier 7

#### [](#user-input-5)User Input

> "Our city council is considering a Universal Basic Income pilot program and needs a detailed
> research brief on its potential fiscal impacts to inform their decision. Can you help me create a
> C.R.E.A.T.E. prompt for an LLM to draft this comprehensive analysis?"

#### [](#promptcraft-pro-output-6)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are a senior municipal-finance analyst, meticulously quantifying new public-policy pilot budget effects.

**2. Background Information**:
A mid-sized city, 'Cityville' (population approx. 250,000; median household income $65,000; primary industries: light manufacturing, healthcare, retail), is formally proposing a **two-year Universal Basic Income (UBI) pilot program**. The pilot aims to provide **$1,000 per month to 1,000 low-income households**, selected through a defined eligibility process. The City Council requires a thorough understanding of the net fiscal cost, potential impacts on local tax revenues (sales, property), effects on current social service expenditures (e.g., potential offsets), and broader, quantifiable local economic multiplier effects. Significant public and council debate is anticipated, requiring robust, evidence-informed analysis.

**3. Goal / Intent**:
The primary goal is to produce a **comprehensive Research Brief / Whitepaper** that meticulously analyzes and clearly presents the potential net fiscal impact of the proposed UBI pilot program on Cityville's municipal budget and local economy. This analysis should cover the two-year pilot period and include reasoned projections for potential medium-term (3-5 years post-pilot) fiscal implications. The output must equip City Council members with a clear, unbiased, evidence-based understanding to make informed decisions regarding the approval, design, and funding of the UBI pilot.

---

# R - Request

**1. Deliverable and Format**:
Draft a **Research Brief / Whitepaper** providing a detailed fiscal impact analysis of Cityville's proposed Universal Basic Income (UBI) pilot program. The document should be suitable for review by city council members, city finance staff, and interested members of the public.

**2. Depth and Length**:
The target length is approximately **7,500 words**. This aligns with **Tier 7: Research Brief / Whitepaper** from the C.R.E.A.T.E. guide's depth scale. The analysis must be thorough, well-documented, and methodologically sound.

**3. Core Content Requirements**:
The Research Brief / Whitepaper must include, at a minimum, dedicated sections covering:
    1.  **Executive Summary**: Concise overview of key findings, estimated net fiscal impact, major assumptions, and primary policy recommendations.
    2.  **Introduction**: Background on UBI as a policy concept, detailed description of Cityville's proposed pilot program parameters (beneficiary numbers, payment amounts, duration, eligibility criteria).
    3.  **Fiscal Impact Methodology**: A transparent explanation of the analytical approach used, including:
        *Data sources for demographic and economic baseline information for Cityville.
        * Methods for estimating direct program costs and administrative overhead.
        *Models or assumptions used for projecting impacts on local tax revenues (sales, property, income if applicable).
        * Approach to estimating potential changes in demand for, and costs of, existing social safety net programs.
        *Discussion of any economic multiplier models or assumptions used.
        * Clear articulation of all key assumptions (e.g., take-up rates, labor market responses, behavioral changes).
    4.  **Detailed Cost Analysis**: Comprehensive breakdown of projected direct costs of the UBI payments and estimated administrative/operational costs for the pilot.
    5.  **Revenue Impact Analysis**: Quantitative and qualitative analysis of potential impacts on Cityville’s major revenue streams.
    6.  **Expenditure Impact Analysis**: Analysis of potential cost savings or shifts in other municipal expenditure areas (e.g., reduced demand for certain social services, healthcare, or public safety interventions, if justifiable with evidence).
    7.  **Net Fiscal Impact and Multiplier Effects**: Calculation of the estimated net fiscal impact on Cityville's budget. Discussion of potential local economic multiplier effects (positive or negative).
    8.  **Sensitivity Analysis**: Examination of how the fiscal impact estimates change under varying key assumptions (e.g., different UBI take-up rates, varied labor supply responses, different local economic conditions).
    9.  **Comparative Insights**: Brief review of fiscal outcomes and methodologies from UBI pilots or similar programs in other comparable jurisdictions, highlighting relevant lessons for Cityville (if robust data is available).
    10. **Funding Considerations (Overview)**: A high-level discussion of potential funding mechanisms for the pilot program and preliminary thoughts on long-term fiscal sustainability if the program were to be scaled or made permanent.
    11. **Conclusion and Policy Recommendations**: Summary of the overall fiscal outlook for the pilot, and specific, data-driven policy recommendations for the City Council concerning program design, fiscal monitoring, and future decision-making.

---

# E - Examples

*(N/A for providing a full output example of the entire Research Brief. The structure is extensively guided by the Core Content Requirements in R and the Augmentations. However, the target LLM should be capable of generating clear, professional tables and conceptual charts as described in Augmentations.)*

---

# A - Augmentations

**1. Analytical Framework and Rigor**:

- The core analysis must apply principles of **Fiscal Impact Analysis** and incorporate elements of **Cost-Benefit Analysis (CBA)** where appropriate (e.g., when discussing offsetting savings in other program areas).
- All quantitative analysis must be clearly explained, and methodologies should be transparent and replicable in principle.

**2. Evidence and Data Source Mandate**:

- Projections and analyses must be based on **credible public data sources** (e.g., U.S. Census Bureau for Cityville demographics, Bureau of Economic Analysis (BEA) for regional economic data, Bureau of Labor Statistics (BLS) for labor market data).
- Reference **peer-reviewed academic studies on UBI, reports from established research institutions (e.g., Brookings, Urban Institute, J-PAL), and findings from prior UBI experiments or pilots** globally and domestically.
- All significant data points, methodologies, and external study findings must be meticulously cited.
- Clearly state all underlying assumptions and provide justification for their use.

**3. Recency and Data Tools**:

- For comparative data on other UBI pilots, economic conditions, or relevant policy research, use `web.search_query` with a recency filter of **<= 3 years** to ensure current information. Prioritize .gov, .edu, or reputable .org research institutions.
- If generating summary tables or performing calculations based on retrieved data, the use of `python_user_visible` is encouraged for transparency and potential replication.

**4. Illustrative Content and Data Presentation**:

- Include at least **3-4 summary tables or conceptual charts** to present key data effectively (e.g., breakdown of program costs, summary of revenue/expenditure impacts, results of sensitivity analysis). These should be clearly labeled and referenced in the text. The LLM should describe these tables/charts in a way that allows a human to recreate them graphically, or generate them directly if using `python_user_visible`.
- Tag any significant analytical conclusions or projections not directly derivable from cited data or standard models as `[Expert Judgment: Based on established economic principles and synthesis of available data]`.

**5. Content Guardrails and Constraints**:

- Maintain strict **objectivity and neutrality**. The report is an analytical document, not an advocacy piece for or against UBI. Present findings, including potential downsides or uncertainties, transparently.
- Clearly distinguish between direct fiscal impacts on the municipal budget and broader, less direct socio-economic effects (though the latter can be discussed qualitatively if supported by evidence).
- Thoroughly acknowledge all significant **limitations of the analysis** and areas of uncertainty due to data availability or the inherent complexities of predicting behavioral responses to UBI.

---

# T - Tone and Format

**1. Tone and Voice**:

- Adopt a **"Formal / Scholarly"** and **"C-Suite Neutral / Objective"** tone.
- Language: precise, data-driven, analytical, demonstrating high expertise in public finance/policy.
- Explain complex concepts accessibly for intelligent non-experts. Avoid contractions.

**2. Stylometry and Stylistic Directives (Auto-Injected Defaults)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; sigma >= 8. Use varied sentence openings/types.
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside, applied judiciously to maintain neutrality and clarity.
- **Paragraph Pacing**: Mix short (2-3 sentence) and longer (4-6+ sentence) paragraphs with smooth, logical transitions.

**3. Structural Formatting and Punctuation**:

- Include Table of Contents, Executive Summary, comprehensive Bibliography/References (Chicago style, footnotes + full bibliography).
- Organize per R.3 (Core Content) using H2 (main sections), H3/H4 (sub-sections).
- Clearly title, number, and reference all tables/charts.
- Use bullet points/lists sparingly (narrative prose first).
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid and professionally presented.

---

# E - Evaluation

Before finalizing the Research Brief / Whitepaper on the UBI pilot's fiscal impact, perform these critical self-checks. Document any major deviations or uncertainties, and revise to meet all checks:

**1. Core Requirements and Content (vs. R and A)**:
    ***Comprehensive Analysis**: Does the brief fully and thoroughly address all 11 core content areas specified in R.3 (Exec Summary, Intro, Methodology, Costs, Revenue Impact, Expenditure Impact, Net Impact/Multipliers, Sensitivity Analysis, Case Studies, Funding, Conclusion/Recs)?
    * **Methodological Soundness**: Is the fiscal impact methodology clearly articulated and appropriate? Is the approach to CBA/Fiscal Impact Analysis evident?
    ***Augmentations Met**: Are credible public data and research cited appropriately? Is recency considered for external data? Are 3-4 summary tables/charts effectively used and described? Are `[Expert Judgment]` tags applied correctly for significant unsourced inferences? Are all guardrails (objectivity, limitations acknowledged) met?
    * **Length Adherence**: Does the report achieve the substantial detail expected for a ~7,500-word (Tier 7) document?

**2. Accuracy, Grounding and Neutrality (Anti-Hallucination/Bias)**:
    ***Data and Analytical Integrity**: Is all quantitative data accurately presented and sourced? Are calculations and projections logically derived and transparent? Are there *any* fabricated data points, misrepresentations of source material, or unsupported analytical leaps (hallucinations)?
    * **Objectivity and Neutrality**: Is the entire report free from advocacy or bias, presenting a balanced view of potential fiscal impacts, including uncertainties and negative possibilities?
    * **Source Substantiation**: Are all significant claims, findings, and discussions of other UBI pilots properly attributed through Chicago-style citations (footnotes and bibliography)?

**3. Clarity, Tone and Formatting (vs. T and C.Goal)**:
    ***Accessibility for Policymakers**: Despite its depth, is the report written in a way that is clear, precise, and understandable for city council members and other non-expert but informed stakeholders? Are complex terms or models adequately explained?
    * **Tone Consistency**: Does the response consistently maintain the "Formal / Scholarly" and "C-Suite Neutral / Objective" tone? Is sentence-length variability used effectively?
    * **Structural and Formatting Excellence**: Is the report professionally structured with a TOC, logical sections (H2/H3/H4), clear tables/charts, and correctly formatted Chicago citations/bibliography? Is Markdown valid?

**4. Overall Goal Achievement and Decision Support (vs. C.Goal)**:
    *Does the Research Brief effectively provide a comprehensive, evidence-based, and unbiased fiscal impact analysis of the proposed UBI pilot?
    * Does it equip Cityville's policymakers with the critical information needed to make well-informed decisions regarding the UBI pilot program?

*After these checks, briefly summarize your confidence in meeting each major category and detail any significant assumptions, data limitations, or areas where the analysis warrants particular caution or further specialized research.*

# Length Check [Ethics]

| Tier | Name and Synonyms                    | Words                   | Core Use-Case                       |
|------|------------------------------------|-------------------------|-------------------------------------|
| 6    | In-Depth Analysis (technical note) | 2000 - 5000 words       | Internal white memos, policy briefs |
| **7**| **Research Brief / Whitepaper** | **5000 - 10000 words** | **Investor decks, conference papers** |
| 8    | Monograph (comprehensive report)   | 10000 - 25000 words     | Strategy bluebooks, agency playbooks|

**Suggested tier**: **7** | **OK?** (yes / choose another)
**Other changes?**(add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-policy)ANCHOR-FS-POLICY

## [](#4-policy-and-program)4. Policy and Program

## [](#anchor-fs-policy-41)ANCHOR-FS-POLICY-4.1

## [](#41-national-parks-plastic-waste-reduction-policy-monograph---tier-8)4.1. National Parks Plastic Waste Reduction Policy Monograph - Tier 8

#### [](#user-input-6)User Input

> "I need to develop a comprehensive policy monograph proposing strategies to drastically cut
> down on plastic waste in all U.S. National Parks. This needs to be a detailed, actionable plan
> suitable for high-level government review. Can you help craft the C.R.E.A.T.E. prompt for an
> LLM to draft this?"

#### [](#promptcraft-pro-output-7)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are a senior environmental-policy strategist, dedicated to designing bold nationwide park waste-reduction plans.

**2. Background Information**:
Plastic waste accumulation within the U.S. National Park System presents a severe and escalating threat to ecological integrity, wildlife health, visitor experience, and the pristine nature these parks are meant to preserve. Current plastic waste management and reduction efforts are often localized, under-resourced, or insufficient to address the scale of the problem, which includes visitor-generated litter, operational waste from concessions, and plastics entering parks from external sources. A unified, forward-thinking national policy is urgently required to transition the National Park Service (NPS) and its partners towards a model of significantly reduced plastic consumption and improved waste circularity. This Monograph is intended to serve as a foundational document for congressional consideration, NPS strategic planning, and engagement with key stakeholders.

**3. Goal / Intent**:
The primary goal is to produce a **Monograph: A National Policy Proposal for Plastic Waste Reduction in U.S. National Parks**. This comprehensive document aims to:
    a. Thoroughly define the scope and impact of the plastic waste problem in National Parks.
    b. Establish ambitious, yet achievable, national goals for plastic waste reduction and management within the park system over the next decade (e.g., specific percentage reduction targets for single-use plastics, landfill diversion rates).
    c. Detail a suite of integrated policy interventions, innovative strategies, and robust implementation plans.
    d. Analyze potential economic, environmental, and social impacts (both positive and challenging).
    e. Provide clear legislative and regulatory pathways for enactment.
The ultimate impact is to catalyze systemic change, leading to a drastic and sustained reduction of plastic pollution in America's National Parks, thereby protecting these natural treasures for future generations and setting a global example for sustainable park management.

---

# R - Request

**1. Deliverable and Format**:
Draft a **Monograph: A National Policy Proposal for Plastic Waste Reduction in U.S. National Parks**.
The output must be a comprehensive, formally structured policy document suitable for submission to federal legislative bodies, executive agencies (NPS, DOI, EPA), and review by environmental policy experts, NGOs, and industry stakeholders.

**2. Depth and Length**:
The target length is approximately **15,000 words**. This aligns with **Tier 8: Monograph (comprehensive report / strategy bluebook)** from the C.R.E.A.T.E. guide's depth scale. The document must exhibit extensive detail, rigorous analysis, and comprehensive coverage of all specified aspects.

**3. Core Content Requirements (to be structured as chapters/major sections)**:
    1.  **Executive Summary**: A high-level overview of the plastic waste problem in National Parks, the proposed policy's vision, primary goals, key strategic interventions, anticipated impacts, and core recommendations (approx. 500-750 words).
    2.  **Chapter 1: Introduction - The Plastic Crisis in America's Crown Jewels**: Detailed exposition of the problem: types and sources of plastic waste in parks, documented impacts on ecosystems, wildlife, water quality, and visitor experience. Review of existing (often fragmented) policies and their limitations. The urgent imperative for a national strategy.
    3.  **Chapter 2: Vision, Policy Goals, and SMART Objectives**: Articulation of a long-term vision for plastic-free or minimal-plastic National Parks. Definition of clear, measurable, achievable, relevant, and time-bound (SMART) national policy goals and specific objectives (e.g., elimination of specific single-use plastics by YYYY, X% increase in recycling rates, Y% reduction in plastic waste generation per visitor).
    4.  **Chapter 3: Proposed Policy Interventions and Strategic Pillars**: In-depth presentation of a multi-pronged strategic approach, detailing specific policy interventions under pillars such as:
        ***Source Reduction and Prevention**: Restrictions/phase-outs of problematic single-use plastics (e.g., bottles, bags, cutlery, packaging) sold or brought into parks; promoting reusable alternatives.
        * **Sustainable Procurement and Operations**: Mandates and incentives for NPS and park concessioners to adopt sustainable procurement practices, minimize plastic in supply chains, and implement plastic-free operational changes.
        ***Enhanced Waste Management and Circularity**: Investment in modern, standardized waste collection, sorting, recycling, and composting infrastructure within and near parks; strategies for creating local circular economies for park-generated waste.
        * **Visitor Engagement and Public Stewardship**: Comprehensive public education campaigns, clear park-specific guidance, behavioral incentives (and disincentives), and citizen science initiatives.
        * **Innovation and Research**: Support for research into plastic alternatives, advanced recycling technologies suitable for park environments, and microplastic mitigation.
    5.  **Chapter 4: Implementation Framework and Governance**: Detailed plan for phased implementation, including timelines, lead and partner agencies (NPS, DOI, EPA, state agencies), interagency coordination mechanisms, required budgetary allocations (with preliminary estimates), staffing needs, and proposed governance/oversight structures for the national policy.
    6.  **Chapter 5: Stakeholder Engagement, Partnerships and Communication**: Strategies for effectively engaging diverse stakeholders (park visitors, gateway communities, tourism industry, beverage and food industries, plastics industry, environmental NGOs, Indigenous communities, youth groups) in policy development, implementation, and long-term success. Comprehensive communication plan.
    7.  **Chapter 6: Impact Assessment - Environmental, Economic, and Social**: A thorough assessment of the anticipated positive environmental impacts (reduced pollution, ecosystem health). Analysis of potential economic impacts (costs to government/businesses, potential for green job creation, impacts on tourism). Discussion of social equity considerations and benefits.
    8.  **Chapter 7: Proposed Legislative and Regulatory Framework**: Outline of necessary new federal legislation, amendments to existing laws (e.g., NPS Organic Act, procurement laws), and/or specific regulatory changes required at the federal (and potentially state) level to fully enact and enforce the proposed policy.
    9.  **Chapter 8: Monitoring, Evaluation and Adaptive Management**: A framework for monitoring progress towards goals, evaluating policy effectiveness, and adapting the policy over time based on new data, technological advancements, and lessons learned. Key Performance Indicators (KPIs) should be defined.
    10. **Chapter 9: Conclusion and Call to Action**: A powerful summary reinforcing the importance of the policy, reiterating key recommendations, and issuing a strong call to action for all stakeholders to support and implement the vision for plastic-free National Parks.
    11. **Appendices (as appropriate)**: May include detailed data tables, summaries of relevant case studies from other countries or large-scale initiatives, specific legislative language proposals, or detailed cost-benefit analyses for key interventions.

---

# E - Examples

*(N/A for a full output example of this extensive monograph. The detailed Core Content Requirements in R, coupled with the Augmentations and Tone/Format sections, provide comprehensive guidance on the expected structure, content, and style. The persona implies familiarity with the structure of major policy proposals and whitepapers.)*

---

# A - Augmentations

**1. Analytical Frameworks and Approach**:

- The overall policy proposal should implicitly or explicitly utilize a **Logic Model / Theory of Change** approach to demonstrate how proposed activities and outputs will lead to desired short-term, intermediate, and long-term outcomes and impacts regarding plastic waste reduction.
- Chapter 6 (Impact Assessment) should draw on principles of **Environmental Impact Assessment (EIA)** and **Socio-Economic Impact Assessment**.
- Chapter 7 (Legislative and Regulatory Framework) should consider elements of a **Regulatory Impact Analysis (RIA)** for any new proposed regulations.

**2. Evidence and Data Source Mandate**:

- The monograph must be heavily **evidence-based**. All claims, problem statements, and proposed solutions must be supported by credible data from scientific research on plastic pollution and its impacts, official reports from the National Park Service (NPS), Environmental Protection Agency (EPA), National Oceanic and Atmospheric Administration (NOAA), peer-reviewed academic journals, and substantive reports from reputable international bodies (e.g., UNEP, OECD) and major environmental NGOs.
- All sources must be meticulously cited using **APA 7th Edition style**, including in-text citations (Author, Year) and a comprehensive Reference List at the end of the document.

**3. Recency and Data Tools**:

- Prioritize data and research from the **last 5 years** to ensure the policy is informed by the most current understanding of the plastic waste crisis and solutions.
- Utilize `web.search_query` (recency filter as appropriate, e.g., <= 2 years for very current stats or policy examples, <= 5 years for foundational research) to gather:
  - Current statistics on plastic pollution in U.S. National Parks or comparable natural areas.
  - Recent policy initiatives or legislative actions related to plastic reduction (national, state, or international).
  - Best practices and case studies of successful plastic waste reduction programs in large-scale public areas or tourism destinations.
- Any data tables or statistical summaries should clearly state sources and dates. `python_user_visible` can be suggested for generating data visualizations if the LLM is so instructed for specific data.

**4. Illustrative Content and Data Presentation**:

- Incorporate **conceptual frameworks, diagrams (described for later graphic design), or summary tables** (e.g., for policy options comparison, implementation timeline, stakeholder matrix, KPI dashboard). At least 3-5 such illustrative elements should be included or clearly described.
- Use brief, impactful **case study summaries (2-3 examples)** of successful plastic reduction initiatives in other park systems (national or international) or relevant large-scale public venues to highlight feasibility and best practices.
- Tag any novel policy recommendations or significant strategic syntheses not directly derivable from a single cited source as `[Strategic Policy Synthesis based on cited evidence]`.

**5. Content Guardrails and Constraints**:

- The proposal must be **politically aware but ultimately driven by scientific evidence and long-term environmental stewardship goals.** Acknowledge potential political or economic challenges to implementation but focus on constructive, feasible solutions.
- Avoid overly partisan language. The aim is to build broad support.
- Ensure a clear distinction between mandatory policy actions, recommended best practices, and areas requiring further research.
- The economic analysis in Chapter 6 must be balanced, acknowledging both costs of implementation and the economic benefits of cleaner parks and potentially new green industries/jobs.

---

# T - Tone and Format

**1. Tone and Voice**:

- Adopt a **"Formal / Scholarly"** and **"Authoritative Practitioner (Senior Policy Analyst)"** tone.
- Language: highly professional, evidence-based, persuasive, clear; suitable for high-level government/expert audience.
- Voice: confident, visionary, deeply knowledgeable in environmental policy, waste management, public administration. Avoid contractions.
- Define key policy/technical terms upon first use.

**2. Stylometry and Stylistic Directives (Auto-Injected Defaults)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; sigma >= 8. Use varied sentence openings/types.
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside, applied with scholarly subtlety and authority.
- **Paragraph Pacing**: Mix short (2-3 sentence) and longer (4-6+ sentence) paragraphs with smooth, logical transitions.

**3. Structural Formatting and Punctuation**:

- Organize per R.3 (Core Content chapters). Use H1 (Monograph title), H2 (Chapter titles), H3/H4 (sub-sections).
- Generate: Detailed Table of Contents, List of Figures/Tables (if applicable), Executive Summary (R.3.1).
- Comprehensive Reference List (APA 7th Edition) at end, followed by Appendices.
- Use bullet points/lists sparingly (narrative prose first). Well-developed paragraphs.
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid, professional document standards.

---

# E - Evaluation

Before finalizing this extensive Monograph on National Parks Plastic Waste Reduction Policy, perform these critical self-checks with exceptional rigor. Document any major deviations, uncertainties, or areas where assumptions were made, and revise thoroughly to meet all checks:

**1. Core Requirements and Comprehensive Detail (vs. R and A)**:
    ***Chapter Coverage**: Does the Monograph fully and comprehensively address all 11 specified chapters/core content areas from R.3, with appropriate depth and detail for a 15,000-word document?
    * **Framework Application**: Are the Logic Model/Theory of Change, EIA/Socio-Economic Impact, and RIA principles evident and correctly applied in the relevant sections as per Augmentations?
    ***Augmentations Met**: Is the analysis heavily evidence-based with meticulous APA 7th citations and a full Reference List? Is recent data (via `web.search_query`) incorporated? Are 3-5 conceptual visuals/tables effectively included/described? Are case studies used? Is the `[Strategic Policy Synthesis]` tag applied correctly? Are all guardrails met?
    * **Length Adherence**: Does the document substantially meet the ~15,000-word target (Tier 8)?

**2. Accuracy, Grounding and Analytical Soundness (Anti-Hallucination/Bias)**:
    ***Data and Factual Integrity**: Is all statistical data, scientific information, and discussion of existing policies accurate and correctly attributed to credible sources? Are there *any* fabricated data, misattributed claims, or unsupported assertions (hallucinations)?
    * **Analytical Rigor**: Are arguments logical, well-supported by evidence, and internally consistent? Are methodologies for impact assessment sound?
    * **Objectivity and Neutrality**: Is the entire monograph free from undue bias or political slanting, presenting a balanced, evidence-driven case for the proposed policy? Are potential challenges and counterarguments fairly addressed?

**3. Clarity, Persuasiveness, Tone and Formatting (vs. T and C.Goal)**:
    ***Accessibility for Policymakers**: Despite its length and depth, is the monograph written in a clear, precise, and compelling manner that is understandable and persuasive to high-level policymakers, agency heads, and expert stakeholders? Are complex issues broken down effectively?
    * **Tone Consistency**: Does the response consistently maintain the "Formal / Scholarly" and "Authoritative Practitioner" tone? Is sentence-length variability managed well for readability?
    * **Structural and Formatting Excellence**: Is the monograph professionally structured with a TOC, List of Figures/Tables, logical chapter/section flow (H1/H2/H3/H4), and correctly formatted APA 7th citations/references? Is Markdown valid?

**4. Overall Goal Achievement and Policy Impact (vs. C.Goal)**:
    *Does the Monograph present a truly comprehensive, compelling, actionable, and evidence-based national policy proposal for significantly reducing plastic waste in U.S. National Parks?
    * Does it provide a strong foundation for legislative action, agency strategy, and broad stakeholder engagement?

*After these checks, provide a summary of your confidence in meeting each major category (e.g., High for all) and explicitly detail any significant assumptions made (e.g., availability of certain types of data from web search) or areas where the complexity of the topic means that human expert review and refinement would be particularly critical.*

# Length Check

| Tier | Name and Synonyms                    | Words                   | Core Use-Case                       |
|------|------------------------------------|-------------------------|-------------------------------------|
| 7    | Research Brief / Whitepaper        | 5000 - 10000 words      | Investor decks, conference papers   |
| **8**| **Monograph (comprehensive report)**| **10000 - 25000 words** | **Strategy bluebooks, agency playbooks**|
| 9    | Treatise / Compendium (exhaustive) | 25000 - 50000 words     | Regulatory impact studies, book-length work |

**Suggested tier**: **8** | **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-itsec)ANCHOR-FS-ITSEC

## [](#5-it-and-security)5. IT and Security

## [](#anchor-fs-itsec-51)ANCHOR-FS-ITSEC-5.1

## [](#51-zero-trust-architecture-report---tier-5)5.1. Zero Trust Architecture Report - Tier 5

#### [](#user-input-7)User Input

> "I need to develop a report explaining Zero Trust Architecture to a non-technical management
> team."

#### [](#promptcraft-pro-output-8)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are an expert cybersecurity strategist, skilled at explaining complex ZTA concepts to executives clearly.

**2. Background Information**:
The organization is considering a strategic shift towards **Zero Trust Architecture (ZTA)** as a foundational element of its cybersecurity posture enhancement. This initiative requires buy-in and understanding from non-technical executive management, who are aware of general cybersecurity threats (e.g., ransomware, data breaches) but may not be familiar with the specific principles, operational impacts, or strategic benefits and challenges of ZTA. This document is intended to be a comprehensive **briefing report** (or a significant section thereof) that educates them thoroughly. The key challenge is to provide substantial detail and cover broad implications while maintaining clarity and avoiding overly technical language.

**3. Goal / Intent**:
The primary goal is to produce a **detailed yet accessible report that provides non-technical executive management with a comprehensive understanding of Zero Trust Architecture.** The output should enable them to:
    a. Clearly grasp the definition, core philosophy, and fundamental principles of ZTA.
    b. Understand its significant differences from, and advantages over, legacy security models.
    c. Appreciate the broad operational and strategic impacts of ZTA across key areas like identity, network, and vendor risk.
    d. Make informed assessments of the benefits and challenges associated with ZTA adoption.
    e. Internalize key executive takeaways to guide strategic discussions and decision-making regarding ZTA implementation and investment.
The ultimate impact is to foster a well-informed leadership team capable of championing and effectively overseeing the organization's transition towards a Zero Trust security model.

---

# R - Request

**1. Deliverable and Format**:
Produce a comprehensive **Extended Overview** of Zero Trust Architecture (ZTA).
The output should be structured as a detailed briefing document or an in-depth section of a larger report, suitable for informing a non-technical management team. While detailed, the language must remain clear and accessible.

**2. Depth and Length**:
The target length is approximately **1500 words**. This aligns with **Tier 5: Extended Overview (mini-report)** from the C.R.E.A.T.E. guide's depth scale.
The content should provide a thorough understanding of the topic as outlined below.

**3. Core Content Requirements**:
The "Extended Overview" must comprehensively address the following five key areas:
    1.  **Definition and Contrast**: Clearly define Zero Trust Architecture and thoroughly contrast it with legacy perimeter-based security models, explaining the fundamental shift in security philosophy.
    2.  **Core Principles Explained**: Detail and explain the core principles of ZTA, ensuring concepts like “never trust, always verify,” micro-segmentation, and least privilege access are made understandable for a non-technical audience.
    3.  **Impact Areas**: Illustrate and discuss the practical impacts of adopting ZTA across key organizational domains, specifically:
        *Identity management and user access.
        * Network architecture and data flows.
        * Vendor risk management and third-party access.
    4.  **Benefits and Challenges**: Provide a balanced perspective by listing and discussing both the significant business and security benefits of implementing ZTA, as well as common challenges or considerations organizations face during adoption (e.g., complexity, cost, cultural shift).
    5.  **Executive Takeaways**: Conclude with exactly five distinct, actionable executive takeaways that summarize the most critical points for a management audience to understand and consider regarding ZTA.

---

# E - Examples

*(N/A for providing a full output example of the report. However, specific illustrative elements like analogies and "ZTA in Action" callout boxes are requested in Augmentations to guide the style of those parts of the content.)*

---

# A - Augmentations

**1. Evidence and Data Source Guidance**:

- The explanation must be well-grounded in **authoritative industry definitions, frameworks, and foundational principles of Zero Trust Architecture**. Key reference points include **NIST Special Publication 800-207 ("Zero Trust Architecture")** and guidance from CISA (Cybersecurity and Infrastructure Security Agency).
- While the main body should prioritize plain-language explanation, consider including a brief **appendix or a formal reference list** at the end of the report citing these key foundational documents if appropriate for the report's formality. Direct in-text Bluebook style citations are not required for the main body unless explaining a direct quote from a standard.

**2. Recency and Industry Context**:

- Focus on established ZTA concepts, but also incorporate current understanding of benefits, challenges, and adoption trends.
- If possible, use `web.search_query` (recency <= 365 days) to find 1-2 recent, high-level industry survey summaries or reputable analyst reports (e.g., from Gartner, Forrester, or major cybersecurity firms) that touch upon ZTA adoption rates, perceived benefits, or common implementation hurdles. Synthesize any relevant findings briefly into the "Benefits and Challenges" section, citing the source generally (e.g., "Recent industry reports suggest...").

**3. Illustrative Content Requirement**:

- Employ at least **two clear, non-technical analogies** to explain core ZTA concepts (e.g., one for "never trust, always verify" and another perhaps for "microsegmentation" if discussed).
- Integrate **1-2 short "ZTA in Action" callout boxes** (approx. 50-75 words each). These should provide brief, concrete examples of how a ZTA principle might apply in a relatable business scenario (e.g., securing remote access for a specific department, protecting sensitive data in a cloud application).

**4. Content Guardrails and Constraints**:

- **Minimize Deep Technical Jargon**: Where technical terms are unavoidable (e.g., "microsegmentation," "identity and access management (IAM)," "multi-factor authentication (MFA)"), they MUST be immediately followed by a concise, simple parenthetical explanation or woven into a sentence that clarifies their meaning for a non-technical reader.
- **Vendor Neutrality**: The report must remain strictly **vendor-neutral**. Do NOT recommend, mention, or allude to specific commercial products, services, or security vendors. The focus is purely on the ZTA framework, principles, and strategy.
- **Balanced Perspective**: Ensure the "Benefits and Challenges" section is balanced. While the overall goal is to demystify and show value, a credible report acknowledges implementation realities.

---

# T - Tone and Format

**1. Tone and Voice**:

- Adopt a **"C-Suite Neutral"** tone, blended with **"Warm / Conversational"** and **"Plain-Language"** for conceptual explanations.
- Voice: strategic, authoritative, confident, credible, accessible, educational for non-technical executives. Use contractions.
- Engaging but not overly casual.

**2. Stylometry and Stylistic Directives (Auto-Injected Defaults)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; sigma >= 8. Use varied sentence openings/types.
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside, suitable for engaging executives.
- **Paragraph Pacing**: Mix short (2-3 sentence) and medium/longer (4-6+ sentence) paragraphs with smooth transitions.

**3. Structural Formatting and Punctuation**:

- Structure: Intro, body sections per R.3 (Core Content), distinct "Executive Takeaways."
- Use H2 (main sections), H3 (sub-sections).
- Employ short to medium-length paragraphs.
- Use bullet/numbered lists judiciously as requested by user for principles, benefits, challenges, executive takeaways.
- "ZTA in Action" callout boxes: visually distinct (blockquotes or emphasis).
- Reference list/appendix (if included): format appropriately at end.
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid.

---

# E - Evaluation

Before finalizing your "Extended Overview" report on Zero Trust Architecture, perform these critical self-checks rigorously. Document any major deviations or uncertainties, and revise to meet all checks:

**1. Core Requirements and Content (vs. R and A)**:
    ***Comprehensive Coverage**: Does the report fully and thoroughly address all five core content areas specified in the Request (ZTA definition/contrast, core principles with specified examples, impact areas, benefits and challenges, 5 executive takeaways)?
    * **Augmentations Met**: Is the explanation grounded in authoritative ZTA concepts (e.g., NIST SP 800-207 mentioned or its principles clearly reflected)? Are >=2 clear analogies used? Are 1-2 "ZTA in Action" callout boxes included? Are guardrails (jargon explanation, vendor neutrality, balanced view) strictly followed? Is recent industry context (if found via search) appropriately synthesized?
    * **Length Adherence**: Is the response robust and detailed, approaching the ~1500-word target (Tier 5)?

**2. Accuracy, Grounding and Neutrality (Anti-Hallucination/Bias)**:
    ***Factual and Conceptual Integrity**: Is all information regarding ZTA principles, benefits, challenges, and impacts accurate and aligned with established industry understanding and authoritative sources like NIST? Are there *any* fabricated details, misrepresentations, or unsupported claims (hallucinations)?
    * **Objectivity and Vendor Neutrality**: Is the content presented objectively, factually, and strictly vendor-neutral?
    * **Source Integration (if applicable)**: If an appendix/reference list is used, is it accurate? Is any synthesized `web.search_query` data appropriately caveated?

**3. Clarity, Tone and Formatting (vs. T and C.Goal)**:
    ***Executive Accessibility**: Is the entire report exceptionally clear, strategically focused, and easily understood by a non-technical management audience despite its depth? Is technical jargon minimized and always explained?
    * **Tone Consistency**: Does the response consistently maintain the prescribed "C-Suite Neutral," "Warm / Conversational," and "Plain-Language" blend appropriate for the content?
    * **Structural Integrity**: Is the report well-organized with H2/H3 headings? Are paragraphs and lists used effectively for readability? Does the "Executive Takeaways" section stand out clearly? Is Markdown valid?

**4. Overall Goal Achievement and Strategic Impact (vs. C.Goal)**:
    *Does the report effectively demystify Zero Trust Architecture in a comprehensive manner?
    * Does it provide executives with the necessary understanding to engage in informed strategic discussions and make decisions regarding ZTA adoption and investment?

*After these checks, briefly summarize your confidence in meeting each major category and note any significant assumptions made or areas where further refinement by a human SME would be beneficial given the report's depth.*

# Length Check [Ethics]

| Tier | Label             | Words             | Typical use                  |
|------|-------------------|-------------------|------------------------------|
| 4    | Overview          | 400-900           | Brief                        |
| **5**| **Extended Overview** | **900-2000 words** | **Mini-report / Detailed Brief** |
| 6    | In-Depth Analysis | 2000 - 5000 words | Internal white memos / Deep Dive |

**Suggested tier**: **5** | **OK?** (yes / choose another)
**Other changes?**(add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-itsec-52)ANCHOR-FS-ITSEC-5.2

## [](#52-sso-definition-one-liner---tier-1)5.2. SSO Definition One-Liner - Tier 1

#### [](#user-input-8)User Input

> "My boss asked for a one-liner on what 'SSO' means for our internal security memo. Can you
> make a prompt for that?"

#### [](#promptcraft-pro-output-9)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are an IT communications assistant, adept at crafting succinct definitions for business audiences.

**2. Background Information**:
An internal security memo requires a very brief explanation of Single Sign-On (SSO) to ensure all employees understand this common security feature. The explanation needs to be extremely concise.

**3. Goal / Intent**:
To generate a **single, clear sentence defining Single Sign-On (SSO)** that can be easily integrated into a security memo for employees.

---

# R - Request

**1. Deliverable and Format**:
Produce a **one-sentence definition** of Single Sign-On (SSO).

**2. Depth and Length**:
The target length is a **Nano Answer (Tier 1: <= 60 words / approx. 1 sentence)**.

**3. Core Content Requirements**:
The definition must succinctly explain:
    *What SSO allows a user to do (e.g., access multiple applications).
    * The primary benefit (e.g., using a single set of credentials).

---

# E - Examples

*(N/A for a nano-definition task.)*

---

# A - Augmentations

**1. Evidence and Data Source Guidance**:

- Base the definition on generally accepted industry understanding of SSO. No external citation is required in the output sentence itself.

**2. Content Guardrails**:

- Avoid technical jargon within the definition.
- Ensure the definition is accurate and not misleading.

---

# T - Tone and Format

**1. Tone and Voice**:

- Adopt a **"Plain-Language"** and **"Precise"** tone. Language very clear and direct.
- Use contractions if natural for a single sentence.

**2. Stylometry and Stylistic Directives (Applied as relevant to a single sentence)**:

- **Lexical Diversity**: Choose clear, common words; avoid clichés.
- (Hedge, Sentence Variability, Rhetoric, Pacing largely N/A for a single definitional sentence).

**3. Structural Formatting and Punctuation**:

- Output must be a single, grammatically correct sentence.
- Punctuation: Standard sentence punctuation. **No em-dashes.**

---

# E - Evaluation

Before finalizing the SSO definition, perform these self-checks:

**1. Core Requirements (vs. R and A)**:
    *Does the output define SSO and its key benefit within a single sentence?
    * Is the definition jargon-free and accurate?

**2. Length and Clarity (vs. R and T)**:
    *Is the definition <= 60 words (Tier 1)?
    * Is it exceptionally clear and unambiguous?

**3. Goal Achievement (vs. C.Goal)**:
    * Does the sentence effectively provide the required one-liner for the memo?

*After these checks, confirm suitability.*

# Length Check [Ethics]

| Tier | Name and Synonyms                    | Words                 | Core Use-Case                       |
|------|------------------------------------|-----------------------|-------------------------------------|
| **1**| **Nano Answer (blurb, micro-reply)** | **<= 60 words approximately 80 tokens** | **One-line definitions or fact checks** |
| 2    | Executive Snapshot (headline)      | 80 - 150 words        | C-suite bullet-point summary        |
| 3    | Concise Summary (abstract, précis) | 150 - 400 words       | Board memo abstracts, article abstracts |

**Suggested tier**: **1** | **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-itsec-53)ANCHOR-FS-ITSEC-5.3

## [](#53-future-today-strategy-group-2025-tech-trends-report-highlights---tier-2)5.3. Future Today Strategy Group 2025 Tech Trends Report Highlights - Tier 2

#### [](#user-input-9)User Input

> "My director needs a quick rundown of the main points from the new Future Today Strategy
> Group's 2025 Tech Trends report for our team meeting tomorrow. Just the absolute highlights, very short and sweet. Can you build a prompt for this?"

#### [](#promptcraft-pro-output-10)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are an information analyst, skilled at summarizing critical tech report insights for busy professionals.

**2. Background Information**:
A director requires a highly condensed overview of the primary findings from the extensive "Future Today Strategy Group's 2025 Tech Trend Report" (available at `https://ftsg.com/wp-content/uploads/2025/03/FTSG_2025_TR_FINAL_LINKED.pdf`). This summary is for quick dissemination at an internal team meeting to ensure awareness of pivotal technological developments. The emphasis is on extreme brevity and capturing only the most impactful takeaways suitable for a general business audience.

**3. Goal / Intent**:
To generate a **brief "executive snapshot" (3-4 key bullet points) highlighting the most significant overarching themes or a few specific impactful trends** from the "Future Today Strategy Group's 2025 Tech Trend Report," making them easily digestible for a team needing a quick update.

---

# R - Request

**1. Deliverable and Format**:
Produce an **Executive Snapshot** identifying 3-4 key high-level findings or major themes from the "Future Today Strategy Group's 2025 Tech Trend Report."
The output should be a concise bulleted list.

**2. Depth and Length**:
The target length is an **Executive Snapshot (Tier 2: 80-150 words)**. Each bullet point should be a single, impactful sentence.

**3. Core Content Requirements**:
The snapshot must identify and concisely state:
    * Three or four of the most significant, overarching trends or broadly impactful conclusions presented in the report's summary or introduction. Given the report's size (1000 pages), focus on what's highlighted for general understanding rather than deep dives into specific sub-reports.

---

# E - Examples

*(N/A. The bullet-point format is simple and specified in R and T.)*

---

# A - Augmentations

**1. Evidence and Data Source Guidance**:

- **Primary Instruction**: "Your summary should be based on the executive summary, introduction, or clearly stated key takeaways from the 'Future Today Strategy Group's 2025 Tech Trend Report,' accessible via the URL: `https://ftsg.com/wp-content/uploads/2025/03/FTSG_2025_TR_FINAL_LINKED.pdf`.
- You may need to use a Browse tool to access and process content from this PDF URL to identify the main themes or takeaways if direct analysis of the PDF is not possible. Focus on information presented early in the report, typically aimed at a general executive audience.
- Prioritize findings that are highlighted as most impactful or cross-cutting by the report authors themselves.

**2. Content Guardrails**:

- Extract only the most significant, high-level findings or themes. The report is 1000 pages; do not attempt to summarize sub-sections.
- Avoid delving into highly specific details of individual trends if they are not part of the main overarching messages.
- Do not editorialize or add external opinions; stick to summarizing the report's stated key insights.
- Clearly attribute the findings to the "Future Today Strategy Group's 2025 Tech Trend Report."

---

# T - Tone and Format

**1. Tone and Voice**:

- Adopt a **"C-Suite Neutral," "Informative,"** and **"Precise"** tone.
- Language: direct, factual, easily scannable. Use contractions.

**2. Stylometry and Stylistic Directives (Applied to intro sentence and bullet content)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: For sentences used, aim for Avg 17-22 words; >= 15 % < 8 w and >= 15 % > 30 w; sigma >= 8. Use varied openings/types.
- **Rhetorical Devices**: If intro sentence allows, include >= 1 rhetorical Q AND >= 1 first-person or direct-address aside.
- **Paragraph Pacing**: (Applicable to intro sentence if used).

**3. Structural Formatting and Punctuation**:

- Optional single introductory sentence (e.g., "Key highlights... include:").
- Output as a **bulleted list (3 to 4 concise points)** as requested by user. Each bullet: a complete sentence summarizing a key theme/finding.
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid.

---

# E - Evaluation

Before finalizing the snapshot of the "Future Today Strategy Group's 2025 Tech Trend Report," perform these self-checks:

**1. Core Requirements and Focus (vs. R and A)**:
    *Does the output consist of 3-4 distinct bullet points?
    * Do these points genuinely reflect *key, high-level* findings or themes from the report's summary sections?
    * Is it clear that the information is from the specified report?

**2. Brevity and Impact (Tier 2 Length vs. R)**:
    *Is the entire snapshot (all bullet points combined) within the 80-150 word limit (Tier 2)?
    * Is each bullet point impactful and concise?

**3. Clarity and Tone (vs. T and C.Goal)**:
    *Is the language exceptionally clear, unambiguous, and professional ("C-Suite Neutral," "Precise")?
    * Does it directly provide the "need-to-know" highlights for quick team awareness?

*After these checks, confirm suitability for a rapid team briefing.*

# Length Check

| Tier | Name and Synonyms                    | Words                 | Core Use-Case                       |
|------|------------------------------------|-----------------------|-------------------------------------|
| 1    | Nano Answer (blurb, micro-reply)   | <= 60 words            | One-line definitions or fact checks |
| **2**| **Executive Snapshot (headline)** | **80 - 150 words** | **C-suite bullet-point summary** |
| 3    | Concise Summary (abstract, précis) | 150 - 400 words       | Board memo abstracts, article abstracts |

**Suggested tier**: **2** | **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-taxacc)ANCHOR-FS-TAXACC

## [](#6-tax-and-accounting)6. Tax and Accounting

## [](#anchor-fs-taxacc-61)ANCHOR-FS-TAXACC-6.1

## [](#61-earned-income-credit-overview---tier-4)6.1. Earned Income Credit Overview - Tier 4

#### [](#user-input-10)User Input

> “I need to learn more about the earned income credit.”

#### [](#promptcraft-pro-output-11)PromptCraft Pro Output

```markdown
# C - Context

Role: You are an expert U.S. tax advisor, specializing in demystifying the Earned Income Credit
Background: Explaining the Earned Income Credit (EIC) for the most recent tax year; many filers misunderstand eligibility.
Goal: Demystify EIC for a financially curious, non-expert reader.

# R - Request

**Overview (~600 words)** covering

1. Purpose of the EIC
2. Eligibility rules (with/without children)
3. How the credit is calculated (phase-in / phase-out ranges)
4. Refundability impact on liability
5. Two numeric illustrations

# E - Examples

N/A

# A - Augmentations

- Cite IRS Pub 596 (year-stamped).
- Two numeric examples (single w/o child; MFJ + 2 children).
- Plain-language metaphors for *refundability* and *phase-out*.
- “No tax advice” disclaimer + IRS resources link.

# T - Tone and Format

**1. Tone and Voice**:

- **"Warm, conversational."** Use contractions.

**2. Stylometry and Stylistic Directives (Auto-Injected Defaults)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; sigma >= 8. Use varied sentence openings/types.
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside.
- **Paragraph Pacing**: Mix short (2-3 sentence) and longer (4-6+ sentence) paragraphs with smooth transitions.

**3. Structural Formatting and Punctuation**:

- Use bold section heads.
- Chicago footnotes for citations.
- Use bullet points/lists sparingly (narrative prose first).
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid.

# E - Evaluation

Self-check - ensure coverage of five items; FK 10-12; Reading Ease 50-60; numeric examples present; `[Expert Judgment]` tags where uncited.

# Length Check

| Tier | Label          | Words | Typical use       |
|----|----------------|-------|-------------------|
| 3 | Concise        | 150-400 | Slide / memo      |
| **4** | **Overview** | **400-900** | **Brief report** |
| 5 | Extended       | 900-2000 | Mini-report       |

**Suggested tier**: **4** | **OK?** (yes / choose another)
**Other changes?**(add / delete / tweak any C-R-E-A-T-E block before we finalise)

```

## [](#anchor-fs-compglob)ANCHOR-FS-COMPGLOB

# [](#7-comparative--global)7. Comparative / Global

## [](#anchor-fs-compglob-71)ANCHOR-FS-COMPGLOB-7.1

## [](#71-renewable-energy-strategies-germany-vs-japan---tier-9)7.1. Renewable Energy Strategies (Germany vs. Japan) - Tier 9

#### [](#user-input-11)User Input

> "I need an exhaustive, book-length treatise comparing Germany's and Japan's renewable energy
> strategies and policy outcomes over the last two decades, say 2005 to 2025. This must be a deep
> academic work, identifying transferable lessons for other developed nations. Can you help me
> structure the C.R.E.A.T.E. prompt for an LLM to undertake such a significant research and writing
> task?"</USER>

#### [](#promptcraft-pro-output-12)PromptCraft Pro Output

```markdown
# C - Context

**1. Role**:
You are a distinguished professor of international energy policy, known for rigorous global
renewable strategy comparisons.

**2. Background Information**:
Germany (with its "Energiewende") and Japan (especially post-Fukushima) represent two major
industrialized nations that have pursued distinct and highly consequential pathways towards increasing
renewable energy (RE) adoption and transforming their energy sectors over the past two decades
(approximately 2005-2025). A comprehensive, critical, and comparative examination of their respective
policy frameworks (e.g., feed-in tariffs (FiTs), auction mechanisms, carbon pricing, RandD investment
strategies), technological choices (solar PV, onshore/offshore wind, biomass, geothermal, hydrogen),
grid integration challenges, socio-economic contexts (public acceptance, industry structure, land use),
and resulting successes and failures in deployment and emissions reduction offers invaluable, though
complex, lessons for other developed and developing nations navigating their own energy transitions
in the face of the global climate imperative. This treatise is intended as a definitive scholarly
reference.

**3. Goal / Intent**:
The primary goal is to produce an **exhaustive, academically rigorous Treatise / Compendium** that
provides a profound, critical, and meticulously documented comparative analysis of renewable energy
adoption strategies, policy effectiveness, and broader socio-economic and environmental impacts in
Germany and Japan covering the period from approximately 2005 to 2025. The treatise must:
    a. Systematically deconstruct and compare the energy policy landscapes and specific RE support
    mechanisms in both nations.
    b. Critically evaluate the outcomes, efficiencies, and distributional effects of these policies.
    c. Analyze the interplay of technological, economic, political, social, and institutional factors
    shaping RE development in each country.
    d. Identify key drivers of success, persistent challenges, unintended consequences, and instances
    of policy learning or failure.
    e. Derive nuanced, context-sensitive, and transferable lessons along with robust policy
    recommendations applicable to other developed (and potentially developing) nations aiming to
    accelerate their renewable energy deployment and achieve ambitious climate mitigation targets.
The ultimate impact is to significantly contribute to the global academic and policy understanding
of large-scale energy transitions, providing a definitive reference work for scholars, policymakers,
international organizations, and advanced students.

---

# R - Request

**1. Deliverable and Format**:
Draft a **Treatise / Compendium: "A Comparative Analysis of Renewable Energy Strategies and Policy
Effectiveness in Germany and Japan (2005-2025): Lessons for Global Sustainable Energy Transitions."**
The output must be a substantial, book-length scholarly work, suitable for academic publication or as
a definitive reference for high-level international policy bodies.

**2. Depth and Length**:
The target length is approximately **30,000 - 40,000 words**. This aligns with **Tier 9: Treatise /
Compendium (exhaustive, book-length work)** from the C.R.E.A.T.E. guide's depth scale. The work must
demonstrate exceptional depth of research, analytical rigor, and comprehensive coverage.

**3. Core Content Requirements (to be structured as major Parts and detailed Chapters)**:
    **Part I: Theoretical Foundations and Methodological Framework**
        *Chapter 1: Introduction - The Global Imperative for Energy Transition and Comparative Policy
        Analysis (Research questions, significance, theoretical underpinnings of comparative energy
        policy, methodological approach for the treatise, scope, limitations, and structure of the work).
        * Chapter 2: The Political Economy of Energy Transitions - A Framework for Analyzing Germany and Japan.
    **Part II: Case Study - Germany's Energiewende: Ambitions, Policies, and Outcomes (2005-2025)**
        *Chapter 3: Historical Context, Political Drivers, and Evolution of the Energiewende.
        * Chapter 4: Key Policy Instruments for Renewable Energy Deployment (EEG, FiTs, auctions,
        emissions trading, nuclear phase-out, efficiency measures) - Design, Implementation, and Revisions.
        *Chapter 5: Technological Focus, Innovation, and Grid Integration Strategies (Solar PV,
        Onshore/Offshore Wind, Biomass, Storage, Smart Grids).
        * Chapter 6: Quantitative Analysis of RE Deployment, Energy Mix Transformation, and Climate
        Target Achievement.
        *Chapter 7: Economic Impacts - Costs of the Transition, Electricity Prices, Industrial
        Competitiveness, Employment Effects.
        * Chapter 8: Social and Political Dimensions - Public Acceptance, Stakeholder Coalitions,
        Regional Disparities, Justice and Equity Issues.
        *Chapter 9: Critical Assessment - Successes, Unintended Consequences, and Enduring Challenges
        of the Energiewende.
    **Part III: Case Study - Japan's Renewable Energy Trajectory: Post-Fukushima Realities and Future
    Aspirations (2005-2025)**
        * Chapter 10: Energy Policy Before and After Fukushima - Shifting Paradigms and RE Drivers.
        *Chapter 11: Key Policy Instruments for Renewable Energy (FiTs, Strategic Energy Plans, carbon
        targets, hydrogen strategy) - Design, Implementation, and Effectiveness.
        * Chapter 12: Technological Focus, Innovation, and Grid Integration Strategies (Solar PV
        dominance, Offshore Wind development, Geothermal, Hydrogen).
        *Chapter 13: Quantitative Analysis of RE Deployment, Energy Mix Transformation, and Climate
        Target Achievement.
        * Chapter 14: Economic Impacts - Costs of RE, Electricity System Resilience, Energy Security,
        Industrial Impacts.
        *Chapter 15: Social and Political Dimensions - Public Opinion on Nuclear vs. RE, Land Use
        Conflicts, Community Benefit Models.
        * Chapter 16: Critical Assessment - Progress, Bottlenecks (grid, regulatory, market), and Unmet
        Potential.
    **Part IV: Rigorous Comparative Analysis and Synthesis**
        *Chapter 17: Comparing Policy Design and Governance Models - Effectiveness of FiTs vs. Auctions,
        Centralized vs. Decentralized Approaches.
        * Chapter 18: Contrasting Technological Pathways, RandD Strategies, and Innovation Ecosystems.
        *Chapter 19: Economic Performance Compared - Cost-Effectiveness, System Costs, and Industrial
        Policy Outcomes.
        * Chapter 20: The Role of Political Systems, Institutional Capacities, Incumbent Interests,
        and Civil Society Engagement in Shaping Divergent Outcomes.
        *Chapter 21: Synthesizing Key Convergences, Divergences, and Cross-Cutting Factors of Success
        and Failure.
    **Part V: Transferable Lessons and Global Policy Recommendations for Accelerating Sustainable
    Energy Transitions**
        * Chapter 22: Distilling Critical, Context-Adaptable Lessons from the German and Japanese
        Experiences for Other Developed (and G20) Nations.
        *Chapter 23: Specific, Evidence-Based Policy Recommendations for:
            * Designing robust and adaptive RE support schemes.
            *Fostering technological innovation and cost reduction.
            * Modernizing electricity grids and markets for high RE penetration.
            *Ensuring social equity, public participation, and just transitions.
            * Overcoming political, institutional, and economic barriers to RE scale-up.
        *Chapter 24: Considerations for Tailoring Lessons to Diverse National Contexts and Stages
        of Development.
    **Part VI: Conclusion**
        * Chapter 25: Summary of Major Comparative Findings, a Forward-Looking Perspective on the Future
        of Global Renewable Energy, and Areas for Future Research.
    **Comprehensive Bibliography and Appendices** (e.g., detailed comparative data tables, policy
    instrument summaries, stakeholder interview lists (conceptual)).

---

# E - Examples

*(N/A for providing a full output example of this highly extensive treatise. The detailed chapter
structure in R, coupled with the methodological guidance in A, will shape the output. The persona
implies expertise in structuring such comprehensive, book-length academic works.)*

---

# A - Augmentations

**1. Analytical and Theoretical Frameworks**:

- The treatise must be grounded in a robust **Comparative Policy Analysis framework**, explicitly
stated and applied in Part IV. This should outline the dimensions for comparison (e.g., policy goals,
specific instruments, implementation processes, institutional settings, actor constellations, policy
outcomes, contextual variables).
- Integrate relevant theories from political science, economics, and sociology of technology to explain policy choices and outcomes (e.g., theories of policy learning, path dependency, socio-technical transitions, Varieties of Capitalism).
- The **OECD Better-Regulation Toolkit principles** should be an implicit guide for evaluating policy effectiveness and design. Where appropriate, concepts from **PESTLE analysis** can be used to frame discussions of the broader country-specific contexts.

**2. Evidence and Data Source Mandate (Utmost Rigor)**:

- This treatise requires **extensive and meticulous reliance on primary and secondary academic sources, official government documents, energy statistics from Germany (e.g., BMWi/BMWK, Destatis, Fraunhofer ISE, Agora Energiewende) and Japan (e.g., METI, ANRE, ISEP), comprehensive data and flagship reports from premier international energy organizations (IEA, IRENA, REN21, IPCC, World Bank), peer-reviewed articles from leading energy policy and social science journals, and authoritative reports from respected energy policy think tanks and research institutes.**
- All sources must be cited precisely and comprehensively using **The Chicago Manual of Style (17th edition or later), utilizing footnotes for substantive commentary and citations, and a complete Bibliography at the end.**

**3. Recency, Data Tools and Triangulation**:

- Primary data analysis should cover the approximate period of 2005-2025. Analytical commentary and literature review should include the most current available research (up to the last 1-2 years where possible).
- Extensive use of `web.search_query` with specific keywords, domain restrictions (.gov, .edu, .org for IGOs/NGOs), and date filters will be essential to:
  - Retrieve specific government energy plans, policy evaluations, and statistical yearbooks from both countries.
  - Access flagship comparative reports and datasets from IEA, IRENA, etc.
  - Find key academic papers and working papers from NBER, university research centers, etc.
- Data should be triangulated from multiple sources where possible. Any discrepancies or limitations in data must be noted.
- If presenting complex quantitative comparisons, use of `python_user_visible` to generate summary statistics or describe data for tables/charts is highly encouraged.

**4. Illustrative Content and Data Presentation**:

- The treatise must include **numerous (at least 10-15) comparative tables, charts, and potentially conceptual diagrams** (e.g., policy timelines, RE deployment trajectories, cost curves, institutional maps, summaries of policy instrument features). These must be clearly titled, numbered, sourced, and discussed in the text. The LLM should describe these in detail for later graphic design or generate them directly using `python_user_visible` where feasible for tabular data.
- Tag any major unsourced novel theoretical syntheses or high-level comparative judgments as `[Scholarly Synthesis and Interpretation based on comprehensive evidence review]`.

**5. Content Guardrails and Constraints**:

- Maintain strict **academic objectivity, impartiality, and a deeply critical (yet constructive) analytical stance.** Avoid any nationalistic bias or uncritical endorsement of any single policy model.
- Thoroughly explore and acknowledge the complexities, trade-offs, and contested aspects of energy transitions in both countries.
- All data must be presented with full source attribution and methodological transparency.
- Ensure a clear distinction is made between empirical data, policy descriptions, analytical interpretations, and normative recommendations.

---

# T - Tone and Format

**1. Tone and Voice**:

- Tone: **"Formal / Scholarly,"** reflecting **"Authoritative Practitioner" (Distinguished Professor / International Policy Expert)** persona.
- Language: exceptionally precise, nuanced, analytical, deeply evidence-based; suitable for sophisticated international expert audience. Avoid contractions.
- Prose: clear, well-structured, complex yet understandable. Define specialized terms meticulously.

**2. Stylometry and Stylistic Directives (Auto-Injected Defaults)**:

- **Hedge Density**: Moderate 5-10 %.
- **Lexical Diversity**: TTR >= 0.40; no word > 2 % tokens; avoid clichés.
- **Sentence Variability**: Avg 17-22 words; >= 15 % sentences < 8 words and >= 15 % > 30 words; sigma >= 8. Use varied sentence openings/types, balancing complexity with clarity for a book-length work.
- **Rhetorical Devices**: Include >= 1 rhetorical question AND >= 1 first-person or direct-address aside, applied with scholarly subtlety (e.g., in introductions, conclusions, or framing arguments).
- **Paragraph Pacing**: Mix short (2-3 sentence) and longer (4-6+ sentence) paragraphs with smooth, logical transitions, appropriate for academic treatise.

**3. Structural Formatting and Punctuation**:

- Organize into Parts/Chapters (per R.3). Use H1 (Treatise title), H2 (Part titles), H3 (Chapter titles), H4/H5 (sub-sections).
- Generate: Comprehensive Table of Contents (listing Parts, Chapters, key H3/H4), List of Tables, List of Figures.
- Abstract/Executive Summary (per R.3.1) precedes Part I.
- Comprehensive Bibliography (Chicago Manual of Style) at end. Appendices follow. Footnotes mandatory for citations/substantive asides.
- Use bullet points/lists sparingly (narrative prose first).
- Punctuation: Use commas for asides, colons for expansion, semicolons for linked clauses. **Ban em-dashes altogether.**
- Ensure all Markdown is valid, convertible to professional print/PDF.

---

# E - Evaluation

Before finalizing this Treatise, perform these exhaustive self-checks with the utmost rigor. Document any deviations, uncertainties, or areas where assumptions were made, and revise to meet all criteria:

**1. Comprehensive Coverage and Analytical Depth (vs. R and A)**:
    ***All Sections Addressed**: Does the Treatise fully and exhaustively cover all specified Parts and Chapters (Core Content Requirements R.3) with the appropriate depth and detail for a 30,000-40,000-word scholarly work?
    * **Framework Application**: Is the Comparative Policy Analysis framework (and other mentioned theoretical underpinnings) explicitly stated and consistently applied? Are principles from OECD/PESTLE integrated effectively?
    ***Augmentations Met**: Is the work heavily grounded in diverse, high-quality academic and official sources? Are Chicago citations (footnotes and bibliography) flawless? Is recent data/literature (via `web.search_query`) thoroughly integrated? Are at least 10-15 substantive comparative tables/charts/diagrams effectively included and discussed? Is the `[Scholarly Synthesis]` tag used judiciously and appropriately? Are all guardrails for objectivity and critical analysis met?
    * **Length Adherence**: Does the document substantially meet the Tier 9 word count target?

**2. Accuracy, Grounding and Evidence (Anti-Hallucination/Bias)**:
    ***Data and Factual Integrity**: Is all statistical data, policy information, historical context, and discussion of energy technologies/systems meticulously accurate and correctly attributed? Are there *any* factual errors, misinterpretations of sources, or unsupported/hallucinated claims?
    * **Methodological Soundness**: Is the comparative methodology robust, transparent, and consistently applied? Are analytical claims well-defended by evidence?
    * **Objectivity and Balanced Argumentation**: Is the treatise entirely free from national bias or advocacy for a particular viewpoint beyond what is supported by evidence? Are complexities, counterarguments, and differing scholarly interpretations fairly presented and engaged with?

**3. Clarity, Scholarly Tone and Formatting (vs. T and C.Goal)**:
    ***Intellectual Accessibility and Precision**: Despite its academic nature and length, is the treatise written with exceptional clarity, precision, and logical coherence, making complex arguments understandable to an expert international audience? Are all specialized terms rigorously defined?
    * **Tone Consistency**: Does the response consistently maintain the "Formal / Scholarly" and "Authoritative Expert" tone? Is sentence-length variability managed effectively to maintain engagement over a long text?
    * **Structural and Formatting Excellence**: Is the treatise impeccably structured (TOC, Parts, Chapters, H1-H5 headings, Lists of Tables/Figures, comprehensive Bibliography, Appendices)? Are Chicago style footnotes and bibliography perfectly formatted? Is Markdown flawless?

**4. Overall Goal Achievement and Scholarly Contribution (vs. C.Goal)**:
    *Does the Treatise provide a profound, definitive, and insightful comparative analysis of renewable energy strategies in Germany and Japan?
    * Does it generate significant, nuanced, and actionable lessons for global energy policy and academic discourse?
    * Does it fulfill the expectation of an exhaustive, publication-quality, book-length academic work?

*After these checks, provide a detailed summary of your confidence in meeting each major category (e.g., High for all, with specific attention to data triangulation if applicable) and explicitly detail any significant assumptions made (e.g., about the scope of accessible data via search), limitations of the analysis, or areas where human expert peer review would be essential before considering the work complete.*

# Length Check

| Tier | Name and Synonyms                    | Words                   | Core Use-Case                       |
|------|------------------------------------|-------------------------|-------------------------------------|
| 8    | Monograph (comprehensive report)   | 10000 - 25000 words     | Strategy bluebooks, agency playbooks|
| **9**| **Treatise / Compendium (exhaustive)**| **25000 - 50000 words** | **Regulatory impact studies, book-length work** |
| 10   | Max-Window Synthese                | 50000 - 75000 + words   | API-driven archival dumps, corpuses|

**Suggested tier**: **9** | **OK?** (yes / choose another)
**Other changes?** (add / delete / tweak any C-R-E-A-T-E block before we finalise)

```
