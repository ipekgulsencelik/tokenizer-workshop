"""
tokenize.py

Tokenize endpoint'i için request ve response modelleri.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from tokenizer_workshop.api.schemas.base import BaseTextRequest


class TokenizeRequest(BaseTextRequest):
    """
    Tekli tokenization işlemi için istemciden gelen request modelidir.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "Merhaba dünya!",
                    "tokenizer_name": "char",
                },
                {
                    "text": "This is a tokenizer test.",
                    "tokenizer_name": "word",
                },
            ]
        }
    )

    tokenizer_name: str = Field(
        ...,
        min_length=1,
        description=(
            "Kullanılacak tokenizer adı. "
            "Desteklenen değerler backend tarafında belirlenir."
        ),
        examples=["char", "byte", "word"],
    )

    @field_validator("tokenizer_name")
    @classmethod
    def validate_tokenizer_name(cls, value: str) -> str:
        """
        tokenizer adını normalize eder ve boş isimleri engeller.
        """
        cleaned_value = value.strip().lower()

        if not cleaned_value:
            raise ValueError("tokenizer_name boş olamaz.")

        return cleaned_value


class TokenizeResponse(BaseModel):
    """
    Tekli tokenization sonucunu temsil eden response modelidir.
    """

    tokenizer_name: str = Field(
        ...,
        description="Tokenization sırasında kullanılan tokenizer adı.",
        examples=["char"],
    )

    tokens: list[str] = Field(
        ...,
        description="Tokenization sonucu oluşan token listesi. Sıralama korunur.",
        examples=[["M", "e", "r", "h", "a", "b", "a"]],
    )

    token_count: int = Field(
        ...,
        ge=0,
        description="Toplam token sayısı. Bu değer len(tokens) ile hesaplanır.",
        examples=[7],
    )

    vocab_size: int = Field(
        ...,
        ge=0,
        description="Benzersiz token sayısı. Bu değer len(set(tokens)) ile hesaplanır.",
        examples=[6],
    )