"""Make `import skillabus` work when pytest runs from the repo root."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def demand_sample(monkeypatch):
    """match.py reads tests/fixtures/role_skill_demand_sample.csv instead of the committed demand table."""
    import skillabus.match as match_module
    monkeypatch.setattr(match_module, "DEMAND_CSV", Path(__file__).parent / "fixtures/role_skill_demand_sample.csv")
    match_module._blocks.cache_clear()
    yield
    match_module._blocks.cache_clear()
