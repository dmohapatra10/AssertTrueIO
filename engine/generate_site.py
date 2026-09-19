#!/usr/bin/env python3
"""THE single, unified site generator — replaces the six separate,
duplicated migrate_*.py scripts. Takes one track's manifest.json + raw
content files and produces the complete, wrapped site output: every lesson
page and the roadmap page, using one shared template.

Usage: generate_site.py <track_slug>
Reads:  /home/claude/engine/extracted/<track_slug>/_manifest.json + raw *.html
Writes: /home/claude/site/asserttrue-static/<track_slug>/*.html
"""
import re, os, json, sys

SITE = '/home/claude/site/asserttrue-static'
EXTRACTED = '/home/claude/engine/extracted'
CSS_V = '93'

ICON_LAYERS = '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>'
ICON_SETTINGS = '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
ICON_PUZZLE = '<path d="M4 7h4V5a2 2 0 0 1 4 0v2h4v4h2a2 2 0 0 1 0 4h-2v4H4v-4H2a2 2 0 0 1 0-4h2z"/>'
ICON_CODE = '<polyline points="8 6 2 12 8 18"/><polyline points="16 6 22 12 16 18"/>'
ICON_ROTATION = [ICON_LAYERS, ICON_SETTINGS, ICON_PUZZLE, ICON_CODE]

# Per-track config: nav label, theme body class ('' for the default/green
# track), hero title, hero lede, canonical base path.
TRACK_CONFIG = {
    'playwright': {'nav_label': 'Playwright', 'theme_class': '', 'hero_title': 'Playwright Tutorial',
        'hero_lede': "Go from basics to advanced with hands-on examples, real-world projects, and best practices."},
    'restassured': {'nav_label': 'RestAssured', 'theme_class': 'theme-restassured', 'hero_title': 'RestAssured Tutorial',
        'hero_lede': 'Learn API testing with RestAssured — practical examples and real-world scenarios.'},
    'k6': {'nav_label': 'K6', 'theme_class': 'theme-k6', 'hero_title': 'K6 Performance Testing',
        'hero_lede': 'Learn performance testing with K6 — scripting, load testing, and analysis.'},
    'github-actions': {'nav_label': 'GitHub Actions', 'theme_class': 'theme-gh', 'hero_title': 'GitHub Actions Tutorial',
        'hero_lede': 'Learn CI/CD with GitHub Actions — automate tests, build workflows, integrate with real projects.'},
    'agentic-ai-testing': {'nav_label': 'AI Testing', 'theme_class': 'theme-ai', 'hero_title': 'Agentic AI Testing',
        'hero_lede': 'Learn how AI agents can plan, generate, execute, and repair automated tests.'},
    'ai-powered-playwright': {'nav_label': 'AI Playwright', 'theme_class': 'theme-aipw', 'hero_title': 'AI-Powered Playwright Automation',
        'hero_lede': 'Evolve deterministic Playwright automation into intelligent, AI-assisted and eventually autonomous browser testing.'},
}

ALL_TRACKS_NAV = [
    ('playwright', 'Playwright'), ('restassured', 'RestAssured'), ('k6', 'K6'),
    ('github-actions', 'GitHub Actions'), ('agentic-ai-testing', 'AI Testing'),
    ('ai-powered-playwright', 'AI Playwright'),
]

ALL_BOOKS = [
    {'url': 'https://www.amazon.in/CRACKING-PLAYWRIGHT-INTERVIEW-Interview-Preparation-ebook/dp/B0H7MGN2XK',
     'img': '../images/books/book-1-cracking-playwright-interview.webp', 'alt': 'Cracking the Playwright Interview book cover',
     'title': 'Cracking the Playwright Interview', 'tagline': 'The Complete Interview Preparation Guide'},
    {'url': 'https://www.amazon.in/Playwright-Automation-Testing-Complete-TypeScript-ebook/dp/B0G492YGYJ',
     'img': '../images/books/book-2-playwright-automation-testing.jpg', 'alt': 'Playwright Automation Testing book cover',
     'title': 'Playwright Automation Testing', 'tagline': 'Complete Guide with TypeScript'},
    {'url': 'https://www.amazon.in/API-Testing-Playwright-TypeScript-Practical-ebook/dp/B0GS99CDCK',
     'img': '../images/books/book-3-api-testing-playwright-typescript.webp', 'alt': 'API Testing with Playwright & TypeScript book cover',
     'title': 'API Testing with Playwright & TypeScript', 'tagline': 'A Practical Guide from Zero to Expert'},
    {'url': 'https://www.amazon.in/Playwright-Mastery-TypeScript-Cucumber-Applications-ebook/dp/B0GPKXYB9Q',
     'img': '../images/books/book-4-playwright-mastery-typescript-cucumber.jpg', 'alt': 'Playwright Mastery with TypeScript & Cucumber book cover',
     'title': 'Playwright Mastery with TypeScript & Cucumber', 'tagline': 'Building Robust, Scalable Test Frameworks'},
    {'url': 'https://www.amazon.in/Complete-Rest-Assured-Testing-Guide/dp/B0FYXTD7Z7',
     'img': '../images/books/book-5-complete-restassured-testing-guide.jpg', 'alt': 'The Complete RestAssured Testing Guide book cover',
     'title': 'The Complete RestAssured Testing Guide', 'tagline': 'Mastering API Testing with Java'},
    {'url': 'https://www.amazon.in/CRACKING-RESTASSURED-INTERVIEW-Automation-Real-World-ebook/dp/B0GX38K64W',
     'img': '../images/books/book-6-cracking-restassured-interview.webp', 'alt': 'Cracking the RestAssured Interview book cover',
     'title': 'Cracking the RestAssured Interview', 'tagline': 'A Practical Guide to Mastering REST API Testing with RestAssured'},
    {'url': 'https://www.amazon.in/Performance-Testing-Automation-Engineering-Applications-ebook/dp/B0GTYVVGVD',
     'img': '../images/books/book-7-performance-testing-with-k6.jpg', 'alt': 'Performance Testing with k6 book cover',
     'title': 'Performance Testing with k6', 'tagline': 'A Practical Guide to Automation Engineering with Applications'},
    {'url': 'https://www.amazon.in/GITHUB-ACTIONS-ACTION-Developers-Automating-ebook/dp/B0GX2YXBN1',
     'img': '../images/books/book-8-github-actions-in-action.jpg', 'alt': "GitHub Actions in Action book cover",
     'title': 'GitHub Actions in Action', 'tagline': "The Complete Developer's Guide to Automating CI/CD Pipelines"},
]
_BY_TITLE = {b['title']: b for b in ALL_BOOKS}

