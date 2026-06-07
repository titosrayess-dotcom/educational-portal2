#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DzExams.com Scraper - يجلب المواضيع والحلول من موقع ديزاد اكزام
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import base64
import json
import os
import re
import time
import traceback
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.dzexams.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
DELAY = 0.8

PROJECT_ROOT = Path(__file__).parent.parent
CONTENT_DIR = PROJECT_ROOT / "assets" / "content"
DATA_FILE = CONTENT_DIR / "data.json"

session = requests.Session()
session.headers.update(HEADERS)


def decode_data_id(data_id):
    try:
        decoded = base64.b64decode(data_id).decode("latin-1")
        result = "".join(chr(ord(c) - 8) for c in decoded)
        return result
    except Exception:
        return None


def fetch(url):
    time.sleep(DELAY)
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  [!] Error fetching {url}: {e}")
        return None


def scrape_subjects_grid(html, level_code):
    """Scrape subjects from a grid layout (used by 0ap / القسم التحضيري)."""
    soup = BeautifulSoup(html, "lxml")
    subjects = []
    for a_tag in soup.select("div.row.grid-modules a.item"):
        href = a_tag.get("href", "")
        m = re.search(rf"/{re.escape(level_code)}/(.+?)$", href)
        if not m:
            continue
        slug = m.group(1)
        if slug in ("moyenne", "advices", ""):
            continue

        title_el = a_tag.select_one(".item-module .nowrap")
        label = title_el.get_text(strip=True) if title_el else slug

        small = a_tag.select_one(".item-module small")
        count = 0
        if small:
            m2 = re.search(r"(\d+)", small.get_text())
            if m2:
                count = int(m2.group(1))

        subjects.append({"slug": slug, "label": label, "count": count})
    return subjects


def scrape_subjects_btns(html, level_code):
    """Scrape subjects from button list layout (used by 1ap+)."""
    soup = BeautifulSoup(html, "lxml")
    subjects = []
    for panel_id in ("panel-sujets-cat", "panel-documents-cat"):
        panel = soup.select_one(f"#{panel_id}")
        if not panel:
            continue
        for a_tag in panel.select("a.btn-group.item-tablist"):
            href = a_tag.get("href", "")
            m = re.match(rf"/ar/{re.escape(level_code)}/(.+?)$", href)
            if not m:
                continue
            slug = m.group(1)
            # skip non-subject links (e.g. category/, moyenne, advices)
            if "/" in slug or slug in ("moyenne", "advices", ""):
                continue

            btn_content = a_tag.select_one(".btn-group-content")
            label = btn_content.get_text(strip=True) if btn_content else slug

            btn_count = a_tag.select_one(".btn-group-count")
            count = 0
            if btn_count:
                m2 = re.search(r"(\d+)", btn_count.get_text())
                if m2:
                    count = int(m2.group(1))

            subjects.append({"slug": slug, "label": label, "count": count})
    return subjects


def scrape_categories(html, level_code, subject_slug):
    """Scrape categories from a subject page."""
    soup = BeautifulSoup(html, "lxml")
    categories = []

    for panel_id in ("panel-sujets-cat", "panel-documents-cat"):
        panel = soup.select_one(f"#{panel_id}")
        if not panel:
            continue
        for a_tag in panel.select("a.btn-group.item-tablist"):
            href = a_tag.get("href", "")
            m = re.match(
                rf"/ar/{re.escape(level_code)}/{re.escape(subject_slug)}/(.+?)$",
                href,
            )
            if not m:
                continue
            cat_slug = m.group(1)
            if "/" in cat_slug or cat_slug in ("moyenne", "advices", ""):
                continue

            btn_content = a_tag.select_one(".btn-group-content")
            label = btn_content.get_text(strip=True) if btn_content else cat_slug

            btn_count = a_tag.select_one(".btn-group-count")
            count = 0
            if btn_count:
                m2 = re.search(r"(\d+)", btn_count.get_text())
                if m2:
                    count = int(m2.group(1))

            categories.append({"slug": cat_slug, "label": label, "count": count})

    return categories


def scrape_files(html):
    """Scrape files from a category page."""
    soup = BeautifulSoup(html, "lxml")
    files = []

    for panel_id in ("panel-documents", "panel-sujets"):
        panel = soup.select_one(f"#{panel_id}")
        if not panel:
            continue
        for item_div in panel.select(".item"):
            a_tag = item_div.select_one("a.btn-item-document")
            if not a_tag:
                a_tag = item_div.select_one("a.btn-item-sujet")
            if not a_tag:
                continue

            data_id = a_tag.get("data-id", "")
            title = a_tag.get_text(strip=True) if a_tag else ""

            if data_id:
                doc_slug = decode_data_id(data_id)
                download_url = f"{BASE_URL}/ar/documents/{doc_slug}" if doc_slug else None
            else:
                doc_slug = None
                download_url = None

            files.append({
                "title": title,
                "data_id": data_id,
                "doc_slug": doc_slug,
                "download_url": download_url,
            })

    return files


