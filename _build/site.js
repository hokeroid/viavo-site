// Viavo site: small progressive enhancements. Without JS every section still shows its first state.
(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

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
