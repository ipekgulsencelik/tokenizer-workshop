"""
schemas.py

Bu dosya, FastAPI uygulamasında kullanılan veri modellerini (schemas) tanımlar.

Amaç:
- API ile istemci arasındaki veri sözleşmesini (contract) tanımlamak
- Gelen request verilerini doğrulamak (validation)
- Dönen response yapısını standart hale getirmek
- Swagger / OpenAPI dokümantasyonunu otomatik olarak üretmek

Mimari rol:
-----------
Bu katman "data boundary" olarak görev yapar.

Yani:
- dış dünyadan gelen veriyi kontrol eder
- iç sistemin daha güvenli ve öngörülebilir çalışmasını sağlar

Önemli not:
-----------
Bu dosyada business logic bulunmaz.
Sadece veri yapıları, doğrulama kuralları ve açıklamalar yer alır.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------
# Base Request Models
# ---------------------------------------------------------
class BaseTextRequest(BaseModel):
    """
    Ham metin alanı taşıyan request modelleri için ortak davranış sağlar.

    Bu sınıfın amacı:
    - text alanını tek yerde tanımlamak
    - tekrar eden validation mantığını merkezi hale getirmek
    - tüm text tabanlı request modellerinde tutarlılık sağlamaktır
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
            "Merhaba dünya! Tokenization öğreniyorum.",
            "Hello world! This is a tokenizer test.",
        ],
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """
        text alanını normalize eder ve yalnızca whitespace içeren girdileri engeller.
        """
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("text alanı boş veya yalnızca boşluk karakterlerinden oluşamaz.")

        return cleaned_value


class BaseTokenizerListRequest(BaseTextRequest):
    """
    Tokenizer listesi taşıyan request modelleri için ortak davranış sağlar.

    Bu sınıfın amacı:
    - tokenizer_names alanını tek yerde tanımlamak
    - normalize / duplicate kontrolünü merkezi hale getirmek
    - compare ve report request modellerinde tekrar eden kodu azaltmaktır
    """

    tokenizer_names: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "İşlemde kullanılacak tokenizer isimlerinin listesi. "
            "En az bir tokenizer içermelidir."
        ),
        examples=[["char", "word"], ["bpe", "byte_bpe"]],
    )

    @field_validator("tokenizer_names")
    @classmethod
    def validate_tokenizer_names(cls, value: list[str]) -> list[str]:
        """
        tokenizer isimlerini normalize eder, boş değerleri ve tekrarları engeller.
        """
        normalized_names = [name.strip().lower() for name in value]

        if any(not name for name in normalized_names):
            raise ValueError("tokenizer_names içinde boş değer bulunamaz.")

        if len(set(normalized_names)) != len(normalized_names):
            raise ValueError("Aynı tokenizer birden fazla kez gönderilemez.")

        return normalized_names


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------
class TokenizeRequest(BaseTextRequest):
    """
    Tekli tokenization işlemi için istemciden gelen request modelidir.

    Bu model:
    - tek bir ham metin alır
    - tek bir tokenizer seçimi alır
    - tokenize endpoint'i için giriş verisini doğrular

    Kullanım senaryosu:
        POST /api/tokenize
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


class CompareRequest(BaseTokenizerListRequest):
    """
    Aynı ham metni birden fazla tokenizer ile karşılaştırmalı olarak çalıştırmak için
    kullanılan request modelidir.

    Bu modelin amacı:
    - tek bir input text almak
    - birden fazla tokenizer seçimini kabul etmek
    - compare endpoint'i için veri doğrulamasını sağlamak

    Kullanım senaryosu:
        POST /api/compare

    Not:
    - tokenizer isimleri normalize edilir
    - boş değerler engellenir
    - tekrarlı seçimler engellenir
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


