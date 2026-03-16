# Changelog

## [0.4.1] - TBD

### 🚀 Added

* **Optimization & Token Leak Analyzer:** Upgraded the `TelemetryTracker` to not only count tokens and calculate costs but to actively analyze the AI crew's execution trajectory for inefficiencies.

* **Agent-Level Diagnostics:** The framework now uses LangChain `role:` tags to track exactly which agent is consuming tokens. At the end of a run, it generates a diagnostic report flagging "Context Bloat" (exponentially growing prompts), "Thrashing" (agents stuck in failure loops), and "High Waste Ratios" (sending massive context for tiny outputs).

### ⚙️ Changed

* **Configuration-Driven Agent Factory:** Migrated the crew instantiation logic out of the Python codebase and into a centralized `config/crew.yaml` file. The `build_crew` factory now utilizes Python module reflection (`getattr`) to dynamically instantiate agent classes based on the YAML blueprint.

* **Explicit Agent Tagging:** Refactored `BaseAgent.from_config` initialization to explicitly accept a `node_name` parameter. This string is injected as a LangChain tag (`node:{node_name}`) during LLM creation, ensuring telemetry and cost tracking remain perfectly stable even if underlying class names are refactored.

## [0.4.0] - 2026-03-15

### 🚀 Added

* **Streamlit Web Dashboard (`app.py`):** Introduced a fully interactive graphical user interface. Users can now start new projects via file upload, view the granular execution timeline in a sortable data table, and use a visual form to inject time-travel feedback.

* **Time Travel & State Injection (Human-in-the-Loop):** Added `--feedback` and `--as-node` arguments to the CLI. The framework can now intercept graph execution, inject human feedback directly into the SQLite state, and force LangGraph to route backward (e.g. impersonating the `reviewer` to send tasks back to the `developer`).

* **True Time Travel (`--checkpoint`):** Upgraded the state injection feature to support true timeline rewinding. Users can now pass a specific checkpoint ID to fork the graph from a past state, preventing race conditions where the graph had already moved on to the next task before feedback was injected.

* **Granular Timeline History (`--history`):** Added a CLI flag to print a formatted, chronological timeline of the crew's execution.

## [0.3.0] - 2026-03-14

### 🚀 Added

* **Universal Runtime Support:** The `DockerSandbox` is no longer hardcoded to Python. It now supports a registry of languages (Python, Node.js, etc.) via a centralized `config/sandbox.yaml` file.

* **Architect-Driven Tech Stacks:** The `SystemArchitect` agent now explicitly defines the project's `runtime` in its output schema, which dictates the Docker container and test commands used by the QA Engineer.

* **Builder Pattern for Agents:** Introduced `.with_sandbox()` to the `QAEngineer` class, allowing cleaner, fluent dependency injection in the `build_crew` factory without polluting the `BaseAgent` class.

### ⚙️ Changed

* **Detached Docker Execution:** Upgraded `DockerSandbox.run_tests()` to run containers in `detach=True` mode with a `.wait()` block. This guarantees 100% capture of `stdout/stderr` logs, even if the container crashes instantly on import.

* **Language-Agnostic QA Prompts:** Completely rewrote the `qa-engineer-sandbox.md` prompt. Removed Python-specific jargon (`pytest`, `Traceback`) in favor of universal testing concepts (Compilation Errors, Stack Traces, Test Frameworks) to support multi-language CI/CD.

* **Strict Prompt Hierarchies:** Restructured the QA Engineer's diagnostic instructions into a strict, numbered hierarchy (Rules 1-4) to prevent smaller local models (like 7B) from eagerly pattern-matching the wrong errors.

* **Developer Test Enforcement:** Updated the `senior-developer.md` prompt to strictly enforce TDD (requiring at least two files per task) and wrapping CLI logic in `__main__` guards to prevent execution during test collection.

### 🐛 Fixed

* **Async Checkpointer Crashes:** Fixed `asyncio.exceptions.InvalidStateError` and `AttributeError` by replacing synchronous LangGraph calls (`get_state`, `update_state`) with their proper async counterparts (`aget_state`, `aupdate_state`) in the `VirtualCrew.execute` loop.

* **Python Pathing Errors:** Injected `PYTHONPATH=/workspace` into the Docker environment variables to resolve `ModuleNotFoundError` issues when `pytest` attempts to import files from the `src/` directory.

* **Network Isolation Blocking Tests:** Disabled `network_disabled=True` in the Docker Sandbox to allow the container to correctly fetch testing frameworks (like `pytest`) during the test run.

* **Agent Hallucinations on "0 Items Collected":** Fixed an edge case where test runners throwing collection errors (like broken imports) were misidentified by the LLM as "missing test files".

## [0.2.0] - 2026-03-13

### 🚀 Added

* **Intelligent Model Routing (`LLMFactory`):** Added semantic routing to dynamically assign the most cost-effective and capable models based on task category (`reasoning`, `code-generator`, `code-analyzer`, `fast-utility`) and chosen provider (`groq`, `ollama`, `openai`).

* **Command Line Interface (CLI):** Built the `devteam` CLI tool to kick off projects directly from a `project.txt` file, complete with `--provider` and `--rpm` (Rate Limiter) arguments.

* **Strict Test-Driven Development (TDD):** Enforced an architecture where the System Architect embeds testing criteria into every JSON task, and the Developer writes unit tests alongside the implementation code.

* **Rate Limiting & Telemetry:** Added a `RateLimiter` to safely manage API quotas and a `TelemetryTracker` to calculate token usage and latency.

### ⚙️ Changed

* **Centralized Prompt Configuration:** Abstracted all agent personas, system instructions, and constraints out of Python strings and into clean Markdown files with YAML frontmatter (`config/agents/**`).

* **Structured Outputs:** Overhauled graph state management to strictly use Pydantic and LangChain's structured output parsers, entirely eliminating "Markdown spillage" and broken JSON payloads.

* **Async Execution:** Migrated the `VirtualCrew.execute` workflow and SQLite checkpointer to fully asynchronous operations for better performance.

## [0.1.0] - 2026-03-09

### 🚀 Added

* **Multi-Agent Architecture:** Introduced the core autonomous AI agency powered by LangGraph. Specialized agents include `ProductManager`, `SystemArchitect`, `SeniorDeveloper`, `CodeReviewer`, `QAEngineer`, `FinalQAEngineer`, and `Reporter`.

* **Extensions System:** Implemented pluggable lifecycle hooks, including `WorkspaceSaver` (for writing generated code to disk) and `HumanInTheLoop` (for pausing the graph and requiring manual user approval).
