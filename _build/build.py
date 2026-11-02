#!/usr/bin/env python3
"""Builds the static Viavo site (VIA-472) into the repository root.

  python3 -I _build/build.py            # base URL from VIAVO_BASE_URL or the default below

Sources: _build/content/<lang>.json (page copy), _build/site.css, _build/site.js,
_build/legal-src/** (the legal texts, copied verbatim into the new layout), assets/** (images, fonts, badges).
Outputs: index.html, <lang>/index.html, press/index.html, privacy|terms|messengers[/ru]|support/index.html.
ops/ (the internal report, VIA-399) is never touched. Root files for search (sitemap, robots, llms.txt) belong
to VIA-473; every page carries a <!-- seo:head --> marker for their additions.
"""
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qr as qrcode  # noqa: E402  _build/qr.py

# One place for the address: canonical, hreflang and og:url must be absolute, so a new domain is this one line.
BASE_URL = os.environ.get('VIAVO_BASE_URL', 'https://hokeroid.github.io/viavo-site').rstrip('/')
APP_ID = '6761760437'
PT = '127870899'  # App Store Connect provider token (providerId) for campaign links, from VIA-474; clicks show in ASC → Analytics → Campaigns

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / '_build'

# code, url folder, hreflang, native name, English name, direction, App Store country ('' = the visitor's own store),
# og locale, badge file. Serbian pages are written in Latin script. Viavo is not in the Russian or Chinese stores.
LANGS = [
    ('ar', 'ar', 'ar', 'العربية', 'Arabic', 'rtl', 'sa', 'ar_AR'),
    ('zh-hans', 'zh-hans', 'zh-Hans', '简体中文', 'Chinese Simplified', 'ltr', '', 'zh_CN'),
    ('zh-hant', 'zh-hant', 'zh-Hant', '繁體中文', 'Chinese Traditional', 'ltr', 'tw', 'zh_TW'),
    ('hr', 'hr', 'hr', 'Hrvatski', 'Croatian', 'ltr', 'hr', 'hr_HR'),
    ('cs', 'cs', 'cs', 'Čeština', 'Czech', 'ltr', 'cz', 'cs_CZ'),
    ('nl', 'nl', 'nl', 'Nederlands', 'Dutch', 'ltr', 'nl', 'nl_NL'),
    ('en', '', 'en', 'English', 'English', 'ltr', '', 'en_US'),
    ('fr', 'fr', 'fr', 'Français', 'French', 'ltr', 'fr', 'fr_FR'),
    ('de', 'de', 'de', 'Deutsch', 'German', 'ltr', 'de', 'de_DE'),
    ('el', 'el', 'el', 'Ελληνικά', 'Greek', 'ltr', 'gr', 'el_GR'),
    ('he', 'he', 'he', 'עברית', 'Hebrew', 'rtl', 'il', 'he_IL'),
    ('hi', 'hi', 'hi', 'हिन्दी', 'Hindi', 'ltr', 'in', 'hi_IN'),
    ('hu', 'hu', 'hu', 'Magyar', 'Hungarian', 'ltr', 'hu', 'hu_HU'),
    ('id', 'id', 'id', 'Bahasa Indonesia', 'Indonesian', 'ltr', 'id', 'id_ID'),
    ('it', 'it', 'it', 'Italiano', 'Italian', 'ltr', 'it', 'it_IT'),
    ('ja', 'ja', 'ja', '日本語', 'Japanese', 'ltr', 'jp', 'ja_JP'),
    ('ko', 'ko', 'ko', '한국어', 'Korean', 'ltr', 'kr', 'ko_KR'),
    ('pl', 'pl', 'pl', 'Polski', 'Polish', 'ltr', 'pl', 'pl_PL'),
    ('pt', 'pt', 'pt', 'Português', 'Portuguese', 'ltr', 'br', 'pt_BR'),
    ('ro', 'ro', 'ro', 'Română', 'Romanian', 'ltr', 'ro', 'ro_RO'),
    ('ru', 'ru', 'ru', 'Русский', 'Russian', 'ltr', '', 'ru_RU'),
    ('sr', 'sr', 'sr-Latn', 'Srpski', 'Serbian', 'ltr', 'rs', 'sr_RS'),
    ('es', 'es', 'es', 'Español', 'Spanish', 'ltr', 'es', 'es_ES'),
    ('sv', 'sv', 'sv', 'Svenska', 'Swedish', 'ltr', 'se', 'sv_SE'),
    ('th', 'th', 'th', 'ไทย', 'Thai', 'ltr', 'th', 'th_TH'),
    ('tr', 'tr', 'tr', 'Türkçe', 'Turkish', 'ltr', 'tr', 'tr_TR'),
    ('uk', 'uk', 'uk', 'Українська', 'Ukrainian', 'ltr', 'ua', 'uk_UA'),
    ('vi', 'vi', 'vi', 'Tiếng Việt', 'Vietnamese', 'ltr', 'vn', 'vi_VN'),
]
L = {x[0]: dict(zip(('code', 'folder', 'hreflang', 'native', 'english', 'dir', 'cc', 'og'), x)) for x in LANGS}
GAP = ['pl', 'cs', 'ro', 'el', 'hu', 'hr', 'sr', 'uk']  # Siri does not speak these (apple.com feature availability, VIA-466)
# Pages that open with the Siri band (their language has no Siri, or the global English page). Elsewhere Siri speaks the
# reader's language, so a general, smaller band about the eight sits further down, without a screen.
STORY = set(GAP) | {'en'}
LATIN_HEADLINES = {'en', 'hr', 'cs', 'nl', 'fr', 'de', 'hu', 'id', 'it', 'pl', 'pt', 'ro', 'sr', 'es', 'sv', 'tr', 'vi'}

