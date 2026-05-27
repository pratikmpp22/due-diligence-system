"""
Streamlit UI for the Due Diligence Agent.

Launch with: streamlit run app.py

Features:
- Company input with analysis depth selection
- Real-time pipeline progress with agent status indicators
- Interactive report viewer with collapsible sections
- Budget and cost tracking dashboard
- Pipeline execution trace visualization
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

# Load .env file if present (users can copy .env.example to .env)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import streamlit as st

# Must be first Streamlit call
st.set_page_config(
    page_title="Due Diligence Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.agents.graph import run_pipeline, build_graph
from src.guardrails.manager import GuardrailManager
from src.llm import token_tracker
from src.config import load_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

def init_session():
    if "result" not in st.session_state:
        st.session_state.result = None
    if "running" not in st.session_state:
        st.session_state.running = False
    if "history" not in st.session_state:
        st.session_state.history = []


init_session()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("Configuration")

    # API Key input
    api_key = st.text_input(
        "Google API Key",
        type="password",
        help="Get a free key at https://aistudio.google.com/apikey",
    )
    if api_key:
        import os
        os.environ["GOOGLE_API_KEY"] = api_key

    tavily_key = st.text_input(
        "Tavily API Key (optional)",
        type="password",
        help="Get a free key at https://tavily.com. Falls back to DuckDuckGo if not set.",
    )
    if tavily_key:
        import os
        os.environ["TAVILY_API_KEY"] = tavily_key

    groq_key = st.text_input(
        "Groq API Key (optional)",
        type="password",
        help="Get an API key at https://console.groq.com/",
    )
    if groq_key:
        import os
        os.environ["GROQ_API_KEY"] = groq_key

    st.divider()

    # Model Settings
    st.subheader("Model Settings")
    provider_options = ["google", "openai", "groq", "ollama"]
    selected_provider = st.selectbox(
        "Model Provider",
        provider_options,
        index=0,
        help="Choose the active LLM provider."
    )
    
    model_defaults = {
        "google": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        "groq": ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "llama3-8b-8192"],
        "ollama": ["llama3", "mistral", "phi3"]
    }
    
    selected_model = st.selectbox(
        "Model Name",
        model_defaults[selected_provider],
        index=0,
        help="Select the specific model to use."
    )

    st.divider()

    # Budget controls
    st.subheader("Budget Limits")
    max_cost = st.slider("Max cost (USD)", 0.10, 2.00, 0.50, 0.10)
    max_tokens = st.slider("Max tokens (K)", 10, 200, 100, 10)

    st.divider()

    # Analysis history
    st.subheader("History")
    for item in reversed(st.session_state.history[-5:]):
        risk = item.get("risk", "?")
        color = {"low": "green", "moderate": "orange", "high": "red", "critical": "red"}.get(risk, "gray")
        st.markdown(f":{color}[{risk.upper()}] **{item['company']}** - {item.get('duration', '?')}s")


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------

st.title("Multi-Agent Due Diligence Analyst")
st.markdown("*Enterprise-grade company research powered by 6 AI agents with fact-checking and contradiction resolution.*")

# Input form
col1, col2 = st.columns([3, 1])
with col1:
    company_name = st.text_input(
        "Company / Entity Name",
        placeholder="e.g., Tesla, Stripe, Databricks...",
    )
with col2:
    depth = st.selectbox(
        "Analysis Depth",
        ["quick", "standard", "deep"],
        index=1,
        help="Quick: ~1 min, Standard: ~2-3 min, Deep: ~5 min",
    )

query = st.text_area(
    "Specific Focus (optional)",
    placeholder="e.g., Focus on AI safety risks and competition with Google...",
    height=68,
)

# Run button
run_clicked = st.button(
    "Run Due Diligence Analysis",
    type="primary",
    disabled=st.session_state.running or not company_name,
    use_container_width=True,
)

if run_clicked and company_name:
    st.session_state.running = True
    st.session_state.result = None

    # Progress indicators
    progress_bar = st.progress(0, text="Initializing pipeline...")
    status_container = st.container()

    agent_stages = [
        ("Planning research...", 0.05),
        ("Financial analysis...", 0.20),
        ("News & sentiment analysis...", 0.35),
        ("Competitive intelligence...", 0.50),
        ("Risk assessment...", 0.65),
        ("Fact-checking claims...", 0.80),
        ("Resolving contradictions...", 0.90),
        ("Synthesizing report...", 0.95),
    ]

    try:
        # Run the pipeline
        guardrail_mgr = GuardrailManager()

        # Update budget config before guardrail reads it
        from src.config import load_config, reset_config
        import os
        os.environ["DD_MODEL_PROVIDER"] = selected_provider
        os.environ["DD_MODEL_NAME"] = selected_model

        reset_config()          # Clear cache so GuardrailManager reads fresh values
        config = load_config()
        config.setdefault("budget", {})["max_cost_usd"] = max_cost
        config.setdefault("budget", {})["max_total_tokens"] = max_tokens * 1000

        guardrail_mgr.start_pipeline()

        # Show agent pipeline visually
        with status_container:
            agent_cols = st.columns(6)
            agent_labels = ["Financial", "News", "Competitive", "Risk", "Fact-Check", "Synthesis"]
            agent_placeholders = []
            for i, (col, label) in enumerate(zip(agent_cols, agent_labels)):
                with col:
                    ph = st.empty()
                    ph.markdown(f"**{label}**\n\n:gray[Waiting...]")
                    agent_placeholders.append(ph)

        # Run pipeline with streaming
        generator = run_pipeline(
            company_name=company_name,
            query=query,
            depth=depth,
            guardrail_mgr=guardrail_mgr,
            stream=True,
        )

        agent_map = {
            "financial_analyst": (0, "Financial", 0.30),
            "news_sentiment": (1, "News", 0.45),
            "competitive_intel": (2, "Competitive", 0.60),
            "risk_assessor": (3, "Risk", 0.70),
            "fact_checker": (4, "Fact-Check", 0.85),
            "synthesize_report": (5, "Synthesis", 0.95),
        }

        latest_state = None
        
        for update in generator:
            if update["type"] == "update":
                latest_state = update["data"]
                
                # Check traces to see which agents have finished
                traces = latest_state.get("pipeline_trace", [])
                
                for agent_key, (idx, label, pct) in agent_map.items():
                    # Find if this agent has a trace
                    agent_trace = next((t for t in traces if t.get("agent") == agent_key or str(t.get("agent")).startswith(agent_key)), None)
                    
                    if agent_trace:
                        progress_bar.progress(pct, text=f"Finished {label} analysis...")
                        ph = agent_placeholders[idx]
                        if agent_trace.get("error"):
                            ph.markdown(f"**{agent_labels[idx]}**\n\n:red[Error]")
                        else:
                            dur = agent_trace.get("duration_seconds", 0)
                            ph.markdown(f"**{agent_labels[idx]}**\n\n:green[Done] {dur:.1f}s")
                            
            elif update["type"] == "complete":
                if latest_state:
                    latest_state["total_tokens_used"] = update.get("tokens", {}).get("total_tokens", 0)
                    latest_state["total_cost_usd"] = update.get("tokens", {}).get("estimated_cost_usd", 0)
                    latest_state["_execution_time_seconds"] = update.get("elapsed", 0)
                    latest_state["_budget_status"] = update.get("budget", {})
                    latest_state["_token_summary"] = update.get("tokens", {})
                    
            elif update["type"] == "error":
                raise Exception(update.get("error", "Unknown pipeline error"))

        result = latest_state or {}

        # Auto-save to artifacts/reports/
        if "final_report" in result and result["final_report"]:
            from datetime import datetime
            safe_name = company_name.replace(' ', '_').replace('/', '_')[:50]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            auto_path = Path("artifacts/reports") / f"{safe_name}_{timestamp}.md"
            auto_path.parent.mkdir(parents=True, exist_ok=True)
            auto_path.write_text(result["final_report"], encoding="utf-8")
            logger.info("Report auto-saved to %s", auto_path)

        progress_bar.progress(1.0, text="Analysis complete!")
        st.session_state.result = result
        st.session_state.running = False

        # Add to history
        st.session_state.history.append({
            "company": company_name,
            "risk": result.get("overall_risk_rating", "unknown"),
            "confidence": result.get("overall_confidence", 0),
            "duration": result.get("_execution_time_seconds", 0),
        })

    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.session_state.running = False
        logger.error("Pipeline error: %s", e, exc_info=True)

# ---------------------------------------------------------------------------
# Results Display
# ---------------------------------------------------------------------------

if st.session_state.result:
    result = st.session_state.result
    st.divider()

    # Executive Summary Card
    risk = result.get("overall_risk_rating", "unknown")
    confidence = result.get("overall_confidence", 0)
    risk_color = {"low": "green", "moderate": "orange", "high": "red", "critical": "red"}.get(risk, "gray")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Rating", risk.upper())
    col2.metric("Confidence", f"{confidence:.0%}")
    col3.metric("Duration", f"{result.get('_execution_time_seconds', 0):.1f}s")

    token_summary = result.get("_token_summary", {})
    col4.metric("Cost", f"${token_summary.get('estimated_cost_usd', 0):.4f}")

    exec_summary = result.get("executive_summary", "")
    if exec_summary:
        st.info(f"**Verdict:** {exec_summary}")

    # Tabbed report view
    tab_report, tab_findings, tab_trace, tab_raw = st.tabs(
        ["Full Report", "Findings by Agent", "Execution Trace", "Raw Data"]
    )

    with tab_report:
        report = result.get("final_report", "No report generated.")
        st.markdown(report)

        # Download button
        st.download_button(
            "Download Report (Markdown)",
            data=report,
            file_name=f"due_diligence_{company_name.lower().replace(' ', '_')}.md",
            mime="text/markdown",
        )

    with tab_findings:
        for category, key, title in [
            ("financial", "financial_findings", "Financial Analysis"),
            ("news", "news_findings", "News & Sentiment"),
            ("competitive", "competitive_findings", "Competitive Intelligence"),
            ("risk", "risk_findings", "Risk Assessment"),
        ]:
            findings = result.get(key, [])
            with st.expander(f"{title} ({len(findings)} findings)", expanded=False):
                for f in findings:
                    sev = f.get("severity", "info")
                    sev_icon = {"critical": "!!!", "high": "!!", "medium": "!", "low": "", "info": ""}.get(sev, "")
                    st.markdown(f"**{sev_icon} {f.get('title', 'Untitled')}**")
                    st.caption(f"Severity: {sev} | Confidence: {f.get('confidence', 0):.0%} | {'Verified' if f.get('verified') else 'Unverified'}")
                    st.write(f.get("detail", ""))
                    if f.get("sources"):
                        st.caption(f"Sources: {', '.join(f.get('sources', []))}")
                    st.divider()

        # Fact-check results
        fc = result.get("fact_check_results", [{}])
        if fc:
            fc_data = fc[0] if fc else {}
            with st.expander("Fact-Check Results", expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Checked", fc_data.get("total_checked", 0))
                c2.metric("Verified", fc_data.get("verified", 0))
                c3.metric("Contradicted", fc_data.get("contradicted", 0))
                c4.metric("Reliability", fc_data.get("overall_reliability", "?"))

    with tab_trace:
        traces = result.get("pipeline_trace", [])
        if traces:
            for t in traces:
                icon = "!!!" if t.get("error") else "OK"
                st.markdown(
                    f"**{t.get('agent', '?')}** - {t.get('action', '?')} "
                    f"({t.get('duration_seconds', 0):.1f}s) [{icon}]"
                )
                st.caption(t.get("summary", ""))
                if t.get("error"):
                    st.error(t["error"])

        # Budget status
        budget = result.get("_budget_status", {})
        if budget:
            st.subheader("Budget Usage")
            st.progress(min(budget.get("tokens_pct", 0) / 100, 1.0), text=f"Tokens: {budget.get('tokens_pct', 0):.1f}%")
            st.progress(min(budget.get("cost_pct", 0) / 100, 1.0), text=f"Cost: {budget.get('cost_pct', 0):.1f}%")

        # Errors and warnings
        errors = result.get("errors", [])
        warnings = result.get("warnings", [])
        if errors:
            st.subheader("Errors")
            for e in errors:
                st.error(e)
        if warnings:
            st.subheader("Warnings")
            for w in warnings:
                st.warning(w)

    with tab_raw:
        # Sanitize for JSON display (remove non-serializable types)
        raw = {}
        for k, v in result.items():
            try:
                json.dumps(v)
                raw[k] = v
            except (TypeError, ValueError):
                raw[k] = str(v)
        st.json(raw)
