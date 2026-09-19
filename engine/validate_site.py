#!/usr/bin/env python3
"""Persisted, reusable validation for the whole site. Run this after ANY
regeneration or manual edit. This is every check that was previously run
ad-hoc, by hand, in a single session — now a real script anyone can run,
any time, instead of relying on a human remembering to check.

Usage: python3 validate_site.py
Exit code 0 = all clean. Non-zero = at least one real problem found.
"""
import re, os, glob, sys
from html.parser import HTMLParser

SITE = '/home/claude/site/asserttrue-static'
TRACKS = ['playwright', 'restassured', 'k6', 'github-actions', 'agentic-ai-testing', 'ai-powered-playwright']
ROOT_FILES = ['index.html', 'books.html', 'about.html', 'changelog.html', 'contribute.html']

class TagChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []
    def handle_starttag(self, tag, attrs):
        void = {'meta','link','img','br','circle','path','rect','stop','ellipse','polyline','use','input','line'}
        if tag not in void: self.stack.append(tag)
    def handle_startendtag(self, tag, attrs): pass
    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag: self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag: self.errors.append(f'auto-closed {self.stack.pop()} for {tag}')
            if self.stack: self.stack.pop()
        else: self.errors.append(f'unexpected close: {tag}')

def check_tag_balance():
    problems = []
    for f in glob.glob(os.path.join(SITE, '**/*.html'), recursive=True):
        html = open(f, errors='ignore').read()
        c = TagChecker(); c.feed(html)
        if c.stack or c.errors:
            problems.append((f, c.stack, c.errors[:5]))
    return problems

def check_links():
    all_pages = {}
    for t in TRACKS:
        for f in glob.glob(os.path.join(SITE, t, '*.html')):
            all_pages[f'{t}/{os.path.basename(f)}'] = f
    for f in ROOT_FILES:
        all_pages[f] = os.path.join(SITE, f)
    broken = []
    for label, f in all_pages.items():
        html = open(f, errors='ignore').read()
        base_dir = os.path.dirname(f)
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith('http') or href.startswith('#') or href.startswith('mailto:') or not href.endswith('.html'):
                continue
            resolved = os.path.normpath(os.path.join(base_dir, href)).replace('\\', '/')
            rel = os.path.relpath(resolved, SITE).replace('\\', '/')
            if rel not in all_pages:
                broken.append((label, href))
    return broken

def check_double_escaping():
    problems = []
    for t in TRACKS:
        for f in glob.glob(os.path.join(SITE, t, '*.html')):
            html = open(f, errors='ignore').read()
            if 'amp;amp' in html:
                problems.append(f)
    return problems

def check_chapter_numbering():
    problems = []
    for t in TRACKS:
        path = os.path.join(SITE, t, 'index.html')
        if not os.path.exists(path): continue
        html = open(path, errors='ignore').read()
        nums = re.findall(r'chapter-num">(\d+)', html)
        seen = {}
        for n in nums:
            seen[n] = seen.get(n, 0) + 1
        dupes = {n: c for n, c in seen.items() if c > 1}
        if dupes:
            problems.append((t, dupes))
    return problems


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def mix(c1, c2, pct):
    return tuple(round(c1[i] * pct/100 + c2[i] * (100-pct)/100) for i in range(3))

def relative_luminance(rgb):
    def channel(c):
        c = c / 255
        return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055) ** 2.4
    r, g, b = [channel(c) for c in rgb]
    return 0.2126*r + 0.7152*g + 0.0722*b

def contrast_ratio(rgb1, rgb2):
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

# The 4 color themes' key values, kept in sync with css/style.css by hand
# (there are only 4, so duplicating here is simpler than parsing color-mix()
# out of the stylesheet). If you add or change a theme, update this too.
THEMES = {
    'Forest':  {'accent': '#0e6b52', 'accent-strong': '#0a5240'},
    'Ocean':   {'accent': '#3e4c8a', 'accent-strong': '#2e3a6c'},
    'Violet':  {'accent': '#723a5e', 'accent-strong': '#572a47'},
    'Sunset':  {'accent': '#a85d3b', 'accent-strong': '#82442a'},
}
WHITE, BLACK = (255, 255, 255), (0, 0, 0)
TONE_PCTS = [100, 88, 76, 94, 65, 82]  # must match --tone-1..6 in style.css

def check_theme_contrast():
    """White text/numbers must stay readable (WCAG AA, 4.5:1) against every
    theme's accent, accent-strong, and all six chapter-number tone shades."""
    problems = []
    for name, t in THEMES.items():
        accent = hex_to_rgb(t['accent'])
        accent_strong = hex_to_rgb(t['accent-strong'])
        for label, bg in [('accent', accent), ('accent-strong', accent_strong)]:
            r = contrast_ratio(WHITE, bg)
            if r < 4.5:
                problems.append(f"{name} white-on-{label}: {r:.2f}")
        for i, pct in enumerate(TONE_PCTS, 1):
            tone = mix(accent, BLACK, pct) if pct < 100 else accent
            r = contrast_ratio(WHITE, tone)
            if r < 4.5:
                problems.append(f"{name} white-on-tone-{i}: {r:.2f}")
    return problems

def main():
    ok = True

    print("Checking HTML tag balance...")
    p = check_tag_balance()
    if p:
        ok = False
        print(f"  FAIL: {len(p)} files with tag issues")
        for f, stack, errs in p[:10]: print(f"    {f}: stack={stack} errors={errs}")
    else:
        print("  OK")

    print("Checking internal links...")
    p = check_links()
    if p:
        ok = False
        print(f"  FAIL: {len(p)} broken links")
        for label, href in p[:10]: print(f"    {label} -> {href}")
    else:
        print("  OK")

    print("Checking for repeated-HTML-escaping corruption...")
    p = check_double_escaping()
    if p:
        ok = False
        print(f"  FAIL: {len(p)} files affected")
        for f in p[:10]: print(f"    {f}")
    else:
        print("  OK")

    print("Checking chapter numbering...")
    p = check_chapter_numbering()
    if p:
        ok = False
        print(f"  FAIL: {len(p)} tracks with duplicate chapter numbers")
        for t, dupes in p: print(f"    {t}: {dupes}")
    else:
        print("  OK")

    print("Checking theme color contrast (WCAG AA, white text on accent/tones)...")
    p = check_theme_contrast()
    if p:
        ok = False
        print(f"  FAIL: {len(p)} combinations below 4.5:1")
        for c in p: print(f"    {c}")
    else:
        print("  OK")

    print()
    print("ALL CHECKS PASSED" if ok else "VALIDATION FAILED — see above")
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
