from typing import Any

from .helpers import (
    REPORT_WIDTH,
    append_section_title,
    extract_compare_payload,
    format_number,
    hr,
    safe_str,
    truncate_list,
    utc_now_iso,
    wide_hr,
    get_metrics,
    get_metric,
    latency_microseconds,
    format_top_tokens,
    format_reconstruction,
)


def build_text_report(compare_result: dict[str, Any]) -> str:
    text, total, results, pairwise = extract_compare_payload(compare_result)

    lines: list[str] = []
    append = lines.append

    append(wide_hr("="))
    append("TOKENIZER EVALUATION REPORT".center(120))
    append(wide_hr("="))
    append(f"Generated At (UTC): {utc_now_iso()}")
    append("")

    append_section_title(lines, "SOURCE TEXT")
    append(text if text else "No source text provided.")
    append("")

    append("OVERVIEW")
    append(wide_hr("-"))
    append("This report evaluates multiple tokenization strategies applied to the same input text.")
    append("It analyzes segmentation granularity, token diversity, computational efficiency, and structural overlap.")
    append("")

    append("SUMMARY TABLE")
    append(wide_hr("-"))
    append(
        "Tokenizer | Tokens | Unique | Uniq Ratio | Avg Len | Min | Max | "
        "Chars/Token | Unknown | Latency (µs) | Eff. Score | Comp."
    )
    append(
        "----------+--------+--------+------------+---------+-----+-----+"
        "-------------+---------+--------------+------------+------"
    )

    for item in results:
        metrics = get_metrics(item)
        append(
            f"{safe_str(item.get('tokenizer_name')):<9} | "
            f"{metrics.get('token_count', item.get('token_count', 0)):<6} | "
            f"{metrics.get('unique_token_count', item.get('vocab_size', 0)):<6} | "
            f"{format_number(metrics.get('unique_ratio'), 2):<10} | "
            f"{format_number(metrics.get('average_token_length'), 2):<7} | "
            f"{metrics.get('min_token_length', '-'):<3} | "
            f"{metrics.get('max_token_length', '-'):<3} | "
            f"{format_number(metrics.get('avg_chars_per_token'), 2):<11} | "
            f"{format_number(metrics.get('unknown_rate'), 2):<7} | "
            f"{latency_microseconds(metrics):<12} | "
            f"{format_number(metrics.get('efficiency_score'), 2):<10} | "
            f"{format_number(metrics.get('compression_ratio'), 2)}"
        )
    append("")

    append("KEY INSIGHTS")
    append(wide_hr("-"))

    if not results:
        append("No insights available.")
        append("")
    else:
        lowest_token = min(results, key=lambda item: item.get("token_count", 0))
        highest_token = max(results, key=lambda item: item.get("token_count", 0))
        highest_vocab = max(results, key=lambda item: item.get("vocab_size", 0))
        best_efficiency = max(results, key=lambda item: get_metrics(item).get("efficiency_score", 0))
        best_compression = max(results, key=lambda item: get_metrics(item).get("compression_ratio", 0))
        fastest = min(results, key=lambda item: get_metrics(item).get("latency_seconds", float("inf")))

        append(f"• Lowest token count        : {safe_str(lowest_token.get('tokenizer_name'))} ({lowest_token.get('token_count', 0)})")
        append(f"• Highest token count       : {safe_str(highest_token.get('tokenizer_name'))} ({highest_token.get('token_count', 0)})")
        append(f"• Best efficiency score     : {safe_str(best_efficiency.get('tokenizer_name'))} ({format_number(get_metric(best_efficiency, 'efficiency_score'), 2)})")
        append(f"• Highest unique token count: {safe_str(highest_vocab.get('tokenizer_name'))} ({highest_vocab.get('vocab_size', 0)})")
        append(f"• Fastest tokenizer         : {safe_str(fastest.get('tokenizer_name'))} ({latency_microseconds(get_metrics(fastest))} µs)")
        append(f"• Best compression ratio    : {safe_str(best_compression.get('tokenizer_name'))} ({format_number(get_metric(best_compression, 'compression_ratio'), 2)})")
        append("")

    append("INTERPRETATION")
    append(wide_hr("-"))

    if not results:
        append("No interpretation available.")
    else:
        lowest_token = min(results, key=lambda item: item.get("token_count", 0))
        highest_token = max(results, key=lambda item: item.get("token_count", 0))
        highest_vocab = max(results, key=lambda item: item.get("vocab_size", 0))
        best_efficiency = max(results, key=lambda item: get_metrics(item).get("efficiency_score", 0))
        fastest = min(results, key=lambda item: get_metrics(item).get("latency_seconds", float("inf")))

        append(
            f"The '{safe_str(lowest_token.get('tokenizer_name'))}' tokenizer produces the most compact segmentation "
            f"with {lowest_token.get('token_count', 0)} tokens."
        )
        append(
            f"The '{safe_str(highest_token.get('tokenizer_name'))}' tokenizer produces the most granular segmentation "
            f"with {highest_token.get('token_count', 0)} tokens."
        )
        append(
            f"The '{safe_str(best_efficiency.get('tokenizer_name'))}' tokenizer achieves the best efficiency score "
            f"({format_number(get_metric(best_efficiency, 'efficiency_score'), 2)}), indicating stronger compression per token."
        )
        append(
            f"The fastest tokenizer is '{safe_str(fastest.get('tokenizer_name'))}' "
            f"with {latency_microseconds(get_metrics(fastest))} µs latency."
        )
        append(
            "Overall, tokenizer choice directly affects input length, processing cost, semantic granularity, "
            "and downstream model efficiency."
        )
    append("")

    append("TOKENIZER DETAILS")
    append(wide_hr("-"))
    append("")

    if not results:
        append("No tokenizer details available.")
    else:
        for index, item in enumerate(results, start=1):
            tokenizer_name = safe_str(item.get("tokenizer_name"))
            token_count = item.get("token_count", 0)
            vocab_size = item.get("vocab_size", 0)
            tokens = item.get("tokens", [])
            metrics = item.get("metrics")

            append(f"[{index}] {tokenizer_name}")
            append(f"Token Count          : {token_count}")
            append(f"Vocab Size           : {vocab_size}")
            append("Tokens:")
            append(f"  {truncate_list(tokens)}")

            if isinstance(metrics, dict):
                append(f"Unique Token Count   : {metrics.get('unique_token_count', '-')}")
                append(f"Unique Ratio         : {format_number(metrics.get('unique_ratio'), 2)}")
                append(f"Average Token Length : {format_number(metrics.get('average_token_length'), 2)}")
                append(f"Min Token Length     : {metrics.get('min_token_length', '-')}")
                append(f"Max Token Length     : {metrics.get('max_token_length', '-')}")
                append(f"Avg Chars / Token    : {format_number(metrics.get('avg_chars_per_token'), 2)}")
                append(f"Unknown Count        : {metrics.get('unknown_count', '-')}")
                append(f"Unknown Rate         : {format_number(metrics.get('unknown_rate'), 2)}")

                latency = metrics.get("latency_seconds")
                append(
                    f"Latency              : {latency:.6f}s"
                    if isinstance(latency, (int, float))
                    else "Latency              : -"
                )

                append(
                    f"Latency / Token      : {format_number(metrics.get('latency_per_token'), 6)}"
                )
                append(
                    f"Efficiency Score     : {format_number(metrics.get('efficiency_score'), 2)}"
                )
                append(
                    f"Compression Ratio    : {format_number(metrics.get('compression_ratio'), 2)}"
                )

                top_tokens = format_top_tokens(metrics.get("top_tokens"))
                if top_tokens:
                    append("Top Tokens:")
                    lines.extend(top_tokens)
                    append("")

                reconstruction = format_reconstruction(metrics)
                if reconstruction:
                    append("Reconstruction:")
                    lines.extend(reconstruction)
                    append("")

                token_length_distribution = metrics.get("token_length_distribution")
                if isinstance(token_length_distribution, dict):
                    append("Token Length Distribution:")
                    for length, count in sorted(token_length_distribution.items()):
                        append(f"  Length {length}: {count} tokens")
                    append("")
            append(hr("-"))

    append("OVERALL RANKING")
    append(wide_hr("-"))

    ranked = sorted(
        results,
        key=lambda item: (
            get_metrics(item).get("efficiency_score", 0),
            -get_metrics(item).get("latency_seconds", float("inf")),
        ),
        reverse=True,
    )

    if not ranked:
        append("No ranking available.")
    else:
        append("Ranking is based on efficiency score and latency.")
        append("")
        for index, item in enumerate(ranked, start=1):
            metrics = get_metrics(item)
            append(
                f"{index}. {safe_str(item.get('tokenizer_name'))} "
                f"(eff={format_number(metrics.get('efficiency_score'), 2)}, "
                f"latency={latency_microseconds(metrics)} µs)"
            )

    append("")

    if pairwise:
        append_section_title(lines, "PAIRWISE COMPARISONS")

        for item in pairwise:
            append(f"{item.get('left_name')} ↔ {item.get('right_name')}")
            append(f"Overlap Ratio       : {format_number(item.get('overlap_ratio'), 2)}")
            append("Observation:")

            ratio = item.get("overlap_ratio")

            if isinstance(ratio, (int, float)):
                if ratio == 0:
                    append("  No shared tokens were found, indicating completely different tokenization strategies.")
                elif ratio < 0.25:
                    append("  Minimal overlap exists; tokenization strategies differ significantly.")
                elif ratio < 0.6:
                    append("  Moderate overlap suggests partial similarity in segmentation.")
                else:
                    append("  High overlap indicates similar tokenization behavior.")
            else:
                append("  No observation available.")

            append("")
            append(f"Common Tokens       : {truncate_list(item.get('common_tokens', []))}")
            append(f"Only Left           : {truncate_list(item.get('unique_to_left', []))}")
            append(f"Only Right          : {truncate_list(item.get('unique_to_right', []))}")
            append(hr("-"))

        append("")

    append("END OF REPORT".center(120))
    append(wide_hr("="))

    return "\n".join(lines)