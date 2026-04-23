"""
services.py

Bu modül, FastAPI katmanının ihtiyaç duyduğu uygulama servislerini içerir.

Temel amaç:
- tokenizer seçimini merkezi bir yapı üzerinden yönetmek
- tokenization işlemini route/controller katmanından ayırmak
- compare işlemlerini tek yerde toplamak
- business logic'i presentation layer dışına çıkarmak
- sistemi yeni tokenizer türlerine açık hale getirmek

Neden ayrı bir service katmanı var?
Doğrudan route içinde tokenizer seçimi ve tokenization yapmak ilk bakışta
kolay görünse de zamanla aşağıdaki problemlere yol açar:

1. Route dosyaları büyür ve okunabilirlik düşer
2. Test yazmak zorlaşır
3. Yeni tokenizer eklemek maliyetli hale gelir
4. API framework'üne bağımlılık artar
5. Kodun yeniden kullanılabilirliği azalır

Mimari rol:
-----------
Route katmanı yalnızca request alır ve response döner.
Asıl uygulama davranışı bu servis katmanında yürütülür.

Akış:
-----
route -> service -> tokenizer implementation

Buradaki roller:
- route:
    HTTP request alır, validation sonrası service çağırır, response döner
- service:
    iş akışını yönetir, tokenizer seçer, çıktıyı normalize eder
- tokenizer implementation:
    gerçek tokenization davranışını uygular

Önemli mimari not:
Bu dosya framework-agnostic tutulmalıdır.
Yani burada FastAPI'ye özgü:
- HTTPException
- Request / Response nesneleri
- status code yönetimi
bulunmamalıdır.

Bu tercih sayesinde service katmanı:
- CLI tarafından da kullanılabilir
- testlerde doğrudan çağrılabilir
- farklı bir web framework'üne taşınabilir
"""

from __future__ import annotations

from typing import Any

from collections import Counter
from itertools import combinations
from time import perf_counter

# ---------------------------------------------------------
# Tokenizer Imports
# ---------------------------------------------------------
# Bu importlar, sistemin desteklediği tokenizer implementasyonlarını içeri alır.
#
# Her tokenizer sınıfının minimum beklentisi şudur:
# - tokenize(text) isminde callable bir metodu bulunmalı
#
# Eğer ileride yeni bir tokenizer eklenmek istenirse:
# 1. ilgili sınıfı burada import edilmeli
# 2. TokenizerFactory.get_registry() içine kaydedilmeli
from tokenizer_workshop.tokenizers.char_tokenizer import CharTokenizer
from tokenizer_workshop.tokenizers.byte_tokenizer import ByteTokenizer
from tokenizer_workshop.tokenizers.simple_bpe_tokenizer import SimpleBPETokenizer
from tokenizer_workshop.tokenizers.byte_bpe_tokenizer import ByteBPETokenizer
from tokenizer_workshop.tokenizers.word_tokenizer import WordTokenizer


# ---------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------
class UnsupportedTokenizerError(ValueError):
    """
    Desteklenmeyen tokenizer adı verildiğinde yükseltilen özel hata türü.

    Bu exception özellikle:
    - route katmanında 400 Bad Request üretmek
    - hata tipini daha anlamlı hale getirmek için kullanılır.

    Avantajları:
    - route katmanında bu hatay özel olarak yakalanabilir
    - 400 Bad Request gibi uygun HTTP response üretmek kolaylaşır
    - hata mesajları daha anlamlı olur
    - debugging sırasında hangi tip hatanın oluştuğu daha net anlaşılır

    Bu hata tipi özellikle route katmanında istemci hatası ile
    sistem hatasını ayırmak için kullanılır.
    """


class TokenizationServiceError(Exception):
    """
    Service katmanında oluşan beklenmeyen veya teknik hataları temsil eder.

    Kullanım amacı:
    - low-level hataları üst katmanlara kontrollü biçimde iletmek
    - tokenizer çıktısı bozuksa veya arayüz sözleşmesi sağlanmıyorsa bunu anlamlı bir servis hatasına dönüştürmek
    - normalize veya compare akışındaki teknik sorunları sarmalamak

    Örnek senaryolar:
    - tokenizer nesnesinde tokenize() metodu yoksa
    - tokenizer çıktısı iterable değilse
    - tokenize işlemi sırasında beklenmeyen bir hata oluşursa
    """


