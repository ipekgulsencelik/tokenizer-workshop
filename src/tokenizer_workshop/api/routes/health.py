"""
health.py

Bu modül, uygulamanın sağlık durumunu raporlamak için kullanılan health-check endpoint'lerini içerir.

Amaç:
- Servisin çalışır durumda olup olmadığını doğrulamak (liveness)
- Harici bağımlılıkların erişilebilirliğini kontrol etmek (readiness)
- Monitoring / orchestration sistemlerine (Docker, Kubernetes, load balancer) makine-okunur bir durum bilgisi sunmak
- container / orchestration araçlarının servis sağlığını izlemesini sağlamak

Neden ayrı bir modül?
---------------------
Health endpoint'leri genellikle:
- yüksek trafik alır (health probes)
- kritik altyapı bileşenleri tarafından kullanılır
- container / orchestration araçlarının servis sağlığını izlemesini sağlamak

Neden health endpoint'i önemlidir?
----------------------------------
Gerçek dünya projelerinde bir API'nin yalnızca "çalışıyor görünmesi" yeterli değildir.
Sistemin:
- erişilebilir olması,
- request kabul edebilmesi,
- belirli seviyede cevap verebilmesi
gerekir.

Bu nedenle health endpoint'leri aşağıdaki ortamlarda kritik rol oynar:
- Docker container health check senaryoları
- Kubernetes liveness / readiness probe yapıları
- load balancer sağlık kontrolleri
- uptime monitoring araçları
- deploy sonrası smoke test kontrolleri
- CI/CD deploy doğrulamaları

Bu dosyada ne var?
------------------
Bu örnekte temel bir health endpoint tanımlanmıştır:
    GET /api/health

Bu endpoint şu an için basit bir "liveness check" görevi görür.

Liveness ne demek?
------------------
Liveness, uygulamanın hayatta olup olmadığını söyler.
Yani en temel soru şudur:
    "Servis crash olmadan ayakta mı?"

Bu endpoint neyi yapmaz?
------------------------
Bu örnek henüz aşağıdakileri kontrol etmez:
- veritabanı bağlantısı
- cache sistemi erişimi
- dış API bağımlılıkları
- disk / queue / message broker durumu

Mimari not:
-----------
Bu dosya API route katmanının bir parçasıdır.
Burada:
- request karşılanır
- response döndürülür

Burada bulunmaması gerekenler:
- ağır business logic
- uzun süren dependency testleri
- gereksiz performans yükü oluşturan kontroller

Health endpoint'leri mümkün olduğunca:
- hızlı
- deterministik
- hafif
olmalıdır.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, status


# ---------------------------------------------------------
# Router Definition
# ---------------------------------------------------------
# APIRouter kullanmamızın amacı:
# - route modüllerini birbirinden ayırmak
# - main.py dosyasını sade tutmak
# - endpoint'leri mantıksal gruplara bölmek
#
# tags=["health"]:
#   Swagger / OpenAPI dokümantasyonunda bu endpoint'i "health"
#   kategorisi altında göstermemizi sağlar.
router = APIRouter(tags=["health"])


# ---------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------
@router.get(
    "/api/health",
    status_code=status.HTTP_200_OK,
    summary="Service health check",
    description=(
        "Uygulamanın erişilebilir ve çalışır durumda olup olmadığını kontrol eder. "
        "Bu endpoint genellikle monitoring sistemleri, container orchestrator'lar "
        "ve deploy sonrası doğrulama süreçleri tarafından kullanılır."
    ),
    response_description="Servis sağlıklı durumda",
)
def health_check() -> dict:
    """
    Uygulamanın temel sağlık durumunu döndüren liveness endpoint'idir.

    Bu endpoint'in sorumluluğu:
    ---------------------------
    - servisin ayakta olduğunu göstermek
    - ağ üzerinden erişilebilir olduğunu doğrulamak
    - istemcilere ve monitoring araçlarına hızlı bir sağlık sinyali vermek

    Neden hafif tasarlanmalıdır?
    ----------------------------
    Health endpoint'leri çoğu zaman sık aralıklarla çağrılır.
    Eğer burada ağır işlemler yapılırsa:
    - gereksiz performans yükü oluşur
    - monitoring trafiği artar
    - sistemin genel verimliliği düşebilir

    Bu nedenle bu endpoint:
    - hızlı
    - deterministik
    - minimal maliyetli
    olacak şekilde tasarlanmalıdır.

    Response alanları:
    ------------------
    status:
        Servisin genel sağlık durumunu belirtir.
        Bu örnekte "ok" değeri kullanılır.

    service:
        Cevabı üreten servisin adını belirtir.
        Özellikle çok servisli mimarilerde hangi servisin yanıt verdiğini ayırt etmek için yararlıdır.

    timestamp:
        Response'un üretildiği UTC zamanı gösterir.
        Debugging, log korelasyonu ve gözlemlenebilirlik açısından faydalıdır.

    Returns:
        dict[str, str]:
            Servisin temel sağlık bilgisini içeren JSON yapı.

            Örnek response:
                {
                    "status": "ok",
                    "service": "tokenizer-workshop",
                    "timestamp": "2026-04-23T10:15:30.123456+00:00"
                }

    Liveness vs Readiness:
    ----------------------
    Bu endpoint bir liveness check örneğidir.

    - Liveness:
        Uygulama çalışıyor mu? (Bu endpoint bunu temsil eder)

    - Readiness:
        Uygulama trafik almaya hazır mı? (DB, cache, external servisler hazır mı?)
        Örneğin:
        - veritabanına bağlanabiliyor mu?
        - cache hazır mı?
        - gerekli bağımlılıklar erişilebilir mi?

    Bu implementasyon:
        Sadece liveness kontrolü yapar.
    """

    return {
        "status": "ok",
        "service": "tokenizer-workshop",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }