from typing import Any
from .helpers import *


def build_text_report(compare_result: dict[str, Any]) -> str:
    text, total, results, pairwise = extract_compare_payload(compare_result)

    lines: list[str] = []
    append = lines.append

    append(hr("="))
    append("TOKENIZER COMPARISON REPORT".center(REPORT_WIDTH))
    append(hr("="))
    append(f"Generated At (UTC): {utc_now_iso()}")
    append("")

    append("SOURCE TEXT")
    append(hr("-"))
    append(text if text else "No source text provided.")
    append("")

    append("SUMMARY")
    append(hr("-"))
    append(f"Total Tokenizers: {total}")
    append(f"Results: {len(results)}")
    append("")

    if results:
        append("DETAILS")
        append(hr("-"))

        for r in results:
            append(r.get("tokenizer_name", "-"))
            append(f"Tokens: {truncate_list(r.get('tokens', []))}")
            append(hr("-"))

    return "\n".join(lines)