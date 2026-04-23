from tokenizer_workshop.api.services.compare_service import run_compare
from tokenizer_workshop.api.reports.factory import get_report_builder


def generate_report_service(
    text: str,
    tokenizer_names: list[str],
    fmt: str,
) -> dict:
    compare_result = run_compare(text, tokenizer_names)

    builder, filename = get_report_builder(fmt)
    report = builder(compare_result)

    return {
        "report": report,
        "format": fmt,
        "filename": filename,
    }