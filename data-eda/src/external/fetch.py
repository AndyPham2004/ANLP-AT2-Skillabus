import requests, time, sys, pathlib
out = pathlib.Path(sys.argv[1])
HEADERS = {"User-Agent": "Mozilla/5.0 (UTS 36118 student project)"}
codes = ["36118","37252","41066","25865","090012","79603","32548","32601","013992","36100","220700","49255"]
hb = ["36118","37252","013992","220700"]
urls = [(c, "evop", f"https://studentforms.uts.edu.au/evop/access/search.cfm?subjectcode={c}") for c in codes]
urls += [(c, "hb", f"https://coursehandbook.uts.edu.au/subject/2026/{c}") for c in hb]
assert len(urls) <= 20
s = requests.Session(); s.headers.update(HEADERS)
n = 0
for code, kind, url in urls:
    if n: time.sleep(1.5)
    n += 1
    try:
        r = s.get(url, timeout=40)
        p = out / f"{kind}_{code}.html"
        p.write_text(r.text, encoding="utf-8")
        print(f"{n:2d} {kind} {code} status={r.status_code} bytes={len(r.text)} final={r.url}")
    except Exception as e:
        print(f"{n:2d} {kind} {code} ERROR {e!r}")
print("total requests:", n)
