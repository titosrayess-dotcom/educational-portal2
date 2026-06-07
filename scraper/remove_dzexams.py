#!/usr/bin/env python3
"""
Remove all dzexams references from HTML files:
- Replace text mentions of dzexams/dzexams.pro
- Remove external links to dzexams.com / dzexams.pro
- Replace internal links to dzexams.html / dzexams-pro.html with content.html
- Remove download buttons that link to dzexams.com in content.html
- Repurpose dzexams.html and dzexams-pro.html
"""
import re, os

sectors = "sectors"

def replace_in_file(filepath, replacements):
    """Apply list of (old, new) string replacements to a file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    before = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != before:
        count = sum(1 for old, _ in replacements if old in before)
        print(f"  {os.path.basename(filepath)}: {count} replacements")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


# =====================================================================
# 1. dzexams.html → Replace content with redirect
# =====================================================================
dzexams_html = os.path.join(sectors, "dzexams.html")
if os.path.exists(dzexams_html):
    with open(dzexams_html, "r", encoding="utf-8") as f:
        content = f.read()
    # Replace the body content (keep header/footer pattern)
    new_body = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>المكتبة التعليمية | البوابة التعليمية</title>
    <meta name="description" content="المكتبة التعليمية: جميع المواضيع والفروض والاختبارات">
    <link rel="icon" href="../assets/images/icon.png" type="image/png">
    <link rel="stylesheet" href="../assets/css/style-sector.css">
    <meta http-equiv="refresh" content="0;url=content.html">
</head>
<body>
    <p style="text-align:center;padding:4rem;font-family:Tajawal,sans-serif;">جاري التحويل إلى <a href="content.html">المكتبة التعليمية</a>...</p>
</body>
</html>"""
    with open(dzexams_html, "w", encoding="utf-8") as f:
        f.write(new_body)
    print("  dzexams.html → redirect to content.html")


# =====================================================================
# 2. dzexams-pro.html → Replace content with redirect
# =====================================================================
dzexams_pro_html = os.path.join(sectors, "dzexams-pro.html")
if os.path.exists(dzexams_pro_html):
    with open(dzexams_pro_html, "r", encoding="utf-8") as f:
        content = f.read()
    new_body = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>المكتبة التعليمية | البوابة التعليمية</title>
    <meta name="description" content="المكتبة التعليمية: جميع المواضيع والفروض والاختبارات">
    <link rel="icon" href="../assets/images/icon.png" type="image/png">
    <link rel="stylesheet" href="../assets/css/style-sector.css">
    <meta http-equiv="refresh" content="0;url=content.html">
</head>
<body>
    <p style="text-align:center;padding:4rem;font-family:Tajawal,sans-serif;">جاري التحويل إلى <a href="content.html">المكتبة التعليمية</a>...</p>
</body>
</html>"""
    with open(dzexams_pro_html, "w", encoding="utf-8") as f:
        f.write(new_body)
    print("  dzexams-pro.html → redirect to content.html")


# =====================================================================
# 3. Process all other HTML files
# =====================================================================
html_files = [f for f in os.listdir(sectors) if f.endswith(".html") and f not in ("dzexams.html", "dzexams-pro.html")]
html_files.append("index.html")

for fname in html_files:
    fpath = os.path.join(sectors, fname) if fname != "index.html" else fname
    if not os.path.exists(fpath):
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    before = content

    # --- Text replacements ---
    # Visible text mentions (case-insensitive handled by specific patterns)
    content = content.replace("Dzexams.pro", "المكتبة التعليمية")
    content = content.replace("dzexams.pro", "المكتبة التعليمية")
    content = content.replace("Dzexams", "المكتبة التعليمية")
    # be careful not to replace URLs containing "dzexams"
    # But we already removed the URLs, so remaining "dzexams" is text

    # Replace any remaining lowercase "dzexams" in text (not URLs)
    # Use regex to find "dzexams" that's not part of a URL
    def replace_dzexams_text(m):
        # Skip if it's part of a URL or href
        start = max(0, m.start() - 20)
        prefix = content[start:m.start()].lower()
        if 'href=' in prefix or 'src=' in prefix:
            return m.group(0)
        return "المكتبة التعليمية"
    
    if "dzexams" in content.lower():
        # More careful: replace visible text mentions
        # Pattern: "dzexams" or "Dzexams" that appears as text (not in tags/attributes)
        content = re.sub(
            r'(?i)(?<!["\']/)dzexams(?!\.(?:com|pro|html|png|jpg|svg|ico|webp))',
            "المكتبة التعليمية",
            content,
        )

    # --- External link removal ---
    # Remove external links to dzexams.com (already mostly done, catch any remaining)
    content = re.sub(
        r'<a\s+href="https?://(?:www\.)?dzexams\.com[^"]*"[^>]*>.*?</a>',
        "",
        content,
    )
    content = re.sub(
        r'<a\s+href="https?://dzexams\.pro[^"]*"[^>]*>.*?</a>',
        "",
        content,
    )

    # --- Internal link redirections ---
    content = content.replace('href="dzexams.html"', 'href="content.html"')
    content = content.replace("href='dzexams.html'", "href='content.html'")
    content = content.replace('href="dzexams-pro.html"', 'href="content.html"')
    content = content.replace("href='dzexams-pro.html'", "href='content.html'")
    content = content.replace('href="../sectors/dzexams.html"', 'href="content.html"')
    content = content.replace('href="../sectors/dzexams-pro.html"', 'href="content.html"')

    if content != before:
        print(f"  {fname}: updated")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)


# =====================================================================
# 4. content.html: Remove download buttons that link to dzexams.com
# =====================================================================
content_html = os.path.join(sectors, "content.html")
if os.path.exists(content_html):
    with open(content_html, "r", encoding="utf-8") as f:
        content = f.read()
    before = content
    
    # Remove the download link from the file-item template
    # Change: showing file title with download button → just file title
    old_file_template = '''                    <span class="file-title"><i class="fas fa-file-pdf" style="color:var(--accent);margin-left:0.5rem"></i>${title}</span>
                    <a href="${url}" target="_blank" rel="noopener noreferrer" class="file-download"><i class="fas fa-download"></i> تحميل</a>'''
    new_file_template = '''                    <span class="file-title"><i class="fas fa-file-pdf" style="color:var(--accent);margin-left:0.5rem"></i>${title}</span>'''
    content = content.replace(old_file_template, new_file_template)
    
    # Also remove the url variable since it's no longer used in the template
    # The files loop still works, just doesn't use f.url
    # Actually let me check the code structure...
    
    if content != before:
        print("  content.html: removed download buttons")
        with open(content_html, "w", encoding="utf-8") as f:
            f.write(content)

print("\nDone! All dzexams references removed.")
