# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🚀 Added

* **CrewFactory:** Added a dedicated `CrewFactory` to centralize and standardize crew instantiation.
* **LLM Thinking Output:** New `--thinking` CLI flag streams raw LLM token output (including `<think>` reasoning) to stderr in real-time via a new `StreamHandler` callback. When enabled, all LLM instances are created with `streaming=True`.

## [0.5.0] - 2026-03-18

### 🚀 Added

* **GitCommitter Extension:** New `GitCommitter` extension that automatically initializes a local git repository inside the project's `workspace` subfolder and commits every developer update with a message of the form `Task {index} - revision {n}`.

### ⚙️ Changed

* **VirtualCrew Constructor:** `project_folder: Path` is now the first positional argument. `WorkspaceSaver` and `GitCommitter` are wired in as dedicated keyword parameters (`workspace_saver`, `git_committer`) with sensible defaults, so callers no longer need to pass them via the generic `extensions` list.

* **WorkspaceSaver Live Workspace:** In addition to writing versioned snapshots under `00_planning/`, `01_task/rev_N/`, etc., `WorkspaceSaver` now mirrors every developer-produced file to a flat `workspace` subfolder inside the project folder. This folder serves as the live working tree that `GitCommitter` tracks.

* **Phase-Driven Lifecycle State:** Introduced `current_phase` field (`planning`, `development`, `integration`, `complete`) in project state.

### 🐛 Fixed

* **Escaped Newline File Corruption:** Normalized malformed LLM file payloads containing literal `\\n` sequences before workspace merge, preventing invalid source files from being written and breaking test collection.

### 🔧 Internal

* **WorkspaceSaver Directory Routing by Phase:** Refactored target directory resolution to rely on `current_phase` instead of node-name heuristics, keeping planning/development/integration outputs aligned with the outer lifecycle graph.

* **Sanitization Helper Centralization:** Moved workspace content normalization into `utils.sanitizer` and reused it from schema validation for a single sanitization source of truth.

## [0.4.2] - 2026-03-17

### 🚀 Added

* **Live Execution Dashboard Enhancements:** The Streamlit UI now visualizes crew execution in real time with phase tracking, agent activity timeline, task progress, communication log, and generated workspace file previews.

* **Dedicated UI Launcher Command:** Added `devteam-ui` as a separate entry point to launch the Streamlit dashboard directly.

### ⚙️ Changed

* **Verbose Logging Cleanup:** Reduced runtime log noise by moving multiple internal messages from `INFO` to `DEBUG` (crew lifecycle checkpoints and telemetry accumulation/generation traces).

* **Resume Lifecycle Hook Flow:** Resume paths now consistently trigger extension resume hooks, enabling extensions to react to both plain resume and feedback-injection resume flows.

* **GUI Runtime Controls & Logging:** Added LLM timeout input to the UI (default `120s`) and applied the selected value to settings before run start. UI process logging now uses the same file logger pipeline as CLI.

### 🔧 Internal

* **Crew Config Loading Refactor:** Extracted crew YAML parsing into a dedicated helper (`load_crew_config`) to simplify the agent factory flow.

## [0.4.1] - 2026-03-16

### 🚀 Added

* **Bring Your Own Config (BYOC):** Added `--config` CLI flag allowing users to pass custom directories for agent prompts and LLM routing without forking the repository.

* **Customizable LLM Timeout:** Added `--timeout` CLI flag to globally control the maximum wait time for LLM responses, allowing users to easily adjust for slower local models (like Ollama) or incredibly fast cloud providers (like Groq).

* **Optimization & Token Leak Analyzer:** Upgraded the `TelemetryTracker` to not only count tokens and calculate costs but to actively analyze the AI crew's execution trajectory for inefficiencies.

* **Agent-Level Diagnostics:** The framework now uses LangChain `role:` tags to track exactly which agent is consuming tokens. At the end of a run, it generates a diagnostic report flagging "Context Bloat" (exponentially growing prompts), "Thrashing" (agents stuck in failure loops), and "High Waste Ratios" (sending massive context for tiny outputs).

### 🐛 Fixed

* **Optimization Diagnostics Bug:** Fixed an `unhashable type: 'list'` runtime error in the telemetry tracker by replacing a faulty set initialization with a proper set comprehension.

* **State Evaluation Crash:** Fixed a bug in the async stream loop of the `execute` method where it attempted to read `final_state` before the loop completed. Now safely evaluates `full_state` during active iteration.

### 🔧 Internal

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
