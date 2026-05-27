"""
Shared utility functions for agents.

Avoids code duplication across specialist agent modules.
"""

from __future__ import annotations

from datetime import datetime


def build_search_context(results: list) -> str:
    """Build a formatted context string from search results.

    Deduplicates by URL and caps at 15 unique results.

    Args:
        results: List of SearchResult objects.

    Returns:
        Formatted string of search results for LLM prompt context.
    """
    lines = []
    seen_urls = set()
    for r in results:
        if r.url in seen_urls:
            continue
        seen_urls.add(r.url)
        lines.append(f"Source: {r.url}\nTitle: {r.title}\nContent: {r.snippet}\n")
    return "\n---\n".join(lines[:15])  # Cap at 15 unique results


def get_current_year_range() -> str:
    """Return a year range string for search queries (current and previous year).

    Returns:
        e.g., '2025 2026' if current year is 2026.
    """
    current_year = datetime.now().year
    return f"{current_year - 1} {current_year}"
