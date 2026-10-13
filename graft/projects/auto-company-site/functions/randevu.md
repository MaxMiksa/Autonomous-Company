# projects/auto-company-site/functions/randevu.js · [[auto-company-site-functions]]

Branded booking front door that redirects recipients to the operator's Google Calendar appointment page, or shows a fallback page when the destination is unconfigured.

- onRequestGet · function · L17-L34 — Redirects to the configured appointment URL, but only when it is a valid https URL; otherwise serves a 503 fallback page instead of guessing a destination.
- page · function · L36-L47 — Renders a branded HTML fallback page with a given title, message, and HTTP status.
