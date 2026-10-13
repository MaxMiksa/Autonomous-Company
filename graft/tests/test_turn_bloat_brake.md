# tests/test_turn_bloat_brake.py · [[turn-economy-bloat-control]]

Test suite for the turn-bloat-brake script, verifying streak counting, alarm threshold crossing, hard feedback, reset behavior, env-configurable K, and kill switch.

- newapp · function · L15-L18 — Creates a fresh temp app directory with a logs subdir for each test scenario.
- rec · function · L21-L27 — Runs the script in --record mode with a given cycle and verdict, returning exit code and stdout.
- fb · function · L30-L36 — Runs the script in --feedback mode for an app and returns its stdout.
- consecutive · function · L39-L40 — Reads the persisted consecutive-bloat count from the app's state JSON.
- check · function · L43-L46 — Prints PASS/FAIL for a test condition and records failures for the final exit status.
