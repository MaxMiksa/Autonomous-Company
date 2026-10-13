(function () {
  'use strict';
  const factories = new Map(), assets = new Map();
  let active, center, detail, frame, version = 0, target = location.href, transition;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const route = url => /^\/products\/[^/]+\/?$/.test(url.pathname) ? 'journal' : /^\/(center\/?)?$/.test(url.pathname) ? 'center' : null;

  function viewDocument(view) {
    return new Proxy(document, {
      get(original, key) {
        if (key === 'body') return view.root;
        if (key === 'hidden') return !view.active || original.hidden;
        if (key === 'getElementById') return id => view.root.querySelector('#' + CSS.escape(id) + ', [data-parked-id="' + CSS.escape(id) + '"]');
        if (key === 'querySelector' || key === 'querySelectorAll') return selector => view.root[key](selector);
        if (key === 'addEventListener') return (type, handler, options) => view.listen(type === 'visibilitychange' ? original : view.root, type, handler, options);
        if (key === 'dispatchEvent') return event => view.root.dispatchEvent(event);
        const value = Reflect.get(original, key, original);
        return typeof value === 'function' ? value.bind(original) : value;
      },
      set(original, key, value) { if (view.active) Reflect.set(original, key, value); return true; },
    });
  }
  function createView(kind, url, source) {
    // The HTML supplies the styled shell before deferred scripts load.
    let root = source.querySelector(':scope > .workspace-view, :scope > .app-frame > .workspace-view');
    if (!root) {
      root = document.createElement('div'); root.className = 'workspace-view'; root.dataset.view = kind;
      for (const child of [...source.childNodes]) if (child.nodeName !== 'SCRIPT') root.append(child);
    }
    const inner = root.querySelector('.app-frame');
    if (inner) inner.className = 'view-frame';
    const events = new AbortController(), reads = new Set();
    const view = { kind, url, root, active: true, epoch: 0, scroll: 0, ui: null, controller: null,
      listen(node, type, callback, options) { node.addEventListener(type, callback, { ...(typeof options === 'boolean' ? { capture: options } : options), signal: events.signal }); },
      request(controller, options) {
        const reading = !options.method || options.method === 'GET', epoch = view.epoch;
        if (reading && !view.active) throw new DOMException('Inactive view', 'AbortError');
        if (reading) reads.add(controller);
        return { valid: () => !reading || (view.active && epoch === view.epoch), done: () => reads.delete(controller) };
      },
      pause() {
        if (!view.active) return;
        view.scroll = scrollY; view.controller?.pause(); view.ui?.pause(); view.active = false; ++view.epoch;
        reads.forEach(controller => controller.abort()); reads.clear();
        root.inert = true; root.setAttribute('aria-hidden', 'true');
        root.querySelectorAll('[id]').forEach(node => { node.dataset.parkedId = node.id; node.removeAttribute('id'); });
      },
      resume() {
        root.querySelectorAll('[data-parked-id]').forEach(node => { node.id = node.dataset.parkedId; delete node.dataset.parkedId; });
        root.inert = false; root.removeAttribute('aria-hidden'); view.active = true;
        view.controller?.resume();
      },
      dispose() { view.pause(); events.abort(); view.controller?.dispose(); view.ui?.dispose(); root.remove(); },
    };
    view.document = viewDocument(view);
    frame.append(root);
    view.ui = window.createDashboardUI(view.document);
    view.controller = factories.get(kind)(view);
    return view;
  }
  function style(kind) {
    for (const link of document.querySelectorAll('link[href="/center.css"], link[href="/styles.css"]')) link.media = 'all';
    document.body.classList.toggle('center-journal', kind === 'journal' && route(new URL(target)) === 'journal');
  }
  function asset(path, type = 'script') {
    if (assets.has(path)) return assets.get(path);
    const existing = document.querySelector((type === 'script' ? 'script[src' : 'link[href') + '="' + path + '"]');
    if (existing) return Promise.resolve();
    const promise = new Promise((resolve, reject) => {
      const node = document.createElement(type === 'script' ? 'script' : 'link');
      if (type === 'script') node.src = path; else { node.rel = 'stylesheet'; node.href = path; node.media = 'all'; }
      node.onload = resolve; node.onerror = () => { assets.delete(path); node.remove(); reject(new Error('Cannot load ' + path)); };
      document.head.append(node);
    });
    assets.set(path, promise); return promise;
  }
  async function prepare(kind, url) {
    const response = await fetch(url, { headers: { Accept: 'text/html' } });
    if (!response.ok) throw new Error('Cannot load workspace');
    const parsed = new DOMParser().parseFromString(await response.text(), 'text/html');
    if (!parsed.querySelector(kind === 'center' ? '#centerMain' : '#mainContent')) throw new Error('Unexpected workspace');
    // Only fixed application assets execute; scripts in fetched markup are inert.
    parsed.querySelectorAll('script').forEach(node => node.remove());
    await Promise.all([asset(kind === 'center' ? '/center.css' : '/styles.css', 'style'), asset(kind === 'center' ? '/center-i18n.js' : '/i18n.js')]);
    await asset(kind === 'center' ? '/center.js' : '/app.js');
    return parsed.body;
  }
  function settle() { transition?.finish(); transition = null; }
  function activate(view) {
    if (active !== view) active?.pause();
    active = view; style(view.kind);
    frame.append(view.root); view.root.hidden = false;
    view.resume(); scrollTo({ top: view.scroll, behavior: 'instant' });
  }
  async function navigate(value, { historyMode = 'push', source = null } = {}) {
    const url = new URL(value, location.href), kind = route(url);
    if (!kind || url.origin !== location.origin || window.__disableWorkspaceNavigation) { location.href = url.href; return; }
    if (url.href === target && active?.url === url.href) { active.ui.pause(); return; }
    const token = ++version; target = url.href;
    if (historyMode === 'push') history.pushState({}, '', url);
    if (kind === 'center' && center) {
      if (transition && transition.detail === active) {
        activate(center); restoreFocus();
        transition.reverse(() => { if (token !== version) return; detail?.root.remove(); transition = null; });
      } else {
        settle(); const previous = active; activate(center); restoreFocus();
        const row = [...center.root.querySelectorAll('[data-focus-key]')].find(node => node.dataset.focusKey === center.focusKey)?.closest('.product-row');
        if (previous === detail && row && !reduced.matches && !document.hidden && !window.__disableDashboardMotion) {
          transition = window.DashboardMotion.workspace(detail.root, row.getBoundingClientRect(), () => { detail.root.remove(); transition = null; }, true,
            () => { center.root.hidden = true; transition = null; });
          if (transition.finished) transition = null; else transition.detail = detail;
        } else { detail?.root.remove(); center.ui.reveal(center.root.querySelector('main')); }
      }
      return;
    }
    if (transition && detail?.url === url.href) {
      activate(detail); transition.forward(); return;
    }
    // The target changes immediately, including while its template is loading.
    source ||= center?.root.querySelector(`a.product-link[href="${CSS.escape(url.pathname)}"]`);
    const row = source?.closest('.product-row');
    const origin = row?.getBoundingClientRect();
    const name = row?.querySelector('.product-link')?.textContent || '';
    if (source && center) center.focusKey = source.dataset.focusKey || row?.querySelector('.product-link')?.dataset.focusKey;
    active?.pause();
    try {
      let next = kind === 'journal' ? detail : center;
      const markup = next?.url === url.href ? null : await prepare(kind, url.href);
      if (token !== version) return;
      settle();
      if (markup) {
        if (kind === 'journal') detail?.dispose();
        style(kind); next = createView(kind, url.href, markup);
        if (kind === 'journal') detail = next; else center = next;
      }
      activate(next);
      if (name && !next.root.querySelector('#workspaceProjectName')?.textContent) next.root.querySelector('#workspaceProjectName').textContent = name;
      const back = next.root.querySelector('#journalBackLink'); if (back) back.hidden = false;
      const other = kind === 'journal' ? center : detail;
      if (other) other.root.hidden = true;
      if (kind === 'journal' && origin && !reduced.matches && !document.hidden && !window.__disableDashboardMotion) {
        if (other) other.root.hidden = false;
        transition = window.DashboardMotion.workspace(next.root, origin, () => { if (other) other.root.hidden = true; transition = null; });
        if (transition.finished) transition = null; else transition.detail = next;
      } else next.ui.reveal(next.root.querySelector('main'));
      (back || next.root.querySelector('main'))?.focus({ preventScroll: true });
    } catch (_) {
      if (token !== version) return;
      // A single ordinary navigation handles an initialization failure.
      location.replace(url.href);
    }
  }
  function restoreFocus() {
    const node = [...center.root.querySelectorAll('[data-focus-key]')].find(node => node.dataset.focusKey === center.focusKey);
    (node || center.root.querySelector('main'))?.focus({ preventScroll: true });
  }
  function boot(kind) {
    if (frame || !window.createDashboardUI) return;
    frame = document.querySelector('body > .app-frame');
    let source = frame;
    if (!frame?.querySelector(':scope > .workspace-view')) {
      frame = document.createElement('div'); frame.className = 'app-frame';
      source = document.createElement('div');
      for (const child of [...document.body.childNodes]) if (!child.hasAttribute?.('data-persistent-ui')) source.append(child);
      document.body.append(frame);
    }
    active = createView(kind, location.href, source);
    if (kind === 'center') center = active; else detail = active;
    document.addEventListener('click', event => {
      const link = event.target.closest('a[href]');
      if (!link || event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || link.target || link.hasAttribute('download')) return;
      const url = new URL(link.href);
      if (url.origin !== location.origin || !route(url)) return;
      event.preventDefault(); navigate(url.href, { source: link });
    });
    addEventListener('popstate', () => navigate(location.href, { historyMode: 'pop' }));
    addEventListener('resize', settle);
    document.addEventListener('visibilitychange', () => { if (document.hidden) settle(); });
    reduced.addEventListener('change', settle);
  }
  window.DashboardNavigation = { register(kind, factory) { factories.set(kind, factory); boot(kind); }, navigate,
    inspect: () => ({ active: active?.kind, views: Number(Boolean(center)) + Number(Boolean(detail)), transitioning: Boolean(transition), target, centerScroll: center?.scroll, detailScroll: detail?.scroll }) };
})();
