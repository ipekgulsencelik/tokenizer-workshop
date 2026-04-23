"""
base.py

Ortak request modelleri.

Amaç:
- Tüm text tabanlı request'lerde tekrar eden alanları merkezi hale getirmek
- Validation mantığını tek yerde toplamak
- Tutarlı API contract sağlamak
"""

from pydantic import BaseModel, Field, field_validator


class BaseTextRequest(BaseModel):
    """
    Tüm text tabanlı request modelleri için ortak base class.

    Sağladıkları:
    - text alanı tanımı
    - whitespace temizleme
    - boş veri engelleme
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description=(
            "İşlenecek ham metin. "
            "Boş olamaz, yalnızca whitespace içeremez ve en fazla 10.000 karakter olabilir."
        ),
        examples=[
            "Merhaba dünya!",
            "Hello world!",
        ],
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """
        text alanını normalize eder:
        - baştaki ve sondaki boşlukları siler
        - tamamen boş olan input'u engeller
        """
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("text alanı boş olamaz")

        return cleaned


class BaseTokenizerListRequest(BaseTextRequest):
    """
    Birden fazla tokenizer alan request'ler için base class.

    Sağladıkları:
    - tokenizer_names listesi
    - normalize (lowercase, trim)
    - duplicate engelleme
    """

    tokenizer_names: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "İşlemde kullanılacak tokenizer isimlerinin listesi. "
            "En az bir tokenizer içermelidir."
        ),
        examples=[
            ["char", "word"],
            ["bpe", "byte_bpe"],
        ],
    )

    @field_validator("tokenizer_names")
    @classmethod
    def validate_tokenizer_names(cls, value: list[str]) -> list[str]:
        """
        tokenizer isimlerini normalize eder:
        - trim + lowercase
        - boş değerleri engeller
        - duplicate'leri engeller
        """
        normalized = [name.strip().lower() for name in value]

        if any(not name for name in normalized):
            raise ValueError("tokenizer_names içinde boş değer bulunamaz")

        if len(set(normalized)) != len(normalized):
            raise ValueError("Aynı tokenizer birden fazla kez gönderilemez")

        return normalized