# Which books each track's promo card shows. Tracks with a directly relevant
# book show only that subset (matching the site's original, real pattern).
# The two AI tracks have no topic-specific book yet, so they show the full
# catalog rather than nothing.
TRACK_BOOKS = {
    'playwright': [_BY_TITLE[t] for t in [
        'Cracking the Playwright Interview', 'Playwright Automation Testing',
        'API Testing with Playwright & TypeScript', 'Playwright Mastery with TypeScript & Cucumber']],
    'restassured': [_BY_TITLE[t] for t in [
        'The Complete RestAssured Testing Guide', 'Cracking the RestAssured Interview']],
    'k6': [_BY_TITLE['Performance Testing with k6']],
    'github-actions': [_BY_TITLE['GitHub Actions in Action']],
    'agentic-ai-testing': ALL_BOOKS,
    'ai-powered-playwright': ALL_BOOKS,
}

def build_book_card(slug):
    books = TRACK_BOOKS.get(slug, [])
    if not books:
        return ''
    slides = []
    dots = []
    for i, b in enumerate(books):
        active = ' active' if i == 0 else ''
        slides.append(
            f'<div class="book-slide{active}" data-index="{i}">\n'
            f'  <a href="{b["url"]}" target="_blank" rel="nofollow noopener" class="book-cover-mock">'
            f'<img src="{b["img"]}" alt="{b["alt"]}" loading="lazy" /></a>\n'
            f'  <div class="book-info">\n'
            f'    <h5>{b["title"]}</h5>\n'
            f'    <p>{b["tagline"]}</p>\n'
            f'    <a href="{b["url"]}" target="_blank" rel="nofollow noopener" class="book-buy-btn">View on Amazon '
            f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M13 6l6 6-6 6"/></svg></a>\n'
            f'  </div>\n</div>')
        if len(books) > 1:
            dots.append(f'<button type="button" class="book-dot{active}" data-goto="{i}" aria-label="Book {i+1}"></button>')

    nav_arrows = ''
    counter = ''
    if len(books) > 1:
        nav_arrows = (
            '  <button type="button" class="book-nav-arrow book-nav-prev" data-dir="-1" aria-label="Previous book">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg></button>\n'
            '  <button type="button" class="book-nav-arrow book-nav-next" data-dir="1" aria-label="Next book">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg></button>\n'
        )
        counter = f'<span class="book-promo-counter"><span class="book-counter-current">1</span> / {len(books)}</span>'
        progress = '<div class="book-progress-track"><div class="book-progress-fill running"></div></div>'
    else:
        progress = ''

    dots_html = f'    <div class="book-dots">{"".join(dots)}</div>\n' if dots else ''
    return (f'      <div class="rail-card book-promo-card">\n'
            f'  <div class="book-promo-inner">\n'
            f'    <div class="book-promo-badge">&#128218; Recommended Reading</div>{counter}\n'
            f'    <div class="book-carousel">\n{nav_arrows}    {"".join(slides)}\n    </div>\n'
            f'{dots_html}'
            f'    {progress}\n'
            f'  </div>\n</div>\n')


def build_topnav(current_slug):
    links = []
    for slug, label in ALL_TRACKS_NAV:
        href = 'index.html' if slug == current_slug else f'../{slug}/index.html'
        active = ' class="active"' if slug == current_slug else ''
        links.append(f'      <a href="{href}"{active}>{label}</a>')
    return '\n'.join(links)

