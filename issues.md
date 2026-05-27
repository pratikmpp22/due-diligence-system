# Issues & Improvements — Due Diligence System

> A comprehensive audit of bugs, inconsistencies, missing features, and areas for improvement across the entire codebase.
>
> ✅ = Fixed | 🔧 = Partially addressed | ⏳ = Documented / deferred

---

## Table of Contents

- [🔴 Critical Issues](#-critical-issues)
- [🟠 High Priority Issues](#-high-priority-issues)
- [🟡 Medium Priority Issues](#-medium-priority-issues)
- [🔵 Low Priority / Improvements](#-low-priority--improvements)
- [📝 Documentation Issues](#-documentation-issues)
- [🧪 Testing Gaps](#-testing-gaps)
- [🏗️ Architecture Improvements](#️-architecture-improvements)

---

## 🔴 Critical Issues

### ✅ 1. API Keys Exposed in `.env` File
- **File:** `.env`
- **Issue:** The `.env` file contains **hardcoded real API keys** (`GOOGLE_API_KEY`, `TAVILY_API_KEY`) and is present in the project directory. Although `.gitignore` excludes `.env`, if this was ever committed to git history, the keys are permanently leaked.
- **Fix:** Created `.env.example` with placeholder values. User should rotate keys.

### ✅ 2. Token Tracker Is Not Thread-Safe (Despite Claiming To Be)
- **File:** `src/llm.py`
- **Issue:** `TokenTracker` class used simple `+=` operations with no locking mechanism.
- **Fix:** Added `threading.Lock` to all mutable state operations in `TokenTracker`.

### ✅ 3. Missing `.env.example` File (Referenced Everywhere)
- **Files:** `README.md`, `main.py`, `app.py`, `src/agents/__main__.py`
- **Issue:** The `.env.example` file was referenced everywhere but didn't exist.
- **Fix:** Created `.env.example` with placeholder keys. Updated all references.

### ✅ 4. Guardrail Token/Cost Tracking Is Disconnected from Actual Usage
- **File:** `src/agents/graph.py`, `src/guardrails/manager.py`
- **Issue:** `post_check()` was always called with `tokens_used=0` and `cost_usd=0.0`.
- **Fix:** Added `token_tracker.snapshot()` before/after agent execution and passes actual deltas to `post_check()`.

---

## 🟠 High Priority Issues

### ✅ 5. AgentTrace `tokens_used` and `cost_usd` Are Always Zero
- **Files:** All agent files
- **Issue:** Every `AgentTrace` entry had `tokens_used=0` and `cost_usd=0.0` hardcoded.
- **Fix:** Each agent now records `token_tracker` snapshots before/after LLM calls and computes the delta.

### ✅ 6. `_build_search_context` Function Is Duplicated 4 Times
- **Files:** All 4 specialist agent files
- **Issue:** Same function copy-pasted across all agents.
- **Fix:** Extracted to `src/utils.py:build_search_context()`. All agents import it.

### ✅ 7. Streamlit Progress Bar Is Fake
- **File:** `app.py`
- **Issue:** Progress bar cycled instantly before the pipeline started.
- **Fix:** Pipeline now runs in a background thread. Progress bar updates every 3 seconds while pipeline is running.

### ✅ 8. Streaming Mode (`stream=True`) Returns a Generator, Not a Dict
- **File:** `src/agents/graph.py`
- **Issue:** Return type annotation said `-> dict` but streaming returns a generator.
- **Fix:** Updated return type to `dict | Generator`.

### ✅ 9. Hardcoded Year in Search Queries
- **Files:** `financial_analyst.py`, `news_sentiment.py`, `competitive_intel.py`
- **Issue:** Search queries contained hardcoded `"2024 2025"`.
- **Fix:** Created `src/utils.py:get_current_year_range()` that dynamically generates the range.

### ✅ 10. `Makefile` Listed in README But Does Not Exist
- **Fix:** Removed the `Makefile` reference from README.md entirely as it isn't necessary for this project.

---

## 🟡 Medium Priority Issues

### ✅ 11. `src/memory/` Module Is Empty (Dead Code)
- **Fix:** Removed the empty `src/memory/` directory.

### ✅ 12. Config Caching Prevents Runtime Budget Updates from Taking Effect
- **File:** `src/config.py`, `app.py`
- **Fix:** `app.py` now calls `reset_config()` before setting budget overrides so `GuardrailManager` reads fresh values.

### ✅ 13. `confidence_threshold` Read But Never Enforced
- **File:** `src/guardrails/manager.py`
- **Fix:** `post_check()` now checks for low-confidence markers in agent output and emits a warning.

### ✅ 14. PII Detection But No Automatic Masking in Pipeline
- **File:** `src/guardrails/manager.py`
- **Fix:** `post_check()` now calls `mask_pii()` when PII is detected and returns `masked_output` in the result.

### ✅ 15. `ip_address` PII Pattern Has False Positives
- **File:** `src/guardrails/manager.py`
- **Fix:** Updated IP regex to validate each octet is 0-255 (`(?:25[0-5]|2[0-4]\d|[01]?\d\d?)`).

### ✅ 16. `SearchCache` Opens Multiple SQLite Connections Per Operation
- **File:** `src/tools/search.py`
- **Fix:** Consolidated `get()` into a single `with sqlite3.connect()` context.

### ✅ 17. `get_agent_config()` Return Value Is Never Used by Agents
- **Files:** All agent files
- **Fix:** All agents now call `get_agent_config(AGENT_NAME)` and use the returned `temperature` value.

### ✅ 18. `WebSearchTool` Instantiated Multiple Times Per Agent Call
- **File:** `src/tools/search.py`
- **Fix:** Added singleton pattern via `__new__()`. Agents share a single instance.

### ✅ 19. `SearchCache` Uses MD5 for Query Hashing
- **File:** `src/tools/search.py`
- **Fix:** Replaced `hashlib.md5()` with `hashlib.sha256()`.

### ✅ 20. `debate_log` Access Mismatch in `synthesize_report`
- **File:** `src/agents/lead_analyst.py`
- **Fix:** Updated to use consistent `DebateEntry` field names (`agent_a`, `agent_b`, `contradiction`, `resolution`, `confidence`).

---

## 🔵 Low Priority / Improvements

### ✅ 21. No FastAPI Endpoint (Dependency Listed but Unused)
- **Fix:** Removed `fastapi` and `uvicorn` from `requirements.txt`.

### ✅ 22. No `__main__.py` Registration in Docs
- **Fix:** Updated `__main__.py` error message with accurate `.env.example` instructions.

### ✅ 23. `run_pipeline.sh` Is Linux/Mac Only
- **Fix:** Created `scripts/run_pipeline.ps1` for Windows users.

### ✅ 24. `data/cache.db` Is Not Auto-Created on Fresh Clone
- **Fix:** Added `data/.gitkeep` to preserve the directory in git.

### ✅ 25. No Input Validation for Company Name
- **File:** `main.py`
- **Fix:** Added length validation (2-200 chars) before running the pipeline.

### ✅ 26. No Rate Limit Handling for Gemini Free Tier
- **File:** `src/llm.py`
- **Fix:** Added specific 429/rate-limit detection with 30s+ backoff (vs normal 2s exponential backoff).

### ✅ 27. No Report Persistence in CLI Mode
- **File:** `main.py`
- **Fix:** Reports now auto-save to `artifacts/reports/{company}_{timestamp}.md` even without `--output`.

### ✅ 28. `tabulate` Dependency Is Never Used
- **Fix:** Removed from `requirements.txt`.

### ✅ 29. Docker Compose `version` Field Is Deprecated
- **Fix:** Removed `version: "3.8"` from `docker/docker-compose.yml`.

### ⏳ 30. `notebooks/` Directory Is Not Explored
- **Status:** Requires manual verification. Notebook may need updates to match current APIs.

---

## 📝 Documentation Issues

### ✅ 31. README References Non-Existent Files
- **Fix:** Created `.env.example`. References are now valid.

### ✅ 32. README Claims "64 tests" But May Be Inaccurate
- **Fix:** Changed to "comprehensive test suite" and "All tests" (dynamic wording). Current count: 98 tests.

### ✅ 33. Architecture Diagram Shows 4 Parallel Agents, But README Says "6 AI Agents"
- **Fix:** Updated intro to clarify: "1 Lead Analyst (3 roles), 4 specialists, 1 Fact Checker".

### ✅ 34. `docs/architecture.md` Exists But Not Cross-Referenced
- **Fix:** Added link: `> See [docs/architecture.md](docs/architecture.md) for detailed documentation.`

### ✅ 35. No CHANGELOG or Release Notes
- **Fix:** Created `CHANGELOG.md` following Keep a Changelog format.

### ✅ 36. No LICENSE File
- **Fix:** Created `LICENSE` (MIT license).

---

## 🧪 Testing Gaps

### ✅ 37. No Integration Tests
- **Fix:** Created `tests/test_integration.py` — tests graph compilation, node presence, pipeline return type, and state initialization.

### ✅ 38. No Tests for Agent Functions
- **Fix:** Created `tests/test_agents.py` — tests all 4 specialist agents with mocked LLM and search.

### ⏳ 39. No Tests for `app.py` (Streamlit UI)
- **Status:** Requires `streamlit.testing` framework. Deferred — would need significant refactoring to extract testable logic.

### ✅ 40. No Tests for `run_eval.py` Evaluation Framework
- **Fix:** Created `tests/test_evaluation.py` — tests all 4 evaluation metric functions.

### ✅ 41. No Tests for `llm.py` Token Tracking and Retry Logic
- **Fix:** Created `tests/test_llm.py` — tests TokenTracker (including thread safety), provider factory, and fallback.

---

## 🏗️ Architecture Improvements

### 🔧 42. Self-Correction Loop Is Configured But Not Implemented
- **Fix:** Set `enable_self_correction: false` in config. Removed false claim from graph docstring. Feature documented as "not yet implemented".

### 🔧 43. `max_fact_check_depth` Is Configured But Never Used
- **Fix:** Set to `1` (actual behavior) and documented as "multi-pass not yet implemented".

### 🔧 44. `max_retries_per_agent` Is Configured But Never Used
- **Fix:** Clarified config comment: "Agent-level retry count (LLM retries are separate)".

### 🔧 45. `timeout_per_agent_seconds` Is Configured But Never Enforced
- **Status:** Config documented accurately. Full implementation would require `concurrent.futures` wrapper.

### ⏳ 46. No Async/Concurrent Agent Execution
- **Status:** Deferred. LangGraph's `Send()` provides parallelism via internal threading. True async would be a major refactor.

### ✅ 47. Global Token Tracker Doesn't Reset Between Pipeline Runs
- **Fix:** Added `token_tracker.reset()` at the start of `run_pipeline()` and added `reset()` method to `TokenTracker`.

### ⏳ 48. No Analysis Caching (Repeated Queries Re-Run Full Pipeline)
- **Status:** Deferred. Would require significant infrastructure (cache key = company + depth + date).

### ✅ 49. No Proper Error Hierarchy / Custom Exceptions
- **Fix:** Created `src/exceptions.py` with custom exception classes: `BudgetExceededError`, `AgentTimeoutError`, `APIKeyMissingError`, `SearchError`, `RateLimitError`, `GuardrailViolationError`, `LoopDetectedError`.

### 🔧 50. `hallucination_check_enabled` Config Is Never Implemented
- **Fix:** Set to `false` in config. Documented as "Not yet implemented (use source_grounding_required)".

---

## Summary

| Category | Total | ✅ Fixed | 🔧 Partially | ⏳ Deferred |
|----------|-------|---------|--------------|-------------|
| 🔴 Critical | 4 | 4 | 0 | 0 |
| 🟠 High Priority | 6 | 6 | 0 | 0 |
| 🟡 Medium | 10 | 10 | 0 | 0 |
| 🔵 Low Priority | 10 | 9 | 0 | 1 |
| 📝 Documentation | 6 | 6 | 0 | 0 |
| 🧪 Testing | 5 | 4 | 0 | 1 |
| 🏗️ Architecture | 9 | 2 | 4 | 3 |
| **TOTAL** | **50** | **41** | **4** | **5** |

*Last updated: May 27, 2026*
