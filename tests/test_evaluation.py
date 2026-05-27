"""
Tests for the evaluation framework functions.

Tests the metric calculation functions independently of the full pipeline.
Fixes Issue #40.
"""

import pytest
from evaluation.run_eval import (
    evaluate_coverage,
    evaluate_source_diversity,
    evaluate_factual_consistency,
    evaluate_actionability,
)


# -----------------------------------------------------------------------
# evaluate_coverage
# -----------------------------------------------------------------------

class TestEvaluateCoverage:
    def test_full_coverage(self):
        result = {
            "financial_findings": [{"title": "f1"}],
            "news_findings": [{"title": "n1"}],
            "competitive_findings": [{"title": "c1"}],
            "risk_findings": [{"title": "r1"}],
            "fact_check_results": [{"total_checked": 5}],
        }
        out = evaluate_coverage(result)
        assert out["score"] == 1.0
        assert out["covered"] == 5
        assert out["total"] == 5

    def test_partial_coverage(self):
        result = {
            "financial_findings": [{"title": "f1"}],
            "news_findings": [],
            "competitive_findings": [],
            "risk_findings": [{"title": "r1"}],
            "fact_check_results": [],
        }
        out = evaluate_coverage(result)
        assert out["score"] == 2 / 5
        assert out["covered"] == 2

    def test_empty_result(self):
        out = evaluate_coverage({})
        assert out["score"] == 0.0
        assert out["covered"] == 0


# -----------------------------------------------------------------------
# evaluate_source_diversity
# -----------------------------------------------------------------------

class TestEvaluateSourceDiversity:
    def test_high_diversity(self):
        result = {
            "financial_findings": [
                {"sources": [f"https://source{i}.com" for i in range(10)]}
            ],
            "news_findings": [
                {"sources": [f"https://news{i}.com" for i in range(6)]}
            ],
            "competitive_findings": [],
            "risk_findings": [],
        }
        out = evaluate_source_diversity(result)
        assert out["unique_sources"] == 16
        assert out["score"] == 1.0  # Capped at 1.0

    def test_no_sources(self):
        out = evaluate_source_diversity({})
        assert out["unique_sources"] == 0
        assert out["score"] == 0.0

    def test_duplicate_sources_deduped(self):
        result = {
            "financial_findings": [{"sources": ["https://a.com", "https://a.com"]}],
            "news_findings": [{"sources": ["https://a.com"]}],
            "competitive_findings": [],
            "risk_findings": [],
        }
        out = evaluate_source_diversity(result)
        assert out["unique_sources"] == 1


# -----------------------------------------------------------------------
# evaluate_factual_consistency
# -----------------------------------------------------------------------

class TestEvaluateFactualConsistency:
    def test_high_consistency(self):
        result = {"fact_check_results": [{"total_checked": 10, "verified": 9, "contradicted": 1}]}
        out = evaluate_factual_consistency(result)
        assert out["score"] > 0.8

    def test_no_checks(self):
        result = {"fact_check_results": [{}]}
        out = evaluate_factual_consistency(result)
        assert out["score"] == 0.5  # Default when no claims checked

    def test_empty(self):
        out = evaluate_factual_consistency({})
        assert out["score"] == 0.5


# -----------------------------------------------------------------------
# evaluate_actionability
# -----------------------------------------------------------------------

class TestEvaluateActionability:
    def test_fully_actionable(self):
        result = {
            "executive_summary": "Tesla is a strong company.",
            "overall_risk_rating": "moderate",
            "final_report": "## Next Steps\nBased on data gaps and uncertain regulatory environment, we recommend...",
        }
        out = evaluate_actionability(result)
        assert out["score"] == 1.0

    def test_no_actionability(self):
        result = {
            "executive_summary": "",
            "overall_risk_rating": "unknown",
            "final_report": "",
        }
        out = evaluate_actionability(result)
        assert out["score"] == 0.0

    def test_partial(self):
        result = {
            "executive_summary": "Company is fine.",
            "overall_risk_rating": "low",
            "final_report": "No further details.",
        }
        out = evaluate_actionability(result)
        assert 0.0 < out["score"] < 1.0
