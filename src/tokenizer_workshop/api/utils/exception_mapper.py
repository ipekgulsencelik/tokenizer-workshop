from fastapi import HTTPException, status
from tokenizer_workshop.api.services import (
    UnsupportedTokenizerError,
    TokenizationServiceError,
)


def map_service_exception(exc: Exception) -> None:
    if isinstance(exc, UnsupportedTokenizerError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if isinstance(exc, TokenizationServiceError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    raise exc