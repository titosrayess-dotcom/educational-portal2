#!/usr/bin/env python3
import re

for fn in ["sectors/dzexams.html", "sectors/exam-compos.html"]:
    with open(fn, "r", encoding="utf-8") as f:
        c = f.read()
    cnt = c.count("dzexams.com")
    c = re.sub(
        r'<a\s+href="https?://(?:www\.)?dzexams\.com[^"]*"[^>]*>',
        '<a href="content.html">',
        c,
    )
    with open(fn, "w", encoding="utf-8") as f:
        f.write(c)
    print(f"{fn}: replaced {cnt} links")
print("Done!")
