#!/usr/bin/env python3
"""Replace dzexams.com links in sector pages with local content.html links."""
import re

pages = {
    "primary.html": "sectors/primary.html",
    "secondary.html": "sectors/secondary.html",
}

for page_name, page_path in pages.items():
    with open(page_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Count dzexams links
    count_before = content.count("dzexams.com")

    # Replace patterned links: <a href="https://www.dzexams.com/ar/..." target="_blank" rel="noopener noreferrer" class="...">
    # with: <a href="content.html" class="...">
    def replace_anchor(m):
        classes = ""
        cls_m = re.search(r'class="([^"]*)"', m.group(0))
        if cls_m:
            classes = f' class="{cls_m.group(1)}"'
        return f"<a href=\"content.html\"{classes}>"

    content = re.sub(
        r'<a\s+href="https?://(?:www\.)?dzexams\.com/[^"]*"[^>]*>',
        replace_anchor,
        content,
    )

    count_after = content.count("dzexams.com")
    replaced = count_before - count_after
    print(f"{page_name}: replaced {replaced} dzexams links (remaining: {count_after})")

    with open(page_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Done!")
