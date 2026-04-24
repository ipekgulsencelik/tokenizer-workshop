from datetime import datetime, timezone
from typing import Any

REPORT_WIDTH = 88
REPORT_TABLE_WIDTH = 120


def wide_hr(char: str = "=") -> str:
    return char * REPORT_TABLE_WIDTH


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


def get_metrics(item: dict[str, Any]) -> dict[str, Any]:
    metrics = item.get("metrics")
    return metrics if isinstance(metrics, dict) else {}


def get_metric(item: dict[str, Any], key: str, fallback: Any = "-") -> Any:
    metrics = get_metrics(item)
    return metrics.get(key, fallback)


def latency_microseconds(metrics: dict[str, Any]) -> str:
    latency = metrics.get("latency_seconds")

    if isinstance(latency, (int, float)):
        return str(int(latency * 1_000_000))

    return "-"


def format_top_tokens(top_tokens: Any) -> list[str]:
    if not isinstance(top_tokens, list):
        return []

    formatted: list[str] = []

    for item in top_tokens[:5]:
        if isinstance(item, dict):
            token = item.get("token")
            count = item.get("count")
            formatted.append(f"  {token} → {count}")
        else:
            formatted.append(f"  {item}")

    return formatted


def format_reconstruction(metrics: dict[str, Any]) -> list[str]:
    reconstruction_match = metrics.get("reconstruction_match")
    reconstructed_text = metrics.get("reconstructed_text")

    if reconstruction_match is None and reconstructed_text is None:
        return []

    icon = "✔" if reconstruction_match else "✘"

    lines = [
        f"  Match: {icon} {reconstruction_match}",
    ]

    if reconstructed_text:
        lines.append(f'  Output: "{reconstructed_text}"')

    return lines


def append_section_title(lines: list[str], title: str) -> None:
    lines.append(title)
    lines.append(hr("-"))


def extract_compare_payload(compare_result: dict[str, Any]) -> tuple[str, int, list[dict[str, Any]], list[dict[str, Any]]]:
    text = safe_str(compare_result.get("text", ""), "")
    total = int(compare_result.get("total_tokenizers") or 0)

    results = compare_result.get("results") or []
    if not isinstance(results, list):
        results = []

    pairwise = compare_result.get("pairwise_comparisons") or []
    if not isinstance(pairwise, list):
        pairwise = []

    return text, total, results, pairwise