class ReportRequest(BaseTokenizerListRequest):
    """
    Tokenizer karşılaştırma raporu üretmek için kullanılan request modelidir.

    Bu model:
    - ham metni alır
    - compare işlemine dahil edilecek tokenizer listesini alır
    - çıktı formatını belirler
    - report endpoint'i için giriş verisini doğrular
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


# ---------------------------------------------------------
# Basic Response Models
# ---------------------------------------------------------
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

    Bu model, compare endpoint'inin sade çıktısı için uygundur.
    Rich metrics veya pairwise analysis kullanılmayan senaryolarda tercih edilir.
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


# ---------------------------------------------------------
# Rich Comparison Response Models
# ---------------------------------------------------------
class TopTokenResponse(BaseModel):
    """
    En sık görülen token bilgisini temsil eder.
    """

    token: str = Field(..., description="Token değeri.")
    count: int = Field(..., ge=0, description="Token frekansı.")


class MetricsResponse(BaseModel):
    """
    Tek bir tokenizer değerlendirmesi için hesaplanan metrikleri temsil eder.
    """

    token_count: int = Field(..., ge=0, description="Toplam token sayısı.")
    unique_token_count: int = Field(..., ge=0, description="Benzersiz token sayısı.")
    unique_ratio: float = Field(..., ge=0, description="Unique token oranı.")
    average_token_length: float = Field(..., ge=0, description="Ortalama token uzunluğu.")
    min_token_length: int = Field(..., ge=0, description="En kısa token uzunluğu.")
    max_token_length: int = Field(..., ge=0, description="En uzun token uzunluğu.")
    avg_chars_per_token: float = Field(
        ...,
        ge=0,
        description="Token başına ortalama karakter sayısı.",
    )
    unknown_count: int = Field(..., ge=0, description="Bilinmeyen token sayısı.")
    unknown_rate: float = Field(..., ge=0, description="Bilinmeyen token oranı.")
    latency_seconds: float = Field(..., ge=0, description="Toplam tokenization süresi.")
    latency_per_token: float = Field(..., ge=0, description="Token başına düşen ortalama süre.")
    efficiency_score: float = Field(..., ge=0, description="Verimlilik skoru.")
    compression_ratio: float = Field(..., ge=0, description="Sıkıştırma / verimlilik oranı.")

    top_tokens: list[TopTokenResponse] = Field(
        default_factory=list,
        description="En sık görülen tokenlar.",
    )

    token_length_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Token uzunluğu dağılımı.",
    )

    reconstructed_text: str | None = Field(
        default=None,
        description="Varsa tokenlardan yeniden oluşturulmuş metin.",
    )

    reconstruction_match: bool | None = Field(
        default=None,
        description="Yeniden oluşturulan metin kaynak metinle eşleşiyor mu?",
    )


class EvaluationResponse(BaseModel):
    """
    Tek bir tokenizer için detaylı karşılaştırma sonucunu temsil eder.
    """

    tokenizer_name: str = Field(..., description="Tokenizer adı.")
    tokens: list[str] = Field(..., description="Üretilen token listesi.")
    metrics: MetricsResponse = Field(..., description="Hesaplanan metrikler.")


class PairwiseComparisonResponse(BaseModel):
    """
    İki tokenizer arasındaki pairwise karşılaştırma sonucunu temsil eder.
    """

    left_name: str = Field(..., description="Sol tokenizer adı.")
    right_name: str = Field(..., description="Sağ tokenizer adı.")
    common_tokens: list[str] = Field(
        default_factory=list,
        description="İki tokenizer arasında ortak tokenlar.",
    )
    unique_to_left: list[str] = Field(
        default_factory=list,
        description="Sadece sol tokenizer'da bulunan tokenlar.",
    )
    unique_to_right: list[str] = Field(
        default_factory=list,
        description="Sadece sağ tokenizer'da bulunan tokenlar.",
    )
    overlap_ratio: float = Field(..., ge=0, description="Örtüşme oranı.")


class CompareRichResponse(BaseModel):
    """
    Zenginleştirilmiş çoklu tokenizer karşılaştırma sonucunu temsil eder.

    Bu model:
    - source text'i
    - her tokenizer için detaylı evaluation verisini
    - pairwise comparison sonuçlarını
    tek bir response altında toplar
    """

    source_text: str = Field(
        ...,
        description="Karşılaştırma yapılan kaynak metin.",
    )

    evaluations: list[EvaluationResponse] = Field(
        ...,
        description="Her tokenizer için detaylı değerlendirme sonuçları.",
    )

    pairwise_comparisons: list[PairwiseComparisonResponse] = Field(
        default_factory=list,
        description="Tokenizer çiftleri arasındaki karşılaştırmalar.",
    )