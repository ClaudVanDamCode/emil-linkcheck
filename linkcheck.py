#!/usr/bin/env python3
"""Broken-link crawler (stdlib only, GET/HEAD reads only, polite).
Usage: linkcheck.py START_URL MAX_PAGES OUT.json
Crawls same-host pages up to MAX_PAGES, checks every link/image target once.
"""
import sys, json, time, ssl, re, socket
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

UA = "emil-linkcheck/1.0 (+https://github.com/ClaudVanDamCode/emil-linkcheck)"
PLACEHOLDERS = ["lorem ipsum", "hello world!", "hei, verden", "sample page", "eksempelside",
                "just another wordpress site", "nok et wordpress-nettsted", "ny side"]
socket.setdefaulttimeout(15)


class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.imgs = []; self.title = ""; self._t = False; self.text = []
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        elif tag in ("img", "script") and a.get("src"): self.imgs.append(a["src"])
        elif tag == "link" and a.get("href") and "stylesheet" in (a.get("rel") or ""): self.imgs.append(a["href"])
        elif tag == "title": self._t = True
    def handle_endtag(self, tag):
        if tag == "title": self._t = False
    def handle_data(self, d):
        if self._t: self.title += d
        self.text.append(d)


def fetch(url, method="GET"):
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"}, method=method)
    try:
        r = urlopen(req, context=ssl.create_default_context())
        body = r.read(2_000_000) if method == "GET" else b""
        return r.status, r.geturl(), r.headers.get("Content-Type", ""), body, None
    except HTTPError as e:
        return e.code, url, "", b"", None
    except ssl.SSLError as e:
        return None, url, "", b"", "certificate: %s" % e
    except (URLError, socket.timeout, ConnectionError, OSError) as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, ssl.SSLError) or "CERTIFICATE" in str(reason).upper():
            return None, url, "", b"", "certificate: %s" % reason
        return None, url, "", b"", str(reason)


def main(start, maxpages, out):
    host = urlparse(start).netloc
    queue, seen_pages, checked, pages, problems = [start], set(), {}, [], []
    while queue and len(pages) < maxpages:
        url = queue.pop(0)
        if url in seen_pages: continue
        seen_pages.add(url)
        st, final, ctype, body, err = fetch(url)
        checked[url] = (st, err)
        time.sleep(1.0)
        if err or not st or st >= 400:
            continue
        if "html" not in ctype: continue
        p = P(); p.feed(body.decode("utf-8", "replace"))
        txt = " ".join(p.text).lower()
        ph = [w for w in PLACEHOLDERS if w in txt]
        mixed = urlparse(final).scheme == "https" and bool(re.search(rb'src=["\']http://', body))
        pages.append({"url": final, "title": p.title.strip()[:120], "placeholder": ph, "mixed_content": mixed})
        for raw, kind in [(h, "link") for h in p.links] + [(s, "file") for s in p.imgs]:
            if raw.startswith(("mailto:", "tel:", "javascript:", "#", "data:")): continue
            tgt = urldefrag(urljoin(final, raw))[0]
            if urlparse(tgt).scheme not in ("http", "https"): continue
            same = urlparse(tgt).netloc == host
            if same and kind == "link" and tgt not in seen_pages and tgt not in queue and len(seen_pages) + len(queue) < maxpages * 3:
                if not re.search(r"\.(pdf|jpe?g|png|gif|zip|docx?|xlsx?|mp4|svg|webp)$", tgt, re.I):
                    queue.append(tgt); continue
            if tgt not in checked:
                st2, _, _, _, err2 = fetch(tgt, "HEAD")
                if st2 in (403, 405, 501) or (st2 is None and not err2):
                    st2, _, _, _, err2 = fetch(tgt)
                checked[tgt] = (st2, err2)
                time.sleep(0.5 if same else 0.2)
            st2, err2 = checked[tgt]
            if err2 or not st2 or st2 >= 400:
                problems.append({"page": final, "target": tgt, "kind": kind, "internal": same,
                                 "status": st2, "error": err2})
    for u, (st, err) in checked.items():
        if u in seen_pages and (err or not st or st >= 400):
            problems.append({"page": "(crawl)", "target": u, "kind": "page", "internal": True, "status": st, "error": err})
    json.dump({"start": start, "pages": pages, "problems": problems, "checked": len(checked),
               "when": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}, open(out, "w"), indent=1)
    print("pages", len(pages), "targets checked", len(checked), "problems", len(problems))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
