from tokenizer_workshop.api.services import compare_tokenizers


def run_compare(text: str, tokenizer_names: list[str]) -> dict:
    return compare_tokenizers(
        text=text,
        tokenizer_names=tokenizer_names,
    )