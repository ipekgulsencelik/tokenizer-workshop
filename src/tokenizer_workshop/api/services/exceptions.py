"""
exceptions.py

Service katmanında kullanılan özel exception tipleri.
"""


class UnsupportedTokenizerError(ValueError):
    """
    Desteklenmeyen tokenizer adı verildiğinde yükseltilir.
    """


class TokenizationServiceError(Exception):
    """
    Service katmanında oluşan beklenmeyen veya teknik hataları temsil eder.
    """