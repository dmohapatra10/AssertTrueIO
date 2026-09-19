#!/usr/bin/env python3
"""Extract raw content + a content manifest from an EXISTING, already-built
track. This reconstructs the 'source of truth' this site never actually had
persisted: for every page, pulls out title/description/difficulty/h1/prereqs/
article content, and reads the roadmap's own chapter-list to build a single
manifest.json describing the real chapter/lesson structure — the same
structure that, for Playwright, had silently drifted out of sync with reality
until it was manually reconstructed. This makes that reconstruction permanent
and reusable instead of a one-off fix."""
import re, os, json, html, sys

SITE = '/home/claude/site/asserttrue-static'

def extract_page_data(path):
    raw = open(path, encoding='utf-8').read()
    title_m = re.search(r'<title>(.*?)</title>', raw, re.S)
    desc_m = re.search(r'<meta name="description" content="(.*?)" />', raw, re.S)
    h1_m = re.search(r'<h1>(.*?)</h1>', raw, re.S)
    diff_m = re.search(r'tag-pill (\w+)">', raw)
    prereq_m = re.search(r'<p class="prereqs">(.*?)</p>', raw, re.S)
    article_m = re.search(r'<article class="content">(.*?)</article>', raw, re.S)
    if not (title_m and desc_m and h1_m and article_m):
        return None
    return {
        'title': title_m.group(1).strip(),
        'desc': html.unescape(desc_m.group(1)).strip(),
        'h1': h1_m.group(1).strip(),
        'difficulty': diff_m.group(1) if diff_m else 'Intermediate',
        'prereqs_html': prereq_m.group(1).strip() if prereq_m else '',
        'article_html': article_m.group(1).strip(),
    }

def write_raw_file(out_path, filename, data):
    prereqs = f'<p class="prereqs">{data["prereqs_html"]}</p>\n' if data['prereqs_html'] else ''
    content = f'''<!doctype html>
<html><head>
<title>{data['title']}</title>
<meta name="description" content="{html.escape(data['desc'], quote=True)}" />
<link rel="canonical" href="https://asserttrue.io/TRACK/{filename}" />
</head><body>
<p class="difficulty">{data['difficulty']}</p>
<h1>{data['h1']}</h1>
{prereqs}<article class="content">
{data['article_html']}
</article>
</body></html>
'''
    open(os.path.join(out_path, filename), 'w', encoding='utf-8').write(content)

def extract_manifest(track_dir):
    """Read the roadmap page's own chapter-list to get the real, current
    chapter/lesson structure — trusting it as ground truth since it's the
    thing a human actually sees and would notice if wrong."""
    raw = open(os.path.join(track_dir, 'index.html'), encoding='utf-8').read()
    m = re.search(r'<div class="chapter-list">(.*?)\n      </div>', raw, re.S)
    block = m.group(1)

    chapters = []
    # Split on each top-level chapter unit: either <details class="chapter-card"...
    # or <a href="..." class="chapter-card chapter-card-standalone"...
    units = re.split(r'(?=<details class="chapter-card"|<a href="[^"]+" class="chapter-card chapter-card-standalone")', block)
    for unit in units:
        unit = unit.strip()
        if not unit:
            continue
        num_m = re.search(r'chapter-num">(\d+)<', unit)
        title_m = re.search(r'chapter-title">(.*?)</span>', unit, re.S)
        if not (num_m and title_m):
            continue
        num = int(num_m.group(1))
        title = html.unescape(title_m.group(1)).strip()

        if 'chapter-card-standalone' in unit.split('>')[0] or unit.startswith('<a href='):
            href_m = re.search(r'href="([a-zA-Z0-9_-]+\.html)"', unit)
            chapters.append({'num': num, 'title': title, 'pages': [
                {'file': href_m.group(1), 'label': title}
            ]})
        else:
            pages = []
            for href, label in re.findall(r'<a href="([a-zA-Z0-9_-]+\.html)" class="sub-lesson-row[^"]*"[^>]*>.*?sub-lesson-title">(.*?)</span>', unit, re.S):
                label = html.unescape(label).strip()
                if label == 'Chapter Overview':
                    # use the real page's own h1/title instead of the generic label
                    label = title
                pages.append({'file': href, 'label': label})
            chapters.append({'num': num, 'title': title, 'pages': pages})

    return chapters

def run(track_slug, out_root):
    track_dir = os.path.join(SITE, track_slug)
    out_dir = os.path.join(out_root, track_slug)
    os.makedirs(out_dir, exist_ok=True)

    manifest_chapters = extract_manifest(track_dir)
    all_files = set()
    for ch in manifest_chapters:
        for p in ch['pages']:
            all_files.add(p['file'])

    extracted, missing = 0, []
    for fname in sorted(all_files):
        path = os.path.join(track_dir, fname)
        if not os.path.exists(path):
            missing.append(fname)
            continue
        data = extract_page_data(path)
        if data is None:
            missing.append(fname)
            continue
        write_raw_file(out_dir, fname, data)
        extracted += 1

    manifest = {'slug': track_slug, 'chapters': manifest_chapters}
    json.dump(manifest, open(os.path.join(out_dir, '_manifest.json'), 'w'), indent=2)

    print(f'{track_slug}: {len(manifest_chapters)} chapters, {extracted} pages extracted, {len(missing)} missing/failed: {missing}')

if __name__ == '__main__':
    track = sys.argv[1]
    out_root = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/engine/extracted'
    run(track, out_root)