# ---------------------------------------------------------
# Tokenizer Factory
# ---------------------------------------------------------
# Bu sınıfın görevi:
# - string olarak gelen tokenizer adını almak
# - doğru tokenizer nesnesini üretmek
#
# Böylece route katmanı "if-else" çöplüğüne dönüşmez.
class TokenizerFactory:
    """
    Tokenizer üretiminden sorumlu merkezi factory sınıfı.

    Bu sınıf neden var?
    Kullanıcıdan gelen tokenizer adı string olarak gelir.
    Bu string'i uygun Python nesnesine dönüştürmek gerekir.

    Bunu route içinde yapmak kötü bir yaklaşımdır çünkü:
    - if/elif blokları büyür
    - route katmanı iş mantığıyla kirlenir
    - genişletilebilirlik azalır

    Bu sınıfın amacı:
    - string olarak gelen tokenizer adını normalize etmek
    - uygun tokenizer nesnesini üretmek
    - route katmanında if/elif dağınıklığını önlemek
    - tokenizer registry mantığını tek bir merkezde tutmak

    Factory yaklaşımı sayesinde:
    - tokenizer seçimi tek yerde toplanır
    - yeni tokenizer eklemek çok kolay olur
    - sistem daha maintainable hale gelir

    Örnek:
        TokenizerFactory.create("char") -> CharTokenizer()
        TokenizerFactory.create("byte") -> ByteTokenizer()
    """

    @staticmethod
    def get_registry() -> dict[str, Any]:
        """
        Sistemin desteklediği tokenizer kayıtlarını döndürür.

        Registry mantığı:
        -----------------
        Anahtar:
            dış dünyadan gelen tokenizer adı

        Değer:
            ilgili tokenizer nesnesi

        Neden sözlük kullanıyoruz?
        --------------------------
        Çünkü lookup işlemi nettir, hızlıdır ve genişletmesi kolaydır.

        Returns:
            dict[str, Any]:
                Desteklenen tokenizer isimlerini ilgili tokenizer
                değer olarak tokenizer instance'ı içeren sözlük.
        """

        registry: dict[str, Any] = {
            "char": CharTokenizer(),
            "byte": ByteTokenizer(),
            "bpe": SimpleBPETokenizer(),
            "byte_bpe": ByteBPETokenizer(),
            "word": WordTokenizer(),    
        }

        return registry

    @staticmethod
    def get_supported_tokenizers() -> list[str]:
        """
        Desteklenen tokenizer adlarını liste halinde döndürür.

        Bu metodun kullanım alanları:
        - hata mesajlarında kullanıcıya desteklenen seçenekleri göstermek
        - ileride /api/tokenizers gibi bir endpoint yazılırsa onu beslemek
        - testlerde registry doğrulaması yapmak

        Returns:
            list[str]:
                Sistem tarafından tanınan tokenizer isimleri.

        Örnek:
            ["char", "byte", "bpe", "byte_bpe", "word"]
        """
        return list(TokenizerFactory.get_registry().keys())


    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Tokenizer adını standart forma dönüştürür.

        Yapılan işlemler:
        - baştaki boşlukları temizler
        - sondaki boşlukları temizler
        - tüm karakterleri küçük harfe çevirir

        Bu metod neden ayrı?
        --------------------
        Çünkü normalize etme davranışını tek yerde toplamak isteriz.
        Böylece farklı yerlerde farklı string işleme mantıkları oluşmaz.

        Args:
            name (str):
                Ham tokenizer adı.

        Returns:
            str:
                Normalize edilmiş tokenizer adı.

        Örnek:
            "  Char  " -> "char"
            "BYTE"     -> "byte"
        """
        return name.strip().lower()


    @staticmethod
    def create(name: str):
        """
        Verilen tokenizer adına karşılık gelen tokenizer nesnesini üretir.

        İş akışı:
        ---------
        1. Gelen isim normalize edilir
        2. Registry içinde aranır
        3. Varsa ilgili tokenizer döndürülür
        4. Yoksa anlamlı bir exception yükseltilir

        Args:
            name (str):
                API request'inden veya başka bir katmandan gelen ham tokenizer adı.

        Returns:
            Any:
                tokenize(text) metoduna sahip tokenizer nesnesi.

        Raises:
            UnsupportedTokenizerError:
                Eğer verilen ad registry içinde bulunamazsa yükseltilir.

        Neden normalize ediyoruz?
        -------------------------
        Kullanıcı aşağıdaki gibi varyasyonlar gönderebilir:
        - "Char"
        - " char "
        - "BYTE"
        - "Word"

        Bunların hepsini güvenli biçimde standart hale getirmek isteriz.
        """

        normalized_name = TokenizerFactory.normalize_name(name) # gelen adı standart hale getirir (örneğin " char " -> "char")
        registry = TokenizerFactory.get_registry() # desteklenen tokenizer'ların kayıtlı olduğu sözlüğü alır

        tokenizer = registry.get(normalized_name) # normalize edilmiş adı kullanarak registry'den tokenizer nesnesini almaya çalışır

        if tokenizer is None:
            supported_tokenizers = ", ".join(TokenizerFactory.get_supported_tokenizers()) # desteklenen tokenizer isimlerini virgülle ayrılmış string olarak hazırlar
            raise UnsupportedTokenizerError(
                f"Unsupported tokenizer: '{name}'. "
                f"Supported tokenizers: {supported_tokenizers}"
            )

        return tokenizer


# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------
def _validate_tokenizer_interface(tokenizer: Any, tokenizer_name: str) -> None:
    """
    Verilen tokenizer nesnesinin beklenen minimum arayüzü sağlayıp sağlamadığını doğrular.

    Beklenen minimum sözleşme:
    -------------------------
    Tokenizer nesnesinde:
    - `tokenize` isminde bir metod bulunmalı
    - bu metod callable olmalı

    Neden bu kontrolü yapıyoruz?
    ----------------------------
    Python dinamik tipli bir dil olduğu için yanlış nesneler sisteme kolayca girebilir.
    Örneğin:
    - import hatası sonrası yanlış obje gelebilir
    - registry'ye yanlış tipte bir nesne eklenmiş olabilir
    - geliştirici tokenize yerine başka isim kullanmış olabilir

    Bu kontrol savunmacı programlama sağlar.

    Args:
        tokenizer (Any):
            Factory tarafından üretilen tokenizer nesnesi

        tokenizer_name (str):
            Hata mesajlarında kullanılacak tokenizer adı

    Raises:
        TokenizationServiceError:
            Eğer tokenizer nesnesi beklenen arayüzü sağlamıyorsa
    """

    if not hasattr(tokenizer, "tokenize") or not callable(getattr(tokenizer, "tokenize")):
        raise TokenizationServiceError(
            f"Tokenizer '{tokenizer_name}' does not implement a callable 'tokenize' method."
        )


def _normalize_tokens(tokens: Any) -> list[str]:
    """
    Tokenizer çıktısını API response katmanına uygun, tutarlı bir formata dönüştürür.

    Neden gerekli?
    --------------
    Farklı tokenizer implementasyonları farklı formatlarda çıktı verebilir:
    - Bazı tokenizer'lar list[str] döndürebilir
    - Bazıları list[int] veya başka bir iterable döndürebilir
    - list[str]
    - list[int]
    - tuple
    - generator
    - başka iterable yapılar

    Ancak API katmanında daha stabil ve öngörülebilir bir sözleşme istenir.
    Bu nedenle tüm tokenları string listesine dönüştürülür.

    Strateji:
    ---------
    1. Çıktıyı list(...) ile somutlaştır
    2. Her elemanı str(...) ile string'e çevir
    3. API response modeline güvenli biçimde aktar

    Bunun faydası:
    --------------
    - frontend tarafı daha tutarlı veri alır
    - response modeli basitleşir
    - serializer sürprizleri azalır

    Args:
        tokens (Any):
            Tokenizer tarafından döndürülen ham çıktı

    Returns:
        list[str]:
            String listesine normalize edilmiş tokenlar

     Raises:
        TokenizationServiceError:
            Eğer çıktı listeye dönüştürülemiyor veya normalize edilemiyorsa.
    """

    try:
        return [str(token) for token in list(tokens)] # tokens'ı önce list'e dönüştürür, sonra her elemanı string'e çevirir ve yeni bir liste oluşturur.
    except Exception as exc:
        raise TokenizationServiceError(
            "Tokenizer output could not be normalized into a list of strings."
        ) from exc


def _deduplicate_tokenizer_names(tokenizer_names: list[str]) -> list[str]:
    """
    Tokenizer isimlerini normalize ederek tekrar edenleri kaldırır.

    Neden gerekli?
    --------------
    Frontend aynı tokenizer'ı birden fazla kez gönderebilir.
    Compare akışında aynı tokenizer'ı tekrar tekrar çalıştırmak istemeyiz.

    Strateji:
    ---------
    - sırayı koru
    - normalize et
    - tekrarları kaldır

    Args:
        tokenizer_names (list[str]):
            Ham tokenizer isimleri.

    Returns:
        list[str]:
            Normalize edilmiş ve tekrarları kaldırılmış tokenizer listesi.
    """

    normalized_names: list[str] = [] # normalize edilmiş ve tekrarları kaldırılmış tokenizer isimlerini tutacak liste
    seen: set[str] = set() # normalize edilmiş isimleri takip etmek için set

    for name in tokenizer_names:
        normalized_name = TokenizerFactory.normalize_name(name) # gelen ismi normalize eder (örneğin " char " -> "char")

        if normalized_name not in seen:
            seen.add(normalized_name) # normalize edilmiş ismi gördüklerimize ekle
            normalized_names.append(normalized_name) # normalize edilmiş ismi sonuç listesine ekle

    return normalized_names


def _calculate_metrics(tokens: list[str], latency_seconds: float, source_text: str) -> dict[str, Any]:
    """
    Token listesi üzerinden detaylı metrikler hesaplar.
    """

    token_count = len(tokens)
    unique_token_count = len(set(tokens))
    unique_ratio = (unique_token_count / token_count) if token_count > 0 else 0.0

    token_lengths = [len(token) for token in tokens]
    average_token_length = (
        sum(token_lengths) / token_count if token_count > 0 else 0.0
    )
    min_token_length = min(token_lengths) if token_lengths else 0
    max_token_length = max(token_lengths) if token_lengths else 0

    avg_chars_per_token = (
        len(source_text) / token_count if token_count > 0 else 0.0
    )

    # Şimdilik bilinmeyen token mantığı yoksa 0 bırakıyoruz.
    unknown_count = sum(1 for token in tokens if token in {"[UNK]", "<unk>", "UNK"})
    unknown_rate = (unknown_count / token_count) if token_count > 0 else 0.0

    # Basit bir efficiency score:
    # daha az token + daha düşük unknown rate -> daha iyi
    # bu ilk sürüm için yeterli
    efficiency_score = (
        avg_chars_per_token * (1 - unknown_rate)
        if token_count > 0
        else 0.0
    )

    top_tokens = Counter(tokens).most_common(5)

    token_length_distribution: dict[str, int] = {}
    for length in token_lengths:
        key = str(length)
        token_length_distribution[key] = token_length_distribution.get(key, 0) + 1

    reconstructed_text = " ".join(tokens) if tokens else ""
    reconstruction_match = reconstructed_text == source_text if reconstructed_text else False

    return {
        "token_count": token_count,
        "unique_token_count": unique_token_count,
        "unique_ratio": unique_ratio,
        "average_token_length": average_token_length,
        "min_token_length": min_token_length,
        "max_token_length": max_token_length,
        "avg_chars_per_token": avg_chars_per_token,
        "unknown_count": unknown_count,
        "unknown_rate": unknown_rate,
        "latency_seconds": latency_seconds,
        "efficiency_score": efficiency_score,
        "top_tokens": top_tokens,
        "token_length_distribution": token_length_distribution,
        "reconstructed_text": reconstructed_text,
        "reconstruction_match": reconstruction_match,
    }


def _build_pairwise_comparisons(
    evaluations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Tokenizer sonuçları arasında pairwise comparison üretir.
    """

    pairwise_results: list[dict[str, Any]] = []

    for left, right in combinations(evaluations, 2):
        left_tokens = set(left["tokens"])
        right_tokens = set(right["tokens"])

        common_tokens = sorted(left_tokens & right_tokens)
        unique_to_left = sorted(left_tokens - right_tokens)
        unique_to_right = sorted(right_tokens - left_tokens)

        union_count = len(left_tokens | right_tokens)
        overlap_ratio = (
            len(common_tokens) / union_count if union_count > 0 else 0.0
        )

        pairwise_results.append(
            {
                "left_name": left["name"],
                "right_name": right["name"],
                "common_tokens": common_tokens,
                "unique_to_left": unique_to_left,
                "unique_to_right": unique_to_right,
                "overlap_ratio": overlap_ratio,
            }
        )

    return pairwise_results


