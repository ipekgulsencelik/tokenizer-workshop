from __future__ import annotations

from tokenizer_workshop.comparisons import (
    print_all_sample_results,
    run_all_samples_across_tokenizers,
)


def main() -> None:
    """
    Projedeki sample text'ler üzerinde varsayılan tokenizer compare akışını çalıştırır.
    """
    all_results = run_all_samples_across_tokenizers()
    print_all_sample_results(all_results)


if __name__ == "__main__":
    main()


# For Run:
# uv run python -m tokenizer_workshop.compare