# [](#04-framework-librarymd)04 Framework-Library.md

**Version:** Framework-Library Document v1.0, May 29, 2025
**Source Document:** AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework - v 1. (May 2025)
**ApproxTokens:** approximately 140 k
**Purpose:** This document details a key part of the 'A' (Augmentations) component of the
C.R.E.A.T.E. framework: invoking established analytical frameworks and methodologies. It provides
a comprehensive library of such frameworks, explaining their output patterns, primary use cases,
and example trigger snippets to enhance AI prompts by guiding the LLM to follow specific,
structured processes.

## [](#table-of-contents)Table of Contents

1. [Introduction to Invoking Frameworks and Methodologies in Prompts (The "A" in C.R.E.A.T.E.)](#introduction-to-invoking-frameworks-and-methodologies-in-prompts-the-a-in-create)
   1. [ANCHOR-FL-1](#anchor-fl-1)
2. [1. Why Invoking Frameworks Matters](#1-why-invoking-frameworks-matters)
   1. [ANCHOR-FL-2](#anchor-fl-2)
3. [2. How to Invoke a Framework](#2-how-to-invoke-a-framework)
   1. [ANCHOR-FL-3](#anchor-fl-3)
4. [3. Library of Analytical Framework Keywords (Cross-Domain)](#3-library-of-analytical-framework-keywords-cross-domain)
   1. [3.1. General Analysis Frameworks](#31-general-analysis-frameworks)
   2. [3.2. Legal Frameworks](#32-legal-frameworks)
   3. [3.3. Fiscal Frameworks](#33-fiscal-frameworks)
   4. [3.4. Policy and Program Frameworks](#34-policy-and-program-frameworks)
   5. [3.5. IT and Security Frameworks](#35-it-and-security-frameworks)
   6. [3.6. Tax and Accounting Frameworks](#36-tax-and-accounting-frameworks)
   7. [3.7. Comparative / Global Frameworks](#37-comparative--global-frameworks)

## [](#introduction-to-invoking-frameworks-and-methodologies-in-prompts-the-a-in-create)Introduction to Invoking Frameworks and Methodologies in Prompts (The "A" in C.R.E.A.T.E.)

With Context (C) established, the Request (R) defined, and Examples (E) potentially provided,
Augmentations (A) are where you add layers of sophistication, control, and rigor to your prompt.
Invoking specific analytical frameworks is a primary way to augment your request. These frameworks
transform a simple instruction into a precise, high-fidelity directive, ensuring the LLM performs
the task *how* you need it done.

***

### [](#anchor-fl-1)ANCHOR-FL-1

## [](#1-why-invoking-frameworks-matters)1. Why Invoking Frameworks Matters

Often, you don't just need an answer; you need an answer derived through a specific, structured,
and repeatable process. The AI Prompt Engineering Guide provides a rich catalog of keywords that
act as switches, invoking well-defined analytical frameworks across multiple domains. Using these
keywords ensures the LLM follows a recognized methodology, making the output more rigorous,
defensible, and comparable to other analyses.

***

### [](#anchor-fl-2)ANCHOR-FL-2

## [](#2-how-to-invoke-a-framework)2. How to Invoke a Framework

When providing your input to PromptCraft Pro, you can ensure a specific analytical framework is
used in the C.R.E.A.T.E. prompt that PromptCraft Pro ultimately generates for the downstream LLM.
Here's how to guide this process:

* **Explicitly Request a Framework:** The most direct way is to clearly state in your input to
  PromptCraft Pro which framework from the library (detailed in Section 3 below) you want the
  downstream LLM to apply.
  * *Example user input to PromptCraft Pro:* "I need an analysis of our current market position.
    Please use a SWOT Analysis."
  * The "Trigger Snippet" column in the library tables (Section 3) provides examples of how you
    might phrase such requests.

* **Implicitly Suggest a Framework:** You can also describe your analytical need or the desired
  output structure in a way that strongly implies a particular framework. PromptCraft Pro is
  instructed to recognize such implications.
  * *Instruct the downstream LLM:*
    `"If structured analysis implied, consider/state framework (e.g., SWOT/IRAC per knowledge files)."`

PromptCraft Pro will then incorporate the appropriate framework instruction (either the one you
specified or one it infers as suitable) into the **'A - Augmentations'** block of the C.R.E.A.T.E.
prompt it builds. This ensures the downstream LLM is guided to use that specific methodology.

**Important Considerations When Requesting Frameworks:**

* **Placement by PromptCraft Pro:** Framework instructions are typically placed by PromptCraft Pro
  in the 'A - Augmentations' block, often before stylistic or length cues in the generated
  C.R.E.A.T.E. prompt, to ensure the chosen framework guides the entire response generation process.
* **Interaction with Rigor Level and Advanced Techniques:** Be aware that requesting a particularly
  complex analytical framework, or a task that inherently requires deep, multi-step structured
  reasoning, may influence how PromptCraft Pro configures the overall C.R.E.A.T.E. prompt.
  Specifically, it might:
  * Suggest or default to a higher **Rigor Level** for the prompt it generates (Rigor Levels are
    defined in `ANCHOR-QR-10` of `00 Quick-Reference.md`).
  * Select and incorporate complementary **Advanced Evaluation and Reasoning Techniques** (from the
    library in `ANCHOR-QR-11` of `00 Quick-Reference.md`) to ensure the framework is applied
    robustly by the downstream LLM and that its output is thoroughly evaluated.
  * For instance, a request for a highly structured "Dynamic Scoring per CBO" analysis would likely
    lead PromptCraft Pro to generate a C.R.E.A.T.E. prompt that not only specifies this framework
    but also instructs the downstream LLM to use a higher rigor of self-evaluation.

***

### [](#anchor-fl-3)ANCHOR-FL-3

## [](#3-library-of-analytical-framework-keywords-cross-domain)3. Library of Analytical Framework Keywords (Cross-Domain)

The following table details various analytical frameworks, their typical output patterns, when to
use them, and example trigger snippets for your prompts.

### [](#31-general-analysis-frameworks)3.1. General Analysis Frameworks

| Keyword / Framework             | Output Pattern                                          | When to Use (2-4 sentences)                                  | Trigger Snippet                                       |
|---------------------------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------|
| Root Cause Analysis (5 Whys)    | Iterative "Why?" chain mapping symptom -> cause layers   | Diagnosing process failures or setbacks: repeatedly ask "Why did X occur?" to peel back causal layers to the root cause. | "Apply Root Cause Analysis (5 Whys) to \[problem]."    |
| SWOT Analysis                   | Four quadrants: Strengths, Weaknesses, Opportunities, Threats | Early-stage scoping of initiatives; surfaces internal/external factors to inform strategy and risk-mitigation. | "Conduct a SWOT Analysis of \[project/topic]."         |
| Porter's Five Forces            | Five headings: Competitive Rivalry, Supplier Power, Buyer Power, Entry, Substitutes | Evaluating industry attractiveness or positioning; clarifies where power lies and strategic advantage opportunities. | "Analyze using Porter's Five Forces for \[industry]."  |
| DMAIC (Six Sigma)               | Define -> Measure -> Analyze -> Improve -> Control phases | Quality-improvement projects; guides data-driven problem solving within Six Sigma to reduce defects and variation. | "Apply DMAIC to \[process/problem]."                   |
| Fishbone (Ishikawa) Diagram     | Diagram with main "spine" and cause categories          | Brainstorming to visually map all potential causes of a problem; promotes comprehensive exploration. | "Use Fishbone Diagram for \[issue/cause]."             |

### [](#32-legal-frameworks)3.2. Legal Frameworks

| Keyword / Framework             | Output Pattern                                          | When to Use (2-4 sentences)                                  | Trigger Snippet                                       |
|---------------------------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------|
| IRAC / CREAC / CRRACC           | Issue -> Rule -> (Context) -> Application -> Conclusion (opt. Counter-rules) | Legal memos/statutory interpretations; enforces clear rule articulation and transparent application to facts. | "Apply IRAC (or CREAC/CRRACC) for \[case/statute]."    |
| Stare-Decisis Matrix            | Table: cases, holdings, jurisdictions, facts, alignment/distinction | Comparing conflicting opinions or circuit splits; supports litigation strategy. | "Prepare a Stare-Decisis Matrix for \[legal issue]."   |
| Chevron Two-Step / Major-Questions | Step 1: ambiguity check; Step 2: deference/major-questions | Assessing agency rule defenses, especially post- *Loper Bright*; must flag major-questions doctrine. | "Analyze under Chevron Two-Step (flag Major-Questions) for \[rule]." |
| Scrutiny Ladder                 | Strict, Intermediate, Rational-Basis tests              | Legislation impacting fundamental rights/suspect classes; clarifies government's burden and challenge viability. | "Apply Scrutiny Ladder to \[statute/policy]."          |
| Textualism vs. Purposivism      | Dual-column: plain-text vs. legislative intent          | Anticipate divergent interpretive approaches; helps draft or clarify statutory language. | "Contrast Textualism vs. Purposivism for \[statute]."  |

### [](#33-fiscal-frameworks)3.3. Fiscal Frameworks

| Keyword / Framework             | Output Pattern                                          | When to Use (2-4 sentences)                                  | Trigger Snippet                                       |
|---------------------------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------|
| Cost-Benefit Analysis (CBA)     | NPV and B/C ratio tables + sensitivity analysis           | Quantifying program or infrastructure impacts; aligns with OMB A-4 or state equivalents. | "Conduct a Cost-Benefit Analysis (CBA) for \[project]." |
| Dynamic Scoring per CBO         | Ten-year revenue/expenditure with multipliers           | Tax/incentive bills with macroeconomic feedback; cite CBO methodology. | "Apply Dynamic Scoring per CBO to \[legislation]."    |
| PAYGO / CUTGO Test              | Offset ledger: new spend vs. offsets                    | Ensures compliance with pay-as-you-go rules; flags amendments breaching caps. | "Run PAYGO compliance test on \[amendment]."           |
| GAO 12-Step Cost Estimate       | Lifecycle cost worksheet per GAO-20-195G                | Capital or IT projects requiring defensible estimates; passes audit scrutiny. | "Prepare a GAO 12-Step Cost Estimate for \[project]."  |
| Fiscal Multiplier Analysis      | Multiplier table: short- vs. long-run by spending type  | Evaluates GDP impact of stimulus or grants; guides allocation to maximize growth. | "Provide a Fiscal Multiplier Analysis for \[initiative]." |

### [](#34-policy-and-program-frameworks)3.4. Policy and Program Frameworks

| Keyword / Framework             | Output Pattern                                          | When to Use (2-4 sentences)                                  | Trigger Snippet                                       |
|---------------------------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------|
| Regulatory Impact Analysis (RIA)| Need -> Baseline -> Alternatives -> Benefits/Costs -> Net Benefit | Mandatory for significant rules; enforces transparent trade-off analysis per OMB A-4. | "Prepare a Regulatory Impact Analysis for \[rule]."    |
| PESTLE / PESTEL                 | Headings: Political, Economic, Social, Technological, Legal, Environmental | Broad policy scoping; uncovers external drivers for program/policy success. | "Conduct a PESTLE analysis for \[policy/project]."     |
| MCDA / AHP                      | Weighted-criteria matrix + ranking chart                | Comparing policy options; makes weighting transparent for stakeholders. | "Use MCDA/AHP for option prioritization in \[decision]." |
| Logic Model / Theory of Change  | Inputs -> Activities -> Outputs -> Outcomes -> Impact   | Grant proposals or evaluation frameworks; aligns teams on causal pathways and metrics. | "Develop a Logic Model for \[program]."                |
| Equity Impact Statement         | Disaggregated impact table + mitigation narrative       | Civil-rights compliance (Title VI, Justice40); highlights disparate effects. | "Add an Equity Impact Statement to \[policy]."         |
| Risk Assessment (Qual/Quant)    | LikelihoodxImpact grid; optional Monte-Carlo histogram  | Cybersecurity, supply-chain, or environmental risks; supports contingency planning. | "Perform a Risk Assessment for \[risk domain]."        |

### [](#35-it-and-security-frameworks)3.5. IT and Security Frameworks

| Keyword / Framework             | Output Pattern                                          | When to Use (2-4 sentences)                                  | Trigger Snippet                                       |
|---------------------------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------|
| STRIDE Threat Model             | Spoofing, Tampering, Repudiation, Info Disclosure, Denial, Elevation | Early design reviews to identify and map threats to controls. | "Build a STRIDE Threat Model for \[system/app]."       |
| MITRE ATTandCK Mapping            | Tactic -> Technique -> Mitigation matrix                  | Red/blue-team exercises and SIEM rule alignment. | "Map findings to MITRE ATTandCK framework for \[incident]." |
| CIS Benchmarks Gap Analysis     | Control-by-control compliance scorecard                 | System-hardening or audit preps; highlights missing safeguards. | "Conduct a CIS Benchmarks Gap Analysis for \[platform]." |
| NIST SP 800-53 Control Gap      | Control-ID checklist: Implemented/Partial/None          | FedRAMP and agency IRM readiness; ensures policy alignment. | "Perform a NIST SP 800-53 Gap Analysis for \[system]." |
| OSI Troubleshooting Ladder      | Seven-layer stepwise diagnostic list                    | NOC runbooks or incident bridges to systematically isolate network faults. | "Create an OSI Troubleshooting Ladder for \[issue]."   |
| Google Code-Review Checklist    | Bulleted review points: readability, tests, design, security | Peer-reviewing code diffs; enforces consistent, actionable feedback. | "Use Google Code-Review Checklist on \[PR/code]."      |
| Cisco Enterprise Design Hierarchy | ASCII diagram + Core/Dist/Access layers               | Architecting enterprise LAN/WAN; aligns with Cisco best practices. | "Design network using Cisco Enterprise Hierarchy for \[network]." |

### [](#36-tax-and-accounting-frameworks)3.6. Tax and Accounting Frameworks

| Keyword / Framework             | Output Pattern                                          | When to Use (2-4 sentences)                                  | Trigger Snippet                                       |
|---------------------------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------|
| IRC Pathway Map                 | Hierarchical: Code Section -> Reg -> Ruling -> Cases -> PLRs | Research memos; ensures statutory authority is traced top-down per Circular 230. | "Apply IRC Pathway Map for \[tax position]."           |
| ASC 740 ETR Bridge              | Table: GAAP Income -> Permanent/Temp Adjustments -> Taxable Income -> ETR % | GAAP tax-provision memos; clarifies drivers of effective tax-rate variations. | "Draft an ASC 740 analysis for \[tax provision]."      |
| Schedule M-1/M-3 Recon          | Book-to-tax differences with citations                  | Corporate returns; supports audit documentation and IRS compliance. | "Prepare a Schedule M-1/M-3 Reconciliation for \[entity]." |
| SALT Nexus Matrix               | States vs. filing factors grid (sales, payroll, property) | Multi-state compliance planning; visualizes where nexus triggers exist. | "Develop a SALT Nexus Matrix for \[company]."          |
| Entity-Choice Decision Tree     | Flowchart comparing C Corp, S Corp, P'ship, DRE         | Startup structuring; compares tax treatment, liability, and exit strategies. | "Apply Entity-Choice Decision Tree to \[entity planning]." |
| Basis-Tracking Schedule         | Table: initial basis -> contributions -> allocations -> distributions | Partnership/S Corp planning; ensures correct loss/distribution limits. | "Generate a Basis-Tracking Schedule for \[partner/shareholder]." |
| Six-Step Tax Position Evaluation| Stepwise: Code > Reg > Ruling > PLR > Guidance          | For tax-opinion letters; structures analysis to meet "substantial authority" standards. | "Perform Six-Step Tax Position Evaluation for \[tax item]." |
| Golson Circuit Rule             | Notes binding/persuasive precedent by circuit; flags splits | Multi-state Tax Court strategy; determines venue-specific precedential weight. | "Apply Golson Circuit Rule for \[tax case]."           |

### [](#37-comparative--global-frameworks)3.7. Comparative / Global Frameworks

| Keyword / Framework             | Output Pattern                                          | When to Use (2-4 sentences)                                  | Trigger Snippet                                       |
|---------------------------------|---------------------------------------------------------|--------------------------------------------------------------|-------------------------------------------------------|
| OECD Better-Regulation Toolkit  | KPI table vs. OECD median + traffic-light icons         | Policy alignment with international best practices; regulatory modernization. | "Benchmark with OECD Better-Regulation Toolkit for \[policy]." |
| UN SDG Alignment                | SDG icons + narrative linking policy to goal targets    | Sustainability or grant-funding proposals; shows alignment with global-development goals. | "Map project to UN SDGs for \[initiative]."            |