APPS = [
    ('nav', ['Apple Maps', 'Google Maps', 'Waze']),
    ('music', ['Apple Music', 'Spotify', 'YouTube Music', 'Amazon Music', 'Deezer', 'Apple Podcasts']),
    ('radio', ['Simple Radio', 'TuneIn', 'iHeartRadio']),
    ('msg', ['WhatsApp', 'SMS', 'Telegram', 'Slack']),
    ('home', ['HomeKit', 'Calendar', 'Reminders']),
]
APP_ICON = {'Apple Maps': 'apple_maps', 'Google Maps': 'google_maps', 'Waze': 'waze', 'Apple Music': 'apple_music',
            'Spotify': 'spotify', 'YouTube Music': 'youtube_music', 'Amazon Music': 'amazon_music', 'Deezer': 'deezer',
            'Apple Podcasts': 'apple_podcasts', 'Simple Radio': 'simple_radio', 'TuneIn': 'tunein', 'iHeartRadio': 'iheartradio',
            'WhatsApp': 'whatsapp', 'Telegram': 'telegram', 'Slack': 'slack', 'HomeKit': 'home', 'Calendar': 'calendar',
            'Reminders': 'reminders'}
GROUP_ICONS = ['road', 'music', 'people', 'plans', 'more', 'carplay']
CONVO = [('route', 'road'), ('places', 'pin'), ('music', 'music'), ('messages', 'people')]

SYMBOLS = '''<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="i-road" viewBox="0 0 24 24"><path d="M12 3.5 18.5 19.5 12 16 5.5 19.5Z"/></symbol>
<symbol id="i-music" viewBox="0 0 24 24"><path d="M9 17.5V5.5l10-2v12"/><circle cx="6.5" cy="17.5" r="2.5"/><circle cx="16.5" cy="15.5" r="2.5"/></symbol>
<symbol id="i-people" viewBox="0 0 24 24"><path d="M5 4.5h14a1.5 1.5 0 0 1 1.5 1.5v9a1.5 1.5 0 0 1-1.5 1.5H10l-4.5 3.5v-3.5H5A1.5 1.5 0 0 1 3.5 15V6A1.5 1.5 0 0 1 5 4.5Z"/></symbol>
<symbol id="i-plans" viewBox="0 0 24 24"><rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/></symbol>
<symbol id="i-more" viewBox="0 0 24 24"><rect x="4" y="4" width="6.5" height="6.5" rx="1.8"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.8"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.8"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.8"/></symbol>
<symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/></symbol>
<symbol id="i-carplay" viewBox="0 0 24 24"><rect x="3" y="4.5" width="18" height="12.5" rx="2.5"/><circle cx="12" cy="10.75" r="2.75"/><path d="M9 20h6"/></symbol>
<symbol id="i-down" viewBox="0 0 24 24"><path d="M12 4v11M7 10.5l5 5 5-5M5 19.5h14"/></symbol>
</defs></svg>'''
MARK = ('<svg class="mark" viewBox="6 3 92 92" aria-hidden="true"><g><path d="M34 27 L62 85 L90 27" opacity=".2"/>'
        '<path d="M24 19 L52 77 L80 19" opacity=".45"/><path d="M14 11 L42 69 L70 11"/></g></svg>')
BRAND = re.compile(r'((?:[֐-׿؀-ۿ]+-)?(?:Viavo Plus|Viavo|Siri|CarPlay|App Store|ChatGPT|Gemini|iPhone|AI))')

e = html.escape


def brandsafe(s):
    """Escapes text and keeps Latin brand words on one line, isolated from the surrounding direction (RTL pages)."""
    return BRAND.sub(r'<span class="nw">\1</span>', e(s))


def rel(depth):
    return '../' * depth


