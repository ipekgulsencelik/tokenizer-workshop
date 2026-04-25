from pathlib import Path
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


def build_pdf_report(data: dict, output_path: str | Path) -> Path:
    doc = SimpleDocTemplate(str(output_path))
    styles = getSampleStyleSheet()

    elements = []

    # TITLE
    elements.append(Paragraph("Tokenizer Evaluation Report", styles["Heading1"]))
    elements.append(Spacer(1, 12))

    # SUMMARY TABLE
    elements.append(Paragraph("Summary Table", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    table_data = [
        ["Tokenizer", "Tokens", "Unique", "Eff", "Latency"]
    ]

    for item in data.get("results", []):
        metrics = item.get("metrics", {})
        table_data.append([
            item.get("tokenizer_name"),
            metrics.get("token_count"),
            metrics.get("unique_token_count"),
            round(metrics.get("efficiency_score", 0), 2),
            int(metrics.get("latency_seconds", 0) * 1_000_000),
        ])

    table = Table(table_data)

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ])
    )

    elements.append(table)
    elements.append(Spacer(1, 20))

    # DETAILS
    elements.append(Paragraph("Tokenizer Details", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    for item in data.get("results", []):
        metrics = item.get("metrics", {})

        elements.append(
            Paragraph(
                f"{item.get('tokenizer_name')} → tokens={metrics.get('token_count')}, eff={metrics.get('efficiency_score')}",
                styles["Normal"],
            )
        )
        elements.append(Spacer(1, 6))

    doc.build(elements)

    return Path(output_path)