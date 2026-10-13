# tests/test_directive_writer.py · [[directive-writer-lifecycle]]

Integration test suite that runs the real directive_writer.py script as a subprocess against a temp AC_APP_DIR to verify write/append/archive/status/show behaviors.

- check · function · L22-L25 — Records a pass/fail result for a named assertion, appending the name to FAILS on failure.
- Env · class · L28-L52 — Test harness that sets up a temp app dir with AC_APP_DIR/AC_ACTOR env and runs the writer script as a subprocess.
- __init__ · method · L29-L32 — Builds the subprocess environment with AC_APP_DIR/AC_ACTOR plus overrides and ensures the memories dir exists.
- run · method · L34-L36 — Executes the writer script with given argv and returns the captured subprocess result.
- live · method · L38-L39 — Reads and returns the current human-directive.md body text from the temp app dir.
- audit · method · L41-L43 — Reads and returns the directive-audit.log contents, or empty string if absent.
- show · method · L45-L47 — Runs the writer's show command and parses its key=value stdout lines into a dict.
- f · method · L49-L52 — Writes a text file into the temp app dir and returns its path string for use as a CLI argument.
- main · function · L63-L155 — Runs the full end-to-end scenario covering write, append gates (heading/PENDING/undefined §/size brake), status sha checks, show --sections, and archive resolver/summary behavior.