def store_url(lang, campaign=None):
    cc = L[lang]['cc']
    q = f'ct={campaign or "site-" + lang}' + (f'&pt={PT}&mt=8' if PT else '')
    return f'https://apps.apple.com/{cc + "/" if cc else ""}app/viavo/id{APP_ID}?{q}'


def page_url(lang, path=''):
    f = L[lang]['folder']
    return f'{BASE_URL}/{f + "/" if f else ""}{path}'


def exists(p):
    return (ROOT / p).exists()


def picture(base, widths, sizes, alt, r, w, h, eager=False, cls='', hidden=False):
    srcs = lambda ext: ', '.join(f'{r}assets/img/{base}-{x}.{ext} {x}w' for x in widths)
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return (f'<picture{" hidden" if hidden else ""}{f" class={cls}" if cls else ""}>'
            f'<source type="image/avif" srcset="{srcs("avif")}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{srcs("webp")}" sizes="{sizes}">'
            f'<img src="{r}assets/img/{base}-{widths[0]}.webp" width="{w}" height="{h}" alt="{e(alt)}" {load} decoding="async"></picture>')


def css(r):
    fonts = (ROOT / 'assets/fonts/fonts.css').read_text()
    fonts = re.sub(r'url\(([^)]+\.woff2)\)', lambda m: f'url({r}assets/fonts/{m.group(1)})', fonts)
    body = (SRC / 'site.css').read_text()
    body = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
    body = re.sub(r'\s*\n\s*', '', body)
    return re.sub(r'/\*.*?\*/\s*', '', fonts).replace('\n', '') + body


JS_VERSION = None


def head(lang, title, desc, canonical, r, alternates='', og_image=None, og_title=None):
    li = L[lang]
    preload = ''
    if lang in LATIN_HEADLINES:
        preload = (f'<link rel="preload" href="{r}assets/fonts/space-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>'
                   f'<link rel="preload" href="{r}assets/fonts/manrope-latin.woff2" as="font" type="font/woff2" crossorigin>')
    og = og_image or f'{BASE_URL}/assets/og/{lang}.jpg'
    return f'''<!doctype html>
<html lang="{li["hreflang"]}" dir="{li["dir"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
{alternates}<meta property="og:type" content="website">
<meta property="og:site_name" content="Viavo">
<meta property="og:title" content="{e(og_title or title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{li["og"]}">
<meta name="twitter:card" content="summary_large_image">
<meta name="apple-itunes-app" content="app-id={APP_ID}">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0B0C10">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#F4F3EF">
<link rel="icon" href="{r}assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="{r}assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{r}assets/apple-touch-icon.png">
{preload}<style>{css(r)}</style>
<script src="{r}assets/site.js?v={JS_VERSION}" defer></script>
<!-- seo:head -->
</head>
'''


def header(T, lang, r, available, here=None, current_path=''):
    items = []
    for code, *_ in LANGS:
        if code not in available:
            continue
        cur = ' aria-current="true"' if code == lang else ''
        href = r + (L[code]['folder'] + '/' if L[code]['folder'] else '') + current_path
        items.append(f'<li><a href="{href}" lang="{L[code]["hreflang"]}" hreflang="{L[code]["hreflang"]}"{cur}>{L[code]["native"]}</a></li>')
    home = r + (L[lang]['folder'] + '/' if L[lang]['folder'] and lang in available else '')
    press_cur = ' aria-current="page"' if here == 'press' else ''
    return f'''<a class="skip" href="#main">{e(T["skip"])}</a>
<header class="hdr"><div class="wrap">
<a class="logo" href="{home}" aria-label="Viavo">{MARK}<span>viavo</span></a>
<nav class="nav" aria-label="Viavo"><a href="{home}#features">{e(T["nFeatures"])}</a><a href="{home}#languages">{e(T["nLanguages"])}</a><a href="{r}press/"{press_cur}>{e(T["nPress"])}</a></nav>
<div class="hdr-r">
<details class="lang"><summary aria-label="{e(T["nLangMenu"])}"><span>{L[lang]["native"]}</span><span class="chev"></span></summary><ul>{"".join(items)}</ul></details>
<a class="btn-store" href="{e(store_url(lang))}">App Store</a>
</div></div></header>
'''


def badge(lang, r, campaign=None, cls='badge'):
    b = lang if exists(f'assets/badges/{lang}.svg') else 'en'
    return f'<a class="{cls}" href="{e(store_url(lang, campaign))}"><img src="{r}assets/badges/{b}.svg" alt="{{alt}}" width="160" height="54"></a>'


def qr(lang, T, r):
    if not exists(f'assets/qr/{lang}.svg'):
        return ''
    return f'<div class="qr"><img src="{r}assets/qr/{lang}.svg" alt="" width="64" height="64" loading="lazy"><span>{e(T["scan"])}</span></div>'


