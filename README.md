# AI Agents - Project Starter

This is the starter code for the AI Agents homework. You will be building a multi-agent system capable of performing research, analysis, and writing.

## Structure

The project follows a production-ready `src` layout:

- `src/`: Source code directory.
  - `main.py`: Entry point for the application.
  - `config.py`: Configuration management.
  - `tools/`: Registry and tools implementation.
    - `search_tool.py`: Provided search tools (DONE).
    - `registry.py`: Tool mechanism (TODO).
  - `agent/`: Agent implementation.
    - `observable_agent.py`: The core agent class with observability (TODO).
    - `specialists.py`: Definitions for specific agents (Researcher, Analyst, Writer) (TODO).
  - `observability/`: Tracing and monitoring.
    - `tracer.py`: Execution tracing (TODO).
    - `cost_tracker.py`: Cost monitoring (TODO).
    - `loop_detector.py`: Infinite loop prevention (TODO).
- `tests/`: Test directory.

## Setup

### 1. Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal after installation, then verify:

```bash
uv --version
```

### 2. Create a virtual environment

```bash
uv venv
```

This creates a `.venv` folder in the project root.

### 3. Activate the virtual environment

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (CMD)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
uv pip install -r requirements.txt
```

### 5. Set up environment variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_key_here
MODEL_NAME=gpt-4o
```

### 6. Run the application

```bash
# Run from the project root using the module flag -m
python -m src.main "Your query here"
```

## Git Workflow

### Check status

```bash
git status
```

### Stage and commit changes

```bash
git add .
git commit -m "your commit message"
```

### Create a new branch and switch to it

```bash
git checkout -b your-branch-name
```

### Push branch to remote

```bash
git push -u origin your-branch-name
```

### Set a branch as the default (main) on GitHub

1. Push your branch to remote (see above).
2. Go to your GitHub repo → **Settings** → **Branches**.
3. Under **Default branch**, click the switch icon and select your branch.
4. Confirm the change.

Or rename your current local branch to `main` and push:

```bash
git branch -m main                  # rename current branch to main
git push -u origin main             # push to remote
git push origin --delete old-name   # delete the old branch on remote (if needed)
```

## Tasks

Follow the TODO comments in the files to complete the implementation. Start with `src/tools/registry.py`, then `src/observability/`, and finally `src/agent/observable_agent.py`.
