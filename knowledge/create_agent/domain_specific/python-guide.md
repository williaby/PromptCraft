# [](#anchor-py-1)ANCHOR-PY-1

# [](#python-environment-and-dependencies)Python Environment and Dependencies

*PromptCraft Pro Default Injection: **Python 3.11 with Poetry***

This section defines the standard runtime environment for all Python projects. Prompts must instruct
the LLM to generate code and commands that are compatible with these specifications.

| Directive | Specification | PromptCraft Pro Injection |
| --- | --- | --- |
| **Python Version** | All code must be written for and compatible with **Python 3.11**. | When generating code or scripts, include: \<br>"The solution must be compatible with Python 3.11." |
| **Dependency Mgmt.** | All projects use **Poetry** for dependency management and packaging. | For tasks involving dependencies, instruct the LLM to use `poetry` commands \<br>(e.g., `poetry add`, `poetry install`). |
| **Virtual Environment** | Assume code will be run within a virtual environment managed by Poetry. | For setup instructions, include: \<br>"Ensure all commands are run within the project's Poetry shell." |

***

# [](#anchor-py-2)ANCHOR-PY-2

# [](#python-code-formatting-and-style)Python Code Formatting and Style

*PromptCraft Pro Default Injection: **PEP 8 via Black and Ruff with Type Hints***

This section outlines the strict formatting and style conventions for all Python code. Prompts must
enforce these standards to ensure consistency and readability.

| Directive | Specification | When to use |
| --- | --- | --- |
| **PEP 8 Compliance** | \[cite\_start]All Python code must strictly adhere to the **PEP 8** style guide\[cite: 86]. \<br>We use automated tools to enforce this. | **Always.** This is a non-negotiable standard for all generated Python code. |
| **Code Formatter**| The **Black** code formatter is used to enforce PEP 8 compliance and a consistent style. | For prompts generating complete files or scripts, instruct the LLM: \<br>"The final Python code should be formatted as if `black .` has been run on it." |
| **Linter** | We use **Ruff** for linting to catch errors and style issues beyond basic formatting. | For code review prompts, instruct the LLM: \<br>"Review this code as if you were the `ruff` linter, identifying potential errors and style violations." |
| **Type Hints** | \[cite\_start]All function and method signatures, and all variable declarations where type is not obvious, \<br>must include **type hints** per PEP 484\[cite: 86, 117]. | **Always.** Prompts should explicitly request type hints. \<br>*Example: "Generate a Python function `my_func(data: list[str]) -> int`..."* |
| **Line Length** | Maximum line length is **88 characters**, as enforced by Black. | **Always.** This is handled by the Black formatting directive. |

***

# [](#anchor-py-3)ANCHOR-PY-3

# [](#python-documentation-and-comments)Python Documentation and Comments

*PromptCraft Pro Default Injection: **Google Style Docstrings***

Clear and standardized documentation is critical for maintainability. Prompts should specify the type
and format of all docstrings and comments.

| Directive | Specification | When to use |
| --- | --- | --- |
| **Docstring Format** | \[cite\_start]All modules, classes, functions, and methods must have \<br>**Google Python Style** docstrings\[cite: 86]. | **Always** for any generated function, class, or module. \<br>*Example: "Generate a function... and include a complete Google-style docstring."* |
| **Docstring Content**| Docstrings must include: \<br> *A one-line summary. \<br>* `Args:` section for all arguments. \<br> *`Returns:` section for the return value. \<br>* `Raises:` section for any exceptions. | **Always.** This ensures that the generated documentation is comprehensive and useful. |
| **Inline Comments** | Use inline comments (`#`) to explain complex logic, business rules, or workarounds. \<br>Do not state the obvious. | For prompts generating complex algorithms or business logic, instruct the LLM: \<br>"Add inline comments to clarify any non-obvious parts of the logic." |

***

# [](#anchor-py-4)ANCHOR-PY-4

# [](#python-testing-and-validation)Python Testing and Validation

*PromptCraft Pro Default Injection: **Pytest for all Unit Tests***

All new functionality must be accompanied by tests to ensure correctness and prevent regressions.
Prompts should reflect a test-driven mindset.

| Directive | Specification | When to use |
| --- | --- | --- |
| **Testing Framework** | The **pytest** framework is the standard for all unit and integration tests. | For any prompt generating a new function or feature, a companion prompt should be generated for tests. \<br>*Example: "Now, generate pytest unit tests for the function you just created."* |
| **Test Coverage** | Tests should cover: \<br> *The "happy path" (expected inputs and outputs). \<br>* Edge cases (e.g., empty lists, zero values, `None` inputs). \<br> \* Expected failures and error conditions. | **Always** when generating tests. \[cite\_start]Prompts should explicitly ask for varied test cases\[cite: 87]. |
| **Running Tests** | The standard command to execute tests is `pytest`. | When providing instructions that include a testing step, use the command `pytest`. |

***

# [](#anchor-py-5)ANCHOR-PY-5

# [](#python-specific-prompt-directives)Python-Specific Prompt Directives

*PromptCraft Pro Default Injection: **Varies by Task***

These directives guide the LLM on specific output formats and security considerations, aligning with
the `analysis via python` and `outputs via python_user_visible` instructions.

| Directive | Specification | When to use |
| --- | --- | --- |
| **Analysis via `python`** | When a prompt requests analysis, the LLM should produce a runnable Python script \<br>that performs the analysis (e.g., using pandas, numpy). The script's output should present \<br>the final analysis results clearly. | For any prompt involving data analysis, summarization, or transformation. |
| **Output via `python_user_visible`**| Instructs the LLM that the Python script's output (e.g., via `print()`) \<br>is intended for a non-technical end-user. The output should be well-formatted, easy to understand, \<br>and devoid of debugging information. | When the primary deliverable of the script is its output for a human user, \<br>not a file or data structure. |
| **Secure Code Generation** | For any code that handles user input, file I/O, or network requests, \<br>prompts must explicitly request security considerations. | **Always** for code involving external data or interactions. \<br>\[cite\_start]*Example: "Generate a Flask endpoint... ensuring you sanitize all user inputs \<br>to prevent injection attacks."* \[cite: 88, 335] |
| **Conventional Commits** | For prompts generating commit messages, they must adhere to the \<br>**Conventional Commits** specification. | When using an agent to commit code to version control. \<br>*Example: "Generate a Conventional Commit message for a feature that adds user authentication."* |