def footer(T, lang, r, available):
    home = r + (L[lang]['folder'] + '/' if L[lang]['folder'] and lang in available else '')
    ru = lang in ('ru', 'uk')
    legal = lambda p: f'{r}{p}/' + ('ru/' if ru and p != 'support' else '')
    langs = ''.join(f'<li><a href="{r}{L[c]["folder"] + "/" if L[c]["folder"] else ""}" lang="{L[c]["hreflang"]}">{L[c]["native"]}</a></li>'
                    for c, *_ in LANGS if c in available)
    return f'''<footer class="wrap grid ftr">
<div class="brand"><a class="logo" href="{home}" aria-label="Viavo">{MARK}<span>viavo</span></a><small>{brandsafe(T["eyebrow"])}</small>{badge(lang, r, "site-" + lang + "-footer").replace("{alt}", e(T["badgeAlt"]))}</div>
<nav aria-label="{e(T["fPrivacy"])}"><a href="{legal("privacy")}">{e(T["fPrivacy"])}</a><a href="{legal("terms")}">{e(T["fTerms"])}</a><a href="{legal("messengers")}">{e(T["fMessengers"])}</a><a href="{r}support/">{e(T["fSupport"])}</a><a href="{r}press/">{e(T["fPress"])}</a></nav>
<ul class="fl">{langs}</ul>
<div class="bot"><span>© 2026 Viavo</span><span>{brandsafe(T["tm"])}</span></div>
</footer>
'''


def mbar(T, lang, r):
    b = badge(lang, r, f'site-{lang}-bar').replace('{alt}', e(T['badgeAlt']))
    return (f'<div class="mbar" aria-hidden="false"><img class="ai" src="{r}assets/icon-120.png" alt="" width="40" height="40" loading="lazy">'
            f'<span class="t">Viavo<br><small style="font-weight:500;color:var(--cap)">{brandsafe(T["eyebrow"])}</small></span>{b}</div>')


def phone_lang(lang):
    return lang if exists(f'assets/img/phone-{lang}-route-660.webp') else 'en'


def hero_screen(lang):
    for k in (f'carplay-{lang}-idle', f'carplay-{lang}-night-speaking', f'carplay-{lang}-listening'):
        if exists(f'assets/img/{k}-1080.webp'):
            return k
    return 'carplay-en-idle'


# Czech and Slovak typesetting keeps one-letter words (v, k, s, z, a, i, o, u) with the next word.
NBSP_LANGS = {'cs'}


def typeset(lang, page):
    if lang not in NBSP_LANGS:
        return page
    headpart, body = page.split('</head>', 1)
    fix = lambda m: re.sub(r'(?<=[\s(>])([vkszaiouVKSZAIOU]) ', '\\1\u00a0', m.group(0))
    return headpart + '</head>' + re.sub(r'>[^<]+<', fix, body)


