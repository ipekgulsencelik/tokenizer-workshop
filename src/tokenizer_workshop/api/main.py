"""
main.py

Bu dosya, FastAPI uygulamasının ana giriş noktasıdır (application entrypoint).

Temel sorumlulukları:
- FastAPI uygulamasını başlatmak
- uygulama metadata bilgisini tanımlamak
- API route modüllerini uygulamaya kaydetmek
- frontend dosyalarını FastAPI üzerinden servis etmek
- sistemin dış dünyaya açılan HTTP arayüzünü oluşturmak
- OpenAPI / Swagger / ReDoc gibi geliştirici araçlarını yapılandırmak

Neden bu dosya önemlidir?
-------------------------
Bir FastAPI projesinde main.py, uygulamanın kompozisyon katmanıdır.
Yani sistemin parçaları burada birleştirilir.

Bu dosya tipik olarak:
- app nesnesini oluşturur
- router'ları bağlar
- static file serving yapılandırmasını yapar
- middleware ve global handler kayıtlarını içerir
- uygulamanın giriş davranışını tanımlar

Ancak kritik mimari kural şudur:
    Bu dosya business logic içermez.

Yani burada:
- tokenizer seçimi yapılmaz
- tokenization algoritması çalıştırılmaz
- karşılaştırma mantığı yazılmaz
- request iş mantığı route dışına taşmaz

Bu tür sorumluluklar:
- routes/
- services/
- tokenizers/
- comparisons/
gibi ilgili katmanlarda yer almalıdır.

Çalıştırma:
-----------
Development ortamı:
    $env:PYTHONPATH="src"
    uv run uvicorn tokenizer_workshop.api.main:app --reload

Production benzeri kullanım:
    $env:PYTHONPATH="src"
    uv run uvicorn tokenizer_workshop.api.main:app --host 0.0.0.0 --port 8000
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tokenizer_workshop.api.routes.health import router as health_router
from tokenizer_workshop.api.routes.tokenize import router as tokenize_router


# ---------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------
# Bu bölümün amacı, frontend dosyalarının fiziksel konumlarını
# güvenli, okunabilir ve platform bağımsız şekilde tanımlamaktır.
#
# Neden pathlib.Path kullanıyoruz?
# --------------------------------
# Çünkü path'leri string olarak yazmak kırılgan bir yaklaşımdır.
# Örneğin:
#   "src/tokenizer_workshop/web/index.html"
#
# bu tür sabit string path'ler:
# - çalışma dizini (current working directory) değişirse bozulabilir
# - farklı işletim sistemlerinde path ayracı sorunları yaşanabilir
# - proje başka klasöre taşınırsa uyumsuzluk çıkabilir
#
# Path yaklaşımı ise:
# - daha güvenlidir
# - daha okunabilirdir
# - Windows / Linux / macOS ortamlarında daha tutarlıdır
#
# __file__ nedir?
# ---------------
# __file__, içinde bulunulan Python dosyasının fiziksel konumunu verir.
#
# Path(__file__) ne yapar?
# ------------------------
# __file__ string olarak gelir.
# Path(__file__) bunu Path nesnesine dönüştürür.
#
# .resolve() ne yapar?
# --------------------
# resolve(), path'i absolute (tam) path haline getirir.
# Böylece göreli path karmaşası ortadan kalkar.
#
# .parent ne yapar?
# -----------------
# Path'in bir üst klasörünü verir.
#
# BASE_DIR neyi temsil eder?
# --------------------------
# BASE_DIR, uygulamanın bu bağlamdaki temel package klasörünü temsil eder:
#
# Bu klasör baz alınarak diğer frontend dosyalarının konumu türetilir.
#
# WEB_DIR neyi temsil eder?
# -------------------------
# Frontend dosyalarının bulunduğu ana klasördür:
#
# CSS_DIR neyi temsil eder?
# -------------------------
# CSS dosyalarının bulunduğu klasördür:
#
# JS_DIR neyi temsil eder?
# ------------------------
# JavaScript dosyalarının bulunduğu klasördür:
#
# INDEX_FILE neyi temsil eder?
# ----------------------------
# Kullanıcıya root endpoint'te döndürülecek ana HTML dosyasıdır:
#
# Bu dosya neden ayrı tanımlanıyor?
# ---------------------------------
# Çünkü:
# - root endpoint'te doğrudan bunu döndürüyoruz
# - kodun okunabilirliği artıyor
# - path'i tekrar tekrar yazmak gerekmiyor
#
# Kısacası bu blok, path yönetimini tek yerde merkezileştirir
# ve main.py içindeki static/frontend yapılandırmasını sağlam hale getirir.
BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web" # Frontend dosyalarının bulunduğu ana klasör
CSS_DIR = WEB_DIR / "css" # CSS dosyalarının bulunduğu klasör
JS_DIR = WEB_DIR / "js" # JavaScript dosyalarının bulunduğu klasör
INDEX_FILE = WEB_DIR / "index.html" # Ana HTML dosyası


# ---------------------------------------------------------
# Application Initialization
# ---------------------------------------------------------
# FastAPI uygulamasının ana nesnesi burada oluşturulur.
#
# Bu nesne:
# - gelen HTTP request'lerini karşılar
# - router'ları barındırır
# -  OpenAPI şemasını üretir
# - Swagger ve ReDoc sayfalarını servis eder
# - static file mount yapılarını yönetir
#
# Metadata alanları neden önemli?
# -------------------------------
# title:
#   API'nin görünen adı
#
# description:
#   Swagger / ReDoc üzerinde geliştiricilere bağlam sağlar
#
# version:
#   API versiyonlaması için temel metadata alanı
#
# docs_url:
#   Swagger UI endpoint'i
#
# redoc_url:
#   ReDoc dokümantasyon endpoint'i
#
# openapi_url:
#   Makine-okunur OpenAPI şema çıktısı
app = FastAPI(
    title="Tokenizer Workshop API",
    description=(
        "A professional-grade API for experimenting with, analyzing, "
        "and comparing different tokenization strategies."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ---------------------------------------------------------
# Static File Mounting
# ---------------------------------------------------------
# Bu bölüm, frontend asset dosyalarını (CSS ve JavaScript)
# FastAPI üzerinden servis edilmesini sağlar.
#
# Ne yapıliyor?
# -------------
# app.mount(...) ile belirli URL path'leri, disk üzerindeki
# klasörlere bağlanır (mount edilir).
#
# Örnek:
# -------
# Tarayıcı şunu ister:
#   http://127.0.0.1:8000/css/style.css
#
# FastAPI şunu yapar:
#   web/css/style.css dosyasını bulur
#   ve HTTP response olarak döndürür
#
# Aynı şekilde:
#   /js/app.js → web/js/app.js
#
# Bu yaklaşımın faydaları:
# - frontend ve backend tek uygulama altında birleşir
# - ayrı bir static server ihtiyacı azalır
# - demo ve deployment akışı basitleşir
#
# StaticFiles nedir?
# ------------------
# StaticFiles, FastAPI'nin (Starlette üzerinden gelen)
# statik dosya sunma (static file serving) sınıfıdır.
#
# Bu sınıf:
# - gelen HTTP GET isteğini yakalar
# - ilgili klasörde dosyayı arar
# - bulursa döner
# - bulamazsa 404 verir
#
# Neden static mount kullanılıyor?
# --------------------------------
# - frontend dosyalarını ayrı bir server olmadan sunabilir
# - deployment daha basit olur
# - tek uygulama (backend + frontend) mantığı oluşur
#
# name parametresi ne işe yarar?
# ------------------------------
# name="css" veya name="js":
# - internal routing için isimlendirme sağlar
# - URL reversing (ileride) için kullanılabilir
# - debugging açısından faydalıdır
#
# Güvenlik notu:
# --------------
# StaticFiles sadece belirtilen klasör içinden dosya servis eder.
# Bu sayede:
# - directory traversal saldırıları (../) engellenir
# - sadece izin verilen klasörler açılır
#
# Kısacası:
# ----------
# Bu iki satır:
# - frontend’i backend’e bağlar
# - UI'nin görünmesini sağlar
# - projenin “gerçek uygulama” hissini oluşturur
if CSS_DIR.exists():
    app.mount("/css", StaticFiles(directory=CSS_DIR), name="css")

if JS_DIR.exists():
    app.mount("/js", StaticFiles(directory=JS_DIR), name="js")


# ---------------------------------------------------------
# Router Registration
# ---------------------------------------------------------
# Uygulamadaki route modülleri burada merkezi olarak register edilir.
#
# Neden burada topluyoruz?
# ------------------------
# Çünkü main.py uygulamanın composition root'udur.
# Yani sistemin hangi endpoint gruplarından oluştuğu burada görünür olmalıdır.
#
# Mevcut router'lar:
# - health_router:
#     servis sağlık kontrolleri
#
# - tokenize_router:
#     tokenization ile ilgili API endpoint'leri
app.include_router(health_router)
app.include_router(tokenize_router)


# ---------------------------------------------------------
# Frontend Root Endpoint
# ---------------------------------------------------------
# # Bu endpoint, uygulamanın root (/) adresine gelen HTTP GET isteğini karşılar
# ve JSON yerine doğrudan frontend arayüzünü (index.html) döndürür.
#
# Bu tasarım bilinçli bir tercihtir.
#
# Neden root endpoint UI döndürüyor?
# ----------------------------------
# 1. Kullanıcı deneyimi:
#    Kullanıcı tarayıcıda uygulamayı açtığında doğrudan arayüzü görür.
#    Ek bir route (/ui gibi) bilmesine gerek kalmaz.
#
# 2. Demo / portfolio kolaylığı:
#    Tek URL üzerinden hem API hem UI erişilebilir olur.
#
# 3. Backend + frontend bütünleşik yapı:
#    Ayrı bir frontend server (örneğin Vite, React dev server) olmadan
#    FastAPI üzerinden statik UI servis edilir.
#
# 4. Deployment basitliği:
#    Tek servis → tek container → tek entrypoint
#
# include_in_schema=False:
# ------------------------
# Bu endpoint Swagger/OpenAPI dokümantasyonunda görünmez.
#
# Çünkü:
# - bu bir "API endpoint" değil
# - veri döndürmez, HTML döndürür
# - geliştiriciler için değil, kullanıcılar içindir
#
# Bu sayede /docs ekranı daha temiz kalır.
@app.get("/", include_in_schema=False)
def serve_index() -> FileResponse:
    """
    Uygulamanın ana kullanıcı arayüzünü (index.html) döndürür.

    Bu endpoint, frontend uygulamasının giriş noktasıdır.
    API ile etkileşime geçen UI bu HTML dosyası üzerinden yüklenir.

    Endpoint sorumlulukları:
    ------------------------
    - index.html dosyasını istemciye sunmak
    - frontend uygulamasını başlatmak
    - kullanıcıyı doğrudan arayüze yönlendirmek
    - API ile UI arasında köprü görevi görmek

    UI yükleme akışı:
    -----------------
    1. Kullanıcı tarayıcıda "/" adresine gider
    2. Bu endpoint tetiklenir
    3. index.html dosyası döndürülür
    4. HTML içindeki:
        - CSS (/css/...)
        - JS  (/js/...)
       asset'leri otomatik olarak yüklenir
    5. JavaScript (app.js) API endpoint'lerine istek atmaya başlar

    Bu yapı sayesinde:
    - frontend tamamen statik kalır
    - backend API ile konuşur
    - ek build tool zorunlu olmaz

    Asset path (çok önemli):
    ------------------------
     HTML içinde asset yolları absolute olmalıdır:

        DOĞRU:
            /css/style.css
            /js/app.js

        YANLIŞ:
            ./css/style.css
            ../js/app.js

    Çünkü:
    - FastAPI static mount absolute path bekler
    - relative path kullanımı production'da kırılabilir

    Hata yönetimi:
    --------------
    Eğer index.html dosyası bulunamazsa:
    - bu bir konfigürasyon hatasıdır
    - deployment eksik yapılmıştır
    - static dosyalar düzgün kopyalanmamıştır

    Bu durumda:
    - 500 Internal Server Error döndürülür
    - istemciye teknik detay sızdırılmaz
    - ama log tarafında incelenebilir

    Returns:
        FileResponse:
            index.html dosyası HTTP response olarak döndürülür.

            Content-Type:
                text/html

            Tarayıcı bu dosyayı render ederek UI'yi başlatır.

    Raises:
        HTTPException (500):
            index.html bulunamazsa fırlatılır.

            Bu genellikle:
            - yanlış path konfigürasyonu
            - eksik build/deploy
            - dosya sistemine erişim sorunu
            anlamına gelir.

    Güvenlik notu:
    --------------
    Bu endpoint yalnızca tek bir belirli dosyayı döndürür.
    Kullanıcıdan gelen herhangi bir path parametresi kullanılmaz.

    Bu sayede:
    - directory traversal saldırıları engellenir
    - sadece izin verilen dosya servis edilir
    """

    # index.html dosyasının gerçekten mevcut olup olmadığını kontrol ederiz.
    # Bu kontrol yapılmazsa:
    # - FileResponse runtime error fırlatır
    # - hata kontrolsüz olur
    if not INDEX_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="Frontend entrypoint (index.html) not found.",
        )

    # HTML dosyası doğrudan response olarak döndürülür.
    return FileResponse(INDEX_FILE)