def run(level_names=None):
    """Main scraper - scrapes metadata only (no PDF downloads)."""
    # Load existing data if any (merge mode)
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    else:
        existing = {}
    data = existing

    LEVELS = {
        "primary": {
            "label": "التعليم الإبتدائي",
            "codes": [
                ("0ap", "القسم التحضيري"),
                ("1ap", "السنة الأولى إبتدائي"),
                ("2ap", "السنة الثانية إبتدائي"),
                ("3ap", "السنة الثالثة إبتدائي"),
                ("4ap", "السنة الرابعة إبتدائي"),
                ("5ap", "السنة الخامسة إبتدائي"),
                ("bep", "شهادة التعليم الإبتدائي"),
            ],
        },
        "middle": {
            "label": "التعليم المتوسط",
            "codes": [
                ("1am", "السنة الأولى متوسط"),
                ("2am", "السنة الثانية متوسط"),
                ("3am", "السنة الثالثة متوسط"),
                ("4am", "السنة الرابعة متوسط"),
                ("bem", "شهادة التعليم المتوسط"),
            ],
        },
        "secondary": {
            "label": "التعليم الثانوي",
            "codes": [
                ("1as", "السنة الأولى ثانوي"),
                ("2as", "السنة الثانية ثانوي"),
                ("3as", "السنة الثالثة ثانوي"),
                ("bac", "شهادة البكالوريا"),
            ],
        },
    }

    for level_key, level_info in LEVELS.items():
        if level_names and level_key not in level_names:
            continue

        print(f"\n{'='*60}")
        print(f"Level: {level_info['label']} ({level_key})")
        print(f"{'='*60}")

        level_data = {"label": level_info["label"], "years": {}}

        for code, name in level_info["codes"]:
            print(f"\n  Year: {name} ({code})")

            url = f"{BASE_URL}/ar/{code}"
            print(f"    Fetching {url}")
            html = fetch(url)
            if not html:
                continue

            # Try grid layout first (0ap), then button layout (1ap+)
            subjects = scrape_subjects_grid(html, code)
            if not subjects:
                subjects = scrape_subjects_btns(html, code)

            if not subjects:
                print(f"    [!] No subjects found for {code}")
                continue

            year_data = {"label": name, "subjects": {}}

            for subj in subjects:
                print(f"\n    Subject: {subj['label']} ({subj['slug']}) - {subj['count']} files")

                subj_url = f"{BASE_URL}/ar/{code}/{subj['slug']}"
                subj_html = fetch(subj_url)
                if not subj_html:
                    continue

                categories = scrape_categories(subj_html, code, subj["slug"])
                subject_data = {
                    "label": subj["label"],
                    "count": subj["count"],
                    "categories": {},
                }

                for cat in categories:
                    print(f"      Category: {cat['label']} ({cat['slug']}) - {cat['count']} files")

                    cat_url = f"{BASE_URL}/ar/{code}/{subj['slug']}/{cat['slug']}"
                    cat_html = fetch(cat_url)
                    if not cat_html:
                        continue

                    files = scrape_files(cat_html)
                    cat_data = {
                        "label": cat["label"],
                        "count": cat["count"],
                        "files": files,
                    }

                    subject_data["categories"][cat["slug"]] = cat_data

                year_data["subjects"][subj["slug"]] = subject_data

            level_data["years"][code] = year_data

        data[level_key] = level_data

    # Save
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nData saved to {DATA_FILE}")

    # Summary
    total_subjects = sum(
        len(ld["years"][y]["subjects"])
        for ld in data.values()
        for y in ld["years"]
    )
    total_categories = sum(
        sum(len(s["categories"]) for s in ld["years"][y]["subjects"].values())
        for ld in data.values()
        for y in ld["years"]
    )
    total_files = sum(
        sum(
            sum(len(c["files"]) for c in s["categories"].values())
            for s in ld["years"][y]["subjects"].values()
        )
        for ld in data.values()
        for y in ld["years"]
    )
    print(f"\nSummary: {len(data)} levels, {total_subjects} subjects, {total_categories} categories, {total_files} files")

    return data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DzExams Scraper")
    parser.add_argument(
        "--level",
        nargs="+",
        choices=["primary", "middle", "secondary"],
        help="Levels to scrape (default: all)",
    )
    args = parser.parse_args()
    run(level_names=args.level)