def home(lang, T, available):
    depth = 1 if L[lang]['folder'] else 0
    r = rel(depth)
    alts = ''.join(f'<link rel="alternate" hreflang="{L[c]["hreflang"]}" href="{page_url(c)}">\n' for c, *_ in LANGS if c in available)
    alts += f'<link rel="alternate" hreflang="x-default" href="{page_url("en")}">\n'
    m = T['meta']
    out = [head(lang, m['title'], m['description'], page_url(lang), r, alts, og_title=m['ogTitle']), '<body>', SYMBOLS,
           header(T, lang, r, available)]
    alt_badge = e(T['badgeAlt'])
    q = T['qo'], T['qc']

    # hero
    out.append(f'''<main id="main">
<section class="hero" id="top"><div class="wrap">
<p class="eyebrow">{brandsafe(T["eyebrow"])}</p>
<h1 class="h1"><span>{brandsafe(T["h1a"])}</span><span class="b">{brandsafe(T["h1b"])}</span></h1>
<p class="lead">{brandsafe(T["sub"])}</p>
<div class="cta-row">{badge(lang, r, f"site-{lang}-hero").replace("{alt}", alt_badge)}{qr(lang, T, r)}</div>
<div class="hero-shot{"" if lang in STORY else " solo"}"><div class="glow"></div><div class="car"><div class="scr">{picture(hero_screen(lang), (1080, 1920), "(max-width:760px) 230vw, 1060px", T["heroAlt"], r, 1920, 1080, eager=True)}</div></div></div>
</div></section>
''')

    # Siri band: start with the page's own language when Siri lacks it
    order = ([lang] + [g for g in GAP if g != lang]) if lang in GAP else GAP
    words = [T['bandWords'][g] for g in order]
    shots = ''.join(picture(f'carplay-{g}-listening', (1080, 1920), '(max-width:760px) 230vw, 760px',
                            f'Viavo, CarPlay, {L[g]["english"]}', r, 1920, 1080, hidden=i > 0) for i, g in enumerate(order))
    names = T.get('langNames') or {}
    rows = ''.join(f'<div class="{"on" if i == 0 else ""}"><b lang="{L[g]["hreflang"]}">{L[g]["native"]}</b><span>{e(names.get(g, L[g]["english"]))}</span></div>'
                   for i, g in enumerate(order))
    general = ''
    if lang in STORY:
        out.append(f'''<section class="band" id="story" data-words='{e(json.dumps(words, ensure_ascii=False))}'><div class="wrap grid">
<div class="car"><div class="scr">{shots}</div></div>
<div class="txt"><h2 class="h2">{brandsafe(T["bandPre"])}<span class="w">{e(words[0])}</span>{e(T["bandPost"])} <span class="t">{brandsafe(T["bandTail"])}</span></h2>
<p class="lead">{brandsafe(T["bandSub"])}</p>
<div class="gap">{rows}</div></div>
</div></section>
''')
    else:
        plain = rows.replace('<div class="on">', '<div>')
        general = (f'<section class="sec band-g" id="story"><div class="wrap"><h2 class="h2">{brandsafe(T["bandSub"])}</h2>'
                   f'<div class="gap">{plain}</div></div></section>\n')

    # it does it
    pl = phone_lang(lang)
    exs = ''.join(f'''<button class="ex" type="button" aria-pressed="{"true" if i == 0 else "false"}"><q>{e(T["examples"][i])}</q>
<span class="rep"><span class="who">Viavo</span><span class="said">{brandsafe(T["replies"][i])}</span>
<span class="done"><svg aria-hidden="true"><use href="#i-{icon}"/></svg><span>{brandsafe(T["done"][i])}</span></span></span></button>''' for i, (scr, icon) in enumerate(CONVO))
    phones = ''.join(picture(f'phone-{pl}-{scr}', (660,), '300px', T['examples'][i], r, 1320, 2868, hidden=i > 0) for i, (scr, _) in enumerate(CONVO))
    out.append(f'''<section class="sec say" id="say" style="--q:'{q[0]}' '{q[1]}'"><div class="wrap grid">
<div class="txt"><h2 class="h2">{brandsafe(T["say"])}</h2><p class="lead">{brandsafe(T["sayLead"])}</p><div class="convo">{exs}</div></div>
<div class="ph"><div class="phone"><div class="scr">{phones}<div class="island"></div></div></div></div>
</div></section>
''')

    # features
    cards = ''
    for i, (title, points, eg) in enumerate(T['groups']):
        egt = eg if GROUP_ICONS[i] == 'carplay' else q[0] + eg + q[1]
        lis = ''.join(f'<li>{brandsafe(p)}</li>' for p in points)
        cards += (f'<div class="card"><div class="ico"><svg aria-hidden="true"><use href="#i-{GROUP_ICONS[i]}"/></svg></div>'
                  f'<div class="in"><h3>{brandsafe(title)}</h3><ul>{lis}</ul><p class="eg">{brandsafe(egt)}</p></div></div>')
    out.append(f'<section class="sec" id="features"><div class="wrap grid cards"><h2 class="h2">{brandsafe(T["can"])}</h2>{cards}</div></section>\n')
    out.append(general)

    # works with
    chips = ''.join(f'<button type="button" data-cat="{c}" aria-pressed="{"true" if c == "all" else "false"}">{e(T["cats"][c])}</button>'
                    for c in ['all'] + [a for a, _ in APPS])
    tiles = ''
    for cat, names_ in APPS:
        for n in names_:
            src = f'{r}assets/img/app-{APP_ICON[n]}-112.webp' if n in APP_ICON else f'{r}assets/img/app-sms.svg'
            tiles += f'<li data-cat="{cat}"><img src="{src}" alt="" width="56" height="56" loading="lazy">{e(T["appNames"].get(n, n))}</li>'
    out.append(f'''<section class="sec works" id="works"><div class="wrap grid">
<div class="txt"><h2 class="h2">{brandsafe(T["works"])}</h2><p class="lead">{brandsafe(T["worksSub"])}</p></div>
<div class="apps"><div class="chips">{chips}</div><ul class="tiles">{tiles}</ul></div>
</div></section>
''')

    # languages
    cells = ''
    for c, *_ in LANGS:
        dot = '<span class="dot" aria-hidden="true"></span>' if c in GAP else ''
        tag = 'a' if c in available else 'div'
        href = f' href="{r}{L[c]["folder"] + "/" if L[c]["folder"] else ""}"' if c in available else ''
        cells += f'<li><{tag}{href} lang="{L[c]["hreflang"]}"><b>{L[c]["native"]}</b><span lang="{L[lang]["hreflang"]}">{e(names.get(c, L[c]["english"]))}</span>{dot}</{tag}></li>'
    out.append(f'''<section class="sec langs" id="languages"><div class="wrap grid">
<div class="txt"><h2 class="h2">{brandsafe(T["langsTitle"])}</h2><p class="legend"><span class="dot"></span><span>{brandsafe(T["legend"])}</span></p></div>
<ul class="lgrid">{cells}</ul>
</div></section>
''')

    # steps
    steps = ''.join(f'<div class="step"><span class="n">0{i + 1}</span><h3>{brandsafe(t)}</h3><p>{brandsafe(x)}</p></div>'
                    for i, (t, x) in enumerate(T['stepItems']))
    out.append(f'<section class="sec" id="start"><div class="wrap grid steps"><h2 class="h2">{brandsafe(T["steps"])}</h2>{steps}</div></section>\n')

    # faq
    ru = lang in ('ru', 'uk')
    qas = ''
    for i, item in enumerate(T['faqItems']):
        qq, aa = item[0], item[1]
        links = ''
        if i == len(T['faqItems']) - 1:
            links = (f'<div class="links"><a class="ul" href="{r}privacy/{"ru/" if ru else ""}">{e(T["lPrivacy"])}</a>'
                     f'<a class="ul" href="{r}messengers/{"ru/" if ru else ""}">{e(T["lMessages"])}</a></div>')
        qas += f'<details{" open" if i == 0 else ""}><summary><span>{brandsafe(qq)}</span><span class="pm" aria-hidden="true"></span></summary><div class="a"><p>{brandsafe(aa)}</p>{links}</div></details>'
    out.append(f'<section class="sec faq" id="faq"><div class="wrap grid"><h2 class="h2">{brandsafe(T["faq"])}</h2><div class="qa">{qas}</div></div></section>\n')

    # download
    out.append(f'''<section class="dl" id="download"><div class="wrap">
<img class="appicon" src="{r}assets/icon-208.png" alt="" width="104" height="104" loading="lazy">
<h2 class="h2">{brandsafe(T["cta"])}</h2><p class="lead">{brandsafe(T["ctaSub"])}</p>
<div class="cta-row">{badge(lang, r, f"site-{lang}-cta").replace("{alt}", alt_badge)}{qr(lang, T, r)}</div>
</div></section>
</main>
''')
    out.append(footer(T, lang, r, available))
    out.append(mbar(T, lang, r))
    out.append('</body>\n</html>\n')
    return ''.join(out)


