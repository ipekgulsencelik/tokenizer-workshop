"""
utils.py

Service katmanında ortak kullanılan yardımcı fonksiyonlar.
"""

from __future__ import annotations

from typing import Any

from tokenizer_workshop.api.services.exceptions import TokenizationServiceError
from tokenizer_workshop.api.services.tokenizer_factory import TokenizerFactory


def validate_tokenizer_interface(tokenizer: Any, tokenizer_name: str) -> None:
    """
    Verilen tokenizer nesnesinin tokenize(text) metodunu sağlayıp sağlamadığını doğrular.
    """
    if not hasattr(tokenizer, "tokenize") or not callable(getattr(tokenizer, "tokenize")):
        raise TokenizationServiceError(
            f"Tokenizer '{tokenizer_name}' does not implement a callable 'tokenize' method."
        )


def normalize_tokens(tokens: Any) -> list[str]:
    """
    Tokenizer çıktısını list[str] formatına normalize eder.
    """
    try:
        return [str(token) for token in list(tokens)]
    except Exception as exc:
        raise TokenizationServiceError(
            "Tokenizer output could not be normalized into a list of strings."
        ) from exc


def deduplicate_tokenizer_names(tokenizer_names: list[str]) -> list[str]:
    """
    Tokenizer isimlerini normalize ederek tekrar edenleri kaldırır.
    Sıra korunur.
    """
    normalized_names: list[str] = []
    seen: set[str] = set()

    for name in tokenizer_names:
        normalized_name = TokenizerFactory.normalize_name(name)

        if normalized_name not in seen:
            seen.add(normalized_name)
            normalized_names.append(normalized_name)

    return normalized_names