def build_sidebar(current_file, chapters):
    parts = []
    active = ' active' if current_file == 'index.html' else ''
    parts.append(f'<a href="index.html" class="sidebar-overview-link{active}"><svg class="icon" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></svg><span>Roadmap</span></a>')
    for i, ch in enumerate(chapters):
        icon = ICON_ROTATION[i % len(ICON_ROTATION)]
        num = f"{ch['num']:02d}"
        hub_file, hub_label = ch['pages'][0]['file'], ch['title']
        parts.append('<details class="sidebar-group-toggle" open>')
        parts.append(f'<summary><svg class="icon" viewBox="0 0 24 24">{icon}</svg><span>{num} {ch["title"]}</span><span class="chev">&#9662;</span></summary>')
        parts.append('<div class="sidebar-group-body">')
        active = ' active' if current_file == hub_file else ''
        parts.append(f'<a href="{hub_file}" class="sidebar-link sidebar-parent-link{active}"><span class="dot"></span>{hub_label}</a>')
        if len(ch['pages']) > 1:
            parts.append('<div class="sidebar-sub">')
            for p in ch['pages'][1:]:
                active = ' active' if current_file == p['file'] else ''
                parts.append(f'<a href="{p["file"]}" class="sidebar-link{active}"><span class="dot"></span>{p["label"]}</a>')
            parts.append('</div>')
        parts.append('</div></details>')
    return '\n'.join(parts)

HEAD_TOP = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <script>try{{var t=localStorage.getItem('assertTrueColorTheme');if(t&&t!=='forest'){{document.documentElement.setAttribute('data-color-theme',t);}}}}catch(e){{}}</script>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <link rel="canonical" href="https://asserttrue.io/{slug}/{filename}" />
  <link rel="stylesheet" href="../css/style.css?v={css_v}" />
  <link rel="manifest" href="../manifest.json" />
  <meta name="theme-color" content="#0e6b52" />
  <link rel="icon" href="../icons/icon-192.png" />
