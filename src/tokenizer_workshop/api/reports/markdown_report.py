from typing import Any
from .helpers import *


def build_markdown_report(compare_result: dict[str, Any]) -> str:
    text, total, results, pairwise = extract_compare_payload(compare_result)

    lines: list[str] = []
    append = lines.append

    append("# Tokenizer Comparison Report")
    append(f"**Generated:** {utc_now_iso()}")
    append("")

    append("## Source Text")
    append(f"```text\n{text}\n```" if text else "_No text_")
    append("")

    append("## Summary")
    append(f"- Total: {total}")
    append(f"- Results: {len(results)}")
    append("")

    if results:
        append("## Details")

        for r in results:
            append(f"### {r.get('tokenizer_name')}")
            append(f"- Tokens: `{truncate_list(r.get('tokens', []))}`")

    return "\n".join(lines)