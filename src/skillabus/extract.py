"""Skill extraction, three tiers: dictionary -> spaCy NER -> GPT-4o-mini. Owner: Phuong Nhi."""


def extract(text: str, method: str = "dictionary") -> list[dict]:
    """Return skill mentions (data contract section 1, before normalisation)."""
    raise NotImplementedError