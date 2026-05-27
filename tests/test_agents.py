"""
Tests for individual agent functions with mocked LLM and search.

Uses mocked dependencies to test agent logic without real API calls.
Fixes Issue #38.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.models.state import default_state


# -----------------------------------------------------------------------
# Helper: Create a mock search result
# -----------------------------------------------------------------------

class MockSearchResult:
    def __init__(self, url="https://example.com", title="Test", snippet="Content"):
        self.url = url
        self.title = title
        self.snippet = snippet


def _mock_search_results(count=3):
    return [MockSearchResult(url=f"https://src{i}.com", title=f"Title {i}", snippet=f"Snippet {i}") for i in range(count)]


# -----------------------------------------------------------------------
# Financial Analyst
# -----------------------------------------------------------------------

class TestFinancialAnalyst:
    @patch("src.agents.financial_analyst.invoke_with_tracking")
    @patch("src.agents.financial_analyst.WebSearchTool")
    def test_returns_findings_and_trace(self, mock_search_cls, mock_invoke):
        from src.models.schemas import FinancialAnalysis, FinancialMetric

        mock_search = MagicMock()
        mock_search.search.return_value = _mock_search_results()
        mock_search_cls.return_value = mock_search

        mock_invoke.return_value = FinancialAnalysis(
            company_name="TestCo",
            financial_health_rating="moderate",
            key_metrics=[],
            red_flags=["High burn rate"],
            green_flags=["Growing revenue"],
            sources=["https://src0.com"],
        )

        from src.agents.financial_analyst import financial_analyst
        state = default_state("TestCo")
        result = financial_analyst(state)

        assert "financial_findings" in result
        assert "pipeline_trace" in result
        assert len(result["financial_findings"]) > 0
        assert result["pipeline_trace"][0]["agent"] == "financial_analyst"

    @patch("src.agents.financial_analyst.WebSearchTool")
    def test_fallback_on_no_results(self, mock_search_cls):
        mock_search = MagicMock()
        mock_search.search.return_value = []
        mock_search_cls.return_value = mock_search

        from src.agents.financial_analyst import financial_analyst
        state = default_state("TestCo")
        result = financial_analyst(state)

        assert "financial_findings" in result
        assert any("incomplete" in f.get("title", "").lower() for f in result["financial_findings"])


# -----------------------------------------------------------------------
# News & Sentiment
# -----------------------------------------------------------------------

class TestNewsSentiment:
    @patch("src.agents.news_sentiment.invoke_with_tracking")
    @patch("src.agents.news_sentiment.WebSearchTool")
    def test_returns_findings(self, mock_search_cls, mock_invoke):
        from src.models.schemas import NewsSentimentAnalysis

        mock_search = MagicMock()
        mock_search.search.return_value = _mock_search_results()
        mock_search_cls.return_value = mock_search

        mock_invoke.return_value = NewsSentimentAnalysis(
            company_name="TestCo",
            overall_sentiment="positive",
            sentiment_trend="improving",
            key_events=[],
            sources=["https://src0.com"],
        )

        from src.agents.news_sentiment import news_sentiment
        state = default_state("TestCo")
        result = news_sentiment(state)

        assert "news_findings" in result
        assert "pipeline_trace" in result


# -----------------------------------------------------------------------
# Competitive Intel
# -----------------------------------------------------------------------

class TestCompetitiveIntel:
    @patch("src.agents.competitive_intel.invoke_with_tracking")
    @patch("src.agents.competitive_intel.WebSearchTool")
    def test_returns_findings(self, mock_search_cls, mock_invoke):
        from src.models.schemas import CompetitiveAnalysis

        mock_search = MagicMock()
        mock_search.search.return_value = _mock_search_results()
        mock_search_cls.return_value = mock_search

        mock_invoke.return_value = CompetitiveAnalysis(
            company_name="TestCo",
            industry="Technology",
            market_position="Leader",
            competitors=[],
            sources=["https://src0.com"],
        )

        from src.agents.competitive_intel import competitive_intel
        state = default_state("TestCo")
        result = competitive_intel(state)

        assert "competitive_findings" in result
        assert "pipeline_trace" in result


# -----------------------------------------------------------------------
# Risk Assessor
# -----------------------------------------------------------------------

class TestRiskAssessor:
    @patch("src.agents.risk_assessor.invoke_with_tracking")
    @patch("src.agents.risk_assessor.WebSearchTool")
    def test_returns_findings(self, mock_search_cls, mock_invoke):
        from src.models.schemas import RiskAssessment

        mock_search = MagicMock()
        mock_search.search.return_value = _mock_search_results()
        mock_search_cls.return_value = mock_search

        mock_invoke.return_value = RiskAssessment(
            company_name="TestCo",
            overall_risk_level="moderate",
            risks=[],
            risk_summary="Some risks identified",
            sources=["https://src0.com"],
        )

        from src.agents.risk_assessor import risk_assessor
        state = default_state("TestCo")
        result = risk_assessor(state)

        assert "risk_findings" in result
        assert "pipeline_trace" in result


# -----------------------------------------------------------------------
# Exception Handling
# -----------------------------------------------------------------------

class TestAgentExceptionHandling:
    @patch("src.agents.financial_analyst.invoke_with_tracking")
    @patch("src.agents.financial_analyst.WebSearchTool")
    def test_fallback_on_llm_error(self, mock_search_cls, mock_invoke):
        mock_search = MagicMock()
        mock_search.search.return_value = _mock_search_results()
        mock_search_cls.return_value = mock_search

        mock_invoke.side_effect = Exception("LLM error")

        from src.agents.financial_analyst import financial_analyst
        state = default_state("TestCo")
        result = financial_analyst(state)

        # Should still return a result (fallback)
        assert "financial_findings" in result
        assert "errors" in result
