"""
exceptions.py

Bu modül, uygulamanın servis (service) katmanında kullanılan özel exception
(hata) tiplerini tanımlar.

---------------------------------------------------------------------------
Amaç
---------------------------------------------------------------------------
Bu modülün temel amacı, uygulama içinde oluşabilecek hataları:

- domain’e (iş mantığına) özel hale getirmek
- anlamlı ve ayrıştırılabilir hata türleri oluşturmak
- hata yönetimini merkezi ve tutarlı bir yapıya oturtmak

---------------------------------------------------------------------------
Neden Custom Exception?
---------------------------------------------------------------------------
Python'ın yerleşik exception türleri (ValueError, RuntimeError vb.)
genel amaçlıdır ve çoğu zaman uygulama bağlamını yeterince ifade etmez.

Bu nedenle:

- "UnsupportedTokenizerError" gibi spesifik hatalar,
  hatanın nedenini doğrudan ifade eder
- debugging ve logging süreçleri kolaylaşır
- API katmanında daha doğru HTTP response üretilebilir

---------------------------------------------------------------------------
Mimari Rol
---------------------------------------------------------------------------
Bu exception’lar yalnızca servis katmanında fırlatılır (raise edilir).

Akış şu şekildedir:

    route/controller
        ↓
    service layer (exception burada oluşur)
        ↓
    exception yakalanır
        ↓
    HTTP response’a dönüştürülür

Bu yaklaşım sayesinde:

- servis katmanı HTTP bağımsız kalır
- API katmanı hata dönüşünü kontrol eder
- katmanlar arası sorumluluk ayrımı korunur

---------------------------------------------------------------------------
Kullanım Prensipleri
---------------------------------------------------------------------------
- Her exception belirli bir hata senaryosunu temsil etmelidir
- Generic Exception yerine mümkün olduğunca bu özel türler kullanılmalıdır
- Bu exception’lar doğrudan kullanıcıya gösterilmez,
  API katmanında anlamlı mesajlara dönüştürülür
"""


class UnsupportedTokenizerError(ValueError):
    """
    Desteklenmeyen veya sistemde tanımlı olmayan bir tokenizer adı verildiğinde yükseltilir.

    -----------------------------------------------------------------------
    Ne Zaman Kullanılır?
    -----------------------------------------------------------------------
    - Kullanıcı, sistemde kayıtlı olmayan bir tokenizer talep ettiğinde
    - TokenizerFactory içinde ilgili tokenizer bulunamadığında

    -----------------------------------------------------------------------
    Teknik Anlamı
    -----------------------------------------------------------------------
    Bu hata, giriş verisinin (input) geçersiz olduğunu ifade eder.
    Yani hata, sistemin çalışmasından değil, kullanıcı isteğinden kaynaklanır.

    -----------------------------------------------------------------------
    Örnek Senaryo
    -----------------------------------------------------------------------
    Kullanıcı şu isteği gönderir:

        tokenizer_name = "unknown_tokenizer"

    Sistem bu tokenizer'ı registry içinde bulamaz ve:

        raise UnsupportedTokenizerError(...)

    -----------------------------------------------------------------------
    API Katmanında Beklenen Davranış
    -----------------------------------------------------------------------
    Bu hata genellikle aşağıdaki HTTP response ile eşleştirilir:

        HTTP 400 Bad Request

    Çünkü istemci geçersiz bir değer göndermiştir.
    """


class TokenizationServiceError(Exception):
    """
    Tokenization servis katmanında oluşan beklenmeyen veya teknik hataları temsil eder.

    -----------------------------------------------------------------------
    Ne Zaman Kullanılır?
    -----------------------------------------------------------------------
    - tokenizer çalıştırılırken hata oluştuğunda
    - tokenizer çıktısı beklenen formatta olmadığında
    - metrik hesaplama sırasında exception oluştuğunda
    - sistem içinde öngörülemeyen bir durum ortaya çıktığında

    -----------------------------------------------------------------------
    Teknik Anlamı
    -----------------------------------------------------------------------
    Bu hata, sistemin iç işleyişi sırasında oluşan bir problemi ifade eder.
    Yani hata, kullanıcıdan değil sistemden kaynaklanır.

    -----------------------------------------------------------------------
    Örnek Senaryolar
    -----------------------------------------------------------------------
    - tokenize() fonksiyonu exception fırlatır
    - token listesi normalize edilemez
    - metrik hesaplama sırasında bölme hatası oluşur
    - veri tipi beklenenden farklı gelir

    -----------------------------------------------------------------------
    API Katmanında Beklenen Davranış
    -----------------------------------------------------------------------
    Bu hata genellikle aşağıdaki HTTP response ile eşleştirilir:

        HTTP 500 Internal Server Error

    Çünkü bu bir sistem hatasıdır.

    -----------------------------------------------------------------------
    Not
    -----------------------------------------------------------------------
    Bu exception, kullanıcıya doğrudan gösterilmemelidir.
    Bunun yerine API katmanında:

    - daha genel bir hata mesajı döndürülmeli
    - detaylı hata bilgisi loglanmalıdır
    """