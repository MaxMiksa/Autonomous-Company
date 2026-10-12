# scripts/ops/browse-extract.py · [[browser-extraction-harness]]

One-shot CLI that walks a list of URLs in a single background browser tab, waits for render, greps rendered text, and returns a capped excerpt, replacing multi-turn MCP micro-step chains.

- Gateway · class · L45-L83 — Thin JSON-RPC client over the BrowserOS MCP gateway that tracks the MCP session id and handles SSE-framed responses.
- __init__ · method · L46-L49 — Stores the gateway URL and per-request timeout and initializes the session id to None.
- post · method · L51-L67 — Sends a JSON-RPC request to the gateway, persists the returned mcp-session-id header, and parses either a JSON body or SSE data frames into a dict.
- call · method · L69-L77 — Invokes a named MCP tool with arguments and flattens the response content into a single text string plus an error flag.
- handshake · method · L79-L83 — Performs the MCP initialize/initialized handshake so subsequent tool calls are accepted by the gateway.
- clip · function · L86-L91 — Truncates a text excerpt to a byte cap, returning the clipped string and whether truncation occurred.
- extract · function · L94-L119 — For one page, waits for render (text or fixed time), runs server-side grep over rendered content, and reads a capped excerpt, reporting wait timeouts as inconclusive.
- ToolError · class · L122-L123 — Marker exception used to abort the URL walk mid-flow and surface a tool error with exit code 4.
- main · function · L126-L201 — Parses args, opens one background tab, walks every URL in order extracting per-page results, and closes the tab (or keeps it) while mapping failures to exit codes.
