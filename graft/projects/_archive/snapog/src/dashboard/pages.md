# projects/_archive/snapog/src/dashboard/pages.ts

Module defining all HTML page templates and shared CSS for the SnapOG dashboard and landing site.

- layout · function · L340-L355 — Wraps a page body in the full HTML document shell with shared CSS and metadata.
- nav · function · L357-L367 — Renders the sticky top navigation bar with logo and links.
- footer · function · L369-L376 — Renders the site footer with branding text.
- landingPage · function · L378-L588 — Builds the marketing landing page with hero, live OG preview, API docs, and pricing sections.
- registerPage · function · L590-L628 — Renders the API key registration form, optionally showing an error and preselected tier.
- keyCreatedPage · function · L630-L700 — Displays the newly generated API key once, with email, tier, and waitlist notice.
- dashboardPage · function · L702-L789 — Renders the authenticated dashboard showing the API key, usage meter, and recent activity.
- errorPage · function · L791-L805 — Renders a styled error page for a given HTTP status code and message.