# ---------------------------------------------------------
# Application Service
# ---------------------------------------------------------
def tokenize_text(text: str, tokenizer_name: str) -> dict:
    """
    Verilen ham metni seçilen tokenizer ile işler ve standartlaştırılmış sonuç döndürür.

    Bu fonksiyon service katmanının ana giriş noktasıdır.
    Route katmanı tipik olarak yalnızca bu fonksiyonu çağırmalıdır.

    İş akışı:
    1. Tokenizer adı alınır ve normalize edilir
    2. Factory üzerinden uygun tokenizer nesnesi üretilir
    3. Tokenizer arayüzü doğrulanır
    4. Metin tokenize edilir
    5. Çıktı normalize edilir
    6. Özet metrikler hesaplanır
    7. Çıktı API response katmanına uygun hale getirilir
    8. Özet metriklerle birlikte sözlük döndürülür

    Args:
        text (str):
            Tokenize edilecek ham metin.

        tokenizer_name (str):
            Kullanılacak tokenizer adı.

    Args:
        text (str):
            Tokenize edilecek ham metin.

            Not:
                Bu fonksiyon metnin boş olup olmadığını kontrol etmez;
                bu doğrulama normalde schema katmanında yapılır.

        tokenizer_name (str):
            Kullanılacak tokenizer adı.

            Örnek değerler:
                - "char"
                - "byte"
                - "bpe"
                - "byte_bpe"
                - "word"

    Returns:
        dict[str, Any]:
            API response katmanına uygun sonuç sözlüğü.

            Beklenen yapı:
                {
                    "tokenizer_name": "char",
                    "tokens": ["M", "e", "r"],
                    "token_count": 3,
                    "vocab_size": 3
                }

        Alan açıklamaları:
            tokenizer_name:
                Normalize edilmiş tokenizer adı

            tokens:
                String listesine dönüştürülmüş token çıktısı

            token_count:
                Toplam token sayısı

            vocab_size:
                Benzersiz token sayısı

     Raises:
        UnsupportedTokenizerError:
            Kullanıcı desteklenmeyen bir tokenizer adı gönderirse.

        TokenizationServiceError:
            Tokenizer arayüzü bozuksa, normalize işlemi başarısızsa
            veya service katmanında beklenmeyen bir hata oluşursa.

    Tasarım notu:
    -------------
    Bu fonksiyonun dict döndürmesinin sebebi, route katmanında response modeline
    kolayca map edilebilmesidir.
    """

    try:
        # Tokenizer nesnesini factory üzerinden al.
        tokenizer = TokenizerFactory.create(tokenizer_name)

        # Nesnenin beklenen sözleşmeyi sağlayıp sağlamadığını kontrol et.
        _validate_tokenizer_interface(tokenizer, tokenizer_name)

        # Tokenization işlemini gerçekleştir.
        raw_tokens = tokenizer.tokenize(text)

        # API response için tokenları standardize et.
        normalized_tokens = _normalize_tokens(raw_tokens)

        # Sonuç sözlüğünü oluştur.
        result: dict[str, Any] = {
            "tokenizer_name": TokenizerFactory.normalize_name(tokenizer_name),
            "tokens": normalized_tokens,
            "token_count": len(normalized_tokens),
            "vocab_size": len(set(normalized_tokens)),
        }

        return result

    except UnsupportedTokenizerError:
        # Bu hata tipi kontrollü olduğu için aynen yukarı taşınır.
        raise

    except TokenizationServiceError:
        # Önceden anlamlandırılmış servis hataları aynen yukarı taşınır.
        raise

    except Exception as exc:
        # Beklenmeyen low-level hataları servis seviyesinde sar.
        raise TokenizationServiceError(
            "An unexpected error occurred while tokenizing the text."
        ) from exc


