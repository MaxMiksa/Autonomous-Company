(function () {
  'use strict';
  const key = 'autonomous-company.theme';
  const system = matchMedia('(prefers-color-scheme: dark)');
  let current = 'system', revision = 0;
  function sync(root = document) {
    root.querySelectorAll('[data-theme-select]').forEach(select => { select.value = current; });
  }
  function apply(value, animated = false) {
    current = value === 'dark' || value === 'light' ? value : 'system';
    const resolved = current === 'system' ? (system.matches ? 'dark' : 'light') : current;
    sync();
    const token = ++revision;
    const update = () => {
      if (token !== revision) return;
      document.documentElement.dataset.theme = resolved;
      document.documentElement.classList.toggle('dark', resolved === 'dark');
      document.documentElement.style.colorScheme = resolved;
      window.dispatchEvent(new Event('dashboard:theme'));
    };
    if (animated && window.DashboardMotion?.theme && document.documentElement.dataset.theme !== resolved) {
      window.DashboardMotion.theme(update).catch(update);
    } else update();
  }
  try { current = localStorage.getItem(key) || 'system'; }
  catch (_) { /* Keep usable when storage is unavailable. */ }
  apply(current);
  document.addEventListener('change', event => {
    if (!event.target.matches('[data-theme-select]')) return;
    apply(event.target.value, true);
    try { localStorage.setItem(key, current); } catch (_) { /* The current page still switches. */ }
  });
  system.addEventListener('change', () => { if (current === 'system') apply(current, true); });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) apply(event.newValue, true);
  });
  window.DashboardTheme = { sync };
})();
