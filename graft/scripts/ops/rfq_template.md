# scripts/ops/rfq_template.py · [[rfq-send-pipeline]]

Module defining the OPEX RFQ email content (subject, plain-text and HTML bodies, scope text, signature, and CID logo attachment) that rfq-send.py imports for sending indicative price requests.

- _read_sig · function · L53-L57 — Reads the HTML signature file from disk, returning empty string if it cannot be opened.
- _logo_b64 · function · L60-L62 — Extracts the base64 PNG logo payload from the signature HTML for use as a CID inline attachment.
- _html_signature · function · L68-L76 — Extracts the signature body and rewrites the base64 logo data-URI to a cid: reference so Gmail renders the logo inline.
- attachments · function · L82-L87 — Builds the CID inline logo attachment list for the send payload, returning an empty list when no logo is available.
- subject · function · L98-L99 — Produces the RFQ email subject line naming the procurement category.
- body · function · L102-L119 — Builds the plain-text RFQ request email, anonymizing the venture and listing the requested pricing details plus the signature.
- body_html · function · L122-L142 — Builds the HTML RFQ email, HTML-escaping the scope text and embedding the HTML signature with the CID logo.
