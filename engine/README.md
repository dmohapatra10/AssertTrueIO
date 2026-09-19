# AssertTrueIO Site Engine

This replaces the six separate, duplicated page-generator scripts that
originally built this site. It's the single source of truth that was
missing before — the thing whose absence caused the Playwright chapter-
numbering bug.

## What's here

- **`extracted/<track>/_manifest.json`** — the real chapter/lesson
  structure for each track: chapter numbers, titles, and which files
  belong to which chapter, in order. This is the thing that used to only
  exist duplicated across HTML — now it's one file per track that
  everything else reads from.
- **`extracted/<track>/*.html`** — the raw, unwrapped content for every
  lesson (title, description, difficulty, h1, prerequisites, and the
  actual article body). No navigation, no sidebar, no boilerplate — just
  the real content, extracted once from the site's existing pages.
- **`generate_site.py`** — the one generator, replacing the six old
  `migrate_*.py` scripts. Takes a track's manifest + raw content and
  produces every wrapped page plus the roadmap page.
- **`extract_content.py`** — rebuilds the manifest + raw content for a
  track from its current, live HTML. You shouldn't need this often (the
  manifest is now the source of truth going forward), but it exists in
  case raw content ever needs to be re-derived from the live site again.
- **`validate_site.py`** — every check that was previously run by hand,
  ad hoc, in a single AI conversation. Now a real script.

## Android install prompt (PWA)

The site is installable on Android (Chrome and other Chromium browsers) via
`manifest.json`, `sw.js`, and a custom install banner. The browser only
fires the underlying `beforeinstallprompt` event on a site that's actually
served over HTTPS (or localhost) and meets its installability criteria —
it never fires on `file://`, so this can't be tested by just opening the
HTML files locally. Deploy the site to any static HTTPS host (GitHub
Pages, Netlify, Vercel, etc.) to see the real banner appear on Android.

If you regenerate icons, keep both a plain version (`icons/icon-192.png`,
`icons/icon-512.png`) and a maskable version (`icons/icon-512-maskable.png`)
— Android's adaptive icon shapes crop the outer ~20% of a plain icon, so
the maskable version needs its artwork kept well inside that safe zone.

## Validation

`validate_site.py` checks tag balance, internal links, double-escaping
corruption, chapter numbering, and — as of this update — WCAG AA color
contrast for white text against every theme's accent and chapter-number
tones. If you add a 5th theme or change an existing one's colors, add it
to the `THEMES` dict near the top of `validate_site.py` too, so the new
palette gets checked automatically instead of relying on someone noticing
a hard-to-read color by eye.

## Book promo cards

Every lesson page and roadmap page shows a "Recommended Reading" carousel
in the right rail, pulled from `ALL_BOOKS` and `TRACK_BOOKS` in
`generate_site.py`. Tracks with a directly relevant book show only that
subset (Playwright shows 4 Playwright books, K6 shows 1 k6 book, etc.) —
Agentic AI Testing and AI-Powered Playwright have no topic-specific book
yet, so they show the full 8-book catalog instead of nothing.

To add a new book: add an entry to `ALL_BOOKS`, then add it to whichever
track(s) in `TRACK_BOOKS` it's relevant to (or to every track's list if
it's general). Re-run `generate_site.py` for the affected tracks.

## How to add a new lesson to an existing chapter

1. Add a new raw content file to `extracted/<track>/your-new-lesson.html`,
   following the format of any existing file in that folder (title, meta
   description, difficulty, h1, optional prereqs, article content).
2. Add an entry for it to the right chapter's `pages` list in
   `extracted/<track>/_manifest.json`.
3. Run: `python3 generate_site.py <track>`
4. Run: `python3 validate_site.py`

That's it. The nav, sidebar, breadcrumb, prev/next links, and roadmap page
all update automatically, everywhere, because they're generated from the
manifest — not hand-maintained in 500+ separate files.

## How to add a whole new chapter

Same as above, but add a new chapter object to the manifest's `chapters`
array, in the position you want it numbered. Numbering is automatic and
sequential based on array order — you can't create a duplicate-number bug
this way, because there's nothing to keep in sync by hand anymore.

## How to change something in every page at once

Edit the shared templates directly in `generate_site.py` (the `HEAD_TOP`,
`SCRIPT_TAIL`, `build_sidebar`, `build_page`, `build_roadmap` functions),
then run:

```
for t in playwright restassured k6 github-actions agentic-ai-testing ai-powered-playwright; do
  python3 generate_site.py $t
done
python3 validate_site.py
```

This is the whole point: a structural change is now one edit and one
script run, not hundreds of manual file edits.

## How to add an entirely new track

1. Create `extracted/<new-track>/_manifest.json` and its raw content files.
2. Add a config entry to `TRACK_CONFIG` in `generate_site.py` (nav label,
   theme class, hero title/lede).
3. Add it to `ALL_TRACKS_NAV` so it appears in every page's top nav.
4. Run `generate_site.py <new-track>`, then `validate_site.py`.

## What this doesn't fix

This is still a static-output pipeline, not a live build system — pages
are generated once and saved as plain HTML, not rendered per-request from
a template. That's a deliberate choice matching how this site is hosted
and shared (plain files, no server). If you eventually want true
live templating, the natural next step is porting this same manifest +
content structure into a real static site generator (Eleventy, Astro, or
Hugo) — the manifest format here would translate directly.
