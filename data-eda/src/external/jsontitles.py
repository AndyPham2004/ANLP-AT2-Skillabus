"""Print "title" / "description" strings embedded (HTML-escaped JSON) in data/raw/external_courses_pages/<slug>.html."""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DL = paths.EXTERNAL_PAGES_RAW
TITLE = re.compile(r'"title":"((?:[^"\\]|\\.){3,140})"')
DESC = re.compile(r'"description":"((?:[^"\\]|\\.){20,600})"')
for slug in sys.argv[1:]:
    h = html.unescape((DL / f"{slug}.html").read_text(encoding="utf-8", errors="replace"))
    print("=====", slug)
    seen = []
    for m in TITLE.findall(h):
        if m not in seen:
            seen.append(m)
    for s in seen[:130]:
        print("  T:", s)
    seen = []
    for m in DESC.findall(h):
        if m not in seen:
            seen.append(m)
    for s in seen[:20]:
        print("  D:", s[:500])
