import { tween, timing, quiet, reveal, positions, layout, reconcile } from "./motion";
import { Selection } from "./selection";
import * as React from "react";
import { createRoot, type Root } from "react-dom/client";
import { flushSync } from "react-dom";
import { Button } from "./components/ui/button";
import { Dialog, DialogContent } from "./components/ui/dialog";
import { AlertDialog, AlertDialogContent } from "./components/ui/alert-dialog";
import { Sheet, SheetContent } from "./components/ui/sheet";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "./components/ui/dropdown-menu";
import { Tabs, TabsList, TabsTrigger } from "./components/ui/tabs";
import { ToggleGroup, ToggleGroupItem } from "./components/ui/toggle-group";
import { cn } from "./lib/utils";
import { element, mountControls, primitives, buttonProps, notifications, notify, loading, groupTabs, Hint, productSwitcher, alertMessage, disposeControls } from "./controls";
import { Skeleton } from "./components/ui/skeleton";
import { Alert } from "./components/ui/alert";
import { ChevronDown, EllipsisVertical } from "lucide-react";

type ModalElement = HTMLElement & { showModal: () => void; close: () => void; open: boolean };
type MenuItem = { label: string; disabled?: boolean; reason?: string; danger?: boolean; action: () => void; focusKey?: string };
type MenuProps = { id: string; label: string; items: MenuItem[] };
function createDashboardUI(document: Document) {
const roots: Root[] = [];
const closers: (() => void)[] = [];
const ownRoot = (host: HTMLElement) => { const root = createRoot(host); roots.push(root); return root; };
const menus = new Map<string, { host: HTMLSpanElement; root: Root }>();

// The controllers own records and form values. The shared UI owns modal/menu
// interaction; a stable DOM slot preserves those records when a portal opens.
function installModal(original: HTMLElement, sheet = false) {
  const id = original.id;
  const titleId = original.getAttribute("aria-labelledby") || undefined;
  const confirmation = id === "confirmDialog" || original.dataset.confirmation === "true";
  const host = document.createElement("span");
  host.dataset.uiRoot = sheet ? "sheet" : "dialog";
  document.body.append(host);
  const root = ownRoot(host);
  let open = false;
  let returnFocus: HTMLElement | null = null;
  let content: HTMLDivElement | null = null;
  let exiting: { surface: HTMLElement; slot: HTMLElement; overlay: HTMLElement | null } | null = null;
  let revision = 0;
  let entrance: { visual: { opacity: string; transform: string; rect: DOMRect } | null } | null = null;
  const enter = (node: HTMLDivElement) => {
    if (!entrance) return;
    const visual = entrance.visual; entrance = null;
    const surface = node.parentElement!;
    const backdrop = surface.previousElementSibling as HTMLElement;
    const target = sheet ? 'none' : 'translate(-50%,-50%)';
    surface.style.transition = 'none';
    if (visual) {
      surface.style.transform = target;
      const box = surface.getBoundingClientRect();
      const matrix = new DOMMatrix(getComputedStyle(surface).transform);
      matrix.e += visual.rect.left - box.left; matrix.f += visual.rect.top - box.top;
      Object.assign(surface.style, { opacity: visual.opacity, transform: matrix.toString() });
    } else Object.assign(surface.style, { opacity: '0', transform: sheet ? 'translateX(100%)' : `${target} translateY(6px)` });
    tween(surface, { opacity: '1', transform: target }, sheet ? timing.drawer : timing.local, () => { surface.style.removeProperty('opacity'); surface.style.removeProperty('transform'); });
    if (backdrop?.matches('[data-slot$="overlay"]')) { backdrop.style.opacity = visual?.opacity || '0'; tween(backdrop, { opacity: '1' }, timing.local); }
  };
  original.dataset.dialogId = id;
  if (sheet) original.hidden = true;
  const parkExit = () => {
    if (!exiting) return;
    while (exiting.slot.firstChild) original.append(exiting.slot.firstChild);
    exiting.surface.remove(); exiting.overlay?.remove(); exiting = null; original.id = id;
  };
  const change = (next: boolean, instant = false) => {
    if (instant) { ++revision; parkExit(); }
    if (next === open) return;
    const token = ++revision;
    const liveSurface = content?.parentElement;
    const liveOverlay = liveSurface?.previousElementSibling as HTMLElement | null;
    const previous = exiting?.surface || liveSurface;
    const visual = previous ? { opacity: getComputedStyle(previous).opacity, transform: getComputedStyle(previous).transform, rect: previous.getBoundingClientRect() } : null;
    const anchor = liveSurface ? { left: getComputedStyle(liveSurface).left, top: getComputedStyle(liveSurface).top, width: getComputedStyle(liveSurface).width, height: getComputedStyle(liveSurface).height } : null;
    const surface = !next && liveSurface ? liveSurface.cloneNode(false) as HTMLElement : null;
    const overlay = !next && liveOverlay?.matches('[data-slot$="overlay"]') ? liveOverlay.cloneNode(false) as HTMLElement : null;
    const exitSlot = !next && content ? content.cloneNode(false) as HTMLElement : null;
    const overlayOpacity = liveOverlay ? getComputedStyle(liveOverlay).opacity : '1';
    const resuming = next && Boolean(exiting);
    if (next) parkExit();
    if (next && !resuming) returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    entrance = next && !quiet() && !instant ? { visual } : null;
    open = next;
    flushSync(render);
    if (next && content) enter(content);
    else if (!next) {
      if (surface && exitSlot && visual && !quiet() && !instant) {
        original.id = `${id}-parking`; exitSlot.id = id;
        while (original.firstChild) exitSlot.append(original.firstChild);
        surface.append(exitSlot); surface.inert = true; surface.setAttribute('aria-hidden', 'true'); surface.dataset.motionExit = '';
        // Releasing the modal scroll lock must not move the exit surface.
        surface.style.pointerEvents = 'none'; Object.assign(surface.style, anchor, { opacity: visual.opacity, transform: visual.transform });
        surface.removeAttribute('role'); surface.dataset.state = 'closed';
        if (overlay) { overlay.style.pointerEvents = 'none'; overlay.style.opacity = overlayOpacity; overlay.setAttribute('aria-hidden', 'true'); document.body.append(overlay); }
        document.body.append(surface); exiting = { surface, slot: exitSlot, overlay }; bind(exitSlot);
        tween(surface, { opacity: '0', transform: sheet ? 'translateX(100%)' : 'translate(-50%,-50%) translateY(6px)' }, sheet ? timing.drawer : timing.local,
          () => { if (token === revision) parkExit(); });
        if (overlay) tween(overlay, { opacity: '0' }, timing.local);
      }
      original.dispatchEvent(new Event("close"));
    }
  };
  const attach = (node: HTMLDivElement | null) => {
    if (node) {
      original.id = `${id}-parking`;
      node.id = id;
      while (original.firstChild) node.append(original.firstChild);
      content = node;
      bind(node);
      enter(node);
    } else if (content) {
      while (content.firstChild) original.append(content.firstChild);
      original.id = id;
      content = null;
    }
  };
  const bind = (node: HTMLElement) => {
    Object.defineProperty(node, "open", { configurable: true, get: () => open });
    (node as ModalElement).showModal = () => change(true);
    (node as ModalElement).close = () => change(false);
  };
  function render() {
    const common = {
      className: cn("ac-overlay-content", sheet ? "ac-sheet" : "ac-dialog", original.className),
      "data-dialog-id": id,
      "aria-labelledby": titleId,
      "aria-describedby": undefined,
      showCloseButton: false,
      container: document.body,
      onInteractOutside: (event: CustomEvent<{ originalEvent: Event }>) => {
        // Shell controls retain their DOM identity when moved into this portal.
        // Test containment against DOM, not their original React ancestry.
        const target = event.detail.originalEvent.target as Node;
        if (!target.isConnected || content?.contains(target)) event.preventDefault();
      },
      onOpenAutoFocus: (event: Event) => {
        event.preventDefault();
        const heading = titleId ? document.getElementById(titleId) : null;
        const target = confirmation ? content?.querySelector<HTMLElement>('[data-safe-action], .dialog-close, button:not(.danger):not(:disabled)')
          : id === "newWorkDialog" ? heading
          : content?.querySelector<HTMLElement>(sheet ? "button:not(:disabled)" : "input:not([type=radio]):not(:disabled), textarea:not(:disabled), select:not(:disabled), button:not(:disabled)");
        if (target === heading && heading) heading.tabIndex = -1;
        (target || content)?.focus();
      },
      onCloseAutoFocus: (event: Event) => {
        event.preventDefault();
        const replacement = returnFocus?.dataset.focusKey ? [...document.querySelectorAll<HTMLElement>("[data-focus-key]")].find(node => node.dataset.focusKey === returnFocus?.dataset.focusKey) : null;
        const target = returnFocus?.isConnected ? returnFocus : replacement || document.querySelector<HTMLElement>("#catalogHeading, #mainContent");
        if (target) { if (!target.matches("button,a,input,select,textarea,[tabindex]")) target.tabIndex = -1; target.focus({ preventScroll: true }); }
      },
    };
    const { showCloseButton, onInteractOutside, ...alertProps } = common;
    const slot = <div ref={attach} className="ac-owned-content" data-dialog-id={id} data-confirmation={confirmation || undefined} />;
    root.render(sheet
      ? <Sheet open={open} onOpenChange={change}><SheetContent {...common}>{slot}</SheetContent></Sheet>
      : confirmation ? <AlertDialog open={open} onOpenChange={change}><AlertDialogContent {...alertProps} aria-describedby={original.getAttribute("aria-describedby") || "confirmMessage"}>{slot}</AlertDialogContent></AlertDialog>
      : <Dialog open={open} onOpenChange={change}><DialogContent {...common}>{slot}</DialogContent></Dialog>);
  }
  closers.push(() => change(false, true));
  bind(original);
  flushSync(render);
}

function ProductMenu({ id, label, items }: MenuProps) {
  const trigger = React.useRef<HTMLButtonElement>(null);
  return <DropdownMenu>
    <Hint label={label}><DropdownMenuTrigger asChild>
      <Button ref={trigger} variant="ghost" size="icon-sm" className="more-button" aria-label={label} data-focus-key={`entry:${id}:more`}><EllipsisVertical aria-hidden="true" /></Button>
    </DropdownMenuTrigger></Hint>
    <DropdownMenuContent className="ac-menu" align="end" sideOffset={4}>
      {items.map((item, index) => <React.Fragment key={index}>{item.danger && !items[index - 1]?.danger && <DropdownMenuSeparator />}<DropdownMenuItem disabled={item.disabled} title={item.reason}
        data-focus-key={item.focusKey} className={item.danger ? "ac-danger" : ""}
        onSelect={() => { setTimeout(() => { trigger.current?.focus({ preventScroll: true }); item.action(); }, 0); }}>
        <span>{item.label}{item.disabled && item.reason && <small className="ac-menu-reason">{item.reason}</small>}</span>
      </DropdownMenuItem></React.Fragment>)}
    </DropdownMenuContent>
  </DropdownMenu>;
}

function menu(props: MenuProps) {
  let entry = menus.get(props.id);
  if (!entry) {
    const host = document.createElement("span");
    host.className = "action-menu";
    entry = { host, root: createRoot(host) };
    menus.set(props.id, entry);
  }
  flushSync(() => entry.root.render(<ProductMenu {...props} />));
  return entry.host;
}
function retainMenus(ids: string[]) {
  const retained = new Set(ids);
  for (const [id, entry] of menus) if (!retained.has(id)) {
    entry.root.unmount();
    menus.delete(id);
  }
}

let updateFilter: ((value: string) => void) | undefined;
function selectFilter(value: string) { updateFilter?.(value); }
function CatalogFilters({ node }: { node: Element }) {
  const [value, setValue] = React.useState("all");
  const group = React.useRef<HTMLDivElement>(null);
  const [selection, setSelection] = React.useState({ x: 0, y: 0, width: 0, height: 0 });
  React.useLayoutEffect(() => {
    const container = group.current;
    if (!container) return;
    const measure = () => {
      const active = container.querySelector<HTMLButtonElement>('[data-state="on"]');
      if (!active) return;
      const next = { x: active.offsetLeft, y: active.offsetTop, width: active.offsetWidth, height: active.offsetHeight };
      setSelection(previous => Object.keys(next).every(key => previous[key as keyof typeof next] === next[key as keyof typeof next]) ? previous : next);
    };
    measure();
    const resize = new ResizeObserver(measure);
    resize.observe(container);
    container.querySelectorAll('button').forEach(button => resize.observe(button));
    return () => resize.disconnect();
  }, [value]);
  updateFilter = next => { if (next !== value) flushSync(() => setValue(next)); };
  return <ToggleGroup ref={group} id="filters" className="filters" type="single" value={value}
    aria-label={node.getAttribute("aria-label") || undefined} data-i18n-aria="filterProducts"
    onValueChange={next => { if (next) setValue(next); }}>
    <span className="filter-selection" aria-hidden="true" style={{ transform: `translate(${selection.x}px, ${selection.y}px)`, width: selection.width, height: selection.height }} />
    {[...node.children].map(button => <ToggleGroupItem key={button.getAttribute("data-filter")!}
      value={button.getAttribute("data-filter")!} data-filter={button.getAttribute("data-filter")}
      className="filter-button">
      <span data-i18n={button.firstElementChild?.getAttribute("data-i18n") || undefined}>{button.textContent}</span>
    </ToggleGroupItem>)}
  </ToggleGroup>;
}

function ProfileMenu() {
  const [open, setOpen] = React.useState(false);
  const trigger = React.useRef<HTMLButtonElement>(null);
  const chinese = document.documentElement.lang === "zh-CN";
  return <DropdownMenu open={open} onOpenChange={setOpen}>
    <DropdownMenuTrigger asChild>
      <Button ref={trigger} id="profileButton" variant="ghost" size="sm" className="profile-button" aria-label={chinese ? "本机" : "Local"} data-i18n-aria="localWorkspace">
        <span className="profile-avatar" aria-hidden="true" data-i18n="localInitial">{chinese ? "本" : "L"}</span>
        <span data-i18n="localWorkspace">{chinese ? "本机" : "Local"}</span>
        <ChevronDown className="profile-chevron" aria-hidden="true" />
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent className="ac-menu local-menu" aria-label={chinese ? "本机" : "Local"} align="end" sideOffset={4} />
  </DropdownMenu>;
}

// Render the authored shell once with real shadcn primitives. Record containers
// and uncontrolled form values are then owned by the existing controllers. Never
// re-render this root: interactive islands below have separate, bounded roots.
function mountShell() {
  const propNames: Record<string, string> = { class: "className", for: "htmlFor", tabindex: "tabIndex", readonly: "readOnly", autocomplete: "autoComplete", spellcheck: "spellCheck", autofocus: "autoFocus", maxlength: "maxLength", rowspan: "rowSpan", colspan: "colSpan", "stroke-width": "strokeWidth", "stroke-linecap": "strokeLinecap", "stroke-linejoin": "strokeLinejoin", viewbox: "viewBox" };
  const booleanProps = new Set(["hidden", "disabled", "required", "multiple", "readOnly", "autoFocus", "open"]);
  function convert(node: Node, key: number): React.ReactNode {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent;
    if (!(node instanceof Element)) return null;
    const tag = node.tagName.toLowerCase();
    if (tag === "script") return null;
    if (node.id === "profileButton") return <ProfileMenu key={key} />;
    if (node.id === "filters") return <CatalogFilters key={key} node={node} />;
    const props: Record<string, unknown> = { key };
    for (const attr of node.attributes) {
      const name = propNames[attr.name] || attr.name;
      if (name.startsWith("on")) continue;
      if (name === "style") {
        const style = (node as HTMLElement).style;
        props.style = Object.fromEntries([...style].map(property => [property.startsWith("--") ? property : property.replace(/-([a-z])/g, (_, char: string) => char.toUpperCase()), style.getPropertyValue(property)]));
      } else if (name === "checked") props.defaultChecked = true;
      else if (name === "selected") continue;
      else if (name === "value" && tag === "input") props.defaultValue = attr.value;
      else props[name] = booleanProps.has(name) ? true : attr.value;
    }
    let component: React.ElementType = primitives[tag] || tag as React.ElementType;
    if (tag === "button") Object.assign(props, buttonProps(node.className));
    else if (tag === "textarea") props.defaultValue = node.textContent;
    else if (tag === "select") props.defaultValue = (node as HTMLSelectElement).value;
    else if (tag === "input" && ["checkbox", "radio"].includes(node.getAttribute("type") || "")) component = "input";
    else if (tag === "details") { component = "div"; props["data-disclosure"] = ""; }
    else if (tag === "summary") { component = Button; props.variant = "ghost"; props.type = "button"; props.className = `${props.className || ""} disclosure-trigger`; }
    else if (["actionError", "connectionNotice", "connectionError", "actionStatus", "errorState"].includes(node.id)) { component = Alert; if (node.getAttribute("role") === "alert") props.variant = "destructive"; }
    const children = [...node.childNodes].map(convert);
    if (node.id === "loadingState") return <div {...props}>{children}<Skeleton className="h-8 w-full" /></div>;
    const control = React.createElement(component, props, ...(["input", "textarea", "img", "hr", "br", "link", "meta"].includes(tag) ? [] : children));
    return tag === "button" && node.hasAttribute("title") && node.hasAttribute("aria-label") ? <Hint key={key} label={node.getAttribute("aria-label")!}>{control}</Hint> : control;
  }
  const content = [...document.body.childNodes].map(convert);
  const shell = ownRoot(document.body);
  flushSync(() => shell.render(<>{content}</>));
}

let updateTab: ((value: string) => void) | undefined;
function installTabs() {
  const container = document.querySelector<HTMLElement>("nav.tabs");
  if (!container) return;
  const label = container.getAttribute("aria-label") || "";
  const options = [...container.querySelectorAll<HTMLElement>("[data-tab]")].map(node => ({
    value: node.dataset.tab!, id: node.id, label: node.textContent,
    key: node.dataset.i18n, panel: node.getAttribute("aria-controls") || undefined,
  }));
  container.removeAttribute("role");
  container.className = "ac-tabs-host";
  const root = ownRoot(container);
  function JournalTabs() {
    const [value, setValue] = React.useState(options[0].value);
    updateTab = (next) => { if (next !== value) flushSync(() => setValue(next)); };
    return <Tabs className="ac-tabs" activationMode="manual" value={value} onValueChange={next => {
      document.dispatchEvent(new CustomEvent("ui-tab-change", { detail: next }));
    }}>
      <TabsList variant="line" className="tabs motion-selection-list" aria-label={label}>
        <Selection value={value} />
        {options.map(option => <TabsTrigger key={option.value} value={option.value} id={option.id}
          className="tab" data-tab={option.value} data-i18n={option.key} aria-controls={option.panel}>{option.label}</TabsTrigger>)}
      </TabsList>
    </Tabs>;
  }
  flushSync(() => root.render(<JournalTabs />));
}
function selectTab(value: string) { updateTab?.(value); }

const api = { element, mountControls: (scope: ParentNode = document.body) => mountControls(scope), notify, loading, groupTabs, reveal, positions, layout, reconcile,
  productSwitcher: (entries: Parameters<typeof productSwitcher>[0], current: string, labels: Parameters<typeof productSwitcher>[2], reset = false) => productSwitcher(entries, current, labels, reset, document.body), alertMessage, menu, retainMenus, selectTab, selectFilter,
  pause() { closers.forEach(close => close()); document.body.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true })); },
  dispose() { closers.forEach(close => close()); retainMenus([]); disposeControls(document.body); roots.reverse().forEach(root => root.unmount()); },
};
mountShell();
installTabs();
mountControls(document.body);
productSwitcher([], "", { search: "", empty: "", current: "" }, false, document.body);
document.querySelectorAll<HTMLElement>("dialog").forEach(node => installModal(node));
const queue = document.getElementById("queueDrawer");
if (queue) installModal(queue, true);
document.documentElement.dataset.ui = "shadcn";
return api;
}
declare global {
  interface Window { createDashboardUI: typeof createDashboardUI; DashboardUI: ReturnType<typeof createDashboardUI> }
}
window.createDashboardUI = createDashboardUI;
notifications();
