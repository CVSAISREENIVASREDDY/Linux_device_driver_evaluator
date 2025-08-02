# File Functionality

* **`get_responses.py`**: 
    * Takes a prompt as input.
    * Calls the `GeminiModel` to generate code.
    
* **`score.py`**: This is the main script that orchestrates the entire evaluation process. It contains the `total_evaluator` class, which:
    * Invokes the various evaluators (compilation, security, code quality) on the generated code.
    * Aggregates and returns the final evaluation results.

* **`llm/model.py`**: This file handles the interaction with the generative AI models. The `GeminiModel` class is responsible for:
    * Configuring the `genai` library with an API key.
    * Generating C code for a given prompt using different Gemini models.
    * Handling errors during code generation.

* **`evaluators/compilation.py`**: This module is responsible for compiling the generated C code as a Linux kernel module. The `KernelModuleCompiler` class:
    * Creates a temporary directory with a Makefile to build the driver.
    * Executes the `make` command to compile the code.
    * Parses the compiler output to count errors and warnings, and determines the success of the compilation.

* **`evaluators/clang_analyzer.py`**: This module evaluates the quality of the generated code. It contains two main classes:
    * **`EnhancedClangAnalyzer`**: Uses `clang-tidy` to perform a detailed static analysis of the code, checking for issues related to style, maintainability, performance, and security.
    * **`HybridCodeQualityAnalyzer`**: Combines the results from `clang-tidy` with custom regex-based analysis to provide scores for style compliance, documentation, and maintainability.

* **`evaluators/runtime_analyzer.py`**: This module evaluates the runtime metrics of the generated code. It contains the class:
    * **`RuntimeProfiler`**: It takes raw .c driver code, compiles it with a generated Makefile, inserts the module into the kernel, collects runtime logs (dmesg), gathers key metrics (memory usage, insert time, CPU stats), and removes the module — all in one flow.
    
* **`evaluators/security.py`**: This module scans the code for security vulnerabilities. The `KernelVulnerabilityScanner` class:
    * Contains a set of predefined patterns for common kernel vulnerabilities, such as unchecked user copies, null pointer dereferences, and format string bugs.
    * Analyzes the code against these patterns to identify potential security issues.
    * Calculates security scores for memory safety, concurrency, and API misuse.

* **`evaluators/prompt_complexity.py`**: This simple module contains a function to calculate a complexity score for the input prompt based on the presence of technical terms, specific requirements, and constraints.