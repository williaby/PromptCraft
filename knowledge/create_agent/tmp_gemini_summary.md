# CREATE Framework Summary

The CREATE framework is a structured methodology for prompt engineering, designed to produce consistent, high-quality outputs from large language models. It is an acronym that stands for:

*   **C** - Character & Role: Define the persona, role, and responsibilities the AI should adopt. This sets the context for the interaction and influences the AI's behavior and tone.
*   **R** - Request & Task: Clearly and concisely state the specific request, task, or question. This should be an unambiguous instruction that the AI can follow.
*   **E** - Examples & Exemplars: Provide concrete examples of the desired output format and content. This is one of the most effective ways to guide the model to the correct output.
*   **A** - Adjustments & Ambiguity: Address potential ambiguities, specify constraints, and provide rules for handling edge cases. This helps to prevent the model from making incorrect assumptions.
*   **T** - Tone & Terminology: Specify the desired writing style, tone (e.g., formal, informal, academic), and any specific terminology or jargon to be used.
*   **E** - Evaluation & Evidence: Define the criteria for a successful output and, if applicable, the sources of evidence the model should use to support its response.

## Key Elements of a CREATE Prompt

A prompt structured using the CREATE framework will contain the following key elements:

*   **Role:** A clear definition of the AI's persona.
*   **Task:** A specific and unambiguous instruction.
*   **Context:** Relevant background information, constraints, and rules.
*   **Examples:** One or more examples of the desired output.
*   **Tone:** The desired writing style and voice.
*   **Format:** The desired structure and format of the output (e.g., JSON, Markdown, a specific XML schema).
*   **Evaluation Criteria:** The standards by which the output will be judged.

## Evaluation of the Current Process

After reviewing the code in `src/ui/journeys/journey1_smart_templates.py`, I have the following evaluation of the current process for Journey 1:

**Strengths:**

*   **Solid Foundation:** The code has a good structure, with clear separation of concerns for file processing, prompt enhancement, and UI components.
*   **CREATE Framework Aligned:** The code is explicitly designed around the CREATE framework, with functions and data structures that map to its components.
*   **HyDE Integration:** The use of a `HydeProcessor` to assess query specificity is a sophisticated feature that can significantly improve the quality of the generated prompts.

**Weaknesses:**

*   **Mock Implementation:** The core prompt generation logic in the `enhance_prompt` function relies on `_create_mock_enhanced_prompt` and `_create_mock_create_breakdown`. These functions use hardcoded heuristics and simple keyword matching to generate the CREATE prompt. This is the primary reason the system produces poor results, as it cannot handle the complexity and nuance of natural language prompts.
*   **No LLM-in-the-loop:** The mock implementation does not use a large language model to generate the enhanced prompt. It's a rule-based system that attempts to simulate an AI, which is fundamentally limited.
*   **Underutilized Assets:** The `_create_real_enhanced_prompt` function, which is designed to use the `CreateAgent` and the knowledge files in `/knowledge/create_agent/`, is not being used. This is a missed opportunity to leverage the full power of the system.

**Recommendations:**

To significantly improve the performance of Journey 1, I recommend the following:

1.  **Activate the `CreateAgent`:** Modify the `enhance_prompt` function to call the `_create_real_enhanced_prompt` function instead of the mock functions. This will engage the `CreateAgent` and use the knowledge files to generate a much more sophisticated and context-aware CREATE prompt.
2.  **Remove Hardcoded Logic:** Once the `CreateAgent` is active, the hardcoded logic in the mock functions can be deprecated and eventually removed. This will make the system more flexible and easier to maintain.
3.  **Iterate and Improve:** After activating the `CreateAgent`, the next step will be to evaluate the quality of the generated prompts and iterate on the knowledge base and the agent's logic to continuously improve its performance.

## Project Status and Next Steps

**Current Status:** The project is at a critical juncture. The foundational work for Journey 1 is in place, but the core logic is a placeholder that prevents it from achieving its primary objective. The current system is a proof-of-concept that demonstrates the user interface and the overall workflow, but it does not yet deliver the intelligent prompt enhancement that the CREATE framework promises.

**Key Recommendations for Next Steps:**

To bring Journey 1 into alignment with the CREATE framework and deliver a truly valuable user experience, I recommend the following actions:

1.  **Implement the `CreateAgent`:** This is the most critical next step. The `enhance_prompt` function in `src/ui/journeys/journey1_smart_templates.py` must be refactored to call `_create_real_enhanced_prompt`. This will activate the AI-powered prompt generation and immediately improve the quality of the output.

2.  **Develop a Testing and Evaluation Framework:** As you transition to an AI-driven approach, it is essential to have a robust testing and evaluation framework. This should include:
    *   **A suite of test prompts:** A diverse set of prompts, ranging from simple to complex, to test the agent's capabilities.
    *   **Golden outputs:** A set of ideal CREATE prompts for each test prompt, which can be used as a baseline for comparison.
    *   **Automated evaluation metrics:** Metrics to measure the quality of the generated prompts, such as semantic similarity to the golden outputs, completeness of the CREATE framework, and user satisfaction scores.

3.  **Refine the Knowledge Base:** The knowledge files in `/knowledge/create_agent/` are the foundation of the `CreateAgent`'s expertise. As you test the agent, you will identify areas where the knowledge base can be improved. This may involve:
    *   Adding more examples to the `03_examples-gallery.md` and `10_few-shot-gallery.md`.
    *   Expanding the `04_framework-library.md` with more sophisticated prompt engineering techniques.
    *   Updating the `12_validation-rules.md` to improve the quality of the generated prompts.

