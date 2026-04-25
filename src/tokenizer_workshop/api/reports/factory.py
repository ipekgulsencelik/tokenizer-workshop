"""
factory.py

Bu modül, rapor üretim sürecinde kullanılacak uygun report builder fonksiyonunu seçmekle sorumludur.

Bir başka ifadeyle bu dosya, kullanıcının istediği çıktı formatı ile
o formatı üretecek fonksiyon arasında köprü görevi görür.

Örneğin:
- "txt" formatı istenirse → build_text_report
- "md" formatı istenirse  → build_markdown_report
- "pdf" formatı istenirse → build_pdf_report 

---------------------------------------------------------------------------
Amaç
---------------------------------------------------------------------------
Bu modülün temel amacı:

- rapor formatı seçimini merkezi hale getirmek
- route/controller katmanını format seçim detaylarından arındırmak
- yeni rapor formatları eklenmesini kolaylaştırmak
- report generation akışında if/elif tekrarlarını önlemek
- çıktı dosya adını format seçimiyle birlikte standartlaştırmak

---------------------------------------------------------------------------
Mimari Rol
---------------------------------------------------------------------------
Bu modül, API rapor üretim akışında "factory" rolü üstlenir.

Factory pattern burada şu problemi çözer:

    "Hangi format istendiyse, hangi builder fonksiyonu çalışmalı?"

Akış:

    HTTP Request
        ↓
    Route / Controller
        ↓
    get_report_builder(report_format)
        ↓
    İlgili builder fonksiyonu seçilir
        ↓
    Evaluation sonucu builder'a verilir
        ↓
    Rapor string olarak üretilir
        ↓
    API response içinde report + filename döndürülür

Bu sayede route katmanı yalnızca şunu bilir:

    builder, filename = get_report_builder(request.format)
    report = builder(evaluation_result)

Route katmanı:
- format seçiminin detayını bilmez
- hangi fonksiyonun çağrılacağını bilmez
- yeni format eklendiğinde değişmek zorunda kalmaz

---------------------------------------------------------------------------
Desteklenen Formatlar
---------------------------------------------------------------------------
Şu anda desteklenen formatlar:

- txt:
    Düz metin raporu üretir.
    CLI çıktısı, basit indirme, terminal okuması için uygundur.

- md:
    Markdown raporu üretir.
    GitHub, README, dokümantasyon ve daha okunabilir rapor çıktıları için uygundur.

- pdf:
    PDF raporu üretir.
    Basılı veya dijital dağıtım için uygundur.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tokenizer_workshop.api.reports.markdown_report import build_markdown_report
from tokenizer_workshop.api.reports.text_report import build_text_report

# ReportBuilder tipi, tüm report builder fonksiyonları için ortak sözleşmeyi temsil eder.
ReportBuilder = Callable[[dict[str, Any]], str]


def get_report_builder(report_format: str) -> tuple[ReportBuilder, str]:
    """
    Verilen rapor formatına göre uygun report builder fonksiyonunu ve önerilen dosya adını döndürür.

    -----------------------------------------------------------------------
    Amaç
    -----------------------------------------------------------------------
    Bu fonksiyonun amacı:

    - istemciden gelen format bilgisini normalize etmek
    - desteklenen formatlar arasından doğru builder fonksiyonunu seçmek
    - seçilen formata uygun standart dosya adını döndürmek
    - route katmanını format seçim detaylarından izole etmek

    -----------------------------------------------------------------------
    İş Akışı
    -----------------------------------------------------------------------
    1. report_format değeri alınır
    2. Baştaki ve sondaki boşluklar temizlenir
    3. Format küçük harfe dönüştürülür
    4. Normalize edilmiş format builders sözlüğünde aranır
    5. Format destekleniyorsa:
       - ilgili builder fonksiyonu
       - önerilen dosya adı
       birlikte döndürülür
    6. Format desteklenmiyorsa ValueError yükseltilir

    -----------------------------------------------------------------------
    Args
    -----------------------------------------------------------------------
    report_format (str):
        Kullanıcının istediği rapor formatıdır.

        Desteklenen değerler:
        - "txt"
        - "md"
        Normalize edilen örnekler:
        - " TXT " → "txt"
        - "Md"    → "md"
        - "md"    → "md"

    -----------------------------------------------------------------------
    Returns
    -----------------------------------------------------------------------
    tuple[ReportBuilder, str]:
        İki elemanlı tuple döndürür:

        1. ReportBuilder:
           Raporu üretecek builder fonksiyonu.

        2. str:
           Üretilen rapor için önerilen dosya adı.
        
        Örnek:
            (
                build_markdown_report,
                "tokenizer_report.md"
            )

    -----------------------------------------------------------------------
    Raises
    -----------------------------------------------------------------------
    ValueError:
        report_format desteklenen formatlar arasında değilse yükseltilir.

        Bu hata route katmanında yakalanıp genellikle HTTP 400 response'a
        dönüştürülmelidir.

    -----------------------------------------------------------------------
    Tasarım Notu
    -----------------------------------------------------------------------
    Bu fonksiyon bilinçli olarak report üretmez.

    Yalnızca:
    - doğru builder fonksiyonunu seçer
    - önerilen dosya adını verir

    Böylece:
    - seçim sorumluluğu factory'de
    - üretim sorumluluğu builder'da
    - HTTP response sorumluluğu route katmanında kalır
    """
    normalized_format = report_format.strip().lower() # normalize input

    builders: dict[str, tuple[ReportBuilder, str]] = {
        "txt": (build_text_report, "tokenizer_report.txt"), # önerilen dosya adı da burada tanımlanır
        "md": (build_markdown_report, "tokenizer_report.md"),
    }

    if normalized_format not in builders:
        supported_formats = ", ".join(sorted(builders.keys())) # desteklenen formatları listeler

        raise ValueError(
            f"Unsupported report format: '{report_format}'. "
            f"Supported formats: {supported_formats}."
        )

    return builders[normalized_format]