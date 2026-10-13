# projects/_archive/snapog/src/og/templates.ts · [[snapog-og-image-service]]

Module defining satori-compatible VNode templates for rendering SnapOG open-graph images, including three visual themes and a dispatcher.

- StyleObject · type · L6-L6 — Type alias for inline style objects passed to satori VNodes.
- VNode · type · L8-L15 — Shape of a satori-compatible element node with a type, style, and children.
- AccentBar · function · L18-L33 — Renders a thin vertical accent-colored bar anchored to the left edge as a visual anchor.
- Header · function · L36-L83 — Builds the top row showing the domain on the left and an optional tag pill on the right, with placeholders when either is absent.
- Footer · function · L86-L133 — Builds the bottom row showing the author on the left and an optional snapog.dev watermark on the right.
- defaultTemplate · function · L136-L202 — General-purpose OG template that lays out accent bar, header, title, description, and footer with theme-aware colors and title-size scaling.
- blogTemplate · function · L205-L286 — Editorial blog OG template with a top accent band, serif typography, and date-focused layout.
- articleTemplate · function · L289-L461 — Minimal high-contrast magazine-style OG template with category row, divider, title, and meta footer.
- buildElement · function · L463-L472 — Dispatches to the template matching the requested params.template, defaulting to the general-purpose template.