def compare_tokenizers(text: str, tokenizer_names: list[str]) -> dict[str, Any]:
    """
    Aynı ham metni birden fazla tokenizer ile işler ve sonuçları toplu olarak döndürür.

    Bu fonksiyonun temel amacı:
    ---------------------------
    Tek bir tokenizer ile çalışmak yerine, aynı metin üzerinde birden fazla
    tokenizer davranışını karşılaştırmalı biçimde incelemeyi sağlamaktır.

    Bu fonksiyon:
    - aynı input text'i alır
    - seçilen tokenizer listesini sırayla çalıştırır
    - her tokenizer sonucunu standartlaştırılmış yapıda üretir
    - tüm sonuçları tek bir response sözlüğünde toplar

    Bu fonksiyon neden gereklidir?
    ------------------------------
    Tekli tokenization işlemi için `tokenize_text(...)` fonksiyonu yeterlidir.
    Ancak compare ekranı veya karşılaştırmalı analiz senaryolarında kullanıcı tek bir çağrıyla:

    - char tokenizer sonucu
    - byte tokenizer sonucu
    - word tokenizer sonucu
    - bpe tokenizer sonucu
    - byte_bpe tokenizer sonucu

    gibi çoklu çıktıları aynı anda görmek ister.

    Bu nedenle bu fonksiyon, compare use-case'inin service katmanındaki ana giriş noktasıdır.

    Yüksek seviye iş akışı:
    ----------------------
    1. Gelen tokenizer listesi boş mu kontrol edilir
    2. Tokenizer isimleri normalize edilir
    3. Tekrar eden tokenizer isimleri kaldırılır
    4. Her tokenizer için `tokenize_text(...)` çağrılır
    5. Tüm sonuçlar tek bir toplu response yapısında birleştirilir
    6. UI veya API katmanına hazır veri döndürülür

    Neden tokenizer isimleri normalize edilir?
    ----------------------------------------------
    Kullanıcı veya frontend şu tür varyasyonlar gönderebilir:
    - "Char"
    - " char "
    - "BYTE"
    - "Word"

    Bu farklılıkların aynı tokenizer'a karşılık geldiğini bilmek istenir.
    Bu nedenle önce isimleri normalize edilir.

    Neden tekrar eden isimleri kaldırılır?
    ----------------------------------------
    Kullanıcı teorik olarak şu listeyi gönderebilir:
        ["char", "char", "byte"]

    Böyle bir durumda aynı tokenizer'ı gereksiz yere iki kez çalıştırmak
    hem performans kaybına neden olur hem de compare sonucunu kirletir.

    Bu yüzden:
    - sırayı koruruz
    - ama tekrar eden isimleri tekilleştiririz

    Neden doğrudan tokenizer nesnesiyle değil `tokenize_text(...)` ile çalışılır?
    -------------------------------------------------------------------------------
    Çünkü `tokenize_text(...)` zaten:
    - tokenizer oluşturma
    - interface doğrulama
    - token normalize etme
    - token_count hesaplama
    - vocab_size hesaplama

    gibi tüm ortak iş mantığını merkezi biçimde yapmaktadır.

    Eğer burada tekrar tokenizer nesnesi oluşturup yeniden aynı akışı yazılsaydı:
    - kod tekrarı oluşurdu
    - bakım maliyeti artardı
    - hata riski yükselirdi

    Bu yüzden compare fonksiyonu, tekli tokenize servisinin üstüne kurulu
    daha yüksek seviyeli bir orchestration servisidir.

    Args:
        text (str):
            Tüm tokenizer'lar üzerinde çalıştırılacak ham metin.

            Not:
                Bu fonksiyon metnin boş olup olmadığını ayrıca doğrulamaz.
                Bu doğrulama normalde schema / request model katmanında yapılır.

        tokenizer_names (list[str]):
            Çalıştırılacak tokenizer isimlerinin listesi.

            Örnek:
                ["char", "byte", "word"]

            Not:
                Liste boş ise işlem anlamlı olmadığı için hata yükseltilir.

    Returns:
        dict[str, Any]:
            Compare response modeline uygun sonuç sözlüğü döndürür.

            Beklenen yapı:
                {
                    "text": "Merhaba dünya!",
                    "total_tokenizers": 3,
                    "results": [
                        {
                            "tokenizer_name": "char",
                            "tokens": ["M", "e"],
                            "token_count": 2,
                            "vocab_size": 2
                        },
                        {
                            "tokenizer_name": "byte",
                            "tokens": ["77", "101"],
                            "token_count": 2,
                            "vocab_size": 2
                        }
                    ]
                }

            Alan açıklamaları:
                text:
                    Karşılaştırma yapılan orijinal input metin

                total_tokenizers:
                    Başarıyla çalıştırılan tokenizer sayısı

                results:
                    Her tokenizer için standart tokenization sonucu listesi

    Raises:
        TokenizationServiceError:
            Aşağıdaki durumlarda yükseltilir:
            - tokenizer listesi boşsa
            - compare akışı sırasında beklenmeyen teknik hata oluşursa

        UnsupportedTokenizerError:
            Desteklenmeyen tokenizer adı verilirse yükseltilir.

    Tasarım notu:
    -------------
    Bu fonksiyon `dict[str, Any]` döndürür çünkü route katmanında
    Pydantic response modeline kolayca map edilebilmesi istenir.

    Yani route katmanı şunu rahatça yapabilir:
        CompareResponse(**result)

    Bu yaklaşım:
    - response contract ile service katmanını uyumlu tutar
    - API entegrasyonunu sadeleştirir
    - test yazmayı kolaylaştırır
    """

    # En az bir tokenizer seçilmiş olmalıdır.
    # Boş liste ile compare yapmak anlamsız olduğu için erken hata üretiriz.
    if not tokenizer_names:
        raise TokenizationServiceError("At least one tokenizer must be selected.")

    try:
        # Tokenizer isimlerini normalize eder ve tekrar edenleri kaldırır.
        normalized_names = _deduplicate_tokenizer_names(tokenizer_names)

        # Her tokenizer için mevcut tekli tokenization servis fonksiyonunu çağırır.
        # Böylece ortak mantık tek merkezden yeniden kullanılmış olur.
        results = [
            tokenize_text(text=text, tokenizer_name=name)
            for name in normalized_names
        ]

        # Compare response yapısını oluşturur.
        return {
            "text": text,
            "total_tokenizers": len(results),
            "results": results,
        }

    except UnsupportedTokenizerError:
        # Beklenen ve anlamlı hata tipi olduğu için aynen yukarı taşınır.
        raise

    except TokenizationServiceError:
        # Servis seviyesinde zaten anlamlandırılmış hata olduğu için
        # yeniden sarmalamadan yukarı taşırız.
        raise

    except Exception as exc:
        # Beklenmeyen low-level hataları daha kontrollü bir servis hatasına dönüştürürüz.
        raise TokenizationServiceError(
            "An unexpected error occurred while comparing tokenizers."
        ) from exc


