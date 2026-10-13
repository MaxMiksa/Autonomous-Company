# projects/headinspect/src/render.ts · [[headinspect-renderer]]

Single-template HTML renderer that turns an InspectReport into a full page, badge SVG, and embed snippets with inline CSS, no client-side framework.

- escapeHtml · function · L16-L23 — Escapes HTML-special characters in user-supplied strings so report values and URLs cannot inject markup.
- badgeColor · function · L27-L36 — Maps a grade letter to the shields.io-style hex color used for the badge message segment.
- textWidth · function · L39-L41 — Estimates rendered text width from character count for badge segment sizing.
- renderBadge · function · L46-L79 — Builds a shields.io-flavoured flat SVG badge with pre-computed segment widths and textLength-stretched labels.
- renderEmbedBlock · function · L81-L94 — Generates the embed section with Markdown and HTML snippets for a live badge pointing at the report.
- renderReport · function · L96-L137 — Groups inspected headers by category and renders the report body with grade summary, reasons, and redirects.
- hostOf · function · L139-L141 — Extracts the hostname from a URL, falling back to the raw string on parse failure.
- socialMeta · function · L143-L176 — Builds canonical, description, and Open Graph/Twitter meta tags, deriving title and description from the report grade.
- renderPage · function · L178-L242 — Assembles the full HTML page including form, report/error body, embed block, and inline CSS.
