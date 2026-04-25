from __future__ import annotations

from typing import Any

from tokenizer_workshop.api.services.exceptions import (
    TokenizationServiceError,
    UnsupportedTokenizerError,
)
from tokenizer_workshop.api.services.tokenizer_factory import TokenizerFactory
from tokenizer_workshop.api.services.utils import (
    normalize_tokens,
    validate_tokenizer_interface,
)


def train_tokenizer_if_supported(tokenizer: object, text: str) -> None:
    """
    Tokenizer train() metodunu destekliyorsa, verilen metinle eğitir.
    """
    try:
        if hasattr(tokenizer, "train") and callable(getattr(tokenizer, "train")):
            tokenizer.train(text)
    except Exception as exc:
        raise TokenizationServiceError(
            "Tokenizer training failed before tokenization."
        ) from exc


def tokenize_text(text: str, tokenizer_name: str) -> dict[str, Any]:
    try:
        tokenizer = TokenizerFactory.create(tokenizer_name)
        validate_tokenizer_interface(tokenizer, tokenizer_name)

        train_tokenizer_if_supported(tokenizer, text)

        raw_tokens = tokenizer.tokenize(text)
        normalized_tokens = normalize_tokens(raw_tokens)

        return {
            "tokenizer_name": TokenizerFactory.normalize_name(tokenizer_name),
            "tokens": normalized_tokens,
            "token_count": len(normalized_tokens),
            "vocab_size": len(set(normalized_tokens)),
        }

    except UnsupportedTokenizerError:
        raise

    except TokenizationServiceError:
        raise

    except Exception as exc:
        raise TokenizationServiceError(
            f"Tokenization failed for '{tokenizer_name}': {type(exc).__name__}: {exc}"
        ) from exc