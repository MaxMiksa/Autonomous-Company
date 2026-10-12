# tests/test_compact_yol.py · [[compact-ritual-path-resolution]]

Test suite verifying compact_yol derives ritual file paths from repo name and never raises exceptions.

- check · function · L31-L36 — Records a named assertion result, printing ok/FAIL and appending failures to the global list.
- _load · function · L39-L43 — Loads the compact_yol module from its script path for testing.
- git · function · L46-L49 — Runs a git command in a given directory with safe identity and no GPG signing.
- yeni_repo · function · L52-L59 — Creates a fresh git repository with one committed file in a temp directory.
- temiz_env · function · L62-L63 — Returns the environment with all COMPACT_* override variables removed.
- zaman_asimi · function · L120-L122 — Stub that records kwargs and raises TimeoutExpired to simulate a git timeout.
- git_yok · function · L124-L125 — Stub that raises FileNotFoundError to simulate git being absent.
- test_hepsi_gecti · function · L163-L164 — Fails the pytest run if any recorded check failed.
