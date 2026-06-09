#!/usr/bin/env python3
"""Replace plain content.html links in sector pages with smart parameterized links."""
import re, os
from pathlib import Path

SECTORS_DIR = Path(__file__).parent.parent / "sectors"

LEVEL_MAP = {
    "primary.html": "primary",
    "middle.html": "middle",
    "secondary.html": "secondary",
}

YEAR_MAP = {
    "القسم التحضيري": "0ap",
    "السنة الأولى إبتدائي": "1ap",
    "السنة الثانية إبتدائي": "2ap",
    "السنة الثالثة إبتدائي": "3ap",
    "السنة الرابعة إبتدائي": "4ap",
    "السنة الخامسة إبتدائي": "5ap",
    "شهادة التعليم الإبتدائي": "bep",
    "السنة الأولى متوسط": "1am",
    "السنة الثانية متوسط": "2am",
    "السنة الثالثة متوسط": "3am",
    "السنة الرابعة متوسط": "4am",
    "شهادة التعليم المتوسط": "bem",
    "السنة الأولى ثانوي": "1as",
    "السنة الثانية ثانوي": "2as",
    "السنة الثالثة ثانوي": "3as",
    "شهادة البكالوريا": "bac",
}

SUBJECT_MAP = {
    "الرياضيات": "mathematiques",
    "اللغة العربية": "arabe",
    "اللغة الفرنسية": "francais",
    "اللغة الإنجليزية": "anglais",
    "التربية الإسلامية": "tarbia-islamia",
    "التربية المدنية": "tarbia-madania",
    "التاريخ والجغرافيا": "histoire-geographie",
    "العلوم الفيزيائية": "physique",
    "علوم الطبيعة والحياة": "sciences-naturelles",
    "التربية العلمية": "technologie",
    "التربية الفنية": "dessin",
    "التربية الموسيقية": "musique",
    "الفلسفة": "philosophie",
    "تعلم الكتابة": "ecriture",
    "أنشطة": "activites",
    "ملفات متنوعة": "documents",
    "مراجعة الرياضيات": "mathematiques",
    "مراجعة اللغة العربية": "arabe",
    "مراجعة الفرنسية": "francais",
    "مراجعة التربية الإسلامية": "tarbia-islamia",
    "مراجعة العلوم الفيزيائية": "physique",
    "مواضيع الامتحان": "",
    "نماذج بكالوريا": "",
}

IGNORE_HREF = {"#", ""}


def find_year_in_section(section_html, comment_text):
    for name, code in YEAR_MAP.items():
        if name in section_html or name in comment_text:
            return code
    return None


def get_subject_slug(h4_text):
    h4_text = h4_text.strip()
    if h4_text in SUBJECT_MAP:
        return SUBJECT_MAP[h4_text]
    return None


def process_file(filepath):
    level = LEVEL_MAP.get(filepath.name)
    if not level:
        return 0

    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    original = html
    count = 0

    section_pattern = re.compile(
        r'(<!--\s*=====\s*(.*?)\s*=====\s*-->.*?)'
        r'(?=<!--\s*=====|$)',
        re.DOTALL,
    )

    sections = list(section_pattern.finditer(html))
    for section in sections:
        section_html = section.group(1)
        comment_text = section.group(2)
        year_code = find_year_in_section(section_html, comment_text)
        if not year_code:
            continue

        def replace_link(m):
            nonlocal count
            full_tag = m.group(0)
            h4 = re.search(r'<h4>(.*?)</h4>', full_tag)
            is_action = 'action-link' in full_tag
            is_all_link = is_action and ('كل المواد' in full_tag or 'كل ما' in full_tag)

            if is_all_link:
                new_href = f'content.html?level={level}&year={year_code}'
            elif h4:
                subject = get_subject_slug(h4.group(1))
                if subject:
                    new_href = f'content.html?level={level}&year={year_code}&subject={subject}'
                else:
                    new_href = f'content.html?level={level}&year={year_code}'
            else:
                new_href = f'content.html?level={level}&year={year_code}'

            new_tag = full_tag.replace('href="content.html"', f'href="{new_href}"')
            if new_tag != full_tag:
                count += 1
            return new_tag

        new_section = re.sub(
            r'<a\s+href="content\.html"[^>]*>.*?</a>',
            replace_link,
            section_html,
            flags=re.DOTALL,
        )
        html = html.replace(section_html, new_section, 1)

    if html != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return count
    return 0


def main():
    total = 0
    for fname in sorted(os.listdir(SECTORS_DIR)):
        if fname in ("content.html",):
            continue
        fpath = SECTORS_DIR / fname
        if not fpath.is_file() or not fname.endswith(".html"):
            continue
        n = process_file(fpath)
        if n:
            print(f"  {fname}: {n} links updated")
        total += n
    print(f"\nDone! {total} links updated across all pages.")


if __name__ == "__main__":
    main()
