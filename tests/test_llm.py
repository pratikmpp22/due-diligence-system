"""
Tests for LLM token tracking, retry logic, and provider factory.

Fixes Issue #41.
"""

import pytest
import threading
from unittest.mock import patch, MagicMock

from src.llm import TokenTracker, get_llm, get_structured_llm


# -----------------------------------------------------------------------
# TokenTracker
# -----------------------------------------------------------------------

class TestTokenTracker:
    def test_initial_state(self):
        tracker = TokenTracker()
        assert tracker.total_tokens == 0
        assert tracker.total_calls == 0
        assert tracker.total_errors == 0

    def test_record_adds_tokens(self):
        tracker = TokenTracker()
        tracker.record(100, 50, "test_model", 1.5)
        assert tracker.total_input_tokens == 100
        assert tracker.total_output_tokens == 50
        assert tracker.total_tokens == 150
        assert tracker.total_calls == 1
        assert len(tracker.call_log) == 1

    def test_record_multiple(self):
        tracker = TokenTracker()
        tracker.record(100, 50, "m1", 1.0)
        tracker.record(200, 100, "m2", 2.0)
        assert tracker.total_input_tokens == 300
        assert tracker.total_output_tokens == 150
        assert tracker.total_calls == 2

    def test_record_error(self):
        tracker = TokenTracker()
        tracker.record_error()
        tracker.record_error()
        assert tracker.total_errors == 2

    def test_cost_estimate(self):
        tracker = TokenTracker()
        tracker.record(1000, 1000, "test", 1.0)
        cost = tracker.cost_estimate(input_rate=0.001, output_rate=0.002)
        assert cost == pytest.approx(0.003)

    def test_summary(self):
        tracker = TokenTracker()
        tracker.record(500, 200, "test", 1.0)
        tracker.record_error()
        summary = tracker.summary()
        assert summary["total_calls"] == 1
        assert summary["total_errors"] == 1
        assert summary["total_tokens"] == 700
        assert "estimated_cost_usd" in summary

    def test_reset(self):
        tracker = TokenTracker()
        tracker.record(100, 50, "test", 1.0)
        tracker.record_error()
        tracker.reset()
        assert tracker.total_tokens == 0
        assert tracker.total_calls == 0
        assert tracker.total_errors == 0
        assert tracker.call_log == []

    def test_snapshot(self):
        tracker = TokenTracker()
        tracker.record(100, 50, "test", 1.0)
        snap = tracker.snapshot()
        assert snap["total_input_tokens"] == 100
        assert snap["total_output_tokens"] == 50
        assert snap["total_tokens"] == 150

    def test_thread_safety(self):
        """Verify that concurrent record() calls don't corrupt state."""
        tracker = TokenTracker()
        num_threads = 10
        calls_per_thread = 100

        def _record():
            for _ in range(calls_per_thread):
                tracker.record(1, 1, "thread_test", 0.01)

        threads = [threading.Thread(target=_record) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = num_threads * calls_per_thread
        assert tracker.total_calls == expected
        assert tracker.total_input_tokens == expected
        assert tracker.total_output_tokens == expected


# -----------------------------------------------------------------------
# Provider Factory
# -----------------------------------------------------------------------

class TestGetLLM:
    @patch("src.llm.get_model_config")
    @patch("src.llm._PROVIDER_FACTORY")
    def test_default_provider(self, mock_factory, mock_config):
        mock_config.return_value = {"provider": "google", "name": "gemini-2.5-flash", "temperature": 0.1, "max_output_tokens": 4096}
        mock_fn = MagicMock(return_value=MagicMock())
        mock_factory.get.return_value = mock_fn
        mock_factory.keys.return_value = ["google", "openai", "ollama", "groq"]
        llm = get_llm()
        mock_fn.assert_called_once()

    @patch("src.llm.get_model_config")
    def test_unknown_provider_raises(self, mock_config):
        mock_config.return_value = {"provider": "unknown_provider", "name": "x", "temperature": 0.1, "max_output_tokens": 100}
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_llm()

    @patch("src.llm.get_model_config")
    @patch("src.llm._PROVIDER_FACTORY")
    def test_fallback_model(self, mock_factory, mock_config):
        mock_config.return_value = {
            "provider": "google", "name": "primary", "fallback_name": "fallback",
            "temperature": 0.1, "max_output_tokens": 4096,
        }
        mock_fn = MagicMock(side_effect=[Exception("Primary failed"), MagicMock()])
        mock_factory.get.return_value = mock_fn
        mock_factory.keys.return_value = ["google", "openai", "ollama", "groq"]
        llm = get_llm()
        assert mock_fn.call_count == 2

    @patch("src.llm.os.getenv")
    @patch("src.llm.get_model_config")
    @patch("langchain_groq.ChatGroq")
    def test_groq_provider_initialization(self, mock_chat_groq, mock_config, mock_getenv):
        mock_config.return_value = {
            "provider": "groq", "name": "gemini-2.5-flash",
            "temperature": 0.1, "max_output_tokens": 4096
        }
        mock_getenv.return_value = "fake_key"
        llm = get_llm()
        mock_chat_groq.assert_called_once_with(
            model="openai/gpt-oss-120b",
            groq_api_key="fake_key",
            temperature=0.1,
            max_tokens=4096
        )
