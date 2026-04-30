# 🔍 AI Research Agent

> An autonomous, multi-step research pipeline that plans, searches, grades, synthesises, and self-validates — built with LangGraph, Gemini 2.5 Flash, Tavily, and Streamlit.

---

## What it does

You give it a research question. It figures out the rest.

The agent breaks your question into a plan, fires diverse web searches, scrapes and grades every source, detects where sources agree or contradict each other, writes a structured answer with citations, strips any hallucinated URLs, and rates its own confidence — all in one shot.

**Example:** *"What are the trade-offs between RAG and fine-tuning for production LLMs?"*

The agent returns:
- A 2–3 sentence direct answer
- Verified key findings (each backed by 2+ sources)
- A conflict report showing where experts disagree and why
- Source quality scores (relevance, authority, recency, depth)
- Confidence level with reasoning
- Limitations, assumptions, and suggested follow-up questions

---

## Architecture

The pipeline is a **7-node LangGraph `StateGraph`** running sequentially:

```
Planner → Tool Executor → Source Grader → Conflict Detector
        → Synthesizer → Citation Validator → Confidence Scorer
```

| Node | What it does |
|---|---|
| **Planner** | Breaks the question into 2–4 research steps and generates diverse search queries |
| **Tool Executor** | Runs Tavily web searches, scrapes top results via Jina Reader, logs every API call with latency |
| **Source Grader** | LLM scores each source 1–5 on relevance, authority, recency, depth; filters low-quality sources |
| **Conflict Detector** | Identifies agreed facts, disputed claims (with both positions), and unclear evidence |
| **Synthesizer** | Writes a structured answer with inline citations from the graded sources |
| **Citation Validator** | Cross-checks every URL in findings against retrieved sources; strips hallucinated ones |
| **Confidence Scorer** | LLM rates high/medium/low, then rule-based downgrades override if data doesn't support it |

