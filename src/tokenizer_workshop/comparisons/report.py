from __future__ import annotations

from tokenizer_workshop.comparisons.runner import ComparisonResult


def format_comparison_result(result: ComparisonResult) -> str:
    """
    Tek bir ComparisonResult nesnesini okunabilir bir metin bloğuna dönüştürür.
    """
    metrics = result.metrics

    lines = [
        f"Label: {result.label}",
        f"  tokenizer_name: {metrics.tokenizer_name}",
        f"  vocab_size: {metrics.vocab_size}",
        f"  token_count: {metrics.token_count}",
        f"  char_length: {metrics.char_length}",
        f"  byte_length: {metrics.byte_length}",
        f"  compression_ratio_vs_chars: {metrics.compression_ratio_vs_chars:.3f}",
        f"  compression_ratio_vs_bytes: {metrics.compression_ratio_vs_bytes:.3f}",
        f"  roundtrip_ok: {metrics.roundtrip_ok}",
    ]
    return "\n".join(lines)


def format_result_group(title: str, results: list[ComparisonResult]) -> str:
    """
    Bir comparison result grubunu başlıkla birlikte formatlar.
    """
    lines = [
        "=" * 80,
        title,
        "=" * 80,
    ]

    for result in results:
        lines.append(format_comparison_result(result))
        lines.append("-" * 80)

    return "\n".join(lines)


def print_result_group(title: str, results: list[ComparisonResult]) -> None:
    """
    Formatlanmış sonucu terminale basar.
    """
    print(format_result_group(title, results))


def print_all_sample_results(
    all_results: dict[str, list[ComparisonResult]],
) -> None:
    """
    Tüm sample sonuçlarını sırayla terminale basar.
    """
    for sample_name, results in all_results.items():
        print_result_group(title=f"Sample: {sample_name}", results=results)