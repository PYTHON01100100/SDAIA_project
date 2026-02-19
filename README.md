#  Multi-Agent AI Research System

Multi-agent system built with a **ReAct loop**, full **observability**. The system orchestrates three specialized agents (Researcher, Analyst, and Writer) to answer complex queries using web search and document retrieval.

---

## Features

| Feature | Details |
|---|---|
| **Multi-Agent Orchestration** | Researcher → Analyst → Writer linear pipeline |
| **ReAct Loop** | Iterative Reasoning + Acting with configurable `max_steps` |
| **Structured Tracing** | Every agent step, tool call, and result is logged with `AgentTracer` |
| **Advanced Loop Detection** | Detects both repetition and stagnation via `AdvancedLoopDetector` |
| **Real-time Cost Tracking** | Per-query token usage and USD cost via `CostTracker` + LiteLLM |
| **RAG Pipeline** | PDF extracting → text cleaning → chunking → FAISS vector search |
| **Async Execution** | Fully async agent loop using `acompletion` |

---

## Project Structure

```
.
├── src/
│   ├── main.py                  # Orchestration pipeline
│   ├── config.py                # Model configuration
│   ├── agent/
│   │   ├── observable_agent.py  # Core ReAct agent with observability
│   │   └── specialists.py       # Factory functions: create_researcher/analyst/writer
│   ├── tools/
│   │   ├── registry.py          # Tool registration & execution
│   │   └── search_tool.py       # Web search & webpage reader tools
│   ├── observability/
│   │   ├── tracer.py            # Structured step-by-step tracing
│   │   ├── cost_tracker.py      # Token & USD cost monitoring
│   │   └── loop_detector.py     # Repetition & stagnation detection   
├──RAG.py                        # PDF extraction, chunking, FAISS indexing & search
├──tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

##  Setup

### Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) — fast Python package manager

### 1. Install `uv`

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone & install dependencies

```bash
git clone <repo-url>
cd <project-folder>

# Create virtual environment and install all dependencies
uv sync
```

### 3. Configure environment variables


Create `.env` and fill in your keys:

```env
OPENROUTER_API_KEY=your_openrouter_key_here 
MODEL_NAME=openrouter/stepfun/step-3.5-flash:free
```

---

## Usage

Run the full multi-agent pipeline from the project root:

```bash
uv run python -m src.main "What are the latest AI regulations in Saudi Arabia?"
```

**What happens under the hood:**

1. **Researcher Agent** searches the web and retrieves relevant sources
2. **Analyst Agent** evaluates findings — strengths, weaknesses, clarity
3. **Writer Agent** produces a well-structured Markdown report
4. Total cost and trace ID are printed at the end

---

## Observability

Every run produces a structured trace capturing key events like agent steps, tool calls, and cost.
Detailed per-step logs are available during execution for debugging and monitoring purposes.


---

## RAG Pipeline
Note: The RAG pipeline is implemented in a separate module and not yet integrated into the main agent loop.

```
PDF File
  → extract_pdf_text()       # PyMuPDF page-by-page extraction
  → clean_text_extended()    # Normalize, remove artifacts
  → RecursiveChunker()       # 300 tokens, 50 overlap
  → generate_embedding()     # OpenAI text-embedding-3-small via OpenRouter
  → FAISS IndexFlatL2        # Vector similarity search
  → search_document(query)   # Returns top-k relevant chunks
```

---


## Tech Stack

| Component | Library |
|---|---|
| LLM calls | `litellm` |
| Model | `openrouter/openai/gpt-oss-120b:free` |
| Embeddings | `openai/text-embedding-3-small` (via OpenRouter) |
| Vector DB | `faiss-cpu` |
| PDF parsing | `PyMuPDF (fitz)` |
| Text splitting | `langchain-text-splitters` |
| Structured logging | `structlog` |
| Dependency manager | `uv` |