</head>
<body{body_class}>
  <header class="topnav">
    <button class="mobile-menu-btn" onclick="openSidebar()">&#9776;</button>
    <a href="../index.html" class="brand"><svg class="logo-mark" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"><rect width="40" height="40" rx="11" fill="url(#logoGrad)"/><path d="M11 21.5 L17 27.5 L29.5 13" stroke="#ffffff" stroke-width="4.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/><defs><linearGradient id="logoGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse"><stop stop-color="#22c55e"/><stop offset="1" stop-color="#15803d"/></linearGradient></defs></svg><span class="brand-text">Assert<span class="brand-true">True</span><span class="brand-io">IO</span></span></a>
    <nav class="topnav-links">
{topnav}
      <a href="../about.html">About</a>
      <a href="../books.html">Books</a>
    </nav>
    <div class="topnav-right">
      <div class="topnav-search-wrap">
        <input type="text" class="search-box" id="doc-search-input" placeholder="Search tutorials..." autocomplete="off" aria-label="Search tutorials" aria-expanded="false" />
        <div class="hp-search-results" id="doc-search-results" hidden></div>
      </div>
      <div class="theme-picker">
        <button class="icon-btn theme-picker-btn" onclick="toggleThemePicker()" aria-label="Choose color theme" aria-haspopup="true" aria-expanded="false" id="theme-picker-btn">
          <span style="background:#0e6b52"></span><span style="background:#3e4c8a"></span><span style="background:#723a5e"></span><span style="background:#a85d3b"></span>
        </button>
        <div class="theme-picker-popover" id="theme-picker-popover">
          <button type="button" class="theme-picker-option" data-theme="forest" onclick="setColorTheme('forest')"><span class="theme-picker-swatch" style="background:#0e6b52"></span>Forest<svg class="check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><polyline points="20 6 9 17 4 12"/></svg></button>
          <button type="button" class="theme-picker-option" data-theme="ocean" onclick="setColorTheme('ocean')"><span class="theme-picker-swatch" style="background:#3e4c8a"></span>Ocean<svg class="check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><polyline points="20 6 9 17 4 12"/></svg></button>
          <button type="button" class="theme-picker-option" data-theme="violet" onclick="setColorTheme('violet')"><span class="theme-picker-swatch" style="background:#723a5e"></span>Violet<svg class="check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><polyline points="20 6 9 17 4 12"/></svg></button>
          <button type="button" class="theme-picker-option" data-theme="sunset" onclick="setColorTheme('sunset')"><span class="theme-picker-swatch" style="background:#a85d3b"></span>Sunset<svg class="check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px;"><polyline points="20 6 9 17 4 12"/></svg></button>
        </div>
      </div>
    </div>
  </header>
  <div class="sidebar-backdrop" id="sidebar-backdrop" onclick="closeSidebar()"></div>
  <div class="app-shell">
    <nav class="doc-sidebar" id="doc-sidebar">
{sidebar}
</nav>
    <main class="doc-main">
'''
print("HEAD_TOP template written")

MOBILE_TABBAR = '''  <nav class="mobile-tabbar">
  <a href="../index.html"><svg class="icon" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span>Home</span></a>
  <a href="index.html" class="active"><svg class="icon" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg><span>Tutorials</span></a>
  <a href="../books.html"><svg class="icon" viewBox="0 0 24 24"><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v16H6.5A2.5 2.5 0 0 0 4 20.5"/><path d="M4 4.5v16"/></svg><span>Books</span></a>
  <a href="../about.html"><svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><line x1="12" y1="16" x2="12" y2="11.5"/><circle cx="12" cy="8" r="0.8" fill="currentColor" stroke="none"/></svg><span>About</span></a>
</nav>
'''

SCRIPT_TAIL = '''
  <script>
  document.querySelectorAll('.book-promo-card').forEach(function(card) {
    var slides = card.querySelectorAll('.book-slide');
    var dots = card.querySelectorAll('.book-dot');
    var counter = card.querySelector('.book-counter-current');
    var progressFill = card.querySelector('.book-progress-fill');
    var carousel = card.querySelector('.book-carousel');
    if (slides.length < 2) return;
    var idx = 0, timer = null, paused = false;

    function goTo(newIdx) {
      slides[idx].classList.remove('active');
      if (dots[idx]) dots[idx].classList.remove('active');
      idx = (newIdx + slides.length) % slides.length;
      slides[idx].classList.add('active');
      if (dots[idx]) dots[idx].classList.add('active');
      if (counter) counter.textContent = idx + 1;
      restartProgress();
    }
    function restartProgress() {
      if (!progressFill) return;
      progressFill.classList.remove('running');
      void progressFill.offsetWidth;
      if (!paused) progressFill.classList.add('running');
    }
    function restartTimer() {
      if (timer) clearInterval(timer);
      timer = setInterval(function() { if (!paused) goTo(idx + 1); }, 5000);
    }

    dots.forEach(function(dot) {
      dot.addEventListener('click', function() { goTo(parseInt(dot.getAttribute('data-goto'), 10)); restartTimer(); });
    });
    card.querySelectorAll('.book-nav-arrow').forEach(function(arrow) {
      arrow.addEventListener('click', function() { goTo(idx + parseInt(arrow.getAttribute('data-dir'), 10)); restartTimer(); });
    });
    card.addEventListener('mouseenter', function() { paused = true; if (progressFill) progressFill.classList.remove('running'); });
    card.addEventListener('mouseleave', function() { paused = false; restartProgress(); });

    var touchStartX = null;
    if (carousel) {
      carousel.addEventListener('touchstart', function(e) { touchStartX = e.touches[0].clientX; paused = true; }, { passive: true });
      carousel.addEventListener('touchend', function(e) {
        if (touchStartX === null) return;
        var dx = e.changedTouches[0].clientX - touchStartX;
        if (Math.abs(dx) > 35) { goTo(idx + (dx < 0 ? 1 : -1)); restartTimer(); }
        touchStartX = null;
        paused = false; restartProgress();
      }, { passive: true });
    }

    restartProgress();
    restartTimer();
  });

  function copyCode(btn) {
    const code = btn.nextElementSibling.innerText;
    navigator.clipboard.writeText(code).then(function() {
      btn.textContent = 'Copied';
      btn.classList.add('copied');
      setTimeout(function() { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 1500);
    });
  }
  function openSidebar() {
    document.getElementById('doc-sidebar').classList.add('open');
    document.getElementById('sidebar-backdrop').classList.add('show');
    document.body.classList.add('no-scroll');
  }
  function closeSidebar() {
    document.getElementById('doc-sidebar').classList.remove('open');
    document.getElementById('sidebar-backdrop').classList.remove('show');
    document.body.classList.remove('no-scroll');
  }
  function toggleThemePicker() {
    var popover = document.getElementById('theme-picker-popover');
    var btn = document.getElementById('theme-picker-btn');
    var isOpen = popover.classList.toggle('open');
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }
  function setColorTheme(theme) {
    if (theme === 'forest') {
      document.documentElement.removeAttribute('data-color-theme');
    } else {
      document.documentElement.setAttribute('data-color-theme', theme);
    }
    try { localStorage.setItem('assertTrueColorTheme', theme); } catch (e) {}
    document.querySelectorAll('.theme-picker-option').forEach(function(opt) {
      opt.classList.toggle('active', opt.getAttribute('data-theme') === theme);
    });
    var popover = document.getElementById('theme-picker-popover');
    var btn = document.getElementById('theme-picker-btn');
    if (popover) popover.classList.remove('open');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.theme-picker')) {
      var popover = document.getElementById('theme-picker-popover');
      if (popover) popover.classList.remove('open');
    }
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      var popover = document.getElementById('theme-picker-popover');
      var btn = document.getElementById('theme-picker-btn');
      if (popover && popover.classList.contains('open')) {
        popover.classList.remove('open');
        if (btn) { btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
      }
    }
  });
  (function() {
    var current = 'forest';
    try { current = localStorage.getItem('assertTrueColorTheme') || 'forest'; } catch (e) {}
    var opt = document.querySelector('.theme-picker-option[data-theme="' + current + '"]');
    if (opt) opt.classList.add('active');
  })();
  var docSearchIndex = null;
  var docSearchPromise = null;
  function loadDocSearchIndex() {
    if (!docSearchPromise) {
      docSearchPromise = new Promise(function(resolve) {
        var s = document.createElement('script');
        s.src = '../search-index.js';
        s.onload = function() { docSearchIndex = window.SITE_SEARCH_INDEX || []; resolve(docSearchIndex); };
        s.onerror = function() { docSearchIndex = []; resolve(docSearchIndex); };
        document.head.appendChild(s);
      });
    }
    return docSearchPromise;
  }
  function docEscapeHtml(str) {
    return str.replace(/[&<>"']/g, function(c) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];
    });
  }
  function docHighlight(text, query) {
    var escaped = docEscapeHtml(text);
    if (!query) return escaped;
    var idx = escaped.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return escaped;
    return escaped.slice(0, idx) + '<mark>' + escaped.slice(idx, idx + query.length) + '</mark>' + escaped.slice(idx + query.length);
  }
  function docSearchFn(query) {
    query = query.trim().toLowerCase();
    if (!query || !docSearchIndex) return [];
    var scored = [];
    for (var i = 0; i < docSearchIndex.length; i++) {
      var e = docSearchIndex[i];
      var titleIdx = e.title.toLowerCase().indexOf(query);
      var descIdx = e.desc.toLowerCase().indexOf(query);
      if (titleIdx === -1 && descIdx === -1) continue;
      var score = titleIdx !== -1 ? (titleIdx === 0 ? 0 : 1) : 2;
      scored.push({ entry: e, score: score });
    }
    scored.sort(function(a, b) { return a.score - b.score; });
    return scored.slice(0, 8).map(function(s) { return s.entry; });
  }
  (function() {
    var docInput = document.getElementById('doc-search-input');
    var docResults = document.getElementById('doc-search-results');
    if (!docInput || !docResults) return;
    function renderDocSearch(query) {
      if (!query.trim()) { docResults.hidden = true; docInput.setAttribute('aria-expanded', 'false'); return; }
      if (!docSearchIndex) {
        docResults.innerHTML = '<div class="hp-search-empty">Loading&hellip;</div>';
        docResults.hidden = false;
        loadDocSearchIndex().then(function() { renderDocSearch(docInput.value); });
        return;
      }
      var matches = docSearchFn(query);
      if (matches.length === 0) {
        docResults.innerHTML = '<div class="hp-search-empty">No tutorials found for &ldquo;' + docEscapeHtml(query) + '&rdquo;</div>';
        docResults.hidden = false;
        docInput.setAttribute('aria-expanded', 'true');
        return;
      }
      var html = '<div class="hp-search-hint">' + matches.length + ' result' + (matches.length === 1 ? '' : 's') + '</div>';
      matches.forEach(function(e) {
        var trackClass = e.track === 'Playwright' ? 'pw' : (e.track === 'RestAssured' ? 'ra' : (e.track === 'K6' ? 'k6' : (e.track === 'GitHub Actions' ? 'gh' : (e.track === 'AI-Powered Playwright' ? 'aipw' : 'ai'))));
        html += '<a class="hp-search-item" href="../' + e.url + '">' +
          '<div class="hp-search-item-title">' + docHighlight(e.title, query) + '</div>' +
          '<div class="hp-search-item-desc">' + docEscapeHtml(e.desc) + '</div>' +
          '<span class="hp-search-item-track ' + trackClass + '">' + e.track + '</span>' +
          '</a>';
      });
      docResults.innerHTML = html;
      docResults.hidden = false;
      docInput.setAttribute('aria-expanded', 'true');
    }
    docInput.addEventListener('input', function() { renderDocSearch(docInput.value); });
    docInput.addEventListener('focus', function() { loadDocSearchIndex(); if (docInput.value.trim()) renderDocSearch(docInput.value); });
    docInput.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') { docResults.hidden = true; docInput.blur(); }
      else if (e.key === 'Enter') { var first = docResults.querySelector('.hp-search-item'); if (first) window.location.href = first.getAttribute('href'); }
    });
    document.addEventListener('click', function(e) { if (!e.target.closest('.topnav-search-wrap')) { docResults.hidden = true; } });
  })();

  (function() {
    var deferredInstallPrompt = null;
    function getInstallBanner() { return document.getElementById('install-banner'); }
    window.addEventListener('beforeinstallprompt', function(e) {
      e.preventDefault();
      if (localStorage.getItem('assertTrueInstallDismissed') === '1') return;
      deferredInstallPrompt = e;
      var banner = getInstallBanner();
      if (banner) banner.classList.add('show');
    });
    window.handleInstallClick = function() {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      deferredInstallPrompt.userChoice.then(function() {
        deferredInstallPrompt = null;
        var banner = getInstallBanner();
        if (banner) banner.classList.remove('show');
      });
    };
    window.dismissInstallBanner = function() {
      var banner = getInstallBanner();
      if (banner) banner.classList.remove('show');
      try { localStorage.setItem('assertTrueInstallDismissed', '1'); } catch (e) {}
    };
    window.addEventListener('appinstalled', function() {
      var banner = getInstallBanner();
      if (banner) banner.classList.remove('show');
    });
    try {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('../sw.js').catch(function() {});
      }
    } catch (e) {}
  })();
