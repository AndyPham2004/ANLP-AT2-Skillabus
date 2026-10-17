"""No test may call a paid or rate-limited service. 17 Oct: test_certifications ran a script that loads .env,
which put the real OPENAI_API_KEY into the session, and the evaluation smoke test then called GPT-4o-mini.
conftest.no_live_keys removes the keys and makes load_dotenv a no-op for every test."""
import os

import dotenv

from conftest import LIVE_KEYS


def test_no_test_sees_a_live_key():
    assert [k for k in LIVE_KEYS if os.getenv(k)] == []


def test_loading_env_inside_a_test_adds_no_key(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=sk-not-a-real-key\n", encoding="utf-8")
    dotenv.load_dotenv(env)
    assert not os.getenv("OPENAI_API_KEY")
