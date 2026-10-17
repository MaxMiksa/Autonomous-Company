"""Allowlisted bundled documentation for the product center."""

import html
from pathlib import Path
import sys

CORE = Path(__file__).resolve().parents[1] / "scripts/core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))
import localization


DOCUMENTS = {
    "readme": ("README.md", "README-ZH.md"),
    "troubleshooting": ("docs/troubleshooting.md", None),
    "setup": ("docs/windows-setup.md", None),
    "language": ("i18n/en/README.md", "i18n/README.md"),
}


def documentation_page(name: str, framework_root: Path, language: str) -> str:
    """Only expose bundled documentation, never arbitrary repository files."""
    if name not in DOCUMENTS or language not in {"en", "zh-CN"}:
        raise ValueError("invalid documentation request")
    source, chinese = DOCUMENTS[name]
    framework_root = Path(framework_root)
    if chinese is not None:
        selected = chinese if language == "zh-CN" else source
    else:
        selected = localization.resource_map(framework_root, language).get(source, source)
    allowed = {source, chinese, f"i18n/en/{source}", f"i18n/zh-CN/{source}"}
    if selected not in allowed:
        raise ValueError("invalid documentation path")
    path = framework_root / selected
    # Reject symlinks even when they point back inside the checkout, where a
    # private local configuration could otherwise be exposed as a document.
    if any((framework_root / Path(*Path(selected).parts[:index])).is_symlink()
           for index in range(1, len(Path(selected).parts) + 1)):
        raise ValueError("documentation must not use symlinks")
    path.resolve().relative_to(framework_root.resolve())
    content = path.read_text(encoding="utf-8")
    if language == "zh-CN":
        back = "返回产品中心"
        labels = {"readme": "使用指南", "troubleshooting": "故障排查", "setup": "Windows 安装", "language": "语言设置"}
    else:
        back = "Back to product center"
        labels = {"readme": "Guide", "troubleshooting": "Troubleshooting", "setup": "Windows setup", "language": "Language settings"}
    navigation = f'<a href="/center">{back}</a>' + "".join(
        f' <a href="/docs/{key}">{label}</a>' for key, label in labels.items()
    )
    return (
        f'<!doctype html><html lang="{language}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'style-src &#39;self&#39; &#39;unsafe-inline&#39;; base-uri &#39;none&#39;">'
        '<link rel="stylesheet" href="/design-system.css">'
        f'<title>{labels[name]}</title><style>body{{max-width:960px;margin:32px auto;padding:0 20px;'
        'font:var(--text-body)/1.65 var(--font-ui);color:var(--ui-foreground);background:var(--ui-background)}'
        'h1{font-size:var(--text-page)}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}'
        'a{color:var(--ui-link);text-underline-offset:3px}a:focus-visible{outline:2px solid currentColor;outline-offset:4px}'
        'nav{display:flex;gap:16px;flex-wrap:wrap}</style></head>'
        f'<body><nav>{navigation}</nav><main><h1>{labels[name]}</h1>'
        f'<pre>{html.escape(content)}</pre></main></body></html>'
    )