'''

def estimate_read_time(text):
    words = len(re.findall(r'\w+', text))
    return f'{max(2, round(words / 220))} min read'

def find_chapter_for(filename, chapters):
    for ch in chapters:
        for i, p in enumerate(ch['pages']):
            if p['file'] == filename:
                return ch, i == 0
    return None, False

def flat_page_order(chapters):
    order = []
    for ch in chapters:
        for p in ch['pages']:
            order.append(p['file'])
    return order

def label_for(filename, chapters):
    for ch in chapters:
        for p in ch['pages']:
            if p['file'] == filename:
                return p['label']
    return filename

def build_page(slug, config, filename, raw_html, chapters):
    title_m = re.search(r'<title>(.*?)</title>', raw_html, re.S)
    desc_m = re.search(r'<meta name="description" content="(.*?)" />', raw_html, re.S)
    diff_m = re.search(r'<p class="difficulty">(.*?)</p>', raw_html, re.S)
    h1_m = re.search(r'<h1>(.*?)</h1>', raw_html, re.S)
    prereq_m = re.search(r'<p class="prereqs">(.*?)</p>', raw_html, re.S)
    article_m = re.search(r'(<article class="content">.*?</article>)', raw_html, re.S)

    title = title_m.group(1).strip()
    desc = desc_m.group(1).strip()
    difficulty = diff_m.group(1).strip() if diff_m else 'Intermediate'
    h1 = h1_m.group(1).strip()
    prereqs = prereq_m.group(0) if prereq_m else ''
    article = article_m.group(1)

    ch, is_hub = find_chapter_for(filename, chapters)
    sidebar = build_sidebar(filename, chapters)
    topnav = build_topnav(slug)
    body_class = f' class="{config["theme_class"]}"' if config['theme_class'] else ''

    crumbs = [f'<a href="../index.html">Home</a> <span class="crumb-sep">&rsaquo;</span> <a href="index.html">{config["hero_title"].split(" Tutorial")[0]}</a>']
    if is_hub or ch is None:
        crumbs.append(f'<span class="crumb-current">{h1}</span>')
    else:
        crumbs.append(f'<a href="{ch["pages"][0]["file"]}">{ch["title"]}</a> <span class="crumb-sep">&rsaquo;</span> <span class="crumb-current">{h1}</span>')
    breadcrumb = f'<nav class="breadcrumbs" aria-label="Breadcrumb">{" <span class=\"crumb-sep\">&rsaquo;</span> ".join(crumbs)}</nav>'

    read_time = estimate_read_time(article)
    order = flat_page_order(chapters)
    try:
        idx = order.index(filename)
    except ValueError:
        idx = -1
    prev_file = order[idx - 1] if idx > 0 else None
    next_file = order[idx + 1] if 0 <= idx < len(order) - 1 else None

    pn = []
    pn.append(f'<a href="{prev_file}"><span class="pn-label">&larr; Previous</span>{label_for(prev_file, chapters)}</a>' if prev_file else '<span></span>')
    pn.append(f'<a href="{next_file}" class="pn-next"><span class="pn-label">Next &rarr;</span>{label_for(next_file, chapters)}</a>' if next_file else '<a href="index.html" class="pn-next"><span class="pn-label">Next &rarr;</span>Roadmap</a>')
    prev_next = '\n        '.join(pn)

    related = []
    if ch:
        for p in ch['pages']:
            if p['file'] != filename and len(related) < 5:
                related.append((p['file'], p['label']))
    related_html = '\n'.join(f'<a href="{f}">{t}<svg class="icon icon-sm" viewBox="0 0 24 24"><polyline points="9 6 15 12 9 18"/></svg></a>' for f, t in related)

    head = HEAD_TOP.format(title=title, desc=desc, slug=slug, filename=filename, css_v=CSS_V,
                            body_class=body_class, topnav=topnav, sidebar=sidebar)

    book_card = build_book_card(slug)

    body = f'''      {breadcrumb}

      <div class="page-header-banner">
        <header class="page-head">
          <h1>{h1}</h1>
        </header>
        <div class="meta-row">
          <span class="tag-pill {difficulty}">{difficulty}</span>
          <span class="read-time">{read_time}</span>
        </div>
      </div>

      {prereqs}

      {article}

      <label class="mark-complete-row">
        <input type="checkbox" class="mark-complete-checkbox" data-page-id="{slug}:{filename}" onchange="toggleComplete(this)" />
        <span>Mark this lesson complete</span>
      </label>

      <div class="prev-next">
        {prev_next}
      </div>
    </main>

    <aside class="right-rail">
{book_card}      <div class="rail-card">
        <h4>Related Chapters</h4>
        <div class="related-list">
          {related_html}
        </div>
      </div>
      <div class="rail-card was-helpful-card">
        <span>Was this helpful?</span>
        <button title="Yes">&#128077;</button>
        <button title="No">&#128078;</button>
      </div>
    </aside>
  </div>

