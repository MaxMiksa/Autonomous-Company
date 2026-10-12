---
name: browse-extract MCP gateway client
slug: browse-extract-mcp-gateway-client
type: file
sources:
  - path: tests/test_browse_extract.sh
    hash: 37b269657d3077acf85e81540cd0355f9e97b432f0e6e1d973c2dfc170a887a6
sources_digest: 079a0bb6c7007bc125906c31ea731cf2348652185ae27922be07b0c00c2cb0c9
links: []
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

scripts/ops/browse-extract.py drives a browser MCP gateway over HTTP to grep/read page content, with the critical invariant that the browser tab is always closed even on error paths (verified by a fake gateway test server). Distinct exit codes for distinct failure modes (2 usage, 3 unreachable gateway, 4 tool error), multi-URL handling (one tab opened, one navigate for subsequent URLs), and a truncation message reporting both capped and true content size.
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
