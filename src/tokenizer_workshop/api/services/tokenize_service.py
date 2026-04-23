from tokenizer_workshop.api.services import tokenize_text


def run_tokenize(text: str, tokenizer_name: str) -> dict:
    return tokenize_text(text=text, tokenizer_name=tokenizer_name)