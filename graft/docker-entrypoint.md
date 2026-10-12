---
name: docker-entrypoint
slug: docker-entrypoint
type: file
sources:
  - path: docker-entrypoint.sh
    hash: fbc2010d8d1d9dda2bc7ebd72fba1d674136624f968ff2f453bf7bbb894de017
sources_digest: 4859f8b1dfb24f857df1d999107a7d92d7c4d14a2c247976ae81cbb021029d23
links:
  - to: set-e-lint-invariant
    relation: validates
    description: must pass the lint
generator:
  version: 1
covers: []
---
<!-- context:generated:start -->
## Summary

docker-entrypoint.sh parses runtime.env and must pass the set -e lint (its runtime.env parser uses a safe redirect-fed loop form that a wider lint would false-positive on).

## Related

- validates [[set-e-lint-invariant]] — must pass the lint
<!-- context:generated:end -->

## Notes

_Anything written below the generated block is preserved when the graph is regenerated._
