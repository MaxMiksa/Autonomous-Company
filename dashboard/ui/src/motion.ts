import { animate } from "motion/mini";
import { spring } from "motion";

export const timing = { micro: 120, local: 180, layout: 220, drawer: 240, page: 300 };
export const easing = "cubic-bezier(.2,.7,.2,1)";
const running = new Set<() => void>();
const preference = matchMedia("(prefers-reduced-motion: reduce)");
export const quiet = () => preference.matches || document.hidden || Boolean((window as any).__disableDashboardMotion);

// Motion owns interpolation and interrupted values; the app owns lifecycle completion.
const scopes = new WeakMap<HTMLElement, () => void>();
export function tween(node: HTMLElement, target: Record<string, string>, duration = timing.local, done?: () => void) {
  scopes.get(node)?.();
  if (quiet() || !node.animate) { Object.assign(node.style, target); done?.(); return; }
  let animation: ReturnType<typeof animate>;
  try { animation = animate(node, target, { duration: duration / 1000, ease: [.2, .7, .2, 1] }); }
  catch { Object.assign(node.style, target); done?.(); return; }
  const release = () => { if (scopes.get(node) === stop) scopes.delete(node); running.delete(finish); };
  const stop = () => {
    // Tabs may hide a node before cancellation; browsers cannot commit its styles then.
    try { animation.stop(); } catch { animation.cancel(); }
    release();
  };
  const finish = () => { stop(); Object.assign(node.style, target); done?.(); };
  scopes.set(node, stop); running.add(finish);
  animation.then(() => { if (scopes.get(node) === stop) { release(); done?.(); } });
  return animation;
}

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

function fluidNavigation(navigation: HTMLElement) {
  const { width, height } = navigation.getBoundingClientRect();
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const path = document.createElementNS(svg.namespaceURI, 'path') as SVGPathElement;
  svg.classList.add('navigation-fluid-surface'); svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('viewBox', `0 0 ${width + 24} ${height}`);
  svg.setAttribute('preserveAspectRatio', 'none');
  // Matching path commands let Motion interpolate the crown and both concave feet together.
  const outline = (top: number, crown: number, foot: number) => `M ${12 - foot} ${height} A ${foot} ${foot} 0 0 0 12 ${height - foot} L 12 ${top + crown} A ${crown} ${crown} 0 0 1 ${12 + crown} ${top} L ${width + 12 - crown} ${top} A ${crown} ${crown} 0 0 1 ${width + 12} ${top + crown} L ${width + 12} ${height - foot} A ${foot} ${foot} 0 0 0 ${width + 12 + foot} ${height} Z`;
  const expanded = outline(0, 12, 12), collapsed = outline(height, 0, 0);
  path.setAttribute('d', expanded); svg.append(path);
  const children = [...navigation.children] as HTMLElement[];
  navigation.append(svg); navigation.dataset.fluidNavigation = '';
  const controls: ReturnType<typeof animate>[] = [];
  const options = { duration: .36, type: spring, bounce: 0, autoplay: false };
  const styles = new Map(children.map(node => [node, node.style.transform]));
  const clear = () => {
    controls.forEach(control => control.cancel()); svg.remove(); delete navigation.dataset.fluidNavigation;
    navigation.style.removeProperty('opacity');
    children.forEach(node => { node.style.transform = styles.get(node) || ''; node.style.removeProperty('opacity'); });
  };
  try {
    controls.push(animate(path, { d: [`path("${collapsed}")`, `path("${expanded}")`] }, options));
    controls.push(animate(navigation, { opacity: [0, 1] }, options));
    for (const node of children) {
      const transform = getComputedStyle(node).transform;
      controls.push(animate(node, { transform: [`translateY(8px) ${transform === 'none' ? '' : transform}`, transform], opacity: [0, 1] }, options));
    }
  } catch { clear(); return null; }
  return { controls, clear };
}

export function workspace(root: HTMLElement, origin: DOMRect, done: () => void, returning = false, entered = done) {
  const main = root.querySelector<HTMLElement>('main')!;
  const navigation = root.querySelector<HTMLElement>('.topbar > .navline');
  root.style.zIndex = '4';
  const box = main.getBoundingClientRect();
  const surface = document.createElement('div');
  surface.className = 'workspace-motion-surface'; surface.setAttribute('aria-hidden', 'true');
  Object.assign(surface.style, { left: `${box.left}px`, top: `${box.top}px`, width: `${box.width}px`, height: `${Math.max(box.height, innerHeight - box.top - 24)}px` });
  document.body.append(surface);
  const start = `translate(${origin.left - box.left}px,${origin.top - box.top}px) scale(${origin.width / box.width},${origin.height / Math.max(box.height, innerHeight - box.top - 24)})`;
  const animations: Animation[] = [];
  const fluid = navigation ? fluidNavigation(navigation) : null;
  let reverseDone: (() => void) | undefined = returning ? done : undefined;
  let direction = returning ? -1 : 1;
  let finished = false;
  const clean = () => { animations.forEach(animation => animation.cancel()); fluid?.clear(); surface.remove(); root.style.removeProperty('z-index'); main.style.removeProperty('opacity'); running.delete(finish); };
  const finish = () => { if (finished) return; finished = true; clean(); if (direction < 0) reverseDone?.(); else entered(); };
  try {
    animations.push(surface.animate([{ transform: start }, { transform: 'translate(0,0) scale(1,1)' }], { duration: timing.page, easing, fill: 'both' }));
    animations.push(main.animate([{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: timing.page, easing, fill: 'both' }));
  } catch { finish(); }
  const watch = () => { const currentDirection = direction; Promise.all([...animations.map(animation => animation.finished), ...(fluid?.controls.map(control => control.finished) || [])]).then(() => { if (direction === currentDirection) finish(); }, () => {}); };
  if (returning) animations.forEach(animation => { animation.currentTime = timing.page; animation.reverse(); });
  fluid?.controls.forEach(control => { control.time = returning ? control.duration : 0; control.speed = direction; control.play(); });
  if (!finished) { running.add(finish); watch(); }
  return { get finished() { return finished; }, finish, forward() {
    direction = 1; animations.forEach(animation => { animation.playbackRate = 1; animation.play(); });
    fluid?.controls.forEach(control => { control.speed = 1; control.play(); }); watch();
  }, reverse(callback: () => void) {
    reverseDone = callback; direction = -1;
    if (!surface.isConnected || quiet()) { finish(); return; }
    // Reverse the existing timeline: no endpoint write and no replacement frame.
    animations.forEach(animation => animation.reverse());
    fluid?.controls.forEach(control => { control.speed = -1; control.play(); }); watch();
  } };
}
function finishAll() { [...running].forEach(finish => finish()); }
preference.addEventListener('change', finishAll);
document.addEventListener('visibilitychange', () => {
  document.documentElement.toggleAttribute('data-motion-hidden', document.hidden);
  if (document.hidden) finishAll();
});
let resizeRevision = 0;
addEventListener('resize', () => {
  finishAll(); const revision = ++resizeRevision; document.documentElement.dataset.motionResize = '';
  requestAnimationFrame(() => requestAnimationFrame(() => { if (revision === resizeRevision) delete document.documentElement.dataset.motionResize; }));
});
(window as any).DashboardMotion = { workspace, tween, timing };