{MOBILE_TABBAR}
{SCRIPT_TAIL}
  function toggleComplete(checkbox) {{
    var pageId = checkbox.getAttribute('data-page-id');
    var progress = {{}};
    try {{ progress = JSON.parse(localStorage.getItem('assertTrueProgress') || '{{}}'); }} catch (e) {{}}
    if (checkbox.checked) {{ progress[pageId] = true; }} else {{ delete progress[pageId]; }}
    try {{ localStorage.setItem('assertTrueProgress', JSON.stringify(progress)); }} catch (e) {{}}
  }}
  (function() {{
    var progress = {{}};
    try {{ progress = JSON.parse(localStorage.getItem('assertTrueProgress') || '{{}}'); }} catch (e) {{}}
    var cb = document.querySelector('.mark-complete-checkbox');
    if (cb && progress[cb.getAttribute('data-page-id')]) cb.checked = true;
  }})();
  (function() {{
    var activeLink = document.querySelector('.doc-sidebar a.active');
    if (activeLink) {{ activeLink.scrollIntoView({{ block: 'center' }}); }}
  }})();
  document.addEventListener('click', function(e) {{
    if (e.target.closest('.sidebar-link') && window.matchMedia('(max-width: 860px)').matches) {{ closeSidebar(); }}
  }});
  </script>

    <div class="install-banner" id="install-banner">
      <img src="../icons/icon-192.png" alt="" class="install-banner-icon" />
      <div class="install-banner-text">
        <strong>Install AssertTrueIO</strong>
        <span>Add to your home screen for quick, offline access</span>
      </div>
      <button type="button" class="install-banner-btn" onclick="handleInstallClick()">Install</button>
      <button type="button" class="install-banner-dismiss" onclick="dismissInstallBanner()" aria-label="Dismiss">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="width:16px;height:16px;"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
