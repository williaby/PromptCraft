---
title: Context-Blocks
version: 2.1
status: published
agent_id: create_agent
tags: ['context', 'prompting', 'create_framework', 'ai_guidance']
source: "AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework v2.1 (June 2025)"
purpose: This document provides detailed explanations, guidance, and exemplars for establishing effective 'Context' (the 'C' in C.R.E.A.T.E.) in AI prompts.
approx_tokens: 120k
---

# [](#context-blocks)Context-Blocks
## [](#table-of-contents)Table of Contents

1. [Introduction to Context in Prompting](#introduction-to-context-in-prompting)
2. [ANCHOR-CB-1](#anchor-cb-1)
3. [1. Defining the Role and Persona Clause](#1-defining-the-role-and-persona-clause)
   1. [1.1. Why Defining a Role Matters](#11-why-defining-a-role-matters)
   2. [1.2. What to Include in a Role and Persona Clause](#12-what-to-include-in-a-role-and-persona-clause)
   3. [1.3. How to Write the Role and Persona Clause](#13-how-to-write-the-role-and-persona-clause)
   4. [1.4. Examples](#14-examples)
      1. [1.4.1. Legal](#141-legal)
      2. [1.4.2. Fiscal/Policy](#142-fiscalpolicy)
      3. [1.4.3. IT and Security](#143-it-and-security)
      4. [1.4.4. Tax and Accounting](#144-tax-and-accounting)
      5. [1.4.5. Example of What to Avoid](#145-example-of-what-to-avoid)
   5. [1.5. Specific Guidance and Best Practices](#15-specific-guidance-and-best-practices)
   6. [1.6. Short Persona Clause Library](#16-short-persona-clause-library)
4. [ANCHOR-CB-2](#anchor-cb-2)
5. [2. Providing Background Information](#2-providing-background-information)
   1. [2.1. Why Background Information Matters](#21-why-background-information-matters)
   2. [2.2. What to Include in Background Information](#22-what-to-include-in-background-information)
   3. [2.3. How to Provide Background Information](#23-how-to-provide-background-information)
   4. [2.4. Examples of Background Information](#24-examples-of-background-information)
      1. [2.4.1. For a Fiscal Multiplier Analysis](#241-for-a-fiscal-multiplier-analysis)
      2. [2.4.2. For an IT Compliance Checklist](#242-for-an-it-compliance-checklist)
      3. [2.4.3. For a Comparative Statutory Analysis](#243-for-a-comparative-statutory-analysis)
   5. [2.5. Specific Guidance and Best Practices for Background Information](#25-specific-guidance-and-best-practices-for-background-information)
6. [ANCHOR-CB-3](#anchor-cb-3)
7. [3. Stating the Goal / Intent](#3-stating-the-goal--intent)
   1. [3.1. Why Stating the Goal Matters](#31-why-stating-the-goal-matters)
   2. [3.2. What to Include When Stating the Goal](#32-what-to-include-when-stating-the-goal)
   3. [3.3. How to State the Goal](#33-how-to-state-the-goal)
   4. [3.4. Examples of Stating the Goal](#34-examples-of-stating-the-goal)
      1. [3.4.1. For a SWOT Analysis](#341-for-a-swot-analysis)
      2. [3.4.2. For a Plain-Language Policy Summary](#342-for-a-plain-language-policy-summary)
      3. [3.4.3. For a MITRE ATTACK Mapping](#343-for-a-mitre-attack-mapping)
      4. [3.4.4. For a Comparative Statutory Analysis (Goal)](#344-for-a-comparative-statutory-analysis-goal)
   5. [3.5. Specific Guidance and Best Practices for Stating the Goal](#35-specific-guidance-and-best-practices-for-stating-the-goal)

## [](#introduction-to-context-in-prompting)Introduction to Context in Prompting

**Purpose:** To provide the LLM with the necessary background, identity, and purpose to understand
the "why" and "who" behind your request. This foundation is crucial because it primes the model,
ensuring it approaches the task from the correct perspective and activates the most relevant
knowledge and stylistic patterns learned during its training. A well-defined context is the first
step towards a precise and useful output.

***

## [](#anchor-cb-1)ANCHOR-CB-1

## [](#1-defining-the-role-and-persona-clause)1. Defining the Role and Persona Clause

### [](#11-why-defining-a-role-matters)1.1. Why Defining a Role Matters

Assigning a specific role or persona to the Large Language Model (LLM) is one of the most
potent techniques for steering its output. It's more than just a label; it's a fundamental
instruction that shapes the entire response. When you tell an LLM to "Act as an authoritative
tax practitioner", you're not just asking for a *topic*; you're asking for a specific
*perspective*, *vocabulary*, *level of detail*, and *reasoning style*.

Think of the LLM's vast knowledge as a multi-dimensional map or 'vector space' - like a vast
library where words and ideas are grouped by meaning. Certain words and phrases-especially role
labels-act as powerful signposts, 'lighting up' specific regions of that map, telling the AI
which 'section' of its knowledge to focus on. This guides the model toward the linguistic and
structural patterns it has most strongly associated with that role during its training.

Research confirms that role labels and stylistic adjectives are dominant levers for output
quality. It's like using a mixing console: defining the role sets the primary levels for the
entire track, influencing everything that follows.
By integrating a concise humanizing **persona clause** (detailing origin, setting, or a
specific quirk) directly into the primary "You are a..." role statement, we create a more
unified and relatable identity for the LLM. This helps the model activate relevant linguistic
patterns and world knowledge associated with that specific human experience, leading to
responses that feel more authentic, carry a more distinct voice, and are less like a generic AI.
This integrated approach avoids the potential disconnect of separate persona tags and makes the
humanizing element a core part of the AI's adopted identity for the task.

### [](#12-what-to-include-in-a-role-and-persona-clause)1.2. What to Include in a Role and Persona Clause

When defining the persona for the LLM, you are essentially providing its identity for the task.
To make this as effective as possible, consider including these elements. Ticking these boxes
helps you move from a general instruction to a precise, potent role definition:

* **Role Core**(3-5 tokens): seniority and profession.
* **Persona Clause** (<= 12 words): One brief humanizing detail covering:
  * *Origin/Background:* (e.g., "from the Mississippi Delta," "with roots in classic literature")
  * *Setting/Locale:* (e.g., "working in a bustling public library," "navigating the tech scene
    in Austin")
  * *Specialty/Quirk/Known For:* (e.g., "specializing in debunking myths," "known for a dry
    sense of humor," "who always finds the simplest explanation")

While the core role sentence focuses on the "Role Core" and "Persona Clause," you might also
consider the following for the broader context (though not typically part of the role sentence
itself):

* **Optional Audience for the output**: Who the persona is ultimately addressing (this can
  influence implied tone within the role even if not stated in the role sentence).
* **Optional Immediate Situation/Scenario for the persona**: Any specific context shaping the
  persona's immediate viewpoint (e.g., "troubleshooting a live outage," "presenting to
  skeptical investors").

### [](#13-how-to-write-the-role-and-persona-clause)1.3. How to Write the Role and Persona Clause

* **Template:** *You are a <ROLE core>, <persona clause>.*\
  *Example*: "You are a veteran **street-food chef, running a family taco truck in East LA**."
* **Keep it brief**: avoid parentheses, brand IDs, or self-references such as *AI / LLM / chatbot*.
* **Place first** in the Context block to prime domain tokens early.

### [](#14-examples)1.4. Examples

#### [](#141-legal)1.4.1. Legal

* "Context: You are a senior counsel, specializing in Oregon tax litigation."

#### [](#142-fiscalpolicy)1.4.2. Fiscal/Policy

* "You are an experienced policy advisor, raised on rural infrastructure debates."

#### [](#143-it-and-security)1.4.3. IT and Security

* "You are a seasoned security engineer, hardening public-sector Kubernetes clusters."

#### [](#144-tax-and-accounting)1.4.4. Tax and Accounting

* "You are a veteran tax attorney, guiding crypto-asset clients in New York."

#### [](#145-example-of-what-to-avoid)1.4.5. Example of What to Avoid

* **Incorrect (uses parentheses, mentions AI):** "You are a helpful assistant (Persona:
  RecipeBot AI)."
  * *Better:* "You are a patient culinary guide, ready to explain any recipe step by step."
* **Incorrect (mentions LLM directly in role):** "You are an LLM, acting as a seasoned historian."
  * *Better:* "You are a seasoned historian, specializing in ancient civilizations."
* **Incorrect (persona clause too long):** "You are a junior software developer, who recently
  graduated and is eager to learn about new coding languages while also trying to contribute to
  open source projects and find a mentor."
  * *Better:* "You are a junior software developer, eager to contribute to open source projects."
* **Incorrect (uses Brand ID as persona):** "You are a financial advisor, representing
  GlobalInvest Corp."
  * *Better:* "You are a cautious financial advisor, helping families plan for their future."
* **Incorrect (conflicting internal details within the role sentence):** "Context: You are a
  cheerful and optimistic data analyst, who only delivers pessimistic and critical reports."
  * *Why it's weak:* This prompt gives internally contradictory humanizing details ("cheerful
    and aptimistic" vs. "pessimistic and critical reports") within the role description itself,
    confusing the AI. Aim for role definitions where the elements reinforce a coherent persona.

### [](#15-specific-guidance-and-best-practices)1.5. Specific Guidance and Best Practices

* 💡 **Specificity is Key:** While a general role helps, a *specific* role is often much better.
  Consider adding:
  * **Expertise Level:** Senior Counsel vs. Paralegal.
  * **Target Audience Implication via Persona Clause:** "You are an expert economist, patiently
    explaining inflation to high school students." (The persona clause "patiently explaining
    inflation to high school students" implies the audience focus and a related trait).
  * **Situational Context via Persona Clause:** "You are a network engineer, calmly
    troubleshooting a live data center outage."
* ⚠️ **Combining Details:** Stack only one persona clause; extra qualifiers weaken token signal.
  If style conflicts (e.g., formal + playful), use a Tone Hierarchy in the T-block.
* ✅ **Consistency:** Maintain the same role throughout a longer, multi-turn conversation unless
  you explicitly intend to change perspective.
* **Conciseness of Persona Clause:** Ensure the persona clause is a *brief* humanizing detail,
  adhering to the "<=12 words" guideline to maintain clarity and impact.
* **Adhere to Anti-patterns:** Strictly avoid:
  * Using parentheses for persona elements within the role sentence.
  * Including brand IDs directly in the role definition.
  * Self-references such as AI, LLM, or chatbot in the role sentence (unless the user
    explicitly requests transparency about the AI).

### [](#16-short-persona-clause-library)1.6. Short Persona Clause Library

* "running a family taco truck in East LA."
* "drawing on night-shift experience in New York ERs."
* "writing from a tiny coastal town battered by winter storms."
* "shaped by two decades of open-source kernel hacking."
* "with memories of litigating the Enron fallout."

***

## [](#anchor-cb-2)ANCHOR-CB-2

## [](#2-providing-background-information)2. Providing Background Information

### [](#21-why-background-information-matters)2.1. Why Background Information Matters

If the 'Role' tells the AI *who* it is, 'Background Information' tells it *what it needs to
know* about the specific world it's operating in for *this* request. LLMs don't have access to
your private documents, recent conversations, or the specific history of your project. They
operate solely on the information you provide in the prompt and their (potentially outdated)
training data.

Failing to provide adequate context forces the model to make assumptions, which can lead to:

* **Generic Outputs:** Responses that are too general to be useful.
* **Inaccuracies/Hallucinations:** The model might invent "facts" to fill in the gaps.
* **Misapplied Frameworks:** Complex analyses like CBA or SWOT are meaningless without the
  factual grounding of a specific situation.
* **Irrelevant Results:** The output might be technically correct but miss the point of your
  specific need.

Providing clear, relevant background information is essential for grounding the response in
reality and ensuring the AI's power is directed precisely where you need it.

### [](#22-what-to-include-in-background-information)2.2. What to Include in Background Information

* \[v] **The Core Subject:** What specific bill, rule, project, system, or problem is this about?
  (e.g., \[BILL ID], \[Problem], \[Initiative]).
* \[v] **The Primary Goal:** What is the ultimate objective or desired outcome of this task?
* \[v] **Target Audience:** Who is this output for? (e.g., C-Suite, clients, technical peers,
  non-technical readers).
* \[v] **Key Stakeholders/Entities:** Who or what are the important players or components?
* \[v] **Relevant History/Timeline:** What key events or dates led up to this?
* \[v] **Scope and Boundaries:** What *is* and *is not* in scope for this request?
* \[v] **Known Constraints/Data:** Are there specific budget limits, existing regulations, known
  technical limitations, or data points that *must* be considered?
* \[v] **Definitions:** If using potentially ambiguous terms, define them upfront.

### [](#23-how-to-provide-background-information)2.3. How to Provide Background Information

* **Be Concise but Complete:** Provide enough detail for understanding but avoid unnecessary
  "fluff" that might confuse the model.
* **Structure for Clarity:** Use paragraphs, bullet points, or even key-value pairs to make the
  context easy to parse.
* **Use Delimiters:** Clearly separate background information from other prompt elements using
  markers like `### Background ###`, `---`, or XML-style tags (`<context>...</context>`). This
  helps the model identify its "source material."

### [](#24-examples-of-background-information)2.4. Examples of Background Information

#### [](#241-for-a-fiscal-multiplier-analysis)2.4.1. For a Fiscal Multiplier Analysis

```markdown
## # Background ###
Our state is considering a new infrastructure spending package totalling $5 billion over 3
years, funded by a bond measure.
The primary goal is to stimulate job growth and long-term GDP.
The target audience for this analysis is the legislative budget committee.
We need a Fiscal Multiplier Analysis, focusing on short-run (1-2 years) and long-run (5-10
years) impacts, considering CBO methodologies for different spending types (highway
construction vs. green energy grants).
```

#### [](#242-for-an-it-compliance-checklist)2.4.2. For an IT Compliance Checklist

```markdown
## # Background ###
Our company (a healthcare provider) is preparing for a FedRAMP audit for our new telehealth
platform.
The platform is hosted on AWS GovCloud and uses managed services (S3, EC2, RDS).
We need to perform a gap analysis against NIST SP 800-53 Rev. 5 controls, specifically focusing
on the AC (Access Control) and AU (Audit and Accountability) families.
The goal is to identify missing or partially implemented controls and prioritize remediation
efforts.
```

#### [](#243-for-a-comparative-statutory-analysis)2.4.3. For a Comparative Statutory Analysis

```markdown
## # Background ###
We need to understand the differences in paid family leave legislation between Oregon (ORS
Chapter 657B) and Washington (RCW Title 50A).
The objective is to advise a client operating in both states on compliance requirements.
Focus specifically on eligibility criteria, benefit amounts/duration, funding mechanisms, and
employer notice requirements. We need a side-by-side comparison format.
```

### [](#25-specific-guidance-and-best-practices-for-background-information)2.5. Specific Guidance and Best Practices for Background Information

* 💡 **Front-Load Context:** Provide the most critical background information early in the
  prompt, ideally right after defining the role.
* ⚠️ **Verify Understanding:** For complex contexts, consider adding a step asking the model to
  briefly summarize its understanding of the background before proceeding.
* ✅ **Be Factual:** Stick to objective facts in the background section. Save opinions or
  desired outcomes for later parts of the prompt unless they are part of the 'Goal'.

***

## [](#anchor-cb-3)ANCHOR-CB-3

## [](#3-stating-the-goal--intent)3. Stating the Goal / Intent

### [](#31-why-stating-the-goal-matters)3.1. Why Stating the Goal Matters

You've told the AI who it should be (Role) and what it needs to know (Background). The final,
crucial piece of Context is telling it *why* you are making the request - the Goal or Intent.
What is the ultimate purpose of this output? Will it be used to inform a decision, persuade a
stakeholder, educate an audience, generate options, diagnose a problem, or ensure compliance?

Knowing the *purpose* helps the LLM move beyond simply completing a task to understanding the
*impact* you want to achieve. This allows it to:

* **Prioritize Information:** Emphasize details that are most relevant to achieving your objective.
* **Select Appropriate Strategies:** Choose between informative, persuasive, analytical, or
  exploratory approaches.
* **Tailor Language:** Adjust the complexity and tone to match the intended use case.
* **Improve Relevance:** Ensure the final output is truly "fit-for-purpose" and directly
  addresses the underlying need.

Without a clear goal, the AI might produce a technically correct answer that completely misses
the mark in terms of strategic value or intended impact.

### [](#32-what-to-include-when-stating-the-goal)3.2. What to Include When Stating the Goal

* **The Primary Purpose:** What is the main action you want the output to enable? (e.g., *to
  decide*, *to brief*, *to implement*, *to troubleshoot*).
* **The Intended Use Case:** How will this output be consumed? (e.g., *as part of a board
  presentation*, *as a client-facing letter*, *as a technical runbook*, *as input for a larger
  report*).
* **The Desired Impact:** What change or understanding should the output ideally bring about?
  (e.g., *gain budget approval*, *clarify legal obligations*, *improve system security*).

### [](#33-how-to-state-the-goal)3.3. How to State the Goal

State the goal directly within the context section, using clear, action-oriented language, and
always focus on the outcome you desire.

### [](#34-examples-of-stating-the-goal)3.4. Examples of Stating the Goal

#### [](#341-for-a-swot-analysis)3.4.1. For a SWOT Analysis

```markdown
The goal of this SWOT analysis is to provide a clear, concise overview for the project steering
committee.
It will serve as the foundation for our Q3 strategic planning session, specifically helping us
decide whether to pivot our current marketing strategy or double down.
```

#### [](#342-for-a-plain-language-policy-summary)3.4.2. For a Plain-Language Policy Summary

```markdown
The intent is to create a public-facing fact sheet.
This document must be easily understood by non-technical citizens, aiming to increase awareness
and support for the new [Public Program] initiative.
```

#### [](#343-for-a-mitre-attack-mapping)3.4.3. For a MITRE ATTACK Mapping

```markdown
The primary goal here is to enhance our Security Operations Center's detection capabilities.
This mapping will be used to develop new SIEM correlation rules and inform our upcoming red
team exercise.
```

#### [](#344-for-a-comparative-statutory-analysis-goal)3.4.4. For a Comparative Statutory Analysis (Goal)

```
This analysis will be used by our legal team to advise a major corporate client operating in
multiple jurisdictions. The objective is to clearly highlight differences in compliance
obligations to minimize legal risk for the client.
```

### [](#35-specific-guidance-and-best-practices-for-stating-the-goal)3.5. Specific Guidance and Best Practices for Stating the Goal

* **Link Goal to Audience and Role:** Your Goal should naturally align with the Role you've set
  and the Audience you've identified in the Background. A C-Suite audience usually implies a
  goal related to strategic decision-making and conciseness, whereas a NOC guide implies a goal
  of rapid, accurate technical execution.
* **Distinguish Goal from Task:** The *Task* (covered in Section 2: Request of the main guide)
  is *what* the AI will physically create (e.g., "Draft a 5,000-word whitepaper"). The *Goal*
  is *why* it's creating it (e.g., "To establish our company as a thought leader in this space
  and generate inbound leads"). While related, clearly defining both provides richer direction.
* **Be Realistic:** Ensure your stated goal is achievable given the task and the capabilities
  of the LLM.
* **Impact on PromptCraft Pro Processing:** Clearly articulating a complex, high-stakes, or
  nuanced Goal can assist PromptCraft Pro in its internal processing. Specifically, such a Goal
  might lead PromptCraft Pro to:
  * Suggest or default to a higher **Rigor Level** (e.g., "Intermediate" or "Advanced" as
    defined in `ANCHOR-QR-10` of `00 Quick-Reference.md`) for the C.R.E.A.T.E. prompt it generates.
  * Infer the need for and incorporate specific **Progressive Evaluation Protocols** and
    **Advanced Technique Modes** (from `ANCHOR-QR-8` and `ANCHOR-QR-9` of `00 Quick-Reference.md`)
    into the generated prompt to better meet the sophisticated demands of the stated Goal.
  * Apply appropriate **Diagnostic Flag Systems** (from `ANCHOR-QR-6` of `00 Quick-Reference.md`)
    to ensure quality and accuracy validation aligned with the goal's complexity.