def press(T, available):
    lang, r = 'en', '../'
    m = T['meta']
    out = [head(lang, m['pressTitle'], m['pressDescription'], f'{BASE_URL}/press/', r), '<body>', SYMBOLS,
           header(T, lang, r, {'en'}, here='press')]
    p = json.loads((SRC / 'content/press.json').read_text())
    facts = ''.join(f'<div class="fact"><span>{e(k)}</span><b>{brandsafe(v)}</b></div>' for k, v in p['facts'])
    tile = lambda href, img, label, cls: f'<a href="{href}" download><span class="tile {cls}">{img}</span><span>↓ {e(label)}</span></a>'
    icon = f'<img src="{r}assets/icon-208.png" alt="" width="76" height="76" style="border-radius:17px" loading="lazy">'
    mark = f'<img src="{r}assets/press/viavo-mark.svg" alt="" width="64" height="64" loading="lazy">'
    wm_d = f'<img src="{r}assets/press/viavo-wordmark-light.png" alt="" width="110" height="59" loading="lazy">'
    wm_l = f'<img src="{r}assets/press/viavo-wordmark-dark.png" alt="" width="110" height="59" loading="lazy">'
    assets = (f'<div class="asset"><div class="t"><b>App icon</b><span>PNG · 1024 px</span></div><div class="tw">'
              f'{tile(r + "assets/press/viavo-app-icon-1024.png", icon, "On dark", "dk")}{tile(r + "assets/press/viavo-app-icon-1024.png", icon, "On light", "lt")}</div></div>'
              f'<div class="asset"><div class="t"><b>Mark</b><span>SVG</span></div><div class="tw">'
              f'{tile(r + "assets/press/viavo-mark.svg", mark, "On dark", "dk")}{tile(r + "assets/press/viavo-mark.svg", mark, "On light", "lt")}</div></div>'
              f'<div class="asset"><div class="t"><b>Wordmark</b><span>PNG</span></div><div class="tw">'
              f'{tile(r + "assets/press/viavo-wordmark-light.png", wm_d, "On dark", "dk")}{tile(r + "assets/press/viavo-wordmark-dark.png", wm_l, "On light", "lt")}</div></div>')
    cps = ''.join(f'<div class="shot cp"><a class="im" href="{r}assets/press/{f}.png" download>{picture(f, (1080,), "(max-width:760px) 100vw, 384px", label, r, 1920, 1080)}</a>'
                  f'<div class="row"><span>{e(label)}</span><span>PNG</span></div></div>' for f, label in p['carplay'])
    ips = ''.join(f'<div class="shot ip"><a class="im" href="{r}assets/press/{f}.png" download>{picture(f, (660,), "(max-width:760px) 50vw, 180px", label, r, 1320, 2868)}</a>'
                  f'<div class="row"><span>{e(label)}</span></div></div>' for f, label in p['phone'])
    out.append(f'''<main id="main" class="press">
<section class="hero" style="text-align:start"><div class="wrap">
<h1 class="h1">{e(p["title"])}</h1><p class="lead">{brandsafe(p["about"])}</p>
<div class="grid facts"><h2 class="h2" style="margin-top:96px">{e(p["factsTitle"])}</h2>{facts}</div>
</div></section>
<section class="sec"><div class="wrap grid kit"><div class="hd"><h2 class="h2">{e(p["logosTitle"])}</h2><a class="pill" href="{r}assets/press/viavo-press-kit.zip" download><svg width="18" height="18" style="fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round" aria-hidden="true"><use href="#i-down"/></svg>{e(p["zip"])}</a></div>{assets}</div></section>
<section class="sec shots"><div class="wrap grid"><h2 class="h2" style="grid-column:1/-1">{e(p["shotsTitle"])}</h2>
<p class="cap">CarPlay · 1920 × 1080 PNG</p>{cps}<p class="cap">iPhone · 1320 × 2868 PNG</p>{ips}</div></section>
<section class="contact"><div class="wrap"><h2 class="h2">{e(p["contactTitle"])}</h2><p class="lead">{brandsafe(p["contact"])}</p>
<a class="mail" href="{r}support/">{e(p["contactLink"])}</a></div></section>
</main>
''')
    out.append(footer(T, lang, r, available))
    out.append('</body>\n</html>\n')
    return ''.join(out)


