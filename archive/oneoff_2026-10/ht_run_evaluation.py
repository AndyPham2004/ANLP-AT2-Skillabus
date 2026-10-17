"""Run the evaluation (task #24). Owner: Hoai Thuong. Kept as a shortcut; the code is in src/skillabus/eval_run.py.

    python notebooks/ht_run_evaluation.py [--method dictionary|ner|llm]
is the same as
    python -m skillabus.evaluate --all --methods <method>
Use `python -m skillabus.evaluate --all` for every tier and every table of report section 6.
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from skillabus.eval_run import run_all

ap = argparse.ArgumentParser()
ap.add_argument("--method", default="dictionary", choices=["dictionary", "ner", "llm"])
ap.add_argument("--out")
a = ap.parse_args()
sys.exit(run_all((a.method,), a.out))
