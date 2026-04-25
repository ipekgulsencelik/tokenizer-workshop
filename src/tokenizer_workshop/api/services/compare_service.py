"""
compare_service.py

Çoklu tokenizer karşılaştırma işlemlerinin service katmanı.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from tokenizer_workshop.api.services.exceptions import (
    TokenizationServiceError,
    UnsupportedTokenizerError,
)
from tokenizer_workshop.api.services.metrics_service import (
    build_pairwise_comparisons,
    calculate_metrics,
)
from tokenizer_workshop.api.services.tokenize_service import (
    tokenize_text,
    train_tokenizer_if_supported,
)
from tokenizer_workshop.api.services.tokenizer_factory import TokenizerFactory
from tokenizer_workshop.api.services.utils import (
    deduplicate_tokenizer_names,
    normalize_tokens,
    validate_tokenizer_interface,
)


def compare_tokenizers(text: str, tokenizer_names: list[str]) -> dict[str, Any]:
    """
    Aynı ham metni birden fazla tokenizer ile işler ve sonuçları toplu olarak döndürür.
    """
    if not tokenizer_names:
        raise TokenizationServiceError("At least one tokenizer must be selected.")

    try:
        normalized_names = deduplicate_tokenizer_names(tokenizer_names)

        results = [
            tokenize_text(text=text, tokenizer_name=name)
            for name in normalized_names
        ]

        return {
            "text": text,
            "total_tokenizers": len(results),
            "results": results,
        }

    except UnsupportedTokenizerError:
        raise

    except TokenizationServiceError:
        raise

    except Exception as exc:
        raise TokenizationServiceError(
            f"An unexpected error occurred while comparing tokenizers: {type(exc).__name__}: {exc}"
        ) from exc


def evaluate_tokenizers(text: str, tokenizer_names: list[str]) -> dict[str, Any]:
    """
    Aynı metni birden fazla tokenizer ile çalıştırır ve detaylı evaluation sonucu üretir.
    """
    if not tokenizer_names:
        raise TokenizationServiceError("At least one tokenizer must be selected.")

    try:
        normalized_names = deduplicate_tokenizer_names(tokenizer_names)

        evaluations: list[dict[str, Any]] = []

        for name in normalized_names:
            tokenizer = TokenizerFactory.create(name)
            validate_tokenizer_interface(tokenizer, name)

            train_tokenizer_if_supported(tokenizer, text)

            start = perf_counter()
            raw_tokens = tokenizer.tokenize(text)
            end = perf_counter()

            normalized_tokens = normalize_tokens(raw_tokens)
            latency_seconds = end - start

            metrics = calculate_metrics(
                tokens=normalized_tokens,
                latency_seconds=latency_seconds,
                source_text=text,
            )

            evaluations.append(
                {
                    "tokenizer_name": TokenizerFactory.normalize_name(name),
                    "tokens": normalized_tokens,
                    "metrics": metrics,
                }
            )

        pairwise_comparisons = build_pairwise_comparisons(evaluations)

        return {
            "source_text": text,
            "evaluations": evaluations,
            "pairwise_comparisons": pairwise_comparisons,
        }

    except UnsupportedTokenizerError:
        raise

    except TokenizationServiceError:
        raise

    except Exception as exc:
        raise TokenizationServiceError(
            f"An unexpected error occurred while generating the evaluation result: {type(exc).__name__}: {exc}"
        ) from exc  