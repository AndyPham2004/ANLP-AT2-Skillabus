"""src/skillabus/paths.py: every committed file it names exists, and what the app writes stays out of git."""
import subprocess

import pytest

from skillabus import paths


def test_every_committed_file_named_in_paths_exists():
    missing = [str(p.relative_to(paths.ROOT)) for p in paths.COMMITTED if not p.exists()]
    assert not missing, f"paths.py names files that are not in the repo: {missing}"


def test_raw_and_runtime_are_ignored_and_the_evaluation_cache_is_not():
    if not (paths.ROOT / ".git").exists():
        pytest.skip("not a git checkout")

    def ignored(path):
        rel = path.relative_to(paths.ROOT).as_posix()
        return subprocess.run(["git", "check-ignore", "-q", rel], cwd=paths.ROOT).returncode == 0

    assert ignored(paths.RAW / "any.csv") and ignored(paths.FEEDBACK) and ignored(paths.LLM_CACHE / "x.json")
    assert not ignored(paths.LLM_CACHE_EVAL / "x.json") and not ignored(paths.SKILLS_SEED)
