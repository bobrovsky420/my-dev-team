# My Dev Team 🚀

An autonomous, LangGraph-powered AI development agency. **My Dev Team** takes raw project requirements and processes them through a multi-agent workflow (Product Manager, System Architect, Developers, and QA) to incrementally build, test, and deliver production-ready code.

## Features

* **Multi-Agent Architecture:** Specialized AI agents handle distinct phases of the software development lifecycle.
* **Semantic Model Routing:** Automatically routes tasks to the most cost-effective or capable LLMs based on the task type (reasoning, coding, or fast-utility).
* **Strict Test-Driven Development (TDD):** Testing is never an afterthought. Tasks are generated with embedded testing criteria, and the Developer writes unit tests alongside implementation code for immediate QA validation.
* **State Recovery & Resiliency:** Powered by asynchronous SQLite checkpointing. If an API rate limit is hit or a workflow is interrupted, you can resume the exact thread without losing a single token of progress.
* **Telemetry & Cost Tracking:** Automatically tallies prompt and completion tokens across the entire workflow. Calculates exact USD costs dynamically using LiteLLM's live pricing registry, printing a detailed receipt at the end of every run.
* **Incremental Development:** The System Architect breaks down requirements into a manageable backlog of strictly formatted JSON tasks.
* **Self-Healing Code:** The Developer, Reviewer, and QA Engineer agents continuously loop until unit tests pass and code meets specifications.
* **Structured Outputs:** Powered by Pydantic and LangChain, ensuring zero "Markdown spillage" and robust state management.
* **Extensible:** Easily add custom tools like `HumanInTheLoop` or `WorkspaceSaver`.
* **Cost & Token Optimization Analyzer:** Built-in telemetry tracks API costs down to the fraction of a cent and generates a diagnostic report at the end of every run, actively warning you if agents are stuck in loops or suffering from context bloat.

### Centralized Configuration

Code and configuration are strictly separated to make the framework maintainable and extensible.

* **Model Routing (`config/llms.yaml`):** All provider definitions (Groq, OpenAI, Ollama) and model routing logic (reasoning, coding, fast-utility) are centralized in a single YAML file, making it trivial to update models as new ones are released.
* **Agent Prompts (`config/agents/**`):** Every agent's persona, system instructions, and constraints are stored as clean Markdown files with YAML frontmatter. No massive, hardcoded prompt strings cluttering the Python logic!
* **Sandbox Environments (`config/sandbox.yaml`):** Docker base images and test execution commands for various runtimes (Python, Node.js) are completely decoupled. You can easily add support for entirely new programming languages by simply defining the image and test command in YAML, without touching the core Python engine.

### Sandboxed QA Execution

The QA Engineer agent does not rely on LLM "guesswork" or mental simulation to test code. It executes the generated code in reality.

* **Zero Hallucinations:** The QA node mounts the active workspace into a temporary directory and runs the actual test suite (e.g., `pytest`, `npm test`). It reads the exact `stdout`/`stderr` tracebacks to accurately report bugs back to the Developer.
* **Ephemeral Isolation:** Code is executed securely using the Docker SDK. Containers are strictly isolated, resource-limited (CPU/RAM), and immediately destroyed after the test run, ensuring your host machine is never at risk.
* **Universal Runtime Auto-Detection:** The sandbox dynamically inspects the workspace or takes explicit direction from the System Architect to pull the correct Docker image (Python, Node.js, etc.) on the fly.

### Telemetry & Optimization

Running multi-agent systems can get expensive quickly if models get stuck in loops or context windows grow out of control. **My Dev Team** includes a built-in `TelemetryTracker` that monitors every single LLM call.

At the end of every workflow, the framework prints a granular receipt and an optimization diagnostic report:

