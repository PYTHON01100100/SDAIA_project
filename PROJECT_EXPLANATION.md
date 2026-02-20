# Project Explanation — AI Agentic System
> Interview reference document generated from session analysis.

---

## What This Project Does

This is a **Multi-Agent AI Research System**. You give it a question on the command line, and three specialized AI agents work in sequence to research, analyze, and write a final answer.

```
python -m src.main "What is quantum computing?"
```

---

## Architecture Diagram

```
USER INPUT (query)
        │
        ▼
┌─────────────────────────────────────────┐
│              main.py                    │
│  - Starts CostTracker                   │
│  - Creates 3 agents                     │
│  - Passes output of each to the next    │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                  PIPELINE (Sequential)                  │
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │ RESEARCHER  │───▶│  ANALYST    │───▶│   WRITER    │ │
│  │ max_steps=10│    │ max_steps=20│    │ max_steps=5 │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│       │ raw facts    │ analysis          │ final report  │
└───────┼──────────────┼───────────────────┼──────────────┘
        │              │                   │
        ▼              ▼                   ▼
   search_web      search_web          search_web
  read_webpage    read_webpage        read_webpage
  (from registry) (from registry)    (from registry)
```

---

## The ReAct Loop (Inside Every Agent)

Every agent is an instance of `ObservableAgent` which runs a **ReAct (Reason + Act)** loop:

```
┌──────────────────────────────────────────────────────┐
│                  ObservableAgent.run()               │
│                                                      │
│  for step in range(max_steps):                       │
│       │                                              │
│       ▼                                              │
│  ┌─────────────────────────────┐                     │
│  │  Call LLM (OpenRouter API)  │◀─── system_prompt   │
│  └─────────────────────────────┘     + messages      │
│       │                                              │
│       ├── Tool calls? ──YES──▶ Execute tool          │
│       │                        (search_web /         │
│       │                         read_webpage)        │
│       │                        Append result to      │
│       │                        messages, CONTINUE    │
│       │                                              │
│       └── No tool calls? ──▶  FINAL ANSWER → STOP   │
│                                                      │
│  Observability at every step:                        │
│  ✅ token counting                                   │
│  ✅ loop detection (duplicate response check)        │
│  ✅ latency per step (trace_log)                     │
└──────────────────────────────────────────────────────┘
```

---

## Observability Layer (3 Files)

```
┌──────────────────────────────────────────────────────────────┐
│                    observability/                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  tracer.py  (AgentTracer)                           │    │
│  │  - trace_id per query (uuid)                        │    │
│  │  - Records each step: reasoning, tools, tokens,     │    │
│  │    cost, duration                                   │    │
│  │  - Exports full trace as JSON                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  loop_detector.py  (AdvancedLoopDetector)           │    │
│  │                                                     │    │
│  │  3 Strategies:                                      │    │
│  │  1. EXACT      - same tool + same args called twice │    │
│  │  2. FUZZY      - similar args (Jaccard >= 0.8)      │    │
│  │  3. STAGNATION - last N outputs are too similar     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  cost_tracker.py  (CostTracker)                     │    │
│  │  - Tracks start/end time of entire pipeline         │    │
│  │  - Logs tokens per agent (Researcher/Analyst/Writer)│    │
│  │  - Prints token breakdown at the end                │    │
│  │                                                     │    │
│  │  NOTE: USD cost is estimated inside ObservableAgent │    │
│  │  (_estimate_cost) but not printed here. The model   │    │
│  │  used is free so actual API cost = $0.00.           │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Tool System

```
┌──────────────────────────────────────────────────────┐
│               tools/registry.py                      │
│                                                      │
│  ToolRegistry  ◀──── @registry.register(...)         │
│       │                                              │
│       ├── Tool("search_web")  ──▶ DuckDuckGo search  │
│       └── Tool("read_webpage") ──▶ scrape a URL      │
│                                                      │
│  Each Tool wraps a function and:                     │
│  - Auto-generates OpenAI JSON schema from type hints │
│  - Validates input with Pydantic before executing    │
│  - Returns string-safe output to LLM                 │
│                                                      │
│  Security: validate_url() blocks private IPs         │
│  (127.x, 192.168.x, 10.x, 172.16-31.x)             │
└──────────────────────────────────────────────────────┘
```

---

## RAG / Vector Store (Bonus +15 pts)

```
┌──────────────────────────────────────────────────────┐
│              tools/vector_store.py                   │
│                                                      │
│  TechVectorStore                                     │
│  - Uses sentence-transformers (all-MiniLM-L6-v2)    │
│  - Stores document embeddings in FAISS index         │
│  - Saves/loads to disk (tech_vectors.pkl)            │
│  - query() returns top-K similar documents           │
│                                                      │
│  ┌──────────┐   embed   ┌──────────┐  search  ┌───┐ │
│  │ documents│──────────▶│  FAISS   │─────────▶│top│ │
│  └──────────┘           │  index   │          │ K │ │
│                         └──────────┘          └───┘ │
└──────────────────────────────────────────────────────┘
```

---

## Full Data Flow (End to End)

```
"What is quantum computing?"
         │
         ▼
   CostTracker.start_query()
         │
         ▼
  RESEARCHER runs ReAct loop
  → calls search_web("quantum computing")
  → calls read_webpage(url)
  → returns: raw facts text
  → CostTracker logs tokens
         │
         ▼
  ANALYST receives raw facts
  → analyzes patterns and trends
  → may call search_web for more depth
  → returns: structured analysis
  → CostTracker logs tokens
         │
         ▼
  WRITER receives analysis
  → formats into readable report
  → returns: final polished answer
  → CostTracker logs tokens
         │
         ▼
  CostTracker.end_query()
  CostTracker.print_cost_breakdown()
         │
         ▼
  FINAL OUTPUT printed to terminal
