# Installation Guide

This guide will help you set up **My Dev Team** on your local machine.

## Prerequisites

Before installing, ensure you have the following:

* **Python 3.10+**: Verify by running `python --version`.
* **API Credentials**: You will need at least one of the following:
    * An OpenAI or Groq API Key set in your environment variables.
    * A local instance of **Ollama** running (for free, local execution).

## Standard Installation

We highly recommend using a virtual environment (`venv` or `conda`).

```sh
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the core package
pip install my-dev-team
```

## Optional Dependencies

### Web Dashboard (UI)

If you want to use the interactive Streamlit dashboard to visualize agent handoffs and "time travel" between checkpoints, install the UI extras:

```sh
pip install "my-dev-team[ui]"
```

### Sandboxed QA Execution

For the QA Engineer to execute code in a real, isolated environment (rather than just simulating it), you must have **Docker Engine** installed and running on your host machine.

* [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)

**Build the image:**

```sh
docker build -t python:3.12-pytest -f src/devteam/config/docker/Dockerfile.python3.12-pytest .
```

- This will create an image named `python:3.12-pytest` with pytest preinstalled and `/workspace` as the working directory.
- You can customize the Dockerfile for other Python versions or additional dependencies as needed.

### Ollama (Local LLMs)

To use local LLMs with Ollama, follow the [Ollama Installation Guide](./ollama.md) for setup instructions on Windows, WSL, and Linux.

## Configuration

### Environment Variables

Create `.env` file in your project root to store your keys:

```
OPENAI_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

### Local Development

If you want to contribute or modify the agents, clone the repository and install in editable mode:

```sh
git clone https://github.com/bobrovsky420/my-dev-team.git
cd my-dev-team
pip install -e .
```

## Verify Installation

Once installed, verify the CLI is working by checking the help command:

```sh
devteam --help
```
