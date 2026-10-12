# tests/test_consensus_prune.py · [[consensus-document-pruning]]

Test suite for the consensus-prune.py v2 script, covering v1 fixtures (KEEP=12) and v2 spec cases (p)-(z) including prod-copy verification, tail/head pruning, archive byte-exactness, guard integration, and fail-closed skip/alarm behavior.

- check · function · L24-L27 — Records a pass/fail result for a named test assertion and accumulates failures for the final summary.
- skip · function · L30-L31 — Prints a SKIP line for a test that cannot run (e.g. missing prod fixture).
- newapp · function · L34-L37 — Creates a fresh temporary app directory with the expected memories/logs/docs/operations subdirectories for a test run.
- consensus · function · L40-L41 — Returns the path to the consensus.md file inside a given app directory.
- entry · function · L44-L49 — Builds a single consensus cycle entry bullet padded with filler to a target byte size (default 1800) to simulate realistic large entries.
- para · function · L52-L56 — Builds a paragraph body padded to a target byte size for v2 fixtures.
- doc · function · L59-L70 — Builds a v1 canonical-only consensus fixture whose only entries are What We Did bullets.
- doc2 · function · L73-L95 — Builds a v2 full canonical consensus fixture with paragraph entries, optional head/tail sections, and Key Decisions padded to keep the file over the 70000-byte threshold.
- run · function · L101-L110 — Runs the consensus-prune.py script as a subprocess with the given cycle, app dir, env overrides, dry-run flag, and v1/v2 base env.
- guard · function · L113-L116 — Invokes the ledger-guard.py script as a subprocess against an app dir for a given cycle and returns its stdout.
- headers · function · L119-L120 — Extracts all top-level '## ' header lines from text.
- section · function · L123-L127 — Returns the body of the nth occurrence of a given '## ' header section, excluding the header line.
- non_cycle_paras · function · L130-L131 — Filters a section body down to paragraphs that are not '**Cycle N' entries.
- archive_pieces · function · L134-L158 — Parses the archive file into individual pieces (whole sections or single removed paragraphs/bullets), merging a lone (Prior...) lead-in line with the following **Cycle entry into one piece.
- full · function · L375-L377 — A test helper function (definition truncated in the file view).
- prior_para · function · L410-L411 — Builds a (Prior...) lead-in paragraph fixture of a given byte size for v2 test cases.
- ec_doc · function · L467-L472 — Builds an Execution Controls fixture document for v2 test cases.
