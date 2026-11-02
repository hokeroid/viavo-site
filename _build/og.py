#!/usr/bin/env python3
"""Renders the 1200×630 share image of each language page (assets/og/<lang>.jpg) with headless Chrome.

  python3 -I _build/og.py [lang ...]     # default: every _build/content/<lang>.json
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
FONTS = {'he': "'Noto Sans Hebrew'", 'ru': 'Manrope', 'uk': 'Manrope', 'el': 'Manrope', 'sr': 'Manrope'}


def card(lang, T):
    en = json.loads((ROOT / '_build/content/en.json').read_text())
    T = {**en, **T}
    shot = next((f'carplay-{lang}-{k}' for k in ('idle', 'listening') if (ROOT / f'assets/img/carplay-{lang}-{k}-1080.webp').exists()),
                'carplay-en-idle')
    fonts = (ROOT / 'assets/fonts/fonts.css').read_text().replace('url(', f'url(file://{ROOT}/assets/fonts/')
    head = FONTS.get(lang, "'Space Grotesk'")
    rtl = lang in ('he', 'ar')
    return f'''<!doctype html><html dir="{'rtl' if rtl else 'ltr'}"><head><meta charset="utf-8"><style>{fonts}
html,body{{margin:0;width:1200px;height:630px;background:#0B0C10;color:#F4F3EF;overflow:hidden}}
.w{{position:relative;width:1200px;height:630px;font-family:Manrope,system-ui,sans-serif}}
.glow{{position:absolute;inset:auto -120px -260px auto;width:900px;height:700px;background:radial-gradient(closest-side,rgba(255,178,36,.22),transparent)}}
.logo{{position:absolute;top:56px;inset-inline-start:64px;display:flex;align-items:center;gap:14px;direction:ltr}}
.logo span{{font:700 40px 'Space Grotesk',sans-serif;letter-spacing:-.03em}}
h1{{position:absolute;top:150px;inset-inline-start:64px;width:560px;margin:0;font:700 64px/1.04 {head},Manrope,sans-serif;letter-spacing:-.03em}}
h1 b{{display:block;color:#8ED0FF;font-weight:700}}
.car{{position:absolute;top:150px;inset-inline-end:-120px;width:640px;padding:12px;border-radius:26px;background:linear-gradient(180deg,#1E2027,#101116);border:1px solid rgba(255,255,255,.09);box-shadow:0 40px 80px rgba(0,0,0,.6)}}
.car img{{display:block;width:100%;border-radius:15px}}
.ft{{position:absolute;bottom:56px;inset-inline-start:64px;font-size:22px;color:#A3A7B3}}
</style></head><body><div class="w"><div class="glow"></div>
<div class="logo"><svg viewBox="6 3 92 92" width="44" height="44"><g fill="none" stroke="#FFB224" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"><path d="M34 27 L62 85 L90 27" opacity=".2"/><path d="M24 19 L52 77 L80 19" opacity=".45"/><path d="M14 11 L42 69 L70 11"/></g></svg><span>viavo</span></div>
<h1>{T['h1a']}<b>{T['h1b']}</b></h1>
<div class="car"><img src="file://{ROOT}/assets/img/{shot}-1080.webp"></div>
<div class="ft">{T['eyebrow']}</div></div></body></html>'''


def main(langs):
    out = ROOT / 'assets/og'
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for lang in langs:
            T = json.loads((ROOT / f'_build/content/{lang}.json').read_text())
            page = Path(tmp) / f'{lang}.html'
            page.write_text(card(lang, T))
            png = Path(tmp) / f'{lang}.png'
            subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=1200,630',
                            '--virtual-time-budget=5000', f'--screenshot={png}', f'--user-data-dir={tmp}/prof',
                            '--allow-file-access-from-files', f'file://{page}'], check=True, capture_output=True)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(png), '-q:v', '3', str(out / f'{lang}.jpg')], check=True)
            print(lang)


if __name__ == '__main__':
    main(sys.argv[1:] or sorted(p.stem for p in (ROOT / '_build/content').glob('*.json') if p.stem != 'press'))