def not_found(T, available):
    """GitHub Pages serves /404.html for unknown paths at any depth, so its links are absolute."""
    r = BASE_URL + '/'
    page_head = head('en', 'Page not found · Viavo', T['meta']['description'], BASE_URL + '/', r)
    page_head = page_head.replace(f'<link rel="canonical" href="{BASE_URL}/">\n', '<meta name="robots" content="noindex">\n')
    out = [page_head, '<body>', SYMBOLS,
           header(T, 'en', r, available)]
    out.append(f'''<main id="main"><section class="hero" style="padding-block:120px"><div class="wrap">
<p class="eyebrow">404</p><h1 class="h1"><span>This page took a wrong turn.</span></h1>
<p class="lead">The address may have changed when the site moved. Start from the home page or pick your language below.</p>
<div class="cta-row"><a class="btn-store" style="height:48px;padding:0 24px;font-size:16px" href="{r}">Viavo home</a></div>
</div></section></main>
''')
    out.append(footer(T, 'en', r, available))
    out.append('</body>\n</html>\n')
    return ''.join(out)


LEGAL_UI = {
    'en': {'privacy': 'Privacy Policy', 'terms': 'Terms', 'messengers': 'How Viavo handles your messages', 'support': 'Support',
           'contents': 'Contents', 'other': 'По-русски'},
    'ru': {'privacy': 'Конфиденциальность', 'terms': 'Условия', 'messengers': 'Как Viavo обращается с сообщениями', 'support': 'Поддержка',
           'contents': 'Содержание', 'other': 'English'},
}


def slug(text, i):
    return f's{i}'


