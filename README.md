# My Dev Team 🚀

An autonomous, LangGraph-powered AI development agency. **My Dev Team** takes raw project requirements and processes them through a multi-agent workflow (Product Manager, System Architect, Developers, and QA) to incrementally build, test, and deliver production-ready code.

## Features

* **Multi-Agent Architecture:** Specialized AI agents handle distinct phases of the software development lifecycle.

* **Incremental Development:** The System Architect breaks down requirements into a manageable backlog of tasks.

* **Self-Healing Code:** The Developer, Reviewer, and QA Engineer agents continuously loop until unit tests pass and code meets specifications.

* **Structured Outputs:** Powered by Pydantic and LangChain, ensuring zero "Markdown spillage" and robust JSON state management.

* **Extensible:** Easily add custom tools like HumanInTheLoop or WorkspaceSaver.

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
dev-team project.txt
```

This will automatically create a unique workspace folder (e.g., `workspaces/web_scraper_cli_20260311_181552/`), execute the workflow, and save your generated code there.

## 3. Usage (Python API)

If you want to integrate the crew into your own application or customize the agents, use the clean Python API:

```python
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from my_dev_team import VirtualCrew, ProjectManager
from my_dev_team.agents import (
    ProductManager, SystemArchitect, SeniorDeveloper,
    CodeReviewer, QAEngineer, FinalQAEngineer, Reporter
)
from my_dev_team.extensions import HumanInTheLoop, WorkspaceSaver

load_dotenv()

def build_crew(workspace_dir: Path) -> VirtualCrew:
    # Initialize agents using built-in prompt templates
    agents = {
        'pm': ProductManager.from_config('product-manager.md'),
        'architect': SystemArchitect.from_config('system-architect.md'),
        'developer': SeniorDeveloper.from_config('senior-developer.md'),
        'reviewer': CodeReviewer.from_config('code-reviewer.md'),
        'qa': QAEngineer.from_config('qa-engineer.md'),
        'final_qa': FinalQAEngineer.from_config('final-qa-engineer.md'),
        'reporter': Reporter.from_config('reporter.md')
    }

    # Add extensions like saving files to disk or requiring human approval
    extensions = [
        WorkspaceSaver(workspace_dir=workspace_dir),
        HumanInTheLoop()
    ]

    return VirtualCrew(
        manager=ProjectManager(),
        agents=agents,
        extensions=extensions
    )

async def main():
    requirements = "Build a simple Python calculator CLI with basic arithmetic."
    workspace = Path('./workspaces/calculator_app')

    crew = build_crew(workspace)

    print("🚀 Starting the AI Dev Team...")
    final_state = await crew.execute(
        thread_id="calc_run_01",
        requirements=requirements
    )

    if final_state.get('integration_bugs'):
        print("🚨 Completed with integration bugs.")
    else:
        print("🎉 Project completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

## The AI Agents

* **Product Manager:** Analyzes requirements, asks clarifying questions, and writes detailed Technical Specifications.

* **System Architect:** Breaks specifications down into a cohesive backlog of developer tasks.

* **Senior Developer:** Incrementally writes code and unit tests for the current task.

* **Code Reviewer:** Analyzes the generated code for security, style, and logic issues.

* **QA Engineer:** Mentally simulates execution and evaluates the code against the task requirements.

* **Final QA Engineer:** Performs a full-repository integration test once all tasks are complete.

* **Reporter:** Generates a comprehensive final Markdown report for stakeholders.
