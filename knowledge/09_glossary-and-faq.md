# 09 Glossary-and-FAQ.md

**Version:** Glossary-FAQ-References Document v1.0, May 29, 2025
**Source Document:** AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework - v 1. (May 2025)
**ApproxTokens:** approximately 60k
**Purpose:** This document provides a glossary of relevant terms from the C.R.E.A.T.E. Framework, a
troubleshooting FAQ for common prompting issues, and the reference reading list (Appendix E from the source
document) for further exploration.

## Table of Contents

- [1. Glossary of Terms](#1-glossary-of-terms)
- [2. Troubleshooting FAQ](#2-troubleshooting-faq)
  - [2.1. Common Issues When Using Examples in Prompts](#21-common-issues-when-using-examples-in-prompts)
  - [2.2. Common Output Failures and Recommended Fixes](#22-common-output-failures-and-recommended-fixes)
  - [2.3. API-Based Prompting: Troubleshooting](#23-api-based-prompting-troubleshooting)
- [3. Reference Reading List (from Appendix E of the Source Document)](#3-reference-reading-list-from-appendix-e-of-the-source-document)
  - [3.1. Foundational Concepts and Surveys](#31-foundational-concepts-and-surveys)
  - [3.2. Core Prompt Engineering Guides](#32-core-prompt-engineering-guides)
  - [3.3. Advanced Prompting Techniques](#33-advanced-prompting-techniques)
  - [3.4. AI Ethics and Responsible Use [Ethics]](#34-ai-ethics-and-responsible-use-ethics)
  - [3.5. Security and Safety [Security]](#35-security-and-safety-security)
  - [3.6. Tooling, Frameworks and MLOps [Tools]](#36-tooling-frameworks-and-mlops-tools)
  - [3.7. Platform-Specific Documentation [Docs]](#37-platform-specific-documentation-docs)
  - [3.8. Style and Citation Guidance [Style]](#38-style-and-citation-guidance-style)
  - [3.9. Internal Resources (Placeholders from Source Document)](#39-internal-resources-placeholders-from-source-document)

---

<!-- ANCHOR-GF-1 -->

## 1. Glossary of Terms

This glossary provides definitions for key terms used within the C.R.E.A.T.E. Framework and related AI prompt engineering concepts.

| Term                      | Definition                                                                                                                             |
|---------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| API                       | Application Programming Interface; a programmatic way to send prompts to and receive
responses from an LLM or other service.       |
| Augmentation              | Any external data, tools, or modules (e.g., retrieval systems, calculators) integrated into a prompt to bolster the model’s output.    |
| Bias                      | Systematic skew or unfairness in outputs stemming from imbalances or prejudices in the model’s training data.                          |
| C.R.E.A.T.E. Framework   | Structured prompt-design approach: Context, Request, Examples, Augmentations, Tone and Format, Evaluation.                             |
| Chain-of-Thought        | Technique that asks the model to “think aloud,” providing step-by-step reasoning before delivering a final answer.                     |
| Context (C)               | Background information or role assignment that frames the model’s perspective and scope.                                               |
| Context Window            | Maximum number of tokens an LLM can process at once; determines how much prompt and history it “remembers.”                            |
| Cutoff Date               | The point in time after which an LLM has no factual knowledge, reflecting its last training update.                                    |
| Endpoint                  | Specific URL or network address where an API call is directed to invoke a particular model or service.                                 |
| Evaluation (E)            | Criteria and methods used to assess the accuracy, relevance, and quality of the model’s outputs.                                       |
| Examples (E)              | Sample input-output pairs included in a prompt to guide the model toward the desired format or reasoning pattern.                      |
| Few-Shot Learning         | Providing a small number of examples in the prompt to help the model infer the desired task or style.                                  |
| Fine-Tuning               | Additional training of a pre-trained model on a specific dataset to improve performance on niche tasks.                                |
| Hallucination             | When an LLM generates plausible but incorrect or fabricated details due to lack of grounding.                                          |
| Inference                 | The process of generating a response from a trained model given an input prompt.                                                       |
| Large Language Model (LLM)| AI model trained on vast text corpora to learn linguistic patterns, enabling it to generate or interpret natural language.             |
| Prompt                    | The text or instructions you provide to an LLM to elicit a desired response.                                                           |
| Prompt Injection          | Unintended or malicious insertion of content into a prompt that alters the model’s behavior or output.                                 |
| Prompt Template           | Pre-formatted structure or skeleton for prompts, used to maintain consistency and reuse across tasks.                                  |
| Request (R)               | The specific task description or deliverable you ask the model to produce.                                                             |
| Temperature               | Sampling parameter controlling randomness in generation; lower values yield more deterministic outputs, higher values more varied.     |
| Token                     | Basic unit of text (wordpiece or character) that an LLM processes; prompts and outputs are measured in tokens.                         |
| Top-K Sampling            | Sampling method that restricts the model’s choices to the top k most probable tokens at each step. t                                   |
| Top-P (Nucleus Sampling)  | Sampling strategy selecting from the smallest set of tokens whose cumulative probability exceeds p, balancing diversity and coherence. |
| Tone and Format (T)         | Instructions specifying the style, voice, structure, and formatting guidelines for the model’s output.                               |
| Zero-Shot Learning        | Task execution by the model without any examples, relying solely on clear instructions.                                                |

---

<!-- ANCHOR-GF-2 -->

## 2. Troubleshooting FAQ

### 2.1. Common Issues When Using Examples in Prompts

This advice is drawn from Section 3.5 of the AI Prompt Engineering Guide.

- **Q: My LLM seems to be introducing biases based on the examples I provided. What can I do?**
    A: Your examples might inadvertently introduce bias. Review your examples for any
    subtle (or overt) biases and try to provide a more balanced or neutral set if the task requires it.
- **Q: The LLM is just copying the structure of my examples but not understanding the underlying task. How can I fix this?**
    A: This is known as overfitting to the examples. Try to vary the structure and content
    of your examples while still demonstrating the core principle. Ensure your examples aren't too narrow
    or overly simplistic representations of the desired output. You might also need to strengthen other
    parts of your prompt (like the Request or Context) to provide better overall guidance.
- **Q: My prompt is getting too long because of the examples, and it might be hitting token limits. What's the solution?**
    A: Examples use up tokens, which can be a concern [Context Cost]. Be concise in your
    examples. Often, 1-3 well-chosen examples are sufficient. If the task is very complex and
    requires many examples, consider if the task can be broken down or if a fine-tuned model is more appropriate.
- **Q: I get different results when I change the order of examples in my prompt. Is this normal?**
    A: Some models can be sensitive to the order in which examples are presented [Order Sensitivity].
    If you observe this, experiment with the order to see if a particular sequence yields better, more consistent results.

### 2.2. Common Output Failures and Recommended Fixes

This table is a summary from Section 7.3 of the AI Prompt Engineering Guide.

| Failure Mode             | Cause                                      | Fix / Guardrail                                           |
|--------------------------|--------------------------------------------|-----------------------------------------------------------|
| Citation Drift           | Evidence directive buried/omitted          | Name guide and authorities before length/style caps       |
| Authority Weight Missing | No ranking of sources                      | Add explicit ranking order: “Statute > Regulation > Case” |
| Hallucinated Facts       | No source constraint                       | Specify primary authorities and recency filters           |
| Output Truncation        | Exceeds token limit                        | Instruct continuation markers: ===CONTINUE===             |
| Ambiguous Tone           | Conflicting style descriptors              | Use Tone Hierarchy: Maintain formal; allow warm...        |
| Logic Leaps              | No reasoning prompt                        | Add CoT/ToT/AoT directive: Think step-by-step...          |
| Format Errors            | Missing structural commands                | Specify formatting: Use H2/H3 headings...                 |

### 2.3. API-Based Prompting: Troubleshooting

This advice is from Appendix A.4 of the AI Prompt Engineering Guide.

| Problem                 | Likely Cause                            | Recommended Fix                      |
|-------------------------|-----------------------------------------|--------------------------------------|
| Output too random       | Temp/top-k too high                     | Lower temp/top-k/top-p               |
| Output repeats endlessly| Few stop sequences, high temp/top-p     | Add stop sequences, lower temp/top-p |
| Output too short        | Max tokens too low                      | Raise max tokens setting             |
| Output always same      | Temp too low                            | Raise temp/top-p                     |

**General Best Practices for API Troubleshooting:** Test with diverse examples. Track prompt effectiveness.
Document versions and settings used for API calls.

---

<!-- ANCHOR-GF-3 -->

## 3. Reference Reading List (from Appendix E of the Source Document)

This curated list provides resources for deepening your understanding of AI, LLMs, and prompt
engineering. Foundational papers are marked with an asterisk (*). Each entry includes a brief annotation.

### 3.1. Foundational Concepts and Surveys

This section covers the core ideas behind modern LLMs and broad overviews of the prompt engineering
field.

- - Vaswani, A., et al. "Attention Is All You Need." Advances in Neural Information Processing Systems 30,
    2017. <https://arxiv.org/abs/1706.03762>.
    [The groundbreaking paper introducing the Transformer architecture, the basis for most modern LLMs.]
- - Devlin, J., et al. "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding."
    arXiv:1810.04805, 2018. <https://arxiv.org/abs/1810.04805>.
    [Introduced BERT, a key milestone in using transformers for understanding language context, with resources
    available on Hugging Face.]
- Zhang, J., et al. "PEGASUS: Pre-training with Extracted Gap-sentences for Abstractive Summarization."
    arXiv:1912.08777, 2020. <https://arxiv.org/abs/1912.08777>.
    [Details the Pegasus model, influential for text summarization tasks and available via Hugging Face.]
- Sahoo, P., et al. “A Systematic Survey of Prompt Engineering in Large Language Models: Techniques and Applications.” arXiv preprint arXiv:2402.07927, 2024. <https://arxiv.org/abs/2402.07927>.
    [A comprehensive academic overview of current PE techniques and their uses.]
- Sun, Z., et al. “Prompt Engineering for Large Language Models: A Survey.” arXiv preprint arXiv:2402.08215, 2024. <https://arxiv.org/abs/2402.08215>.
    [Another excellent, broad survey covering the landscape of prompt engineering research.]
- Google. “Introducing Gemini: Our Largest and Most Capable AI Model.” Google AI Blog, Dec 6, 2023. <https://blog.google/technology/ai/google-gemini-ai/>.
    [An overview of Google's flagship multimodal model family.]
- Anthropic. “Introducing 100K Context Windows in Claude.” Anthropic News, May 11, 2023. <https://www.anthropic.com/news/100k-context-windows>.
    [Explains the significance of large context windows for processing extensive documents.]

### 3.2. Core Prompt Engineering Guides

These are essential starting points for learning the practical aspects of prompt engineering.

- - DAIR.AI. “Prompt Engineering Guide.” Living document, 2023-2025. <https://dair.ai/projects/prompt-engineering/>.
    [A well-regarded, community-driven guide covering a wide range of topics and techniques.]
- - Ng, Andrew, and Isa Fulford. “ChatGPT Prompt Engineering for Developers.” DeepLearning.AI Short Course, 2024. <https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/>.
    [A popular, practical, code-focused course for developers, excellent for hands-on learning.]
- Hewing, M., and Leinhos, V. “The Prompt Canvas: A LiteratureBased Practitioner Guide for Creating Effective Prompts in Large Language Models.” arXiv:2412.05127, 2024. <https://arxiv.org/abs/2412.05127>.
    [A structured approach, based on literature, for practitioners to build prompts.]
- Google. “Introduction to Prompt Design.” Google for Developers. <https://developers.google.com/machine-learning/resources/prompt-eng>.
    [Google's official introduction covering fundamentals and best practices for their models.]
- Anthropic. “Prompt Engineering Overview for Claude.” Anthropic Documentation, 2025. <https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview>.
    [Anthropic's guide tailored for getting the best results from Claude models.]
- Microsoft. “Prompt Engineering Techniques - Azure AI.” Microsoft Learn, 2025. <https://learn.microsoft.com/azure/ai-services/openai/concepts/prompt-engineering>.
    [Microsoft's perspective, often focused on Azure and OpenAI services.]
- Brex. “Prompt Engineering Guide.” GitHub, 2023. <https://github.com/brexhq/prompt-engineering>.
    [An open-source guide providing a range of practical examples and techniques.]
- Vanderbilt University. “Prompt Patterns Quick Reference.” 2024. <https://www.vanderbilt.edu/generative-ai/prompt-patterns/>.
    [A useful quick-reference identifying common, reusable prompt structures.]

### 3.3. Advanced Prompting Techniques

Explore techniques for complex reasoning, retrieval augmentation, and more sophisticated
interactions.

- - Wei, J., et al. “ChainofThought Prompting Elicits Reasoning in Large Language Models.” Advances in Neural Information Processing Systems 35, 2022. <https://arxiv.org/abs/2201.11903>.
    [The foundational paper demonstrating how to make LLMs "show their work" to improve reasoning.]
- - Lewis, P., et al. "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks." Advances in Neural Information Processing Systems 33, 2020. <https://arxiv.org/abs/2005.11401>.
    [The key paper introducing RAG, a technique for grounding LLMs with external, up-to-date information.]
- Yao, S., et al. “Tree of Thoughts: Deliberate Problem Solving with Large Language Models.” arXiv:2305.10601, 2023. <https://arxiv.org/abs/2305.10601>.
    [Explores prompting models to explore multiple reasoning paths for complex problems.]
- Microsoft Research. “Algorithm of Thoughts.” 2023. <https://www.microsoft.com/en-us/research/publication/algorithm-of-thoughts/>.
    [Explores advancing beyond CoT by allowing LLMs to follow more complex, algorithmic thought processes.]
- Gao, Y., et al. "Retrieval-Augmented Generation for Large Language Models: A Survey." arXiv:2312.10997, 2023. <https://arxiv.org/abs/2312.10997>.
    [A recent survey covering the state-of-the-art in RAG techniques.]
- Perplexity Labs. "How Perplexity AI is Building the Future of Search." Perplexity Blog. <https://blog.perplexity.ai/>.
    [Insights into a leading RAG-based search engine, showcasing practical RAG applications.]
- OpenAI Cookbook. “RecencyAware RAG Patterns.” May 2025. <https://cookbook.openai.com/examples/parse_pdf_docs_for_rag>.
    [Practical examples from OpenAI on implementing RAG, focusing on handling recent data.]

### 3.4. AI Ethics and Responsible Use [Ethics]

Understand the ethical implications and frameworks for using AI responsibly.

- - NIST. “AI Risk Management Framework (AI RMF 1.0).” NIST, January 2023. <https://www.nist.gov/itl/ai-risk-management-framework>.
    [A widely adopted framework for understanding and managing the risks associated with AI systems.]
- - State of Oregon. 'AI Recommended Action Plan.' Oregon.gov, February 11, 2025. <https://www.oregon.gov/eis/Documents/SG%20AI%20Final%20Recommended%20Action%20Plan%2020250211.pdf>.
    [The official strategic plan guiding AI adoption and governance for the State of Oregon.]
- Weidinger, L., et al. "Taxonomy of Risks posed by Language Models." arXiv:2112.04359, 2021. <https://arxiv.org/abs/2112.04359>.
    [A foundational paper categorizing the potential risks associated with LLMs.]
- Bender, E. M., et al. "On the Dangers of Stochastic Parrots: Can Language Models Be Too Big? [Bird]" Proceedings of FAccT '21, 2021. <https://dl.acm.org/doi/10.1145/3442188.3445922>.
    [A critical perspective on the environmental and social costs and risks of large models.]
- OECD. "OECD AI Principles." OECD.AI Policy Observatory. <https://oecd.ai/en/ai-principles>.
    [International, intergovernmental principles for responsible stewardship of trustworthy AI.]
- The Partnership on AI (PAI). PAI Website. <https://partnershiponai.org/>.
    [A multi-stakeholder organization developing best practices and conducting research on responsible AI.]
- Add Your Firm's Policy: [Placeholder: Link to Your Firm's Internal AI Use and Ethics Policy].
    [Your organization's specific rules and guidelines for using AI.]

### 3.5. Security and Safety [Security]

Focus on securing LLM applications and ensuring safe operation, including defenses against prompt
injection.

- - OWASP. “OWASP Top 10 for Large Language Model Applications.” OWASP Foundation, 2023/Ongoing. <https://owasp.org/www-project-top-10-for-large-language-model-applications/>.
    [The critical list of the most significant security risks for LLM applications, including prompt injection.]
- Perez, F., and Ribeiro, I. "Ignore This Title and Hack Away: Adversarial Prompt Engineering." DEF CON 31, 2023. <https://simonwillison.net/2023/Aug/27/adversarial-prompt-engineering/>.
    [A practical look at adversarial techniques, highlighting vulnerabilities.]
- Greshake, K., et al. "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection." arXiv:2302.12173, 2023. <https://arxiv.org/abs/2302.12173>.
    [Focuses on indirect prompt injection, a significant threat vector.]
- NIST. “AI 6001 Draft: Guidelines for Safe Prompt Engineering.” NIST, 2025 (Draft). <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>.
    [Specific draft guidance from NIST on secure and safe prompting practices.]
- UK AI Safety Institute. “Prompt Safety Patterns.” UK Government, April 2025. <https://www.gov.uk/government/publications/ai-safety-institute-overview/introducing-the-ai-safety-institute>.
    [An overview of patterns for enhancing the safety of AI prompts.]
- Rossi, S., et al. “Prompt Injection Attacks: Taxonomy and Defenses.” IEEE Symposium on Security and Privacy 2024. <https://arxiv.org/abs/2402.00898>.
    [An academic look at the types of prompt injection attacks and potential defenses.]

### 3.6. Tooling, Frameworks and MLOps [Tools]

Resources for building, managing, and deploying LLM applications and prompts.

- - LangChain Documentation. “Prompt Templates.” LangChain, v0.2. <https://python.langchain.com/docs/concepts/prompt_templates/>.
    [Documentation for a popular framework used to build LLM-powered applications, including prompt management.]
- - GitHub. GitHub Website. <https://github.com/>.
    [Essential platform for version control, collaboration, and CI/CD for prompts, as detailed in Appendix D of the source document.]
- Zhu, Y., et al. “PromptBench: A Benchmark Suite for Prompt Robustness.” arXiv:2312.07910, 2023. <https://arxiv.org/abs/2312.07910>.
    [A benchmark suite for evaluating how robust prompts are to variations and attacks.]
- OpenAI. “Agent with OpenAI SDK.” OpenAI Agents SDK. <https://openai.github.io/openai-agents-python/>.
    [The official SDK from OpenAI for building agentic workflows.]
- CrewAI Documentation. CrewAI. <https://docs.crewai.com/>.
    [A framework focused on orchestrating multi-agent collaboration for complex tasks.]
- Microsoft AutoGen. Microsoft. <https://microsoft.github.io/autogen/>.
    [A framework enabling the development of LLM applications using multiple agents.]
- Hugging Face. Hugging Face Website. <https://huggingface.co/>.
    [A central hub for accessing models (like BERT and Pegasus), datasets, and tools for NLP and AI.]
- LMQL. “Language Model Query Language.” 2025. <https://lmql.ai/>.
    [A programming language specifically designed for interacting with LLMs.]

### 3.7. Platform-Specific Documentation [Docs]

Direct links to the API and key documentation for major LLM providers.

- - OpenAI. “API Reference.” OpenAI Platform. <https://platform.openai.com/docs/api-reference>.
    [Official API documentation for OpenAI models like GPT-4.]
- - OpenAI. "Assistants API." OpenAI Platform. <https://platform.openai.com/docs/assistants/overview>.
    [Documentation for building agent-like experiences with OpenAI models.]
- Google. “Gemini API.” Google Cloud / Vertex AI. <https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini>.
    [Official API documentation for Google's Gemini family of models.]
- Anthropic. “Claude API.” Anthropic Docs. <https://docs.anthropic.com/claude/reference>.
    [Official API documentation for Anthropic's Claude models.]
- Hugging Face. “Transformers Documentation.” Hugging Face. <https://huggingface.co/docs/transformers/index>.
    [Documentation for the widely used Transformers library, essential for working with models like BERT and Pegasus.]
- OpenAI Cookbook. GitHub. <https://github.com/openai/openai-cookbook>.
    [A rich collection of examples and guides for using the OpenAI API effectively.]

### 3.8. Style and Citation Guidance [Style]

Resources for formatting outputs and citing AI-generated content appropriately.

- - The Chicago Manual of Style Online. Chicago Manual of Style. <https://www.chicagomanualofstyle.org/home.html>.
    [The definitive guide for many academic and professional writing styles; check their latest AI citation guidance.]
- APA Style Blog. "How to cite ChatGPT." APA Style. <https://apastyle.apa.org/blog/how-to-cite-chatgpt>.
    [Official guidance from the American Psychological Association.]
- MLA Style Center. "How do I cite generative AI in MLA style?" MLA Style Center. <https://style.mla.org/citing-generative-ai/>.
    [Official guidance from the Modern Language Association.]
- Marist Library. “How to Cite ChatGPT in Chicago Style.” FAQ, 2025. <https://libanswers.marist.edu/faq/415540>.
    [Practical guidance on applying Chicago style to AI-generated content.]
- LexisNexis Practical Guidance. “Lawyers and ChatGPT: Best Practices.” LexisNexis, July 19, 2024. <https://www.lexisnexis.com/pdf/practical-guidance/ai/lawyers-and-chatgpt-best-practices.pdf>.
    [Offers specific advice on using AI tools responsibly within the legal profession.]
- Purdue OWL. "Using and Citing AI Tools." Purdue Online Writing Lab. <https://owl.purdue.edu/owl/research_and_citation/using_citing_ai_tools.html>.
    [A trusted academic resource providing guidance on AI citation.]

### 3.9. Internal Resources (Placeholders from Source Document)

Links to your firm's specific policies, tools, and support channels.

- [Placeholder: Link to Your Firm's Internal AI Use and Ethics Policy]
    [Your organization's specific rules and guidelines for using AI.]
- [Placeholder: Link to Your Firm's Internal Prompt Library / GitHub Repo]
    [Access pre-approved templates and contribute your own.]
- [Placeholder: Link to Your Firm's AI Governance and Compliance Page]
    [Find policies, contact information for the review board, and approved platforms.]
- [Placeholder: Link to Your Firm's AI Support Channel / Contact List]
    [Get help, ask questions, and connect with internal AI experts.]