</body>
</html>
'''
    return head + body

def build_roadmap(slug, config, chapters, extracted_dir):
    topnav = build_topnav(slug)
    sidebar = build_sidebar('index.html', chapters)
    body_class = f' class="{config["theme_class"]}"' if config['theme_class'] else ''
    total_lessons = sum(len(ch['pages']) for ch in chapters)

    head = HEAD_TOP.format(title=f'{config["hero_title"]} — AssertTrueIO', desc=config['hero_lede'],
                            slug=slug, filename='index.html', css_v=CSS_V,
                            body_class=body_class, topnav=topnav, sidebar=sidebar)
    book_card = build_book_card(slug)
    head = head.replace('<main class="doc-main">\n', '<main class="doc-main" style="max-width:900px;">\n')

    hero = f'''      <div class="page-header-banner">
        <div class="hub-hero" id="top">
          <h1>{config["hero_title"]}</h1>
          <p class="lede">{config["hero_lede"]}</p>
        </div>
      </div>

      <div class="hub-stat-cards">
        <div class="stat-card"><div class="stat-num">{len(chapters)}</div><div class="stat-label">Chapters</div></div>
        <div class="stat-card"><div class="stat-num">{total_lessons}</div><div class="stat-label">Lessons Total</div></div>
        <div class="stat-card"><div class="stat-num">Hands-On</div><div class="stat-label">Practical Examples</div></div>
        <div class="stat-card"><div class="stat-num">Production</div><div class="stat-label">Ready</div></div>
      </div>

      <div class="progress-summary" id="progress-summary" style="display:none;">
        <div class="progress-bar-track"><div class="progress-bar-fill" id="progress-bar-fill"></div></div>
        <span id="progress-summary-text"></span>
      </div>
'''
    pages_js = ','.join(f"'{slug}:{p['file']}'" for ch in chapters for p in ch['pages'])
    progress_script = f'''      <script>
      (function() {{
        var pages = [{pages_js}];
        var progress = {{}};
        try {{ progress = JSON.parse(localStorage.getItem('assertTrueProgress') || '{{}}'); }} catch (e) {{}}
        var done = pages.filter(function(p) {{ return progress[p]; }}).length;
        if (done > 0) {{
          var pct = Math.round(done / pages.length * 100);
          document.getElementById('progress-bar-fill').style.width = pct + '%';
          document.getElementById('progress-summary-text').textContent = done + ' of ' + pages.length + ' lessons complete';
          document.getElementById('progress-summary').style.display = 'block';
        }}
        document.querySelectorAll('.chapter-card [data-progress-id]').forEach(function(link) {{
          if (progress[link.getAttribute('data-progress-id')]) {{ link.classList.add('lesson-done'); }}
        }});
      }})();
      function expandAllChapters() {{ document.querySelectorAll('.chapter-card').forEach(function(c) {{ if (c.tagName === 'DETAILS') c.open = true; }}); }}
      function collapseAllChapters() {{ document.querySelectorAll('.chapter-card').forEach(function(c) {{ if (c.tagName === 'DETAILS') c.open = false; }}); }}
      </script>

      <h2 id="chapters-heading" style="font-size:1.1rem;margin-bottom:0.9rem;">Chapters</h2>
      <div class="roadmap-toolbar">
        <button type="button" onclick="expandAllChapters()">Expand all</button>
        <button type="button" onclick="collapseAllChapters()">Collapse all</button>
      </div>
      <div class="chapter-list">
