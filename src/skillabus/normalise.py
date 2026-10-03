"""Map raw skill mentions to ESCO, then Lightcast, else tag as emerging. Owner: Quan."""


def normalise(mentions: list[dict]) -> list[dict]:
    """Fill skill_id, skill_label and vocab on each mention (data contract section 1)."""
    raise NotImplementedError