"""Make `import skillabus` work when pytest runs from the repo root."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# The embedding switch as the shell set it. conftest is imported before any test file, so a test file that
# changes it at import time shows up as a difference (test_match.py checks).
NO_EMBED_AT_START = os.environ.get("SKILLABUS_NO_EMBED")
LIVE_KEYS = ("OPENAI_API_KEY", "LIGHTCAST_CLIENT_ID", "LIGHTCAST_CLIENT_SECRET", "JOBSPIPE_API_KEY",
             "ADZUNA_APP_ID", "ADZUNA_APP_KEY")


@pytest.fixture(autouse=True)
def no_live_keys(monkeypatch):
    """No test calls a paid service: the keys are removed and load_dotenv does nothing, for every test.
    A test that needs a key sets a fake one itself (monkeypatch.setenv) and stubs the call."""
    for key in LIVE_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)


@pytest.fixture
def tfidf_only(monkeypatch):
    """TF-IDF instead of the embedding model for one test: fast, and the same on every machine. Per test, not
    when a file is imported, so the embedding tests in other files still run in a full session."""
    from skillabus import similarity
    monkeypatch.setenv("SKILLABUS_NO_EMBED", "1")
    similarity.embeddings_available.cache_clear()          # it keeps its first answer for the session
    yield
    similarity.embeddings_available.cache_clear()


@pytest.fixture
def demand_sample(monkeypatch):
    """match.py reads tests/fixtures/role_skill_demand_sample.csv instead of the committed demand table."""
    import skillabus.match as match_module
    monkeypatch.setattr(match_module, "DEMAND_CSV", Path(__file__).parent / "fixtures/role_skill_demand_sample.csv")
    match_module._blocks.cache_clear()
    yield
    match_module._blocks.cache_clear()
