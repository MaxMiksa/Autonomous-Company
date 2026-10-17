import { animate } from "motion/mini";
import { spring } from "motion";

export const timing = { micro: 120, local: 180, layout: 220, drawer: 240, page: 300 };
export const sidebarMotion = {
  enter: { transform: 'translateX(0)', opacity: '1' },
  exit: { transform: 'translateX(72px)', opacity: '0' },
  duration: timing.page,
};
export const easing = "cubic-bezier(.2,.7,.2,1)";
const running = new Set<() => void>();
const resizeStable = new Set<() => void>();
const preference = matchMedia("(prefers-reduced-motion: reduce)");
export const quiet = () => preference.matches || document.hidden || Boolean((window as any).__disableDashboardMotion);

// Motion owns interpolation and interrupted values; the app owns lifecycle completion.
const scopes = new WeakMap<HTMLElement, () => void>();
export function tween(node: HTMLElement, target: Record<string, string>, duration = timing.local, done?: () => void, preserveOnResize = false) {
  scopes.get(node)?.();
  if (quiet() || !node.animate) { Object.assign(node.style, target); done?.(); return; }
  let animation: ReturnType<typeof animate>;
  try { animation = animate(node, target, { duration: duration / 1000, ease: [.2, .7, .2, 1] }); }
  catch { Object.assign(node.style, target); done?.(); return; }
  const release = () => { if (scopes.get(node) === stop) scopes.delete(node); running.delete(finish); resizeStable.delete(finish); };
  const stop = () => {
    // Tabs may hide a node before cancellation; browsers cannot commit its styles then.
    try { animation.stop(); } catch { animation.cancel(); }
    release();
  };
  const finish = () => { stop(); Object.assign(node.style, target); done?.(); };
  scopes.set(node, stop); running.add(finish);
  if (preserveOnResize) resizeStable.add(finish);
  animation.then(() => { if (scopes.get(node) === stop) { release(); done?.(); } });
  return animation;
}
export function stopMotion(node: HTMLElement) { scopes.get(node)?.(); }

export function reveal(node: HTMLElement | null) {
  if (!node || quiet()) return;
  if (!scopes.has(node)) node.style.opacity = '0';
  tween(node, { opacity: '1' }, timing.local, () => node.style.removeProperty('opacity'));
}
export function positions(container: HTMLElement, selector: string) {
  const nodes = [...container.querySelectorAll<HTMLElement>(selector)];
  const result = new Map<string, DOMRect>();
  if (nodes.length > 80 || quiet()) return result;
  for (const node of nodes) {
    const rect = node.getBoundingClientRect();
    if (rect.height && rect.top < innerHeight && rect.bottom > 0) result.set(node.dataset.entryId || node.dataset.cycleId || node.dataset.requestId || '', rect);
  }
  return result;
}
export function layout(container: HTMLElement, selector: string, before: Map<string, DOMRect>) {
  if (!before.size || quiet()) return;
  const changes = [...container.querySelectorAll<HTMLElement>(selector)].map(node => ({ node, after: node.getBoundingClientRect(), before: before.get(node.dataset.entryId || node.dataset.cycleId || node.dataset.requestId || '') }));
  for (const { node, after, before: previous } of changes) {
    if (!previous || !after.height || after.bottom < 0 || after.top > innerHeight) continue;
    const x = previous.x - after.x, y = previous.y - after.y;
    if (Math.abs(x) + Math.abs(y) < 1) continue;
    scopes.get(node)?.(); node.style.transform = `translate(${x}px,${y}px)`;
    tween(node, { transform: 'translate(0,0)' }, timing.layout, () => node.style.removeProperty('transform'));
  }
}
export function reconcile(container: HTMLElement, nodes: Node[]) {
  const wanted = new Set(nodes);
  for (const child of [...container.childNodes]) if (!wanted.has(child)) child.remove();
  nodes.forEach((node, index) => { if (container.childNodes[index] !== node) container.insertBefore(node, container.childNodes[index] || null); });
}

