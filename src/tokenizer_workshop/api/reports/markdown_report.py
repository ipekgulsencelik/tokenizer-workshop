from typing import Any

from .helpers import (
    extract_compare_payload,
    format_number,
    format_reconstruction,
    format_top_tokens,
    get_metric,
    get_metrics,
    latency_microseconds,
    safe_str,
    truncate_list,
    utc_now_iso,
)


def build_markdown_report(compare_result: dict[str, Any]) -> str:
    text, total, results, pairwise = extract_compare_payload(compare_result)

    lines: list[str] = []
    append = lines.append

    append("# Tokenizer Evaluation Report")
    append("")
    append(f"**Generated At (UTC):** {utc_now_iso()}")
    append("")

    append("## Source Text")
    append("")
    if text:
        append("```text")
        append(text)
        append("```")
    else:
        append("_No source text provided._")
    append("")

    append("## Overview")
    append("")
    append("This report evaluates multiple tokenization strategies applied to the same input text.")
    append("It analyzes segmentation granularity, token diversity, computational efficiency, and structural overlap.")
    append("")

    append("## Summary Table")
    append("")
    append("| Tokenizer | Tokens | Unique | Uniq Ratio | Avg Len | Chars/Token | Latency µs | Eff. Score | Comp. |")
    append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    for item in results:
        metrics = get_metrics(item)

        append(
            f"| {safe_str(item.get('tokenizer_name'))} "
            f"| {metrics.get('token_count', item.get('token_count', 0))} "
            f"| {metrics.get('unique_token_count', item.get('vocab_size', 0))} "
            f"| {format_number(metrics.get('unique_ratio'), 2)} "
            f"| {format_number(metrics.get('average_token_length'), 2)} "
            f"| {format_number(metrics.get('avg_chars_per_token'), 2)} "
            f"| {latency_microseconds(metrics)} "
            f"| {format_number(metrics.get('efficiency_score'), 2)} "
            f"| {format_number(metrics.get('compression_ratio'), 2)} |"
        )
    append("")

    append("## Key Insights")
    append("")

    if not results:
        append("_No insights available._")
        append("")
    else:
        lowest_token = min(results, key=lambda item: item.get("token_count", 0))
        highest_token = max(results, key=lambda item: item.get("token_count", 0))
        highest_vocab = max(results, key=lambda item: item.get("vocab_size", 0))
        best_efficiency = max(
            results,
            key=lambda item: get_metrics(item).get("efficiency_score", 0),
        )
        best_compression = max(
            results,
            key=lambda item: get_metrics(item).get("compression_ratio", 0),
        )
        fastest = min(
            results,
            key=lambda item: get_metrics(item).get("latency_seconds", float("inf")),
        )

        append(
            f"- **Lowest token count:** {safe_str(lowest_token.get('tokenizer_name'))} "
            f"({lowest_token.get('token_count', 0)})"
        )
        append(
            f"- **Highest token count:** {safe_str(highest_token.get('tokenizer_name'))} "
            f"({highest_token.get('token_count', 0)})"
        )
        append(
            f"- **Best efficiency score:** {safe_str(best_efficiency.get('tokenizer_name'))} "
            f"({format_number(get_metric(best_efficiency, 'efficiency_score'), 2)})"
        )
        append(
            f"- **Highest unique token count:** {safe_str(highest_vocab.get('tokenizer_name'))} "
            f"({highest_vocab.get('vocab_size', 0)})"
        )
        append(
            f"- **Fastest tokenizer:** {safe_str(fastest.get('tokenizer_name'))} "
            f"({latency_microseconds(get_metrics(fastest))} µs)"
        )
        append(
            f"- **Best compression ratio:** {safe_str(best_compression.get('tokenizer_name'))} "
            f"({format_number(get_metric(best_compression, 'compression_ratio'), 2)})"
        )
        append("")

    append("## Interpretation")
    append("")

    if not results:
        append("_No interpretation available._")
        append("")
    else:
        lowest_token = min(results, key=lambda item: item.get("token_count", 0))
        highest_token = max(results, key=lambda item: item.get("token_count", 0))
        best_efficiency = max(
            results,
            key=lambda item: get_metrics(item).get("efficiency_score", 0),
        )
        fastest = min(
            results,
            key=lambda item: get_metrics(item).get("latency_seconds", float("inf")),
        )

        append(
            f"The **{safe_str(lowest_token.get('tokenizer_name'))}** tokenizer produces the most compact segmentation "
            f"with **{lowest_token.get('token_count', 0)} tokens**."
        )
        append("")
        append(
            f"The **{safe_str(highest_token.get('tokenizer_name'))}** tokenizer produces the most granular segmentation "
            f"with **{highest_token.get('token_count', 0)} tokens**."
        )
        append("")
        append(
            f"The **{safe_str(best_efficiency.get('tokenizer_name'))}** tokenizer achieves the best efficiency score "
            f"(**{format_number(get_metric(best_efficiency, 'efficiency_score'), 2)}**), indicating stronger compression per token."
        )
        append("")
        append(
            f"The fastest tokenizer is **{safe_str(fastest.get('tokenizer_name'))}** "
            f"with **{latency_microseconds(get_metrics(fastest))} µs** latency."
        )
        append("")
        append(
            "Overall, tokenizer choice directly affects input length, processing cost, semantic granularity, "
            "and downstream model efficiency."
        )
        append("")

    append("## Tokenizer Details")
    append("")

    if not results:
        append("_No tokenizer details available._")
        append("")
    else:
        for index, item in enumerate(results, start=1):
            tokenizer_name = safe_str(item.get("tokenizer_name"))
            token_count = item.get("token_count", 0)
            vocab_size = item.get("vocab_size", 0)
            tokens = item.get("tokens", [])
            metrics = get_metrics(item)

            append(f"### {index}. {tokenizer_name}")
            append("")
            append(f"- **Token Count:** {token_count}")
            append(f"- **Vocab Size:** {vocab_size}")
            append(f"- **Tokens:** `{truncate_list(tokens)}`")

            if metrics:
                append(f"- **Unique Token Count:** {metrics.get('unique_token_count', '-')}")
                append(f"- **Unique Ratio:** {format_number(metrics.get('unique_ratio'), 2)}")
                append(f"- **Average Token Length:** {format_number(metrics.get('average_token_length'), 2)}")
                append(f"- **Min / Max Token Length:** {metrics.get('min_token_length', '-')} / {metrics.get('max_token_length', '-')}")
                append(f"- **Avg Chars / Token:** {format_number(metrics.get('avg_chars_per_token'), 2)}")
                append(f"- **Unknown Tokens:** {metrics.get('unknown_count', '-')} ({format_number(metrics.get('unknown_rate'), 2)})")
                append(f"- **Latency:** {latency_microseconds(metrics)} µs ({format_number(metrics.get('latency_seconds'), 6)} s)")
                append(f"- **Latency / Token:** {format_number(metrics.get('latency_per_token'), 6)}")
                append(f"- **Efficiency Score:** {format_number(metrics.get('efficiency_score'), 2)}")
                append(f"- **Compression Ratio:** {format_number(metrics.get('compression_ratio'), 2)}")

                top_tokens = format_top_tokens(metrics.get("top_tokens"))
                if top_tokens:
                    append("")
                    append("**Top Tokens:**")
                    for token_line in top_tokens:
                        append(f"- `{token_line.strip()}`")

                token_length_distribution = metrics.get("token_length_distribution")
                if isinstance(token_length_distribution, dict):
                    append("")
                    append("**Token Length Distribution:**")
                    for length, count in sorted(token_length_distribution.items()):
                        append(f"- Length `{length}`: `{count}` tokens")

                reconstruction = format_reconstruction(metrics)
                if reconstruction:
                    append("")
                    append("**Reconstruction:**")
                    for line in reconstruction:
                        append(f"- {line.strip()}")

            append("")

    append("## Overall Ranking")
    append("")

    ranked = sorted(
        results,
        key=lambda item: (
            get_metrics(item).get("efficiency_score", 0),
            -get_metrics(item).get("latency_seconds", float("inf")),
        ),
        reverse=True,
    )

    if not ranked:
        append("_No ranking available._")
        append("")
    else:
        append("Ranking is based on efficiency score and latency.")
        append("")
        for index, item in enumerate(ranked, start=1):
            metrics = get_metrics(item)
            append(
                f"{index}. **{safe_str(item.get('tokenizer_name'))}** "
                f"(eff={format_number(metrics.get('efficiency_score'), 2)}, "
                f"latency={latency_microseconds(metrics)} µs)"
            )
        append("")

    if pairwise:
        append("## Pairwise Comparisons")
        append("")

        for item in pairwise:
            left_name = safe_str(item.get("left_name"))
            right_name = safe_str(item.get("right_name"))
            ratio = item.get("overlap_ratio")

            append(f"### {left_name} ↔ {right_name}")
            append("")
            append(f"- **Overlap Ratio:** {format_number(ratio, 2)}")
            append(f"- **Common Tokens:** `{truncate_list(item.get('common_tokens', []))}`")
            append(f"- **Only In {left_name}:** `{truncate_list(item.get('unique_to_left', []))}`")
            append(f"- **Only In {right_name}:** `{truncate_list(item.get('unique_to_right', []))}`")
            append("- **Observation:**")

            if isinstance(ratio, (int, float)):
                if ratio == 0:
                    append("  - No shared tokens were found, indicating completely different tokenization strategies.")
                elif ratio < 0.25:
                    append("  - Minimal overlap exists; tokenization strategies differ significantly.")
                elif ratio < 0.6:
                    append("  - Moderate overlap suggests partial similarity in segmentation.")
                else:
                    append("  - High overlap indicates similar tokenization behavior.")
            else:
                append("  - No observation available.")

            append("")

    return "\n".join(lines)