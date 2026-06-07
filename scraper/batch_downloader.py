#!/usr/bin/env python3
"""
Batch PDF downloader - processes files in small batches for better timeout handling.
Usage: python batch_downloader.py [batch_size]
"""
import json, os, sys, time, re, base64, hashlib
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.dzexams.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
}
DELAY = 0.3

# Category slugs that redirect to / (not accessible via /ar/sujets/)
ALL_BAD_CATEGORIES = {
    'beginners', 'cniipdtice', 'cours', 'decoration', 'exercices',
    'externes', 'fiches-al', 'fiches-es', 'fiches-it', 'matwiyat',
    'moujtahid', 'olympiades', 'pedagogie', 'rawdabahia', 'tamhidia',
    'theatre', 'vacances_h', 'vacances_p',
}

PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "assets" / "content" / "data.json"
PDF_DIR = PROJECT_ROOT / "assets" / "content" / "pdfs"

session = requests.Session()
session.headers.update(HEADERS)


def init_session():
    try:
        session.get(BASE_URL, timeout=30)
        return True
    except:
        return False


def extract_pdf_url(html):
    soup = BeautifulSoup(html, "lxml")
    link = soup.select_one('a[href*="/uploads/"][href$=".pdf"]')
    if link:
        return link["href"]
    # Try data-src attribute (Google Docs viewer)
    el = soup.select_one("[data-src]")
    if el:
        src = el.get("data-src", "")
        m = re.search(r'url=([^&]+)', src)
        if m:
            from urllib.parse import unquote
            return unquote(m.group(1))
    return None


def get_safe_filename(doc_slug, pdf_url):
    if pdf_url:
        basename = os.path.basename(urlparse(pdf_url).path)
        if basename:
            return basename
    h = hashlib.md5(doc_slug.encode()).hexdigest()[:12]
    return f"dzexams_{h}.pdf"


def main():
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 30

    if not DATA_FILE.exists():
        print(f"[!] Data file not found: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    init_session()

    # Collect all files needing download
    pending = []
    skipped_bad = 0
    for level_key, ld in data.items():
        for year_code, yd in ld["years"].items():
            for subject_slug, subj in yd["subjects"].items():
                for cat_slug, cat in subj["categories"].items():
                    if cat_slug in ALL_BAD_CATEGORIES:
                        # Mark as not downloadable (skip in future)
                        for file_entry in cat["files"]:
                            if not file_entry.get("local_path"):
                                file_entry["local_path"] = "_unavailable"
                        skipped_bad += len(cat["files"])
                        continue
                    for idx, file_entry in enumerate(cat["files"]):
                        doc_slug = file_entry.get("doc_slug", "")
                        local_path = file_entry.get("local_path", "")
                        if not doc_slug:
                            continue
                        if local_path == "_unavailable":
                            continue
                        if not local_path or not (PDF_DIR / local_path).exists():
                            pending.append((level_key, year_code, subject_slug, cat_slug, idx, doc_slug))

    if not pending:
        print("All files already downloaded!")
        # Count stats
        total = sum(len(c["files"]) for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values())
        done = sum(1 for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values() for f in c["files"] if f.get("local_path") and (PDF_DIR / f["local_path"]).exists())
        print(f"Total: {total}, Downloaded: {done}")
        return

    total_pending = len(pending)
    batch = pending[:batch_size]
    remaining = pending[batch_size:]
    
    print(f"Pending: {total_pending}, This batch: {len(batch)}, Remaining: {len(remaining)}, Skipped (resources): {skipped_bad}")
    
    downloaded = 0
    errors = 0
    
    for level_key, year_code, subject_slug, cat_slug, idx, doc_slug in batch:
        sujet_url = f"{BASE_URL}/ar/sujets/{doc_slug}"
        
        # Check for redirect (file not available)
        try:
            time.sleep(DELAY)
            resp = session.get(sujet_url, timeout=30, allow_redirects=False)
            if resp.status_code in (301, 302, 307, 308):
                loc = resp.headers.get("Location", "")
                if loc == "/" or loc == "/ar/":
                    # Mark as unavailable
                    data[level_key]["years"][year_code]["subjects"][subject_slug]["categories"][cat_slug]["files"][idx]["local_path"] = "_unavailable"
                    errors += 1
                    continue
            resp.raise_for_status()
        except Exception as e:
            print(f"  [!] Error: {doc_slug[:20]}... - {e}")
            errors += 1
            continue

        pdf_url = extract_pdf_url(resp.text)
        if not pdf_url:
            print(f"  [!] No PDF URL: {doc_slug[:20]}...")
            # Check if redirect
            if resp.url != sujet_url:
                data[level_key]["years"][year_code]["subjects"][subject_slug]["categories"][cat_slug]["files"][idx]["local_path"] = "_unavailable"
            errors += 1
            continue

        try:
            time.sleep(DELAY)
            pdf_resp = session.get(pdf_url, timeout=60)
            pdf_resp.raise_for_status()
            ct = pdf_resp.headers.get("Content-Type", "")
            if "application/pdf" not in ct and "application/octet-stream" not in ct:
                print(f"  [!] Not PDF: {pdf_url[:60]}")
                errors += 1
                continue
        except Exception as e:
            print(f"  [!] DL error: {pdf_url[:60]} - {e}")
            errors += 1
            continue

        local_filename = get_safe_filename(doc_slug, pdf_url)
        pdf_subdir = PDF_DIR / level_key / year_code / subject_slug / cat_slug
        pdf_subdir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_subdir / local_filename
        
        counter = 1
        while pdf_path.exists():
            name, ext = os.path.splitext(local_filename)
            pdf_path = pdf_subdir / f"{name}_{counter}{ext}"
            counter += 1
        
        with open(pdf_path, "wb") as f:
            f.write(pdf_resp.content)
        
        relative_path = str(pdf_path.relative_to(PDF_DIR))
        # Update the actual file entry in data
        data[level_key]["years"][year_code]["subjects"][subject_slug]["categories"][cat_slug]["files"][idx]["local_path"] = relative_path
        data[level_key]["years"][year_code]["subjects"][subject_slug]["categories"][cat_slug]["files"][idx].pop("download_url", None)
        
        downloaded += 1
        if downloaded % 5 == 0:
            print(f"  ... {downloaded}/{len(batch)}")

    # Save progress
    with open(DATA_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nBatch done: +{downloaded} downloaded, {errors} errors")
    print(f"Remaining: {len(remaining)}")

    # Count overall stats
    total = sum(len(c["files"]) for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values())
    done = sum(1 for ld in data.values() for y in ld["years"].values() for s in y["subjects"].values() for c in s["categories"].values() for f in c["files"] if f.get("local_path") and (PDF_DIR / f["local_path"]).exists())
    print(f"Overall: {done}/{total} files downloaded")
    
    if remaining:
        print(f"\nTo continue, run: python scraper/batch_downloader.py {batch_size}")


if __name__ == "__main__":
    main()
