# Bulgarian website

`bg` in `LANGS` is a **website** locale. Keep it in `SITE_ONLY` until the production app's Bulgarian UI, recognition and spoken replies have all been confirmed. A development build, a store listing in Bulgaria or a translated screenshot is not evidence of all three. When support ships, review the dated answer page, home copy, language grid, screenshot assets, structured data and `llms.txt` together.

- Homepage: `content/bg.json`; search answer and its FAQ schema: `seo/pages/bg/glasov-asistent-carplay.md`; support: `legal-src/support/bg/index.html`.
- The legal texts remain the existing English/Russian originals. Bulgarian support links to both; the home page labels English legal and press links. Do not list those original pages as Bulgarian alternates.
- The site uses the checked-in SEO inputs in `seo/root/` and `seo/jsonld/`. When refreshing external SEO exports, keep website locales distinct from app languages. The Bulgarian home belongs to the home hreflang group, support to the support group, and the Bulgarian-only guide has no equivalent in another language.
- From the repository root, run `python3 -IB _build/og.py bg` when the hero changes, then `python3 -IB _build/build.py`. Commit the generated pages, sitemap and assets with their sources. Use `-B` to avoid updating Python caches.