4.  **Iterate on the `CreateAgent` Logic:** The `CreateAgent` itself will likely require refinement as you test it. This may involve:
    *   Improving the agent's ability to understand user intent.
    *   Enhancing the agent's ability to select and apply the correct knowledge from the knowledge base.
    *   Optimizing the agent's performance to reduce latency and cost.

By following these steps, you can transform Journey 1 from a proof-of-concept into a powerful tool that delivers on the promise of the CREATE framework and provides a valuable service to your users.

## Optimizing the CREATE Framework

To optimize the CREATE framework for generating prompts that are robust against hallucination and bias, and that produce well-sourced, natural-sounding responses, I recommend evolving the framework itself. Here are the most beneficial changes to consider, broken down by each letter of the CREATE acronym:

### **C - Character & Role: From Persona to Grounded Expertise**

*   **Current:** Defines a persona for the AI.
*   **Proposed Change:** Introduce the concept of **Grounded Expertise**. Instead of just a persona, the prompt should define the AI's "knowledge domain" and explicitly state the sources it is allowed to draw from.

*   **Example:**
    *   **Before:** "You are a helpful assistant."
    *   **After:** "You are a financial analyst. Your knowledge is strictly limited to the provided quarterly reports and the attached SEC filings. You must not use any external knowledge or make assumptions beyond what is in these documents."

*   **Benefit:** This immediately constrains the model, reducing the likelihood of hallucination by forcing it to rely on a specific corpus of information.

### **R - Request & Task: From Instruction to Mandate**

*   **Current:** Clearly states the request.
*   **Proposed Change:** Add a **Mandates & Guardrails** section to the request. This section would contain explicit, non-negotiable rules for the AI's behavior.

*   **Example Mandates:**
    *   **Uncertainty Mandate:** "If you cannot answer a question with at least 95% confidence based on the provided sources, you must state: 'I cannot answer this question with certainty based on the provided information.'"
    *   **Sourcing Mandate:** "Every factual claim in your response must be followed by a direct citation in the format [Source, Page Number]."
    *   **No-AI-Persona Mandate:** "You must not refer to yourself as an AI, a language model, or any similar term. You must respond from the perspective of your defined role."

*   **Benefit:** These mandates act as a "code of conduct" for the AI, giving it clear rules to follow and reducing the chance of undesirable behavior.

### **E - Examples & Exemplars: Add Negative Examples**

*   **Current:** Provides examples of good outputs.
*   **Proposed Change:** Introduce **Negative Exemplars**. These are examples of what *not* to do, and they are incredibly effective at steering the model away from common pitfalls.

*   **Example:**
    *   **Positive Exemplar:** Shows a well-sourced, neutrally-toned response.
    *   **Negative Exemplar:**
        *   **Input:** "What is the company's outlook?"
        *   **Bad Output (shows what to avoid):** "As a large language model, I believe the company's outlook is very positive! They are doing great things." (This is biased, unsourced, and uses the AI persona).
        *   **Reasoning for Bad Output:** "This response is not acceptable because it is speculative, uses 'I believe', and refers to itself as a language model."

*   **Benefit:** Negative examples provide a clear contrast and help the model learn the boundaries of acceptable responses much more quickly.

### **A - Adjustments & Ambiguity: From Clarification to Bias Mitigation**

*   **Current:** Addresses potential ambiguities.
*   **Proposed Change:** Add a dedicated **Bias & Neutrality Check** section. This would prompt the model to self-correct for bias before generating its final response.

*   **Example:**
    *   **Bias Check Prompt:** "Before you respond, review your answer for the following:
        *   **Loaded Language:** Have you used any emotionally charged or biased language?
        *   **Alternative Viewpoints:** Have you considered and presented alternative viewpoints if they exist in the source material?
        *   **Assumptions:** Are you making any assumptions that are not explicitly supported by the provided sources?"

*   **Benefit:** This forces the model to perform a "self-reflection" step, which can significantly reduce the amount of subtle bias in its responses.

### **T - Tone & Terminology: From Style to Stylometry**

*   **Current:** Specifies the desired tone.
*   **Proposed Change:** Create a **Stylometry Guide** with a "lexicon" of approved and banned terms.

*   **Example:**
    *   **Approved Lexicon:** "analysis," "report," "data indicates," "according to the source."
    *   **Banned Lexicon:** "I think," "I feel," "in my opinion," "as a large language model," "delve," "tapestry," "unleash."

*   **Benefit:** This gives you fine-grained control over the AI's voice and helps to eliminate the "AI-speak" that makes responses sound unnatural.

### **E - Evaluation & Evidence: From Criteria to Verifiability**

*   **Current:** Defines success criteria.
*   **Proposed Change:** Mandate a **Verifiability Score**. The AI would be required to rate its own response on a scale of 1-5 for how easily a human could verify the information.

*   **Example:**
    *   **Verifiability Score:**
        *   **5:** Every fact is directly cited to a specific page and line number in the provided sources.
        *   **3:** Most facts are cited, but some are inferred from the text.
        *   **1:** The response is mostly speculative and cannot be easily verified.

*   **Benefit:** This gamifies the process of sourcing and encourages the model to produce responses that are not only accurate but also easy to validate.

By incorporating these changes, you can evolve the CREATE framework from a prompt-structuring tool into a comprehensive system for generating high-quality, reliable, and natural-sounding AI responses.