'''

    def get_desc(fname):
        path = os.path.join(extracted_dir, fname)
        if not os.path.exists(path):
            return ''
        raw = open(path, encoding='utf-8').read()
        m = re.search(r'<meta name="description" content="(.*?)" />', raw, re.S)
        return m.group(1) if m else ''

    def truncate(text, limit):
        return (text[:limit].rstrip() + '\u2026') if len(text) > limit else text

    cards = []
    for i, ch in enumerate(chapters):
        num = f"{ch['num']:02d}"
        hub_file = ch['pages'][0]['file']
        hub_desc = truncate(get_desc(hub_file), 95)
        if len(ch['pages']) == 1:
            cards.append(f'<a href="{hub_file}" class="chapter-card chapter-card-standalone" data-progress-id="{slug}:{hub_file}">\n'
                          f'  <span class="chapter-num">{num}</span>\n'
                          f'  <span class="chapter-card-info">\n'
                          f'    <span class="chapter-title">{ch["title"]}</span>\n'
                          f'    <span class="chapter-sub">{hub_desc}</span>\n'
                          f'  </span>\n  <span class="read-btn">Read</span>\n</a>')
        else:
            open_attr = ' open' if i == 0 else ''
            parts = [f'<details class="chapter-card"{open_attr}>\n'
                     f'  <summary class="chapter-card-header">\n'
                     f'    <span class="chapter-num">{num}</span>\n'
                     f'    <span class="chapter-card-info">\n'
                     f'      <span class="chapter-title">{ch["title"]}</span>\n'
                     f'      <span class="chapter-sub">{hub_desc}</span>\n'
                     f'    </span>\n'
                     f'    <span class="chapter-card-meta">\n'
                     f'      <a href="{hub_file}" class="read-btn" onclick="event.stopPropagation()">Read</a>\n'
                     f'      <span class="chapter-chev">&#9662;</span>\n'
                     f'    </span>\n  </summary>\n  <div class="chapter-card-subs">\n'
                     f'    <a href="{hub_file}" class="sub-lesson-row sub-lesson-hub-link" data-progress-id="{slug}:{hub_file}">\n'
                     f'      <span class="sub-lesson-dot"></span>\n'
                     f'      <span class="sub-lesson-info">\n'
                     f'        <span class="sub-lesson-title">Chapter Overview</span>\n'
                     f'      </span>\n      <span class="read-btn-sm">Read</span>\n    </a>']
            for p in ch['pages'][1:]:
                desc = truncate(get_desc(p['file']), 90)
                parts.append(f'<a href="{p["file"]}" class="sub-lesson-row" data-progress-id="{slug}:{p["file"]}">\n'
                              f'      <span class="sub-lesson-dot"></span>\n'
                              f'      <span class="sub-lesson-info">\n'
                              f'        <span class="sub-lesson-title">{p["label"]}</span>\n'
                              f'        <span class="sub-lesson-desc">{desc}</span>\n'
                              f'      </span>\n      <span class="read-btn-sm">Read</span>\n    </a>')
            parts.append('\n  </div>\n</details>')
            cards.append(''.join(parts))

    body = hero + progress_script + '\n'.join(cards) + f'''
      </div>
    </main>
    <aside class="right-rail">
{book_card}      <div class="rail-card">
        <h4>On this page</h4>
        <div class="related-list">
          <a href="#top">Overview<svg class="icon icon-sm" viewBox="0 0 24 24"><polyline points="9 6 15 12 9 18"/></svg></a>
          <a href="#chapters-heading">Chapters<svg class="icon icon-sm" viewBox="0 0 24 24"><polyline points="9 6 15 12 9 18"/></svg></a>
        </div>
      </div>
    </aside>
  </div>

{MOBILE_TABBAR}
{SCRIPT_TAIL}
  </script>

    <div class="install-banner" id="install-banner">
      <img src="../icons/icon-192.png" alt="" class="install-banner-icon" />
      <div class="install-banner-text">
        <strong>Install AssertTrueIO</strong>
        <span>Add to your home screen for quick, offline access</span>
      </div>
      <button type="button" class="install-banner-btn" onclick="handleInstallClick()">Install</button>
      <button type="button" class="install-banner-dismiss" onclick="dismissInstallBanner()" aria-label="Dismiss">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="width:16px;height:16px;"><path d="M18 6 6 18M6 6l12 12"/></svg>
      </button>
    </div>
</body>
</html>
'''
    return head + body

def run(slug):
    config = TRACK_CONFIG[slug]
    extracted_dir = os.path.join(EXTRACTED, slug)
    manifest = json.load(open(os.path.join(extracted_dir, '_manifest.json')))
    chapters = manifest['chapters']
    out_dir = os.path.join(SITE, slug)

    count = 0
    for ch in chapters:
        for p in ch['pages']:
            fname = p['file']
            raw_path = os.path.join(extracted_dir, fname)
            raw = open(raw_path, encoding='utf-8').read()
            wrapped = build_page(slug, config, fname, raw, chapters)
            open(os.path.join(out_dir, fname), 'w', encoding='utf-8').write(wrapped)
            count += 1

    roadmap = build_roadmap(slug, config, chapters, extracted_dir)
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(roadmap)
    print(f'{slug}: regenerated {count} pages + roadmap ({len(chapters)} chapters)')

if __name__ == '__main__':
    run(sys.argv[1])
