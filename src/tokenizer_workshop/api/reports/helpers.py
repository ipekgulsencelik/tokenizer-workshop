from datetime import datetime, timezone
from typing import Any

REPORT_WIDTH = 88


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_str(value: Any, fallback: str = "-") -> str:
    if value is None:
        return fallback
    return str(value)


def truncate_list(items: list[Any], max_items: int = 20) -> str:
    if not items:
        return "[]"

    if len(items) <= max_items:
        return str(items)

    visible = items[:max_items]
    remaining = len(items) - max_items
    return f"{visible} ... (+{remaining} more)"


def format_number(value: Any, digits: int = 2) -> str:
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return "-"


def hr(char: str = "=") -> str:
    return char * REPORT_WIDTH


def extract_compare_payload(compare_result: dict[str, Any]):
    text = safe_str(compare_result.get("text", ""), "")
    total = int(compare_result.get("total_tokenizers") or 0)

    results = compare_result.get("results") or []
    if not isinstance(results, list):
        results = []

    pairwise = compare_result.get("pairwise_comparisons") or []
    if not isinstance(pairwise, list):
        pairwise = []

    return text, total, results, pairwise