def legal(path, T, available):
    """Wraps a legal page's verbatim text in the new layout; only the chrome around it changes."""
    src = (SRC / 'legal-src' / path / 'index.html').read_text()
    lang = 'ru' if path.endswith('/ru') else 'en'
    base = path.split('/')[0]
    depth = path.count('/') + 1
    r = rel(depth)
    title = re.search(r'<title>(.*?)</title>', src, re.S).group(1).strip()
    body = src.split('</header>', 1)[1].split('<footer>', 1)[0].strip()
    h1 = re.search(r'<h1>(.*?)</h1>', body, re.S).group(1)
    body = body.replace(f'<h1>{h1}</h1>', '', 1).strip()
    meta = ''
    mm = re.match(r'<p class="meta">(.*?)</p>', body, re.S)
    if mm:
        meta, body = mm.group(1), body[mm.end():].strip()
    toc, n = [], 0

    def anchor(m):
        nonlocal n
        n += 1
        toc.append((f's{n}', re.sub(r'<[^>]+>', '', m.group(1))))
        return f'<h2 id="s{n}">{m.group(1)}</h2>'
    body = re.sub(r'<h2>(.*?)</h2>', anchor, body, flags=re.S)
    # links inside the texts stay as they were: they were written for the same paths
    ui = LEGAL_UI[lang]
    tabs = []
    for key in ('privacy', 'terms', 'messengers', 'support'):
        target = f'{r}{key}/' + ('ru/' if lang == 'ru' and key != 'support' else '')
        cur = ' aria-current="page"' if key == base else ''
        tabs.append(f'<a href="{target}"{cur}>{e(ui[key])}</a>')
    other = ''
    if base != 'support':
        other_href = (f'{r}{base}/' if lang == 'ru' else f'{r}{base}/ru/')
        other = f'<a class="alt-lang" href="{other_href}" hreflang="{"en" if lang == "ru" else "ru"}">{ui["other"]}</a>'
    toc_html = ''.join(f'<li><a href="#{i}">{e(t)}</a></li>' for i, t in toc)
    canonical = f'{BASE_URL}/{path}/'
    alts = ''
    if base != 'support':
        alts = (f'<link rel="alternate" hreflang="en" href="{BASE_URL}/{base}/">\n'
                f'<link rel="alternate" hreflang="ru" href="{BASE_URL}/{base}/ru/">\n')
    TT = T[lang] if lang in T else T['en']
    desc = re.sub(r'<[^>]+>', '', meta)[:155] if meta else title
    out = [head(lang, title, desc, canonical, r, alts, og_image=f'{BASE_URL}/assets/og/en.jpg'), '<body>', SYMBOLS,
           header(TT, lang, r, available, current_path='')]
    toc_block = (f'<nav class="toc" aria-label="{e(ui["contents"])}"><b>{e(ui["contents"])}</b><ol>{toc_html}</ol></nav>' if toc else '')
    toc_m = (f'<details class="toc-m"><summary>{e(ui["contents"])}<span class="chev"></span></summary><ol>{toc_html}</ol></details>' if toc else '')
    out.append(f'''<main id="main">
<div class="wrap doc-nav"><nav class="tabs">{"".join(tabs)}</nav>{other}</div>
<div class="wrap doc-head"><h1>{h1}</h1>{f'<p class="meta">{meta}</p>' if meta else ''}{toc_m}</div>
<div class="wrap grid doc">{toc_block}<article class="prose">{body}</article></div>
</main>
''')
    out.append(footer(TT, lang, r, available))
    out.append('</body>\n</html>\n')
    return ''.join(out)


def main():
    global JS_VERSION
    js = (SRC / 'site.js').read_text()
    (ROOT / 'assets/site.js').write_text(js)
    JS_VERSION = hashlib.sha1(js.encode()).hexdigest()[:8]
    content = {}
    for c, *_ in LANGS:
        f = SRC / 'content' / f'{c}.json'
        if f.exists():
            content[c] = json.loads(f.read_text())
    en = content['en']
    available = set(content)
    (ROOT / 'assets/qr').mkdir(exist_ok=True)
    for c in available:
        (ROOT / f'assets/qr/{c}.svg').write_text(qrcode.svg(qrcode.build(store_url(c, f'site-{c}-qr'))))
    for c, T in content.items():
        TT = {**en, **T}
        out = ROOT / (L[c]['folder'] or '.') / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(typeset(c, home(c, TT, available)))
    (ROOT / 'press').mkdir(exist_ok=True)
    (ROOT / 'press/index.html').write_text(press(en, available))
    (ROOT / '404.html').write_text(not_found(en, available))
    T = {'en': en, 'ru': {**en, **content.get('ru', {}), **({} if 'ru' in content else LEGAL_FALLBACK_RU)}}
    for path in ('privacy', 'privacy/ru', 'terms', 'terms/ru', 'messengers', 'messengers/ru', 'support'):
        (ROOT / path / 'index.html').write_text(legal(path, T, available))
    print('built', sorted(available), 'base', BASE_URL)


# Russian chrome for the Russian legal pages while ru.json is not there yet
LEGAL_FALLBACK_RU = {'nFeatures': 'Возможности', 'nLanguages': 'Языки', 'nPress': 'Пресса', 'nLangMenu': 'Язык',
                     'eyebrow': 'ИИ-ассистент для CarPlay', 'fPrivacy': 'Конфиденциальность', 'fTerms': 'Условия',
                     'fMessengers': 'Мессенджеры', 'fSupport': 'Поддержка', 'fPress': 'Пресса', 'badgeAlt': 'Загрузите в App Store',
                     'tm': 'Apple, логотип Apple, CarPlay, iPhone и Siri — товарные знаки Apple Inc. App Store — знак обслуживания Apple Inc.',
                     'skip': 'К содержанию'}

if __name__ == '__main__':
    main()
