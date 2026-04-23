from pydantic import BaseModel, Field


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


class TokenizerComparisonResult(BaseModel):
    """
    Zenginleştirilmiş çoklu tokenizer karşılaştırma sonucunu temsil eder.
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