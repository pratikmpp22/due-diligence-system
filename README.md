# Multi-Agent Due Diligence Analyst


![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange.svg)
![Groq](https://img.shields.io/badge/Groq-gpt--oss--120b-purple.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status: Production](https://img.shields.io/badge/Status-Production-brightgreen.svg)

Enterprise-grade company research powered by a **multi-agent AI team** — 1 Lead Analyst (planning, debate, synthesis), 4 specialist researchers (financial, news, competitive, risk), and 1 Fact Checker — with parallel execution, contradiction resolution, and comprehensive guardrails.

```
Input: "Tesla"  ──>  6 Agents (parallel)  ──>  Fact-Check  ──>  Debate  ──>  Final Report
                     Financial Analyst         Independent      Resolve       Risk Rating
                     News & Sentiment          Verification     Conflicts     Recommendation
                     Competitive Intel                                        Action Items
                     Risk Assessor
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/pratikmpp22/due-diligence-system.git
cd due-diligence-system
pip install -r requirements.txt

# 2. Set API key (free at https://aistudio.google.com/apikey)
#    Option A: Create a .env file (recommended)
cp .env.example .env    # Then edit .env and paste your key

#    Option B: Set environment variable directly
#    Linux/Mac:   export GOOGLE_API_KEY=your_key_here
#                 export GROQ_API_KEY=your_groq_key_here
#    Windows CMD: set GOOGLE_API_KEY=your_key_here
#    PowerShell:  $env:GOOGLE_API_KEY='your_key_here'

# 3. Run analysis
python main.py --company "Tesla"

# Or launch the Streamlit dashboard
streamlit run app.py
```

> **Windows users:** If `pip install` fails with permission errors, use `pip install --user -r requirements.txt` or create a virtual environment first: `python -m venv .venv` then `.venv\Scripts\activate`.

## Architecture

> See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

```
                    +------------------+
                    |   Lead Analyst   |  PLAN: Decomposes query
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |              |
     +--------v--+  +-------v----+  +------v-------+  +--v-----------+
     | Financial  |  |   News &   |  | Competitive  |  |    Risk      |
     | Analyst    |  | Sentiment  |  | Intelligence |  |  Assessor    |
     +-----+------+  +-----+-----+  +------+-------+  +------+-------+
           |              |              |                    |
           +--------------+--------------+--------------------+
                             |
                    +--------v---------+
                    |   Fact Checker   |  VERIFY: Independent checks
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Lead Analyst   |  DEBATE: Resolve contradictions
                    +--------+---------+
                             |
                    +--------v---------+
                    |   Lead Analyst   |  SYNTHESIZE: Final report
                    +------------------+
```

### What Makes This Enterprise-Grade

| Feature | Implementation |
|---------|---------------|
| **Parallel Execution** | 4 specialist agents via LangGraph `Send()` - 3x faster |
| **Structured Output** | Pydantic schemas via `.with_structured_output()` - zero parsing errors |
| **Graceful Degradation** | Every agent has try/except fallback - pipeline never halts |
| **Fact-Checking** | Independent verification pass challenges all claims |
| **Contradiction Resolution** | Lead Analyst debates conflicting findings |
| **Budget Guardrails** | Token ceiling, cost cap, loop detection, timeout enforcement |
| **PII Detection** | Email, phone, SSN, credit card pattern matching + masking |
| **Source Grounding** | Source-presence checks with warnings for unsourced outputs |
| **Search Caching** | SQLite-backed with TTL and LRU eviction |
| **Model Fallback** | Primary -> fallback model chain with exponential backoff |
| **Cost Tracking** | Per-agent token usage and cost estimation |

## Project Structure

```
due-diligence-system/
├── configs/
│   └── base.yaml                 # All tunable parameters (single source of truth)
├── src/
│   ├── agents/
│   │   ├── graph.py              # LangGraph pipeline wiring + run_pipeline()
│   │   ├── lead_analyst.py       # Planner + Debater + Synthesizer (3 roles)
│   │   ├── financial_analyst.py  # Revenue, margins, ratios, cash flow
│   │   ├── news_sentiment.py     # News timeline, sentiment trends, PR patterns
│   │   ├── competitive_intel.py  # Competitors, moats, market position
│   │   ├── risk_assessor.py      # Legal, regulatory, operational, ESG risks
│   │   ├── fact_checker.py       # Independent claim verification
│   │   └── __main__.py           # CLI: python -m src.agents "Tesla"
│   ├── tools/
│   │   ├── search.py             # Web search (Tavily/DuckDuckGo) + SQLite cache
│   │   └── calculators.py        # Financial ratios, risk scoring, sentiment calc
│   ├── models/
│   │   ├── state.py              # DueDiligenceState TypedDict (shared state)
│   │   └── schemas.py            # 14 Pydantic schemas for structured LLM output
│   ├── guardrails/
│   │   └── manager.py            # Budget, loops, PII, source grounding, timeout
│   ├── config.py                 # YAML loader with env overrides + caching
│   └── llm.py                    # LLM factory: Google/OpenAI/Ollama + token tracking
├── tests/
│   ├── test_agents.py            # Specialist agent outputs + fallback behavior
│   ├── test_calculators.py       # Financial ratios, risk scores, sentiment
│   ├── test_config.py            # Config loading, env overrides, defaults
│   ├── test_evaluation.py        # Evaluation metrics and scoring logic
│   ├── test_graph.py             # Graph routing, compilation, guarded nodes
│   ├── test_guardrails.py        # PII detection, budget, loops, disable
│   ├── test_integration.py       # End-to-end graph and pipeline integration
│   ├── test_llm.py               # LLM provider factory + token tracker behavior
│   ├── test_search.py            # Search cache CRUD, eviction
│   └── test_state.py             # State schema initialization
├── evaluation/
│   ├── run_eval.py               # Coverage, source diversity, consistency metrics
│   └── judge_prompt.py           # LLM-as-judge prompt templates
├── notebooks/
│   └── Due_Diligence_Agent.ipynb # Step-by-step walkthrough (Kaggle-ready)
├── docs/
│   └── architecture.md           # Detailed architecture docs
├── docker/
│   ├── Dockerfile                # Multi-stage build
│   └── docker-compose.yml        # One-command deployment
├── scripts/
│   ├── run_pipeline.sh           # Shell script for CLI analysis (Linux/Mac)
│   └── run_pipeline.ps1          # PowerShell script for CLI analysis (Windows)
├── app.py                        # Streamlit dashboard
├── main.py                       # CLI entry point (analyze | ui | evaluate)
├── requirements.txt              # Pinned dependencies
└── .env.example                  # API key template
```

## Usage

### CLI Analysis

```bash
# Standard analysis
python main.py --company "Tesla"

# Deep analysis with specific focus
python main.py --company "Stripe" --depth deep --query "Focus on fintech regulation risks"

# Quick scan with report output
python main.py --company "OpenAI" --depth quick --output reports/openai.md

# Via module
python -m src.agents "Databricks" --depth standard
```

### Streamlit Dashboard

```bash
streamlit run app.py
```

Features:
- Company input with depth selection
- **Dynamic Model Selection** (Google, OpenAI, Groq, Ollama)
- **Real-time agent progress streaming** (watch each node finish instantly)
- Tabbed report viewer (Full Report / Findings / Trace / Raw Data)
- Budget and cost tracking
- **Automatic Report Saving** to `artifacts/reports/`
- Report download (Markdown)

### Docker

```bash
# Build and run
docker build -f docker/Dockerfile -t dd-agent .
docker run -p 8501:8501 -e GOOGLE_API_KEY=your_key dd-agent

# Or via docker-compose
cd docker && docker-compose up
```

### Python API

```python
from src.agents.graph import run_pipeline

result = run_pipeline("Tesla", depth="standard")

print(result["executive_summary"])
print(result["overall_risk_rating"])
print(result["final_report"])
```

## Run Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

# Specific test file
python -m pytest tests/test_guardrails.py -v
```

## Configuration

All parameters in `configs/base.yaml`. Override via environment variables:

| Env Variable | Config Path | Default |
|-------------|-------------|---------|
| `GOOGLE_API_KEY` | - | Required (if using Google) |
| `GROQ_API_KEY` | - | Required (if using Groq) |
| `OPENAI_API_KEY` | - | Required (if using OpenAI) |
| `TAVILY_API_KEY` | - | Optional (falls back to DuckDuckGo) |
| `DD_MODEL_PROVIDER`| model.provider | google |
| `DD_MODEL_NAME` | model.name | gemini-2.5-flash (or openai/gpt-oss-120b for Groq) |
| `DD_MAX_COST_USD` | budget.max_cost_usd | 0.50 |
| `DD_MAX_TOTAL_TOKENS` | budget.max_total_tokens | 100000 |
| `DD_LOG_LEVEL` | logging.level | INFO |

## Evaluation

```bash
python main.py --stage evaluate
```

Evaluates on 3 test companies (Tesla, Stripe, Anthropic) across 4 metrics:
- **Coverage**: Breadth of research areas (financial/news/competitive/risk)
- **Source diversity**: Number of unique sources cited
- **Factual consistency**: Cross-agent agreement (via fact-checker)
- **Actionability**: Verdict, risk rating, recommendations, uncertainty acknowledgment

## Cost

Using Google Gemini 2.5 Flash free tier (30 RPM, 1500 RPD):

| Depth | LLM Calls | Tokens | Cost | Duration |
|-------|-----------|--------|------|----------|
| Quick | 7 | ~20K | ~$0.008 | ~60s |
| Standard | 7-9 | ~28K | ~$0.012 | ~120s |
| Deep | 9-12 | ~40K | ~$0.018 | ~180s |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Orchestration | LangGraph (StateGraph, Send, conditional edges) |
| LLM | Google Gemini, OpenAI, Groq (`gpt-oss-120b`), Ollama |
| Structured Output | Pydantic v2 + `.with_structured_output()` |
| Search | Tavily (paid) / DuckDuckGo (free fallback) |
| Caching | SQLite (search results + TTL + LRU) |
| UI | Streamlit |
| Testing | pytest (comprehensive test suite) |
| Deployment | Docker multi-stage build |
| Config | YAML + environment variable overrides |
