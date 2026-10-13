# tests/test_ledger_guard.py · [[ledger-guard]]

Test suite for the ledger-guard script, exercising alarm, exemption, backup-rotation, and kill-switch behaviors across scenarios.

- newapp · function · L15-L20 — Creates a fresh temporary app directory with the docs/operations, memories, and logs subdirectories needed by the script.
- ledger · function · L23-L24 — Returns the path to the test ledger markdown file inside a given app directory.
- run · function · L27-L33 — Invokes the ledger-guard script as a subprocess with a given cycle and app dir, returning its return code and stdout.
- body · function · L36-L42 — Builds a synthetic ledger markdown body with a given number of sections and OPEX rows, plus optional trailing text.
- check · function · L45-L48 — Prints a PASS/FAIL line for a test condition and records failures for the final exit status.
