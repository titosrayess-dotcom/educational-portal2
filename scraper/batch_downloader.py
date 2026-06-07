#!/usr/bin/env python3
"""
Batch URL extractor - fetches /ar/sujets/{doc_slug} and stores the direct PDF URL.
Usage: python batch_downloader.py [batch_size]
"""
import json, os, sys, time, re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.dzexams.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
}
DELAY = 0.3

ALL_BAD_CATEGORIES = {
    'beginners', 'cniipdtice', 'cours', 'decoration', 'exercices',
    'externes', 'fiches-al', 'fiches-es', 'fiches-it', 'matwiyat',
    'moujtahid', 'olympiades', 'pedagogie', 'rawdabahia', 'tamhidia',
    'theatre', 'vacances_h', 'vacances_p',
}

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
            from urllib.parse import unquote
            return unquote(m.group(1))
    return None


def main():
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 80

    if not DATA_FILE.exists():
        print(f"[!] Data file not found: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    try:
        session.get(BASE_URL, timeout=30)
    except:
        pass

    pending = []
    skipped_bad = 0
    for level_key, ld in data.items():
        for year_code, yd in ld["years"].items():
            for subject_slug, subj in yd["subjects"].items():
                for cat_slug, cat in subj["categories"].items():
                    if cat_slug in ALL_BAD_CATEGORIES:
                        for file_entry in cat["files"]:
                            if not file_entry.get("direct_url"):
                                file_entry["direct_url"] = "_unavailable"
                        skipped_bad += len(cat["files"])
                        continue
                    for idx, file_entry in enumerate(cat["files"]):
                        doc_slug = file_entry.get("doc_slug", "")
                        direct_url = file_entry.get("direct_url", "")
                        if not doc_slug:
                            continue
                        if direct_url == "_unavailable":
                            continue
                        if not direct_url:
                            pending.append((level_key, year_code, subject_slug, cat_slug, idx, doc_slug))

    if not pending:
        print("All files already processed!")
        total = sum(len(c["files"]) for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values())
        done = sum(1 for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values() for f in c["files"] if f.get("direct_url") and f["direct_url"] != "_unavailable")
        print(f"Total: {total}, With URLs: {done}")
        return

    total_pending = len(pending)
    batch = pending[:batch_size]
    remaining = pending[batch_size:]

    print(f"Pending: {total_pending}, This batch: {len(batch)}, Remaining: {len(remaining)}, Skipped (resources): {skipped_bad}")

    done = 0
    errors = 0

    for level_key, year_code, subject_slug, cat_slug, idx, doc_slug in batch:
        sujet_url = f"{BASE_URL}/ar/sujets/{doc_slug}"

        try:
            time.sleep(DELAY)
            resp = session.get(sujet_url, timeout=30, allow_redirects=False)
            if resp.status_code in (301, 302, 307, 308):
                loc = resp.headers.get("Location", "")
                if loc == "/" or loc == "/ar/":
                    data[level_key]["years"][year_code]["subjects"][subject_slug]["categories"][cat_slug]["files"][idx]["direct_url"] = "_unavailable"
                    errors += 1
                    continue
            resp.raise_for_status()
        except Exception as e:
            print(f"  [!] Error: {doc_slug[:30]}... - {e}")
            errors += 1
            continue

        pdf_url = extract_pdf_url(resp.text)
        if not pdf_url:
            if resp.url != sujet_url:
                data[level_key]["years"][year_code]["subjects"][subject_slug]["categories"][cat_slug]["files"][idx]["direct_url"] = "_unavailable"
            errors += 1
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
        print(f"\nTo continue, run: python scraper/batch_downloader.py {batch_size}")


if __name__ == "__main__":
    main()
