"""
base.py

Bu modül, API request modellerinde tekrar eden ortak alanları ve
validation kurallarını merkezi hale getirmek için oluşturulmuştur.

Amaç:
-----
- Text tabanlı request modellerinde tekrar eden `text` alanını tek yerde tanımlamak
- Birden fazla tokenizer kullanan request'lerde `tokenizer_names` alanını standartlaştırmak
- Kullanıcıdan gelen veriyi servis katmanına gitmeden önce normalize etmek
- Boş, anlamsız veya tekrar eden input'ları erken aşamada engellemek
- API contract'ını daha tutarlı, okunabilir ve sürdürülebilir hale getirmek

Bu dosyada tanımlanan sınıflar doğrudan endpoint request'i olarak kullanılmak zorunda değildir.
Asıl kullanım amacı, başka request modelleri tarafından miras alınmalarıdır.

Örnek:
------
class CompareRequest(BaseTokenizerListRequest):
    pass

class ReportRequest(BaseTokenizerListRequest):
    format: Literal["txt", "md"] = "txt"

Bu sayede CompareRequest ve ReportRequest modelleri otomatik olarak:
- text alanına
- tokenizer_names alanına
- text validation kurallarına
- tokenizer_names validation kurallarına
sahip olur.
"""

from pydantic import BaseModel, Field, field_validator


class BaseTextRequest(BaseModel):
    """
    Text alanı içeren tüm request modelleri için ortak base model.

    Bu sınıfın temel sorumluluğu:
    ----------------------------
    API'ye gönderilen `text` alanını doğrulamak ve normalize etmektir.

    Yapılan validation işlemleri sayesinde servis katmanına gelen text verisi:
    - text alanı zorunludur
    - text boş string olamaz
    - text yalnızca whitespace karakterlerinden oluşamaz
    - text başındaki ve sonundaki boşluklardan temizlenir
    - text maksimum 10.000 karakter olabilir

    Bu sınıf, API'ye gönderilen ham metin verisinin temel doğrulamasını yapar.    

    Neden base class olarak ayrıldı?
    ------------------------------
    Birden fazla endpoint aynı şekilde text alıyorsa,
    her request modelinde tekrar tekrar aynı Field ve validator yazmak
    kod tekrarına neden olur.

    Örneğin:
    - /tokenize
    - /compare
    - /report
    - /analyze

    Eğer her request modelinde tekrar tekrar `text` alanı ve aynı validation
    kuralları yazılırsa:

    - kod tekrarı artar
    - bakım maliyeti yükselir
    - bir endpoint'te validation varken diğerinde unutulabilir
    - API davranışı tutarsız hale gelebilir

    Bu nedenle ortak davranışı base class içinde toplamak daha doğru bir tasarımdır.

    Bu sınıfın sağladığı contract:
    ------------------------------
    Bu sınıftan türeyen herhangi bir request modelinde `text` alanı her zaman
    anlamlı ve temizlenmiş bir string olarak kabul edilebilir.

    Yani servis katmanı şuna güvenebilir:

        request.text

    değeri:
    - trim edilmiştir
    - boş değildir
    - whitespace-only değildir
    """

    text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description=(
            "İşlenecek ham metin. "
            "Bu alan zorunludur. "
            "Boş string olamaz. "
            "Yalnızca boşluk, tab veya satır sonu karakterlerinden oluşamaz. "
            "Başındaki ve sonundaki boşluklar sistem tarafından temizlenir. "
            "En fazla 10.000 karakter uzunluğunda olabilir."
        ),
        examples=[
            "Merhaba dünya!",
            "Hello world!",
            "Tokenizer karşılaştırması için örnek metin.",
        ],
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """
        text alanını normalize eder ve doğrular.

        Bu validator neden gerekli?
        ---------------------------
        Pydantic tarafında `min_length=1` kullanmak boş string'i engeller.

        Ancak şu değerler hâlâ problemli olabilir:

            "   "
            "\\n"
            "\\t"
            " \\n\\t "

        Bu değerlerin karakter uzunluğu 1'den büyük olabilir.
        Yani teknik olarak string uzunluğu vardır.
        Fakat uygulama açısından anlamlı bir metin değildir.

        Bu yüzden sadece uzunluk kontrolü yeterli değildir.
        Ek olarak semantic validation yapılmalıdır.

        Yapılan işlemler:
        1. Kullanıcının gönderdiği metnin başındaki boşluklar temizlenir.
        2. Kullanıcının gönderdiği metnin sonundaki boşluklar temizlenir.
        3. Temizleme işleminden sonra metin tamamen boş kalıyorsa hata fırlatılır.
        4. Geçerli metin normalize edilmiş haliyle geri döndürülür.

        Örnek:
        -------
        Input:
            "   Merhaba dünya!   "

        Output:
            "Merhaba dünya!"

         Geçersiz örnekler:
        ------------------
            ""
            "   "
            "\\n"
            "\\t"
            " \\n\\t "

        Returns:
        --------
        str
            Normalize edilmiş, başı ve sonu temizlenmiş text değeri.

        Raises:
        -------
        ValueError
            Eğer text boşsa veya yalnızca whitespace karakterlerinden oluşuyorsa.

        Not:
        ----
        Field seviyesinde min_length=1 kontrolü olsa bile,
        sadece whitespace içeren string'ler teknik olarak uzunluğu 1'den büyük
        olabilir. Bu yüzden ayrıca strip kontrolü yapılır.
        """
        cleaned = value.strip() # Baş ve sondaki whitespace karakterlerini temizler

        if not cleaned:
            raise ValueError("text alanı boş olamaz veya yalnızca whitespace içeremez")

        return cleaned