```text
========================================
📊 TELEMETRY & COST REPORT
========================================
Total API Requests:  12
Prompt Tokens:       45,200
Completion Tokens:   3,100
Total Tokens:        48,300
----------------------------------------
Estimated Cost:      $0.0145
========================================

========================================
🔍 TOKEN OPTIMIZATION DIAGNOSTICS
========================================
⚠️ Thrashing Detected: `qa` was called 8 times. The agent might be stuck in a failure loop.
📈 Context Bloat: `reviewer` input grew by 3.2x (Started: 1200, Ended: 3840).
========================================

This allows you to easily identify architectural token leaks, pinpoint which specific agent is struggling, and adjust your `llms.yaml` or prompt templates accordingly!

## AI Agents

1) **Product Manager:** Analyzes requirements, asks clarifying questions, and writes detailed Technical Specifications.
2) **System Architect:** Breaks specifications down into a cohesive backlog of developer tasks.
3) **Senior Developer:** Incrementally writes code and unit tests for the current task.
4) **Code Reviewer:** Analyzes the generated code for security, style, and logic issues.
5) **QA Engineer:** Mentally simulates execution and evaluates the code against the task requirements.
6) **Final QA Engineer:** Performs a full-repository integration test once all tasks are complete.
7) **Reporter:** Generates a comprehensive final Markdown report for stakeholders.

## Installation

You can install the package directly via pip:

```sh
pip install my-dev-team
```

(For local development, clone the repository and run `pip install -e .`)

## 1. Preparing Your Project File

The crew requires a text file outlining your project requirements. By default, it looks for a specific header format to extract the project name and thread ID.

Create a file named `project.txt`:

```
Subject: NEW PROJECT: Web Scraper CLI

I need a Python command-line tool that scrapes articles from a given URL.
It should extract the title, author, and main body text, and save the output as a JSON file.

Requirements:
- Use BeautifulSoup4 for parsing.
- Include a `--url` argument and an `--output` argument.
- Write unit tests for the parsing logic.
```

## 2. Usage (CLI)

The fastest way to use the framework is via the terminal command included in the package.

```sh
devteam project.txt
```

### Advanced CLI Options

You can easily switch between cloud providers and local models, and adjust rate limits based on your API tier:

```sh
# Run entirely locally for free using Ollama, with no rate limit!
devteam project.txt --provider ollama

# Run using OpenAI's flagship models, limited to 15 requests per minute
devteam project.txt --provider openai --rpm 15

# Resume an interrupted run exactly where it left off
devteam --resume web_scraper_cli_20260312_083500
```

#### Available Arguments:

* `project_file`: (Optional if resuming) Path to your project requirements text file.
* `--resume`: Resume a specific thread ID (e.g., my_app_20260312_083500).
* `--provider`: Choose the LLM backend. Options: groq, ollama (default), openai.
* `--rpm`: API requests per minute. Set to 0 to disable rate limiting (default: 0).

Note: Ensure you have the corresponding API keys (e.g., `GROQ_API_KEY`, `OPENAI_API_KEY`) set in your `.env` file, or ensure your local Ollama instance is running.

## 3. Web Interface (Dashboard)

In addition to the CLI, **My Dev Team** includes a fully interactive web dashboard powered by Streamlit. This is perfect for users who want visual control over the autonomous agents.

To launch the web interface, make sure you have Streamlit installed (`pip install streamlit`), then run:

```sh
streamlit run app.py
```

### Dashboard Features

- **Launch Projects:** Upload your project requirements text file directly through your browser and select your LLM provider.
- **Granular Timeline:** View a deeply nested, chronological history of your AI crew's execution, cleanly displaying subgraph agent handoffs.
- **Visual Time Travel:** Easily resume paused workflows, or inject human-in-the-loop feedback by targeting specific graph checkpoints directly from the UI dropdowns.

## 4. Intelligent Model Routing (LLM Factory)

**My Dev Team** doesn't just use one model for everything. It uses an advanced **Semantic Routing** architecture via `LLMFactory`.

Instead of hardcoding a specific model (like `gpt-5.3-codex`), each agent requests a specific capability category and temperature. The Factory evaluates your chosen `--provider` and dynamically spins up the most cost-effective, capable model for that exact task.

#### The Categories

* `reasoning`: For the System Architect and Product Manager. Maps to deep-thinking models.
* `code-generator`: For the Senior Developer. Maps to strict, syntax-heavy models.
* `code-analyzer`: For the QA and Reviewer agents. Maps to deep-context evaluation models.
* `fast-utility`: For the Reporter. Maps to blazing-fast, ultra-cheap models for simple text summarization.

## 5. Usage (Python API)

If you want to integrate the crew into your own application, customize the LLM Factory's routing table, or override specific agent behaviors, use the clean Python API:

```python
import asyncio
import aiosqlite
from pathlib import Path
from dotenv import load_dotenv

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from devteam import VirtualCrew, ProjectManager, LLMFactory
from devteam.agents import ProductManager, SystemArchitect, SeniorDeveloper, CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
from devteam.extensions import HumanInTheLoop, WorkspaceSaver
from devteam.utils import RateLimiter, TelemetryTracker

