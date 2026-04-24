"""
metrics_service.py

Tokenizer çıktıları üzerinden metrik ve pairwise comparison üreten servisler.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any


def calculate_metrics(
    tokens: list[str],
    latency_seconds: float,
    source_text: str,
) -> dict[str, Any]:
    """
    Token listesi üzerinden detaylı metrikler hesaplar.
    """
    token_count = len(tokens)
    unique_token_count = len(set(tokens))
    unique_ratio = (unique_token_count / token_count) if token_count > 0 else 0.0

    token_lengths = [len(token) for token in tokens]
    average_token_length = (
        sum(token_lengths) / token_count if token_count > 0 else 0.0
    )
    min_token_length = min(token_lengths) if token_lengths else 0
    max_token_length = max(token_lengths) if token_lengths else 0

    avg_chars_per_token = (
        len(source_text) / token_count if token_count > 0 else 0.0
    )

    unknown_count = sum(1 for token in tokens if token in {"[UNK]", "<unk>", "UNK"})
    unknown_rate = (unknown_count / token_count) if token_count > 0 else 0.0

    efficiency_score = (
        avg_chars_per_token * (1 - unknown_rate)
        if token_count > 0
        else 0.0
    )

    compression_ratio = (
        len(source_text) / token_count if token_count > 0 else 0.0
    )

    latency_per_token = (
        latency_seconds / token_count if token_count > 0 else 0.0
    )

    top_tokens = Counter(tokens).most_common(5)

    token_length_distribution: dict[str, int] = {}
    for length in token_lengths:
        key = str(length)
        token_length_distribution[key] = token_length_distribution.get(key, 0) + 1

    reconstructed_text = " ".join(tokens) if tokens else ""
    reconstruction_match = reconstructed_text == source_text if reconstructed_text else False

    return {
        "token_count": token_count,
        "unique_token_count": unique_token_count,
        "unique_ratio": unique_ratio,
        "average_token_length": average_token_length,
        "min_token_length": min_token_length,
        "max_token_length": max_token_length,
        "avg_chars_per_token": avg_chars_per_token,
        "unknown_count": unknown_count,
        "unknown_rate": unknown_rate,
        "latency_seconds": latency_seconds,
        "latency_per_token": latency_per_token,
        "efficiency_score": efficiency_score,
        "compression_ratio": compression_ratio,
        "top_tokens": [
            {"token": token, "count": count}
            for token, count in top_tokens
        ],
        "token_length_distribution": token_length_distribution,
        "reconstructed_text": reconstructed_text,
        "reconstruction_match": reconstruction_match,
    }


def build_pairwise_comparisons(
    evaluations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Tokenizer sonuçları arasında pairwise comparison üretir.
    """
    pairwise_results: list[dict[str, Any]] = []

    for left, right in combinations(evaluations, 2):
        left_tokens = set(left["tokens"])
        right_tokens = set(right["tokens"])

        common_tokens = sorted(left_tokens & right_tokens)
        unique_to_left = sorted(left_tokens - right_tokens)
        unique_to_right = sorted(right_tokens - left_tokens)

        union_count = len(left_tokens | right_tokens)
        overlap_ratio = len(common_tokens) / union_count if union_count > 0 else 0.0

        pairwise_results.append(
            {
                "left_name": left["tokenizer_name"],
                "right_name": right["tokenizer_name"],
                "common_tokens": common_tokens,
                "unique_to_left": unique_to_left,
                "unique_to_right": unique_to_right,
                "overlap_ratio": overlap_ratio,
            }
        )

    return pairwise_results