```

---

## Evaluation Criteria Mapping

| Criteria | Weight | Your Implementation | Score |
|---|---|---|---|
| Agent Architecture | 50% | Multi-Agent Orchestration (Researcher → Analyst → Writer) + ReAct loop inside each | Excellent |
| Observability & Reliability | 40% | tracer.py + loop_detector.py (3 strategies) + cost_tracker.py | Good→Excellent |
| Evaluation Framework | 5% | test_observable_agent.py + test_registry.py (no DeepEval yet) | Satisfactory |
| Engineering Excellence | 5% | Modular src/ layout, uv venv, README, .env | Good |

---

## Key Points to Say in the Interview

1. **"3 agents, 1 pipeline"** — not just a single chatbot, this is Multi-Agent Orchestration
2. **"ReAct loop"** — the agent thinks, acts with tools, observes results, repeats
3. **"Loop detection has 3 strategies"** — exact match, fuzzy Jaccard similarity, output stagnation
4. **"Cost tracking is per-agent"** — you can see which agent consumed most tokens
5. **"Vector store with FAISS"** — this is the RAG bonus system for +15 points
6. **"Tool registry with auto-schema"** — tools auto-generate their own OpenAI JSON spec from Python type hints
7. **"URL security validation"** — the web tools block private/internal IP addresses

---

## Cost Display Note

The `_estimate_cost()` method in `ObservableAgent` calculates USD cost from token counts:
- Input: $0.0003 per 1,000 tokens
- Output: $0.0006 per 1,000 tokens

This estimated cost is returned in the `run()` result as `estimated_cost_usd` but is **not forwarded to or printed by `CostTracker`**. Since the model used (`z-ai/glm-4.5-air:free`) is free, the real API cost is $0.00.

---

## File Structure

```
src/
├── main.py                        ← Entry point, orchestrates the pipeline
├── config.py                      ← Configuration
├── logger.py                      ← Logging setup (structlog)
├── utils.py                       ← Utilities
├── agent/
│   ├── observable_agent.py        ← Core ReAct agent with observability
│   └── specialists.py             ← Researcher, Analyst, Writer factories
├── tools/
│   ├── registry.py                ← ToolRegistry + Tool wrapper + Pydantic validation
│   ├── search_tool.py             ← search_web + read_webpage tools
│   └── vector_store.py            ← FAISS RAG vector store
├── observability/
│   ├── tracer.py                  ← AgentTracer (per-step JSON tracing)
│   ├── cost_tracker.py            ← CostTracker (per-agent token tracking)
│   └── loop_detector.py           ← AdvancedLoopDetector (3 strategies)
├── test_observable_agent.py       ← Agent tests
└── test_registry.py               ← Registry tests
```
