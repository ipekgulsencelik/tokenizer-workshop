from pydantic import BaseModel, ConfigDict, Field

from tokenizer_workshop.api.schemas.base import BaseTokenizerListRequest


class CompareRequest(BaseTokenizerListRequest):
    """
    Aynı ham metni birden fazla tokenizer ile karşılaştırmalı olarak çalıştırmak için
    kullanılan request modelidir.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "Merhaba dünya! Tokenizer karşılaştırması yapıyorum.",
                    "tokenizer_names": ["char", "byte", "word"],
                },
                {
                    "text": "Byte Pair Encoding ile character tokenization farkını görmek istiyorum.",
                    "tokenizer_names": ["char", "bpe", "byte_bpe"],
                },
            ]
        }
    )


class CompareItemResponse(BaseModel):
    """
    Basit compare response içinde tek bir tokenizer sonucunu temsil eder.
    """

    tokenizer_name: str = Field(
        ...,
        description="Sonucu üreten tokenizer adı.",
        examples=["char"],
    )

    tokens: list[str] = Field(
        ...,
        description="İlgili tokenizer tarafından üretilen token listesi.",
        examples=[["M", "e", "r"]],
    )

    token_count: int = Field(
        ...,
        ge=0,
        description="Toplam token sayısı.",
        examples=[3],
    )

    vocab_size: int = Field(
        ...,
        ge=0,
        description="Benzersiz token sayısı.",
        examples=[3],
    )


class CompareResponse(BaseModel):
    """
    Basit çoklu tokenizer karşılaştırma sonucunu temsil eder.
    """

    text: str = Field(
        ...,
        description="Karşılaştırma yapılan ham metin.",
        examples=["Merhaba dünya!"],
    )

    total_tokenizers: int = Field(
        ...,
        ge=0,
        description="Çalıştırılan tokenizer sayısı.",
        examples=[3],
    )

    results: list[CompareItemResponse] = Field(
        ...,
        description="Her tokenizer için üretilen karşılaştırma sonuçları.",
    )