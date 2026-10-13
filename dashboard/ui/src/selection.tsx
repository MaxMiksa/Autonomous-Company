import * as React from 'react';

// The indicator belongs to the list; buttons retain their native focus behavior.
export function Selection({ value, vertical = false }: { value: string; vertical?: boolean }) {
  const indicator = React.useRef<HTMLSpanElement>(null);
  React.useLayoutEffect(() => {
    const node = indicator.current, list = node?.parentElement;
    if (!node || !list) return;
    const measure = () => {
      const active = list.querySelector<HTMLElement>('[data-state=active]');
      if (!active) return;
      Object.assign(node.style, {
        transform: `translate(${vertical ? list.clientWidth - 2 : active.offsetLeft}px,${vertical ? active.offsetTop : active.offsetTop + active.offsetHeight + 3}px)`,
        width: `${vertical ? 2 : active.offsetWidth}px`, height: `${vertical ? active.offsetHeight : 2}px`,
      });
    };
    measure();
    const observer = new ResizeObserver(measure); observer.observe(list);
    list.querySelectorAll('button').forEach(button => observer.observe(button));
    return () => observer.disconnect();
  }, [value, vertical]);
  return <span ref={indicator} className="tab-selection" aria-hidden="true" />;
}
