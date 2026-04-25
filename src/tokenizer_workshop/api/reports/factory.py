"""
factory.py

Report formatına göre uygun report builder seçimini yapar.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tokenizer_workshop.api.reports.markdown_report import build_markdown_report
from tokenizer_workshop.api.reports.text_report import build_text_report

ReportBuilder = Callable[[dict[str, Any]], str]


def get_report_builder(report_format: str) -> tuple[ReportBuilder, str]:
    """
    Verilen formata göre uygun report builder ve önerilen dosya adını döndürür.
    """
    normalized_format = report_format.strip().lower()

    builders: dict[str, tuple[ReportBuilder, str]] = {
        "txt": (build_text_report, "tokenizer_report.txt"),
        "md": (build_markdown_report, "tokenizer_report.md"),
    }

    if normalized_format not in builders:
        raise ValueError("Unsupported report format. Use 'txt' or 'md'.")

    return builders[normalized_format]