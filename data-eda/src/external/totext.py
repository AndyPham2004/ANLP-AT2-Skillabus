"""Print headings, paragraphs and list items of dl/<slug>.html in document order.
usage: python totext.py <slug> [maxlines] [--all]"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

DL = Path(__file__).resolve().parent / "dl"
BLOCK = {"h1", "h2", "h3", "h4", "h5", "p", "li", "dt", "dd", "title", "summary", "blockquote"}
SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header"}


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.buf = []
        self.out = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        if tag in BLOCK:
            self.flush()
            self.stack.append(tag)
        if tag == "br":
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip:
            self.skip -= 1
        if tag in BLOCK:
            self.flush()
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()

    def handle_data(self, data):
        if self.skip:
            return
        self.buf.append(data)

    def flush(self):
        text = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if text:
            tag = self.stack[-1] if self.stack else "-"
            self.out.append((tag, text))


sys.stdout.reconfigure(encoding="utf-8", errors="replace")
slug = sys.argv[1]
maxlines = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 400
html = (DL / f"{slug}.html").read_text(encoding="utf-8", errors="replace")
p = P()
p.feed(html)
p.flush()
width = 100000 if "--full" in sys.argv else 400
for i, (tag, text) in enumerate(p.out[:maxlines]):
    print(f"{i:4d} [{tag:5s}] {text[:width]}")
print(f"... {len(p.out)} blocks total")
