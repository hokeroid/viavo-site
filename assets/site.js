// Viavo site: small progressive enhancements. Without JS every section still shows its first state.
(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Visits, counted on our own server without cookies (VIA-492): a random id for this tab only, no IP kept.
  const HIT = 'https://mjepxubktjnrkliidnzj.supabase.co/functions/v1/site-hit';
  const hit = (e, ct) => {
    try {
      if (localStorage.getItem('viavo_team') === '1' || navigator.webdriver) return;
      let s = sessionStorage.getItem('viavo_s');
      if (!s) {
        const b = crypto.getRandomValues(new Uint8Array(16));
        s = btoa(String.fromCharCode(...b)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
        sessionStorage.setItem('viavo_s', s);
      }
      const q = new URLSearchParams(location.search);
      const body = JSON.stringify({ e, p: location.pathname, l: document.documentElement.lang, s, r: document.referrer,
        us: q.get('utm_source') || '', um: q.get('utm_medium') || '', uc: q.get('utm_campaign') || '', ct: ct || '',
        tz: Intl.DateTimeFormat().resolvedOptions().timeZone || '', bl: navigator.language || '' });
      if (!(navigator.sendBeacon && navigator.sendBeacon(HIT, new Blob([body], { type: 'text/plain' }))))
        fetch(HIT, { method: 'POST', keepalive: true, mode: 'cors', body }).catch(() => {});
    } catch (e) {}
  };
  hit('pageview');
  document.addEventListener('click', ev => {
    const a = ev.target.closest && ev.target.closest('a[href*="apps.apple.com"]');
    if (a) { try { hit('appstore_click', new URL(a.href).searchParams.get('ct')); } catch (e) {} }
  });

  // Keep the acquisition channel across same-tab navigation. Only a short
  // channel code persists, and a fresh external entry replaces it.
  try {
    const q = new URLSearchParams(location.search);
    let host = document.referrer ? new URL(document.referrer).hostname : '';
    let previous = '';
    try {
      const redirected = sessionStorage.getItem('viavo_redirect_ref');
      sessionStorage.removeItem('viavo_redirect_ref');
      if (redirected !== null && (!host || host === location.hostname)) host = redirected;
      previous = sessionStorage.getItem('viavo_acquisition') || '';
    } catch (e) {}
    const medium = (q.get('utm_medium') || '').toLowerCase();
    const source = (q.get('utm_source') || '').toLowerCase();
    const googleAd = ['gclid', 'gbraid', 'wbraid'].some(k => q.has(k));
    let channel = '';
    if (googleAd || ['cpc', 'ppc', 'paidsearch', 'paid'].includes(medium)) {
      channel = 'paid-' + (googleAd ? 'google' : source.replace(/[^a-z0-9]/g, '').slice(0, 8) || 'ads');
    } else if ((source === 'google' && medium === 'organic') ||
               (!source && !medium && !q.has('utm_campaign') && !q.has('fbclid') &&
                /^(?:www\.)?google\.(?:[a-z]{2,3}|co\.[a-z]{2}|com\.[a-z]{2})$/.test(host))) {
      const article = location.pathname.replace(/\/index\.html$/, '/').split('/').filter(Boolean).pop();
      const entry = article === 'whatsapp-carplay' ? 'whatsapp' :
        ['siri', 'chatgpt-carplay'].includes(article) ? 'answers' : 'site';
      channel = 'seo-google-' + entry;
    } else if (host === location.hostname && !source && !medium && !q.has('utm_campaign') && !q.has('fbclid')) {
      channel = previous;
    }
    try { sessionStorage.setItem('viavo_acquisition', channel); } catch (e) {}
    if (channel) {
      document.querySelectorAll('a[href*="apps.apple.com"]').forEach(a => {
        const u = new URL(a.href);
        if (u.hostname !== 'apps.apple.com' || !/\/id6761760437(?:\/|$)/.test(u.pathname)) return;
        const token = channel.startsWith('seo-google-') ? channel :
          (channel.slice(5) + '-' + (u.searchParams.get('ct') || 'site')).slice(0, 40);
        u.searchParams.set('ct', token);
        u.searchParams.set('pt', '127870899');
        u.searchParams.set('mt', '8');
        a.href = u.toString();
      });
      const qrCampaign = channel.startsWith('paid-')
        ? (channel === 'paid-google' ? 'google-paid-qr' : 'ads-paid-qr')
        : channel;
      if (['seo-google-answers', 'seo-google-whatsapp', 'seo-google-site', 'google-paid-qr', 'ads-paid-qr'].includes(qrCampaign)) {
        document.querySelectorAll('img[data-qr-dir]').forEach(img => {
          img.src = img.dataset.qrDir + qrCampaign + '.svg';
        });
      }
    }
  } catch (e) {}

  // Siri band: the language word and the real CarPlay screen change together every 3.5 s
  const band = document.querySelector('.band');
  if (band && !reduced) {
    const word = band.querySelector('.w'), shots = [...band.querySelectorAll('.scr picture')], rows = [...band.querySelectorAll('.gap div')];
    const words = JSON.parse(band.dataset.words);
    let i = 0, paused = false;
    band.addEventListener('mouseenter', () => paused = true);
    band.addEventListener('mouseleave', () => paused = false);
    shots.forEach(p => p.querySelector('img').loading = 'eager');
    setInterval(() => {
      if (paused || document.hidden) return;
      word.classList.add('fade');
      setTimeout(() => {
        shots[i].hidden = true; rows[i].classList.remove('on');
        i = (i + 1) % shots.length;
        shots[i].hidden = false; rows[i].classList.add('on');
        word.textContent = words[i]; word.classList.remove('fade');
      }, 150);
    }, 3500);
  }

  // "It does it": one example open at a time, the phone shows its real screen
  const exs = [...document.querySelectorAll('.ex')], phones = [...document.querySelectorAll('.say .phone picture')];
  exs.forEach((b, i) => b.addEventListener('click', () => {
    exs.forEach((x, j) => x.setAttribute('aria-pressed', i === j));
    phones.forEach((p, j) => p.hidden = i !== j);
  }));

  // Works with: category filter
  const chips = [...document.querySelectorAll('.chips button')];
  chips.forEach(c => c.addEventListener('click', () => {
    chips.forEach(x => x.setAttribute('aria-pressed', x === c));
    document.querySelectorAll('.tiles li').forEach(t => t.hidden = c.dataset.cat !== 'all' && t.dataset.cat !== c.dataset.cat);
  }));

  // Phone: the App Store bar slides in once the hero is gone
  const bar = document.querySelector('.mbar'), hero = document.querySelector('.hero');
  if (bar && hero && 'IntersectionObserver' in window)
    new IntersectionObserver(([e]) => bar.classList.toggle('on', !e.isIntersecting && e.boundingClientRect.top < 0)).observe(hero);

  // A language picked by hand is remembered, so the root page stops sending this visitor to the browser's language
  document.querySelectorAll('a[hreflang], .lgrid a, .ftr .fl a').forEach(a => a.addEventListener('click', () => {
    try { localStorage.setItem('viavo-lang', (a.getAttribute('hreflang') || a.lang || '').toLowerCase().replace('sr-latn', 'sr')); } catch (e) {}
    hit('lang_switch');
  }));

  // Language menu closes on an outside click or Escape
  const menu = document.querySelector('.lang');
  if (menu) {
    document.addEventListener('click', e => { if (!menu.contains(e.target)) menu.open = false; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') menu.open = false; });
  }

  // Legal pages: highlight the section being read
  const toc = [...document.querySelectorAll('.toc a')];
  if (toc.length && 'IntersectionObserver' in window) {
    const byId = new Map(toc.map(a => [a.hash.slice(1), a]));
    const io = new IntersectionObserver(es => es.forEach(e => {
      if (!e.isIntersecting) return;
      toc.forEach(a => a.classList.remove('on'));
      byId.get(e.target.id)?.classList.add('on');
    }), { rootMargin: '-20% 0px -70% 0px' });
    document.querySelectorAll('.prose h2[id]').forEach(h => io.observe(h));
  }
})();