The full agent state flows through all nodes via a typed `AgentState` TypedDict — no global state, no hidden coupling between nodes.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Agent framework | [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful graph with clean node isolation |
| Primary LLM | Gemini 2.5 Flash | Fast, cheap, strong at structured JSON output |
| Fallback LLM | Groq Llama 3.3 70B | Kicks in automatically on Gemini rate limits |
| Web search | [Tavily](https://tavily.com/) | Returns clean ranked results with metadata |
| Web scraping | [Jina Reader](https://jina.ai/reader/) | Converts any URL to clean markdown; handles JS-rendered pages |
| UI | [Streamlit](https://streamlit.io/) | Fast to iterate on; good for ML-adjacent tools |
| Config | pydantic-settings | Type-safe env management, no scattered `os.getenv()` |
| Validation | Pydantic v2 | All inter-node data shapes strictly defined |

---

## Key engineering decisions

### LangGraph over a plain loop
Each node is independently testable, has clear inputs/outputs via `AgentState`, and can be reordered or swapped without touching anything else. Adding the `citation_validator` node later required zero changes to any other node — just wired it into `graph.py`.

### Dual LLM with automatic fallback
`llm.py` tries Gemini first. If it gets a rate limit, quota error, or 503, it falls back to Groq transparently. Nodes never know which provider ran. Retries use exponential backoff for transient errors and fail fast for permanent ones.

### Rule-based confidence overrides
The confidence scorer gets an LLM rating first, then applies hard rules: disputes → max medium, fewer than 2 sources → forced low, average source quality < 3.0 → downgrade one level. This prevents the LLM from confidently rating low-quality research as high.

### Citation hallucination detection
The synthesiser LLM regularly invented plausible-looking URLs that weren't actually retrieved. The `citation_validator` node normalises every URL in every finding and strips anything not in `graded_sources`. Verified status (2+ real sources) is recalculated after stripping.

### Prompt injection defence
Jina Reader sometimes returns pages with injection attempts embedded in content ("Ignore all previous instructions…"). The scraper sanitises all content through a pattern blocklist before it reaches the LLM.

---

## Project structure

```
ai_research_agent/
├── app.py                        # Streamlit entrypoint (thin — just config + routing)
├── agent/
│   ├── graph.py                  # LangGraph pipeline wiring
│   ├── schemas.py                # Pydantic models + AgentState TypedDict
│   ├── llm.py                    # LLM client (Gemini + Groq fallback, retry logic)
│   ├── prompts.py                # All LLM prompt templates
│   └── nodes/
│       ├── planner.py
│       ├── tool_executor.py
│       ├── source_grader.py
│       ├── conflict_detector.py
│       ├── synthesizer.py
│       ├── citation_validator.py
│       └── confidence.py
├── agent/tools/
│   ├── web_search.py             # Tavily wrapper
│   └── scraper.py                # Jina Reader + prompt injection sanitiser
├── app/
│   ├── core/runner.py            # Pipeline runner (decoupled from Streamlit)
│   └── ui/                       # Streamlit UI components (results, sidebar, styles)
├── config/settings.py            # Centralised pydantic-settings config
├── utils/logging.py
└── tests/
    ├── test_citation_validator.py
    └── test_scraper.py
```

---

## Getting started

### Prerequisites

- Python 3.11+
- API keys for Gemini and Tavily (both have free tiers)
- Groq is optional but recommended as a fallback

### Install

```bash
git clone https://github.com/yourusername/ai-research-agent.git
cd ai-research-agent
pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
GEMINI_API_KEY=your_gemini_key_here
TAVILY_API_KEY=your_tavily_key_here

# Optional — used as LLM fallback
GROQ_API_KEY=your_groq_key_here
```

Free API keys:
- **Gemini:** https://aistudio.google.com/
- **Tavily:** https://tavily.com/
- **Groq:** https://console.groq.com/

### Run

```bash
streamlit run app.py
```

---

## Configuration

All tunable parameters live in `config/settings.py` (via `.env`):

| Variable | Default | Description |
|---|---|---|
| `MAX_SEARCH_RESULTS` | `5` | Tavily results per query |
| `TOP_N_TO_SCRAPE` | `2` | Full-page scrapes per query (Jina) |
| `MAX_TOOL_CALLS` | `5` | Hard cap on total API calls per run |
| `MAX_SCRAPE_CHARS` | `8000` | Character limit per scraped page |
| `SCRAPE_TIMEOUT_SECONDS` | `8.0` | Jina Reader request timeout |
| `LLM_MAX_RETRIES` | `3` | Retry attempts per LLM call |
| `PIPELINE_TIMEOUT_SECONDS` | `120` | Total pipeline timeout |

---

## Running tests

```bash
pytest tests/ -v
```

Tests cover citation URL normalisation, hallucination stripping, and scraper sanitisation. Node-level unit tests are on the TODO list.

---

## Known limitations

- **No session memory** — each query is fully independent; there's no cross-query context
- **Sequential pipeline** — scraping and grading could run in parallel to reduce latency
- **No streaming** — the UI shows a spinner until the whole pipeline finishes; streaming output is planned
- **Injection blocklist** — the prompt injection defence is pattern-based and can be evaded with creative phrasing
- **Tavily free tier** — rate limits make rapid consecutive queries slow

---

## What I learned building this

- **LangGraph's `StateGraph`** is genuinely useful for multi-step pipelines — the forced separation of state and logic makes each node independently debuggable in a way a plain function chain doesn't.
- **LLMs hallucinate citations consistently** — not occasionally. Building the citation validator wasn't optional; it was required for the output to be trustworthy.
- **Structured JSON prompts need strict validation** — even with `response_mime_type: application/json`, Gemini sometimes wraps output in markdown fences or omits required keys. Defensive parsing is necessary.
- **A fallback LLM is worth the extra setup** — Gemini's free tier rate limits at peak hours meant the agent was unusable without Groq as a backup.

---

## License

MIT
