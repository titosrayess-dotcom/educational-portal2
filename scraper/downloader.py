#!/usr/bin/env python3
"""
Download all PDFs from dzexams.com using the doc_slug values in data.json.
Maps: doc_slug → /ar/sujets/{doc_slug} → extract PDF URL → download
"""
import json, os, sys, time, re, base64, hashlib
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.dzexams.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.7,en;q=0.3",
}
DELAY = 0.3  # seconds between requests
MAX_ERRORS = 50  # stop after this many consecutive errors

PROJECT_ROOT = Path(__file__).parent.parent
DATA_FILE = PROJECT_ROOT / "assets" / "content" / "data.json"
PDF_DIR = PROJECT_ROOT / "assets" / "content" / "pdfs"

session = requests.Session()
session.headers.update(HEADERS)

# Stats
stats = {"found": 0, "downloaded": 0, "skipped": 0, "errors": 0}


def init_session():
    """Warm up the session by visiting the homepage."""
    try:
        resp = session.get(BASE_URL, timeout=30)
        return True
    except Exception as e:
        print(f"  [!] Session init failed: {e}")
        return False


def extract_pdf_url(html):
    """Extract the PDF download URL from a sujet page."""
    soup = BeautifulSoup(html, "lxml")
    # Direct download link
    link = soup.select_one('a[href*="/uploads/"][href$=".pdf"]')
    if link:
        return link["href"]
    # Try Google Docs viewer embed
    el = soup.select_one("[data-src]")
    if el:
        src = el.get("data-src", "")
        # Extract the PDF URL from the Google Docs viewer URL
        m = re.search(r'url=([^&]+)', src)
        if m:
            from urllib.parse import unquote
            return unquote(m.group(1))
    return None


def get_safe_filename(doc_slug, pdf_url, index=0):
    """Generate a safe local filename for a PDF."""
    if pdf_url:
        # Use the original filename from URL
        path = urlparse(pdf_url).path
        basename = os.path.basename(path)
        if basename:
            return basename
    # Fallback: use hash of doc_slug
    h = hashlib.md5(doc_slug.encode()).hexdigest()[:12]
    return f"dzexams_{h}_{index}.pdf"


consecutive_errors = 0


def process_file(file_entry, level_key, year_code, subject_slug, cat_slug):
    """Process a single file: find PDF URL, download, update entry."""
    global stats, consecutive_errors
    doc_slug = file_entry.get("doc_slug", "")
    if not doc_slug:
        stats["errors"] += 1
        return

    # Check if already has a local path
    local_path = file_entry.get("local_path", "")
    if local_path and (PDF_DIR / local_path).exists():
        stats["skipped"] += 1
        return

    sujet_url = f"{BASE_URL}/ar/sujets/{doc_slug}"
    
    try:
        time.sleep(DELAY)
        resp = session.get(sujet_url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [!] Error fetching sujet page {sujet_url[:80]}: {e}")
        stats["errors"] += 1
        consecutive_errors += 1
        return

    pdf_url = extract_pdf_url(resp.text)
    if not pdf_url:
        stats["errors"] += 1
        consecutive_errors += 1
        return

    stats["found"] += 1

    # Download the PDF
    try:
        time.sleep(DELAY)
        pdf_resp = session.get(pdf_url, timeout=60)
        pdf_resp.raise_for_status()
        ct = pdf_resp.headers.get("Content-Type", "")
        if "application/pdf" not in ct and "application/octet-stream" not in ct:
            print(f"  [!] Not a PDF ({ct}) at {pdf_url[:80]}")
            stats["errors"] += 1
            consecutive_errors += 1
            return
    except Exception as e:
        print(f"  [!] Error downloading PDF {pdf_url[:80]}: {e}")
        stats["errors"] += 1
        consecutive_errors += 1
        return

    # Save PDF
    local_filename = get_safe_filename(doc_slug, pdf_url)
    pdf_subdir = PDF_DIR / level_key / year_code / subject_slug / cat_slug
    pdf_subdir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_subdir / local_filename
    
    # Handle duplicate names
    counter = 1
    while pdf_path.exists():
        name, ext = os.path.splitext(local_filename)
        pdf_path = pdf_subdir / f"{name}_{counter}{ext}"
        counter += 1
    
    with open(pdf_path, "wb") as f:
        f.write(pdf_resp.content)
    
    # Update entry with local path (relative to PDF_DIR)
    relative_path = str(pdf_path.relative_to(PDF_DIR))
    file_entry["local_path"] = relative_path
    # Remove old download URL since it's external
    file_entry.pop("download_url", None)
    
    stats["downloaded"] += 1
    consecutive_errors = 0


def save_progress(data, processed, total_files):
    """Save progress to data.json."""
    with open(DATA_FILE, "w", encoding="utf-8-sig") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    pct = round(processed / total_files * 100, 1) if total_files else 0
    print(f"\n  -- Saved progress: {processed}/{total_files} ({pct}%) -- "
          f"DL:{stats['downloaded']} Skip:{stats['skipped']} Err:{stats['errors']} --\n")


def main():
    global stats, consecutive_errors
    print("=" * 60)
    print("DzExams PDF Downloader")
    print("=" * 60)

    # Load data
    if not DATA_FILE.exists():
        print(f"[!] Data file not found: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Init session
    print("\nInitializing session...")
    if not init_session():
        print("[!] Failed to init session, continuing anyway...")

    total_files = sum(
        sum(len(c["files"]) for c in s["categories"].values())
        for ld in data.values()
        for y in ld["years"].values()
        for s in y["subjects"].values()
    )
    print(f"Total files in data.json: {total_files}")

    # Count already processed
    already = sum(
        1 for ld in data.values()
        for y in ld["years"].values()
        for s in y["subjects"].values()
        for c in s["categories"].values()
        for f in c["files"]
        if f.get("local_path") and (PDF_DIR / f["local_path"]).exists()
    )
    print(f"Already downloaded: {already}")
    stats["skipped"] = already

    # Process all files
    processed = 0
    for level_key, ld in data.items():
        for year_code, yd in ld["years"].items():
            for subject_slug, subj in yd["subjects"].items():
                for cat_slug, cat in subj["categories"].items():
                    for file_entry in cat["files"]:
                        if file_entry.get("local_path") and (PDF_DIR / file_entry["local_path"]).exists():
                            processed += 1
                            continue
                        process_file(file_entry, level_key, year_code, subject_slug, cat_slug)
                        processed += 1
                        
                        # Stop on too many consecutive errors
                        if consecutive_errors >= MAX_ERRORS:
                            print(f"\n[!] Too many consecutive errors ({consecutive_errors}). Stopping.")
                            save_progress(data, processed, total_files)
                            sys.exit(1)
                        
                        # Save progress every 100 files
                        if processed % 100 == 0:
                            save_progress(data, processed, total_files)
                        
                        # Print individual progress
                        if stats["downloaded"] % 25 == 0 and stats["downloaded"] > 0:
                            pct = round(processed / total_files * 100, 1)
                            print(f"  [{pct}%] DL:{stats['downloaded']} Skip:{stats['skipped']} Err:{stats['errors']}")

    # Final save
    save_progress(data, processed, total_files)
    
    print(f"\n{'='*60}")
    print(f"Done! Processed {processed} files")
    print(f"  Downloaded:     {stats['downloaded']}")
    print(f"  Skipped:        {stats['skipped']}")
    print(f"  Errors:         {stats['errors']}")
    print(f"Data saved to {DATA_FILE}")

if __name__ == "__main__":
    main()
