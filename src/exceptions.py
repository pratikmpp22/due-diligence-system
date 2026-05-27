"""
Custom exception hierarchy for the due diligence pipeline.

Enables precise error handling and recovery instead of catching generic Exception.
"""


class DueDiligenceError(Exception):
    """Base exception for all due diligence pipeline errors."""
    pass


class BudgetExceededError(DueDiligenceError):
    """Raised when token or cost budget limits are exceeded."""
    def __init__(self, budget_type: str, limit: float, actual: float):
        self.budget_type = budget_type
        self.limit = limit
        self.actual = actual
        super().__init__(
            f"{budget_type} budget exceeded: {actual:.4f} > {limit:.4f}"
        )


class AgentTimeoutError(DueDiligenceError):
    """Raised when an agent exceeds its execution time limit."""
    def __init__(self, agent_name: str, timeout_seconds: float):
        self.agent_name = agent_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Agent '{agent_name}' timed out after {timeout_seconds:.1f}s"
        )


class APIKeyMissingError(DueDiligenceError):
    """Raised when a required API key is not set."""
    def __init__(self, key_name: str, help_url: str = ""):
        self.key_name = key_name
        msg = f"Required API key not set: {key_name}"
        if help_url:
            msg += f" — Get one at {help_url}"
        super().__init__(msg)


class SearchError(DueDiligenceError):
    """Raised when all search providers fail."""
    def __init__(self, query: str, providers_tried: list[str]):
        self.query = query
        self.providers_tried = providers_tried
        super().__init__(
            f"All search providers failed for query '{query[:80]}...': "
            f"tried {', '.join(providers_tried)}"
        )


class RateLimitError(DueDiligenceError):
    """Raised when LLM API rate limits are hit after all retries."""
    def __init__(self, provider: str, retry_count: int):
        self.provider = provider
        self.retry_count = retry_count
        super().__init__(
            f"Rate limited by {provider} after {retry_count} retries"
        )


class GuardrailViolationError(DueDiligenceError):
    """Raised when a guardrail check blocks execution."""
    def __init__(self, guardrail_name: str, reason: str):
        self.guardrail_name = guardrail_name
        self.reason = reason
        super().__init__(f"Guardrail '{guardrail_name}' violation: {reason}")


class LoopDetectedError(DueDiligenceError):
    """Raised when an agent reasoning loop is detected."""
    def __init__(self, agent_name: str, iteration_count: int):
        self.agent_name = agent_name
        self.iteration_count = iteration_count
        super().__init__(
            f"Loop detected in agent '{agent_name}' after {iteration_count} iterations"
        )