function fluidNavigation(navigation: HTMLElement, returning: boolean) {
  const { width, height } = navigation.getBoundingClientRect();
  const inset = matchMedia('(max-width: 640px)').matches ? 0 : 12;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const path = document.createElementNS(svg.namespaceURI, 'path') as SVGPathElement;
  svg.classList.add('navigation-fluid-surface'); svg.setAttribute('aria-hidden', 'true');
  svg.style.left = `${-inset}px`; svg.style.width = `calc(100% + ${inset * 2}px)`;
  svg.setAttribute('viewBox', `0 0 ${width + inset * 2} ${height}`);
  svg.setAttribute('preserveAspectRatio', 'none');
  // Matching path commands let Motion interpolate the crown and both concave feet together.
  const outline = (top: number, crown: number, foot: number) => `M ${inset - foot} ${height} A ${foot} ${foot} 0 0 0 ${inset} ${height - foot} L ${inset} ${top + crown} A ${crown} ${crown} 0 0 1 ${inset + crown} ${top} L ${width + inset - crown} ${top} A ${crown} ${crown} 0 0 1 ${width + inset} ${top + crown} L ${width + inset} ${height - foot} A ${foot} ${foot} 0 0 0 ${width + inset + foot} ${height} Z`;
  const expanded = outline(0, 12, inset), collapsed = outline(height, 0, 0);
  path.setAttribute('d', expanded); svg.append(path);
  const children = [...navigation.children] as HTMLElement[];
  navigation.append(svg); navigation.dataset.fluidNavigation = '';
  const controls: ReturnType<typeof animate>[] = [];
  const options = { duration: .36, type: spring, bounce: 0, autoplay: false };
  const frames = <T,>(from: T, to: T) => returning ? [to, from] : [from, to];
  const styles = new Map(children.map(node => [node, node.style.transform]));
  const clear = () => {
    controls.forEach(control => control.cancel()); svg.remove(); delete navigation.dataset.fluidNavigation;
    navigation.style.removeProperty('opacity');
    children.forEach(node => { node.style.transform = styles.get(node) || ''; node.style.removeProperty('opacity'); });
  };
  try {
    controls.push(animate(path, { d: frames(`path("${collapsed}")`, `path("${expanded}")`) }, options));
    controls.push(animate(navigation, { opacity: frames(0, 1) }, options));
    for (const node of children) {
      const transform = getComputedStyle(node).transform;
      controls.push(animate(node, { transform: frames(`translateY(8px) ${transform === 'none' ? '' : transform}`, transform), opacity: frames(0, 1) }, options));
    }
  } catch { clear(); return null; }
  return { controls, clear };
}

export function workspace(root: HTMLElement, origin: DOMRect, done: () => void, returning = false, entered = done) {
  const main = root.querySelector<HTMLElement>('main')!;
  const navigation = root.querySelector<HTMLElement>('.topbar > .navline');
  root.style.zIndex = '4';
  root.dataset.workspaceMotion = '';
  const box = main.getBoundingClientRect();
  const surface = document.createElement('div');
  surface.className = 'workspace-motion-surface'; surface.setAttribute('aria-hidden', 'true');
  Object.assign(surface.style, { left: `${box.left}px`, top: `${box.top}px`, width: `${box.width}px`, height: `${Math.max(box.height, innerHeight - box.top - 24)}px` });
  document.body.append(surface);
  const start = `translate(${origin.left - box.left}px,${origin.top - box.top}px) scale(${origin.width / box.width},${origin.height / Math.max(box.height, innerHeight - box.top - 24)})`;
  const animations: Animation[] = [];
  const fluid = navigation ? fluidNavigation(navigation, returning) : null;
  let reverseDone: (() => void) | undefined = returning ? done : undefined;
  let direction = returning ? -1 : 1;
  let finished = false;
  const clean = () => { animations.forEach(animation => animation.cancel()); fluid?.clear(); surface.remove(); delete root.dataset.workspaceMotion; root.style.removeProperty('z-index'); main.style.removeProperty('opacity'); running.delete(finish); };
  const finish = () => { if (finished) return; finished = true; clean(); if (direction < 0) reverseDone?.(); else entered(); };
  // Fresh exits use the same quick-start curve as entries; interruptions reverse in place.
  const frames = <T,>(from: T, to: T) => returning ? [to, from] : [from, to];
  try {
    animations.push(surface.animate({ transform: frames(start, 'translate(0,0) scale(1,1)'), opacity: frames(0, 1) }, { duration: timing.page, easing, fill: 'both' }));
    // Keep fixed descendants viewport-anchored and outgoing content at its reading position.
    animations.push(main.animate({ opacity: frames(0, 1) }, { duration: timing.page, easing, fill: 'both' }));
  } catch { finish(); }
  const watch = () => { const currentDirection = direction; Promise.all([...animations.map(animation => animation.finished), ...(fluid?.controls.map(control => control.finished) || [])]).then(() => { if (direction === currentDirection) finish(); }, () => {}); };
  fluid?.controls.forEach(control => { control.time = 0; control.play(); });
  if (!finished) { running.add(finish); watch(); }
  return { get finished() { return finished; }, finish, forward() {
    direction = 1; animations.forEach(animation => { animation.playbackRate = returning ? -1 : 1; animation.play(); });
    fluid?.controls.forEach(control => { control.speed = returning ? -1 : 1; control.play(); }); watch();
  }, reverse(callback: () => void) {
    reverseDone = callback; direction = -1;
    if (!surface.isConnected || quiet()) { finish(); return; }
    // Reverse the existing timeline: no endpoint write and no replacement frame.
    animations.forEach(animation => animation.reverse());
    fluid?.controls.forEach(control => { control.speed = returning ? 1 : -1; control.play(); }); watch();
  } };
}
function finishAll(resizing = false) { [...running].forEach(finish => { if (!resizing || !resizeStable.has(finish)) finish(); }); }
preference.addEventListener('change', () => finishAll());
document.addEventListener('visibilitychange', () => {
  document.documentElement.toggleAttribute('data-motion-hidden', document.hidden);
  if (document.hidden) finishAll();
});
let resizeRevision = 0;
addEventListener('resize', () => {
  finishAll(true); const revision = ++resizeRevision; document.documentElement.dataset.motionResize = '';
  requestAnimationFrame(() => requestAnimationFrame(() => { if (revision === resizeRevision) delete document.documentElement.dataset.motionResize; }));
});
(window as any).DashboardMotion = { workspace, tween, timing };
