# projects/headinspect/src/inspect.ts · [[headinspect-header-inspector]]

Pure functions module that categorizes HTTP response headers, generates per-header commentary and sanity flags, summarizes Set-Cookie without exposing raw values, and grades overall header security with a letter score.

- Category · type · L4-L11 — Union type enumerating the header buckets used to group and order headers in reports.
- HeaderEntry · interface · L13-L19 — Data holder describing one categorized header with its commentary and sanity flag.
- RedirectHop · interface · L21-L25 — Data holder recording one redirect step's status and endpoints.
- Grade · interface · L27-L31 — Data holder for the security letter grade, numeric score, and human-readable reasons.
- InspectReport · interface · L33-L42 — Data holder aggregating the full inspection result: URL, status, redirects, headers, grade, and timing.
- categorize · function · L86-L95 — Maps a header name to its report bucket (security/cache/content/compat/cors/cookie/other).
- HeaderJudgement · interface · L99-L102 — Data holder for a header's one-line commentary and sanity flag.
- judge · function · L104-L213 — Produces per-header commentary and a sanity flag, flagging permissive or fingerprinting-revealing values.
- summarizeSetCookies · function · L217-L231 — Counts Set-Cookie entries and tallies Secure/HttpOnly/SameSite flags, returning a privacy-safe summary string.
- categorizeHeaders · function · L235-L271 — Converts raw Headers into deduplicated, categorized HeaderEntry list sorted by bucket then name.
- grade · function · L275-L356 — Computes a 0-100 security score and letter grade from header presence and soundness, with penalties and a CSP cap.
- has · function · L277-L277 — Trivial lookup helper checking whether a header name is present in the entry map.
- good · function · L278-L278 — Trivial lookup helper checking whether a header is present and flagged as sound.
