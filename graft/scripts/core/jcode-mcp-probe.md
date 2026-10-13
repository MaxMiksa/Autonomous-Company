# scripts/core/jcode-mcp-probe.py · [[mcp-configuration-and-probe]] [[mcp-configuration-boot-probe]] [[mcp-probe-invariants]]

Deterministic MCP boot probe that speaks the MCP protocol itself to verify config/manifest parity, tool reachability, destructive-tool denylist coverage, and a real read-only call per server, failing closed on any mismatch.

- ServerError · class · L43-L44 — Exception type distinguishing probe failures (spawn, timeout, protocol error) from normal results so callers can fail closed.
- StdioClient · class · L47-L155 — Minimal newline-delimited JSON-RPC 2.0 client over a spawned server's stdio, enforcing a shared deadline across all I/O.
- __init__ · method · L50-L65 — Spawns the server subprocess with merged env and a monotonic deadline, raising ServerError if the command cannot start.
- _remaining · method · L67-L71 — Returns seconds left before the deadline, raising ServerError on timeout so every blocking call fails closed.
- _send · method · L73-L79 — Writes a JSON-RPC message as a newline-delimited frame to the server's stdin, converting a closed pipe into ServerError.
- _read_msg · method · L81-L102 — Reads and parses the next newline-delimited JSON-RPC message, skipping log noise and detecting server exit/close as ServerError.
- request · method · L104-L116 — Sends a request and waits for the matching response id, raising ServerError on protocol error and ignoring server-initiated notifications.
- notify · method · L118-L119 — Sends a fire-and-forget JSON-RPC notification with no response expected.
- initialize · method · L121-L127 — Performs the MCP initialize handshake with the pinned protocol version and sends the initialized notification.
- list_tools · method · L129-L137 — Pagination-aware tools/list that accumulates all tool names across cursor pages until exhausted.
- call_tool · method · L139-L140 — One-line delegation issuing a tools/call request for a named tool with given arguments.
- close · method · L142-L155 — Closes the server's stdio and terminates the process, escalating to kill if graceful termination times out.
- probe_server · function · L158-L168 — Runs the full handshake (initialize + tools/list) against one server and returns the live client plus sorted tool names, closing on failure.
- judge_readcheck · function · L171-L186 — Judges a read-only call result at protocol level only: fails on isError, empty content, or first text block beginning with an error string.
- main · function · L189-L362 — Orchestrates the whole boot probe: verifies exact server-set parity, denylist coverage, per-server live destructive-tool parity, and that every readcheck actually ran, then writes evidence and returns a fail-closed exit code.