def compare_tokenizers_rich(text: str, tokenizer_names: list[str]) -> dict[str, Any]:
    """
    Aynı metni birden fazla tokenizer ile çalıştırır ve zenginleştirilmiş
    compare response üretir.

    Dönen yapı:
    - source_text
    - evaluations
    - pairwise_comparisons
    """

    if not tokenizer_names:
        raise TokenizationServiceError("At least one tokenizer must be selected.")

    try:
        normalized_names = _deduplicate_tokenizer_names(tokenizer_names)

        evaluations: list[dict[str, Any]] = []

        for name in normalized_names:
            tokenizer = TokenizerFactory.create(name)
            _validate_tokenizer_interface(tokenizer, name)

            start = perf_counter()
            raw_tokens = tokenizer.tokenize(text)
            end = perf_counter()

            normalized_tokens = _normalize_tokens(raw_tokens)
            latency_seconds = end - start

            metrics = _calculate_metrics(
                tokens=normalized_tokens,
                latency_seconds=latency_seconds,
                source_text=text,
            )

            evaluations.append(
                {
                    "name": TokenizerFactory.normalize_name(name),
                    "tokens": normalized_tokens,
                    "metrics": metrics,
                }
            )

        pairwise_comparisons = _build_pairwise_comparisons(evaluations)

        return {
            "source_text": text,
            "evaluations": evaluations,
            "pairwise_comparisons": pairwise_comparisons,
        }

    except UnsupportedTokenizerError:
        raise

    except TokenizationServiceError:
        raise

    except Exception as exc:
        raise TokenizationServiceError(
            "An unexpected error occurred while generating the rich comparison result."
        ) from exc