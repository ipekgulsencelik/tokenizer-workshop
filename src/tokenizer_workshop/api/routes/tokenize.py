import logging
from fastapi import APIRouter, HTTPException

from tokenizer_workshop.api.schemas import *
from tokenizer_workshop.api.services import *

from tokenizer_workshop.api.reports.text_report import build_text_report
from tokenizer_workshop.api.reports.markdown_report import build_markdown_report
from tokenizer_workshop.api.utils.exception_mapper import map_service_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["tokenization"])


@router.post("/report")
def generate_report(request: ReportRequest):
    try:
        result = compare_tokenizers(
            text=request.text,
            tokenizer_names=request.tokenizer_names,
        )

        builders = {
            "txt": build_text_report,
            "md": build_markdown_report,
        }

        fmt = request.format.lower()

        if fmt not in builders:
            raise HTTPException(400, "Unsupported format")

        return {
            "report": builders[fmt](result),
            "format": fmt,
        }

    except Exception as exc:
        map_service_exception(exc)


@router.post("/tokenize")
def tokenize(request: TokenizeRequest):
    try:
        result = tokenize_text(
            text=request.text,
            tokenizer_name=request.tokenizer_name,
        )
        return TokenizeResponse(**result)

    except Exception as exc:
        map_service_exception(exc)


@router.post("/compare")
def compare(request: CompareRequest):
    try:
        result = compare_tokenizers(
            text=request.text,
            tokenizer_names=request.tokenizer_names,
        )
        return CompareResponse(**result)

    except Exception as exc:
        map_service_exception(exc)