class BaseTokenizerListRequest(BaseTextRequest):
    """
    Birden fazla tokenizer adı alan request modelleri için ortak base model.

    Bu sınıf, BaseTextRequest sınıfından miras alır.
    Bu nedenle otomatik olarak `text` alanını ve text validation mantığını içerir.

    Ek olarak:
    ----------
    - tokenizer_names alanını tanımlar
    - tokenizer isimlerini normalize eder
    - boş tokenizer isimlerini engeller
    - tekrar eden tokenizer isimlerini engeller

    Kullanım senaryoları:
    ---------------------
    Bu sınıf özellikle birden fazla tokenizer ile çalışan endpoint'lerde kullanılır.

    Örneğin:
    - tokenizer karşılaştırma endpoint'i
    - tokenizer raporu üretme endpoint'i
    - çoklu tokenizer analiz endpoint'i

    Örnek kullanım:
    ---------------
    class CompareRequest(BaseTokenizerListRequest):
        pass

    class ReportRequest(BaseTokenizerListRequest):
        format: Literal["txt", "md", "pdf"] = "md"

    Bu durumda CompareRequest ve ReportRequest modelleri şu alanlara sahip olur:

        text: str
        tokenizer_names: list[str]

    Bu sınıfın sağladığı contract:
    ------------------------------
    Bu sınıftan türeyen request modellerinde `tokenizer_names` her zaman:

    - tokenizer_names zorunludur
    - en az bir tokenizer adı içermelidir
    - her tokenizer adı trim edilir
    - her tokenizer adı lowercase hale getirilir
    - boş tokenizer adı gönderilemez
    - aynı tokenizer birden fazla kez gönderilemez

    Böylece servis katmanı tokenizer isimlerini işlerken tekrar tekrar
    şu kontrolleri yapmak zorunda kalmaz:

        if not tokenizer_names:
            ...

        if duplicate_exists:
            ...

        if name.strip() == "":
            ...

    Bu validation yükü model seviyesinde çözülmüş olur.

    Neden normalize ediliyor?
    -------------------------
    Kullanıcı API'ye şu şekilde veri gönderebilir:

        [" Char ", "WORD", " byte_bpe "]

    Bu değerler normalize edilerek şu hale getirilir:

        ["char", "word", "byte_bpe"]

    Böylece servis katmanında tokenizer isimleri daha tutarlı işlenir.
    """

    tokenizer_names: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "İşlemde kullanılacak tokenizer isimlerinin listesi. "
            "Liste en az bir tokenizer adı içermelidir. "
            "Her tokenizer adı sistem tarafından normalize edilir. "
            "Normalize işlemi sırasında baştaki ve sondaki boşluklar temizlenir "
            "ve isimler lowercase hale getirilir. "
            "Aynı tokenizer adı birden fazla kez gönderilemez."
        ),
        examples=[
            ["char", "word"],
            ["bpe", "byte_bpe"],
            ["char", "word", "byte_bpe"],
        ],
    )

    @field_validator("tokenizer_names")
    @classmethod
    def validate_tokenizer_names(cls, value: list[str]) -> list[str]:
        """
        tokenizer_names listesini normalize eder ve doğrular.

        Bu validator'ın amacı:
        ----------------------
        Kullanıcıdan gelen tokenizer isimlerini servis katmanına gitmeden önce
        standart ve güvenilir hale getirmektir.

        Neden normalize ediyoruz?
        -------------------------
        Kullanıcı API'ye tokenizer isimlerini farklı biçimlerde gönderebilir.

        Örneğin:

            [" Char ", "WORD", " byte_bpe "]

        Bu değerler normalize edilmezse sistem içinde şu problemler oluşabilir:

        - " Char " ile "char" farklı string olarak değerlendirilir
        - "WORD" ile "word" farklı string olarak değerlendirilir
        - tokenizer registry içinde eşleşme bulunamayabilir
        - aynı tokenizer farklı yazımlarla tekrar tekrar çalıştırılabilir

        Normalize sonrası liste şu hale gelir:

            ["char", "word", "byte_bpe"]

         Yapılan işlemler:
        -----------------
        1. Her tokenizer adı için `strip()` uygulanır.
           Böylece baştaki ve sondaki boşluklar silinir.

        2. Her tokenizer adı için `lower()` uygulanır.
           Böylece büyük/küçük harf farkından doğan tutarsızlıklar engellenir.

        3. Boş tokenizer adı kontrol edilir.
           Örneğin:
               ["char", ""]
               ["char", "   "]

           Bu input'lar geçersiz kabul edilir.

        4. Duplicate kontrolü yapılır.
           Örneğin:
               ["char", "CHAR"]

           Normalize edildikten sonra:
               ["char", "char"]

           haline gelir ve duplicate kabul edilir.

        5. Normalize edilmiş liste geri döndürülür.

        Neden duplicate engelleniyor?
        -----------------------------
        Aynı tokenizer'ın birden fazla kez gönderilmesi gereksiz işlem yükü
        oluşturur ve karşılaştırma/rapor çıktısında tekrar eden sonuçlara
        neden olabilir.

        Geçerli input örnekleri:
        ------------------------
            ["char"]
            ["char", "word"]
            [" Char ", "WORD", " byte_bpe "]

        Geçersiz input örnekleri:
        -------------------------
            []
            ["char", ""]
            ["char", "   "]
            ["char", "CHAR"]

        Son örnekte "char" ve "CHAR" normalize edildikten sonra
        aynı değere dönüştüğü için duplicate kabul edilir. 

        Returns:
        --------
        list[str]
            Normalize edilmiş tokenizer isimleri listesi.

        Örneğin:

            ["char", "char"]

        Bu durumda sistem:
        - aynı tokenizer'ı iki kez çalıştırabilir
        - raporda tekrar eden sonuçlar üretebilir
        - gereksiz işlem maliyeti oluşturabilir
        - karşılaştırma çıktısını anlamsız hale getirebilir

        Bu yüzden duplicate tokenizer isimleri request seviyesinde engellenir.

        Raises:
        -------
        ValueError
            Eğer listede boş tokenizer adı varsa
            veya aynı tokenizer birden fazla kez gönderilmişse.

        Örnek:
        -------
        Input:
            [" Char ", "WORD", " byte_bpe "]

        Output:
            ["char", "word", "byte_bpe"]              
        """
        normalized = [name.strip().lower() for name in value] # Normalize işlemi: trim + lowercase

        if any(not name for name in normalized): # Boş tokenizer kontrolü
            raise ValueError("tokenizer_names içinde boş değer bulunamaz")

        if len(set(normalized)) != len(normalized): # Duplicate kontrolü
            raise ValueError("Aynı tokenizer birden fazla kez gönderilemez")

        return normalized