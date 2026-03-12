# My Dev Team 🚀

An autonomous, LangGraph-powered AI development agency. **My Dev Team** takes raw project requirements and processes them through a multi-agent workflow (Product Manager, System Architect, Developers, and QA) to incrementally build, test, and deliver production-ready code.

## Features

* **Multi-Agent Architecture:** Specialized AI agents handle distinct phases of the software development lifecycle.
* **Semantic Model Routing:** Automatically routes tasks to the most cost-effective or capable LLMs based on the task type (reasoning, coding, or fast-utility).
* **Strict Test-Driven Development (TDD):** Testing is never an afterthought. Tasks are generated with embedded testing criteria, and the Developer writes unit tests alongside implementation code for immediate QA validation.
* **Incremental Development:** The System Architect breaks down requirements into a manageable backlog of strictly formatted JSON tasks.
* **Self-Healing Code:** The Developer, Reviewer, and QA Engineer agents continuously loop until unit tests pass and code meets specifications.
* **Structured Outputs:** Powered by Pydantic and LangChain, ensuring zero "Markdown spillage" and robust state management.
* **Extensible:** Easily add custom tools like `HumanInTheLoop` or `WorkspaceSaver`.

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
```

#### Available Arguments

* `--provider`: Choose the LLM backend. Options: groq, ollama (default), openai.

* `--rpm`: API requests per minute. Set to 0 to disable rate limiting (default: 0 = disabled).

Note: Ensure you have the corresponding API keys (e.g., `GROQ_API_KEY`, `OPENAI_API_KEY`) set in your `.env` file, or ensure your local Ollama instance is running.

## 3. Intelligent Model Routing (The LLM Factory)

**My Dev Team** doesn't just use one model for everything. It uses an advanced **Semantic Routing** architecture via `LLMFactory`.

Instead of hardcoding a specific model (like `gpt-5.3-codex`), each agent requests a specific capability category and temperature. The Factory evaluates your chosen `--provider` and dynamically spins up the most cost-effective, capable model for that exact task.

#### The Categories

* `reasoning`: For the System Architect and Product Manager. Maps to deep-thinking models.

* `code-generator`: For the Senior Developer. Maps to strict, syntax-heavy models.

* `code-analyzer`: For the QA and Reviewer agents. Maps to deep-context evaluation models.

* `fast-utility`: For the Reporter. Maps to blazing-fast, ultra-cheap models for simple text summarization.

## 4. Usage (Python API)

If you want to integrate the crew into your own application, customize the LLM Factory's routing table, or override specific agent behaviors, use the clean Python API:

```python
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from devteam import VirtualCrew, ProjectManager
from devteam.agents import (
    ProductManager, SystemArchitect, SeniorDeveloper,
    CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
)
from devteam.extensions import HumanInTheLoop, WorkspaceSaver

load_dotenv()

def build_crew(project_folder: Path, llm_factory: LLMFactory, rpm: int = 0) -> VirtualCrew:
    # Initialize agents using built-in prompt templates
    agents = {
        'pm': ProductManager.from_config('product-manager.md'),
        'architect': SystemArchitect.from_config('system-architect.md'),
        'developer': SeniorDeveloper.from_config('senior-developer.md'),
        'reviewer': CodeReviewer.from_config('code-reviewer.md'),
        'qa': QAEngineer.from_config('qa-engineer.md'),
        'final_qa': FinalQAEngineer.from_config('final-qa-engineer.md'),
        # Example: Forcing the reporter to use a more creative reasoning model
        'reporter': Reporter.from_config('reporter.md', model_category='reasoning', temperature=0.7)
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
        rate_limiter=RateLimiter(requests_per_minute=rpm) if rpm > 0 else None
    )

async def main():
    requirements = "Build a simple Python calculator CLI with basic arithmetic."
    workspace = Path('./workspaces/calculator_app')

    crew = build_crew(workspace, provider='groq', rpm=30)

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

if __name__ == "__main__":
    asyncio.run(main())
```

## AI Agents

* **Product Manager:** Analyzes requirements, asks clarifying questions, and writes detailed Technical Specifications.
* **System Architect:** Breaks specifications down into a cohesive backlog of developer tasks.
* **Senior Developer:** Incrementally writes code and unit tests for the current task.
* **Code Reviewer:** Analyzes the generated code for security, style, and logic issues.
* **QA Engineer:** Mentally simulates execution and evaluates the code against the task requirements.
* **Final QA Engineer:** Performs a full-repository integration test once all tasks are complete.
* **Reporter:** Generates a comprehensive final Markdown report for stakeholders.
