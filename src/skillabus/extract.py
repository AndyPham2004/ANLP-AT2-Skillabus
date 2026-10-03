"""Skill extraction, three tiers: dictionary -> spaCy NER (owner: Phuong Nhi) -> GPT-4o-mini (owner: Quan)."""


def extract(text: str, method: str = "dictionary") -> list[dict]:
    """Return skill mentions (data contract section 1, before normalisation)."""
    if method == "llm":
        from .llm_extract import extract_llm
        return extract_llm(text)
    raise NotImplementedError