load_dotenv()

def build_crew(project_folder: Path, llm_factory: LLMFactory, checkpointer: AsyncSqliteSaver, rpm: int = 0) -> VirtualCrew:
    # Initialize agents using built-in prompt templates
    agents = {
        'pm': ProductManager.from_config('pm', 'product-manager.md'),
        'architect': SystemArchitect.from_config('architect', 'system-architect.md'),
        'developer': SeniorDeveloper.from_config('developer', 'senior-developer.md'),
        'reviewer': CodeReviewer.from_config('reviewer', 'code-reviewer.md'),
        'qa': QAEngineer.from_config('qa', 'qa-engineer-sandbox.md').with_sandbox(DockerSandbox()),
        'final_qa': FinalQAEngineer.from_config('final_qa', 'final-qa-engineer.md'),
        # Example: Forcing the reporter to use a more creative reasoning model
        'reporter': Reporter.from_config('reporter', 'reporter.md', model_category='reasoning', temperature=0.7)
    }
    # Add extensions like saving files to disk or requiring human approval
    extensions = [
        WorkspaceSaver(workspace_dir=workspace_dir),
        HumanInTheLoop()
    ]
    return VirtualCrew(
        manager=ProjectManager(),
        agents=agents,
        extensions=extensions,
        checkpointer=checkpointer,
        rate_limiter=RateLimiter(requests_per_minute=rpm) if rpm > 0 else None
    )

async def main():
    requirements = "Build a simple Python calculator CLI with basic arithmetic."
    workspace = Path('./workspaces/calculator_app')
    workspace.mkdir(parents=True, exist_ok=True)
    db_path = workspace / 'state.db'
    telemetry = TelemetryTracker()
    factory = LLMFactory(provider='groq', callbacks=[telemetry])
    try:
        async with aiosqlite.connect(db_path) as conn:
            checkpointer = AsyncSqliteSaver(conn)
            crew = build_crew(workspace, provider='groq', checkpointer=checkpointer, rpm=30)
            print("🚀 Starting the AI Dev Team...")
            final_state = await crew.execute(
                thread_id="calc_run_01",
                requirements=requirements
            )
        if final_state.abort_requested:
            print("❌ Workflow aborted by user or validation failure.")
        elif final_state.success:
            print("🎉 Project completed successfully!")
            print(f"Total Revisions: {final_state.total_revisions}")
            if final_state.final_report:
                print(final_state.final_report)
        else:
            print("🚨 Release failed: Integration bugs found!")
            for bug in final_state.integration_bugs:
                print(f" - {bug}")
    except KeyboardInterrupt:
        print("\n\n🛑 Workflow interrupted by user (Ctrl+C).")
        print(f"💡 You can resume this exact state later by running:")
        print(f"   dev-team --resume {thread_id}")
    finally:
        telemetry.print_receipt()

if __name__ == "__main__":
    asyncio.run(main())
```
