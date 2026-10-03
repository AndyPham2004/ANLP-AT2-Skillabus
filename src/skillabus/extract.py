"""Skill extraction, three tiers: dictionary -> spaCy NER (owner: Phuong Nhi) -> GPT-4o-mini (owner: Quan)."""


def extract(text: str, method: str = "dictionary") -> list[dict]:
    """Return skill mentions (data contract section 1, before normalisation)."""
    raise NotImplementedError