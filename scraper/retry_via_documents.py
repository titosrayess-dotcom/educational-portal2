#!/usr/bin/env python3
"""
Retry _unavailable entries using /ar/documents/ endpoint instead of /ar/sujets/.
Usage: python retry_via_documents.py [batch_size]
"""
import json, os, sys, time, re
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.dzexams.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
}
DELAY = 0.4

PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "assets" / "content" / "data.json"

session = requests.Session()
session.headers.update(HEADERS)


def extract_pdf_url(html):
    soup = BeautifulSoup(html, "lxml")
    link = soup.select_one('a[href*="/uploads/"][href$=".pdf"]')
    if link:
        return link["href"]
    el = soup.select_one("[data-src]")
    if el:
        src = el.get("data-src", "")
        m = re.search(r'url=([^&]+)', src)
        if m:
            return unquote(m.group(1))
    return None


def main():
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 80

    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Warm up session
    try:
        session.get(BASE_URL, timeout=30)
    except:
        pass

    # Collect all _unavailable entries
    pending = []
    for level_key, ld in data.items():
        for year_code, yd in ld["years"].items():
            for subject_slug, subj in yd["subjects"].items():
                for cat_slug, cat in subj["categories"].items():
                    for idx, file_entry in enumerate(cat["files"]):
                        if file_entry.get("direct_url") == "_unavailable":
                            # Use download_url if available, else construct from doc_slug
                            dl_url = file_entry.get("download_url", "")
                            doc_slug = file_entry.get("doc_slug", "")
                            if dl_url:
                                pending.append((level_key, year_code, subject_slug, cat_slug, idx, doc_slug, dl_url))
                            elif doc_slug:
                                # Construct the document URL
                                doc_url = f"{BASE_URL}/ar/documents/{doc_slug}=="
                                pending.append((level_key, year_code, subject_slug, cat_slug, idx, doc_slug, doc_url))

    if not pending:
        print("No _unavailable entries found!")
        return

    total_pending = len(pending)
    batch = pending[:batch_size]
    remaining = pending[batch_size:]

    print(f"Unavailable entries: {total_pending}")
    print(f"This batch: {len(batch)}, Remaining: {len(remaining)}")

    done = 0
    errors = 0

    for level_key, year_code, subject_slug, cat_slug, idx, doc_slug, doc_url in batch:
        try:
            time.sleep(DELAY)
            resp = session.get(doc_url, timeout=30, allow_redirects=False)
            if resp.status_code in (301, 302, 307, 308):
                loc = resp.headers.get("Location", "")
                errors += 1
                if errors <= 3:
                    print(f"  [!] Redirect {resp.status_code} -> {loc[:60]} ({doc_slug[:20]}...)")
                continue
            if resp.status_code != 200:
                errors += 1
                if errors <= 3:
                    print(f"  [!] Status {resp.status_code} ({doc_slug[:20]}...)")
                continue
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  [!] Error: {str(e)[:60]} ({doc_slug[:20]}...)")
            continue

        pdf_url = extract_pdf_url(resp.text)
        if not pdf_url:
            errors += 1
            if errors <= 3:
                print(f"  [!] No PDF found in document page ({doc_slug[:20]}...)")
            continue

        full_pdf_url = pdf_url if pdf_url.startswith("http") else BASE_URL + pdf_url
        data[level_key]["years"][year_code]["subjects"][subject_slug]["categories"][cat_slug]["files"][idx]["direct_url"] = full_pdf_url

        done += 1
        if done % 10 == 0:
            print(f"  ... {done}/{len(batch)}")

    with open(DATA_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nBatch done: +{done} URLs, {errors} errors")
    print(f"Remaining: {len(remaining)}")

    total = sum(len(c["files"]) for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values())
    with_urls = sum(1 for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values() for f in c["files"] if f.get("direct_url") and f["direct_url"] != "_unavailable")
    print(f"Overall: {with_urls}/{total} files with URLs")

    if remaining:
        print(f"\nTo continue, run: python scraper/retry_via_documents.py {batch_size}")


if __name__ == "__main__":
    main()
