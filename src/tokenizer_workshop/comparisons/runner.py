from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from tokenizer_workshop.evaluators import TokenizationMetrics, evaluate_tokenizer
from tokenizer_workshop.tokenizers import (
    BaseTokenizer,
    ByteTokenizer,
    CharTokenizer,
    SimpleBPETokenizer,
)
from tokenizer_workshop.utils import load_sample_texts

TokenizerFactory = Callable[[], BaseTokenizer]


@dataclass(frozen=True)
class ComparisonResult:
    """
    Tek bir comparison run sonucunu temsil eder.

    field'ler:
    - label: Sonucun hangi compare grubuna ait olduğunu açıklar.
    - metrics: İlgili tokenizer evaluation sonucu.
    """

    label: str
    metrics: TokenizationMetrics


def build_default_tokenizer_factories(
    simple_bpe_num_merges: int = 20,
) -> list[tuple[str, TokenizerFactory]]:
    """
    Projede kullandığımız varsayılan tokenizer factory listesini döndürür.

    Neden instance değil de factory döndürüyoruz?
    Çünkü her evaluation için temiz bir tokenizer instance üretmek istiyoruz.
    Böylece state carry-over riskini azaltırız.
    """
    return [
        ("char", CharTokenizer),
        ("byte", ByteTokenizer),
        (
            f"simple_bpe_{simple_bpe_num_merges}_merges",
            lambda: SimpleBPETokenizer(num_merges=simple_bpe_num_merges),
        ),
    ]


def run_same_text_across_tokenizers(
    text: str,
    tokenizer_factories: list[tuple[str, TokenizerFactory]] | None = None,
    train_text: str | None = None,
) -> list[ComparisonResult]:
    """
    Aynı text üzerinde birden fazla tokenizer'ı karşılaştırır.

    Bu compare tipi şu soruya cevap verir:
    "Aynı input, farklı tokenizer'larda nasıl davranıyor?"
    """
    if not text:
        raise ValueError("Comparison text cannot be empty.")

    factories = tokenizer_factories or build_default_tokenizer_factories()
    results: list[ComparisonResult] = []

    for label, factory in factories:
        tokenizer = factory()
        metrics = evaluate_tokenizer(
            tokenizer=tokenizer,
            text=text,
            train_text=train_text,
        )
        results.append(ComparisonResult(label=label, metrics=metrics))

    return results


def run_all_samples_across_tokenizers(
    tokenizer_factories: list[tuple[str, TokenizerFactory]] | None = None,
) -> dict[str, list[ComparisonResult]]:
    """
    config.yaml içinde tanımlı tüm sample text'ler üzerinde
    aynı-text-across-tokenizers compare çalıştırır.

    Dönüş formatı:
        {
            "data/sample_tr.txt": [...],
            "data/sample_en.txt": [...],
            ...
        }
    """
    sample_texts = load_sample_texts()
    all_results: dict[str, list[ComparisonResult]] = {}

    for sample_name, text in sample_texts.items():
        all_results[sample_name] = run_same_text_across_tokenizers(
            text=text,
            tokenizer_factories=tokenizer_factories,
        )

    return all_results


def run_same_tokenizer_across_samples(
    tokenizer_factory: TokenizerFactory,
    tokenizer_label: str,
) -> list[ComparisonResult]:
    """
    Aynı tokenizer'ı farklı sample text'ler üzerinde çalıştırır.

    Bu compare tipi şu soruya cevap verir:
    "Aynı tokenizer, farklı text türlerinde nasıl davranıyor?"
    """
    sample_texts = load_sample_texts()
    results: list[ComparisonResult] = []

    for sample_name, text in sample_texts.items():
        tokenizer = tokenizer_factory()
        metrics = evaluate_tokenizer(
            tokenizer=tokenizer,
            text=text,
        )
        results.append(ComparisonResult(label=f"{tokenizer_label} | {sample_name}", metrics=metrics))

    return results


def run_simple_bpe_merge_sweep(
    text: str,
    merge_values: list[int],
    train_text: str | None = None,
) -> list[ComparisonResult]:
    """
    Aynı text üzerinde farklı num_merges değerleri ile
    SimpleBPETokenizer compare çalıştırır.

    Bu compare tipi şu soruya cevap verir:
    "num_merges değiştikçe tokenization davranışı nasıl değişiyor?"
    """
    if not text:
        raise ValueError("Comparison text cannot be empty.")

    if not merge_values:
        raise ValueError("merge_values cannot be empty.")

    results: list[ComparisonResult] = []

    for num_merges in merge_values:
        tokenizer = SimpleBPETokenizer(num_merges=num_merges)
        metrics = evaluate_tokenizer(
            tokenizer=tokenizer,
            text=text,
            train_text=train_text,
        )
        results.append(
            ComparisonResult(
                label=f"simple_bpe_{num_merges}_merges",
                metrics=metrics,
            )
        )

    return results