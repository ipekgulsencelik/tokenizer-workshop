from typing import Literal

from pydantic import ConfigDict, Field

from tokenizer_workshop.api.schemas.base import BaseTokenizerListRequest
from pydantic import BaseModel


class ReportRequest(BaseTokenizerListRequest):
    """
    Tokenizer karşılaştırma raporu üretmek için kullanılan request modelidir.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "text": "Merhaba dünya! Tokenizer raporu oluştur.",
                    "tokenizer_names": ["char", "word"],
                    "format": "txt",
                },
                {
                    "text": "This is a sample input for tokenizer comparison.",
                    "tokenizer_names": ["word", "bpe", "byte_bpe"],
                    "format": "md",
                },
            ]
        }
    )

    format: Literal["txt", "md"] = Field(
        default="txt",
        description='Üretilecek rapor formatı. Desteklenen değerler: "txt", "md".',
        examples=["txt", "md"],
    )


class ReportResponse(BaseModel):
    """
    Rapor üretme endpoint'inin döndürdüğü response modelidir.
    """

    report: str = Field(
        ...,
        description="Üretilen raporun string içeriği.",
    )

    format: Literal["txt", "md"] = Field(
        ...,
        description="Üretilen rapor formatı.",
        examples=["txt", "md"],
    )

    filename: str = Field(
        ...,
        description="İndirme için önerilen dosya adı.",
        examples=["tokenizer_report.txt", "tokenizer_report.md"],
    )