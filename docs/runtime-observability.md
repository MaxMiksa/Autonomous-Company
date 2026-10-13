# Runtime observations and cycle work reports

The Codex adapter projects its JSONL stream into `logs/<cycle-id>.events.jsonl`.
The dashboard reads that stream while the cycle runs. No extra model calls or
AI summaries are used. Original engine output, exit status and supervision
remain authoritative; observation I/O failure does not turn a task into a
success or abort its CLI invocation.

## What is observed

- Command start/end and reported exit code, file-change paths, process/turn events.
- Agent messages, explicitly treated as work reports rather than verified facts.
- Model and reasoning effort from the exact thread's local session context,
  validated against thread ID and framework cwd. No context means unknown.
- Event times are receive times, not reconstructed task timestamps. Only the
  last twelve visible events are shown; original cycle logs remain accessible.

The local session file format is an optional, version-sensitive Codex capability.
The verified CLI version is 0.155.0. Other engines retain the existing dashboard
and report observation data as unavailable. This is not complete child-agent
telemetry, a live token billing feed, or product acceptance.

Limits: event lines 256 KiB, projection 2,000 events / about 2 MiB per cycle;
dashboard reads at most 30 recent cycles, bounded head/tail and 80 events each.
Oversize/invalid output is omitted and interruptions/partial records remain
explicit. Reasoning bodies and command output are not copied into the projection;
known environment credentials and Bearer tokens in projected text are redacted.
This is not a universal secret detector for arbitrary command arguments.

## Tool-owned artifacts

The normal cycle prompt includes the following tools and their supported
formats. Business tasks need no additional dashboard registration instructions.
The coordinator chooses a matching runner and executes each check once through
it; registration is part of that execution, not a second verification run.
Commands that bypass these explicit entries remain uncollected.

Select a product through the existing human-owned project selection command.
Inside a cycle, `--root` and `--project` default to its runtime context. Outside
a cycle, supply both explicitly, as in the first example. From the framework:

```sh
python3 scripts/core/runtime_artifacts.py --root . --project projects/example check --adapter python-unittest -- discover -s tests
python3 scripts/core/runtime_artifacts.py check --adapter node-test -- tests/example.test.js
python3 scripts/core/runtime_artifacts.py check --adapter playwright -- npx playwright test
python3 scripts/core/runtime_artifacts.py check --adapter junit --report report.xml -- python3 tests.py
python3 scripts/core/runtime_artifacts.py check --adapter exit-code -- node custom-checks.js
python3 scripts/core/runtime_artifacts.py document DELIVERY.md
python3 scripts/core/runtime_artifacts.py preview --directory public
python3 scripts/core/runtime_artifacts.py preview-stop
```

| Adapter | Execution and evidence |
| --- | --- |
| `python-unittest` | Calls the standard unittest loader/runner once, observes terminal test outcomes, and writes a machine JSON report. Pass unittest arguments, not `python -m unittest`. Multiple failing subtests count their parent testcase once. Expected failures count as skipped; unexpected successes count as failures. |
| `node-test` | Calls `node --test` with Node's built-in JUnit reporter and a separate console reporter. Pass test paths/options, not `node --test`; requires Node with its built-in JUnit reporter. TODO cases count as skipped even when their unfinished body fails. |
| `playwright` | Executes the supplied Playwright Test argv with its JSON reporter and a unique output path. Reports count final tests once, including retries; flaky tests that eventually meet expectations are passing. |
| `junit` | Executes the supplied argv and accepts the explicit project-relative XML file only when newly written. Counts actual testcase nodes; unsupported aggregate-only formats are not guessed. |
| `exit-code` | Executes arbitrary explicit argv and records its exit status. It never extracts test counts from console output. |

Arguments are passed as argv without a shell. Shell operators need an explicit
shell in the requested command and are not interpreted by the wrapper. The
wrapper retains recorded command argv, adapter, project/cycle identity, start/end
timestamps, exit code and one unique record ID. That same record transitions
from `running` to `completed`, `interrupted` or `launch_failed`; distinct
executions remain distinct records. A failed check can be `completed` with a
nonzero exit code. Observation-write or report-parse failure preserves that
exit code and never changes governance or causes an automatic rerun.
Recorded argv uses the event writer's known-credential redaction and an 8 KiB
display bound; `commandTruncated` signals omitted text. The executed argv is
unchanged. This is not a general secret detector for arbitrary arguments.

Native adapters write unique reports below the product's
`.autonomous-company/checks/`. New product repositories ignore that generated folder.
Reports are bounded to 1 MiB and hashed. `reportStatus` distinguishes `pending`,
`fresh`, `missing_or_stale`, `unsupported` and `unavailable`. A zero command exit
with no fresh supported report is not evidence of passing tests. Class-fixture
errors in unittest, or global Playwright runner errors, preserve the real
failure and raw report but omit counts that cannot describe those errors.
Changed or missing reports lose usable counts. Registering a document records
its explicit path, modification time, SHA-256, project and cycle; it does not
scan the repository for likely deliverables. The normal delivery instruction
registers the product's `DELIVERY.md` after writing it.

The optional preview runner serves static content from an explicit product
directory on loopback. Its own health response includes a per-run token, so
stopped servers and port reuse do not produce a working preview link. It does
not discover, start or validate arbitrary Vite/Next/backend servers. Those
require separate runner integration. A preview started inside a model cycle is
owned by that cycle and ends during normal supervisor cleanup. Run it as a
long-lived foreground command in the engine's persistent tool session, inspect
the printed URL while that session stays open, then use `preview-stop`. Do not
wait for server exit before opening the URL. Short-lived managed tool terminals
can send a hangup to children when the launching command exits; a background
process that initially passed health can therefore disappear immediately.
Inside a cycle, `--background` is rejected before spawning or registration.
The normal prompt explains this lifecycle without adding acceptance-only task
instructions. Engines without persistent command sessions must report that
preview limitation. `preview-stop` requests shutdown
through that preview's token-checked loopback endpoint, not a remembered PID.
Records include PID, explicit directory, `lifetime` (`cycle` or `operator`) and
start/end times. A retained preview is a separate operator invocation outside
a cycle, not an implicit side effect. Outside cycles, an operator may use
`--background` from a durable terminal; it returns after token-validated health
and does not create a detached session. The loop finalizes unfinished checks as
interrupted after existing process supervision ends; an unknown end time stays
null rather than being replaced by cleanup time.

Artifact records live in `logs/artifacts/`. The reader enumerates filenames and
keeps the newest 500 by modification time/name in a fixed-size heap. It reads
only those 500 records, at most 16 KiB each, and exposes up to 100 records and
three loopback checks per refresh. `scannedRecords` reports all candidate names;
`partial`/`truncated` explicitly mark omitted or invalid evidence. This is not
an unlimited artifact archive.
Lifecycle cleanup streams all record filenames, reading at most 16 KiB per
regular file and handling one record at a time. Display limits never cause a
later cycle-owned process or unfinished check to be excluded from cleanup.

## Product identity and metadata

Before invoking an engine, the loop writes
`logs/<cycle-id>.context.json` with its explicit selected project, cycle ID,
UTC timestamp and `source: runtime_context`. This is program-owned identity;
the dashboard does not derive cycle ownership from a model's title or consensus.
Historical cycles without a reliable project binding remain unknown.

`project-new` creates `projects/<slug>/.autonomous-company-project.json`, defaulting
the display name to the slug and leaving the description empty. The normal
cycle prompt asks the coordinator to describe a new/default product once:

```sh
python3 scripts/core/project_metadata.py --display-name 'Product name' --description 'One sentence describing its purpose'
```

This optional description is authored metadata, not independent certification.
Its versioned schema binds `project` exactly to the containing product and
validates `displayName` (1–80 characters), `description` (0–300), a timezone-aware
`recordedAt` and `source: project_metadata`. Reads are bounded, link-safe and
never parse free-form consensus for a description. Failed updates preserve the
previous file. Missing metadata falls back to the directory name with no
description. Creating/editing metadata never changes selection, language,
Human Overrides, project history or publication permissions.

## Verification settings

Continuous-cycle verification covered both `MODEL=gpt-5.6-luna` and
`MODEL=gpt-5.6-terra`, each with `CODEX_REASONING_EFFORT=high ENGINE=codex`.
Each model completed three successive cycles with distinct session identities,
live and final work reports, preserved historical reports and registered checks.
These are bounded local verification settings, not new production defaults or a
long-term reliability guarantee. `CODEX_REASONING_EFFORT` is optional and does
not substitute for observed configuration in the dashboard.

## Cycle work report v2

The existing `/api/journal` response adds `cycles[].workReport` and
`workReportStatus` (`valid`, `missing`, `invalid`) for the most recent 30 cycles.
The work report is a model-authored description, not verified business state.
Runtime state, unique cycle identity, elapsed time, checks, artifacts and usage
continue to use their existing program-owned sources. No extra model extraction
or summarization call is made, and no new Web API is required.

The coordinator writes early, after material progress or a blocker, and before
finishing. Subagents do not write this report. `auto-loop.sh` appends the same
contract after localized/customized instructions, without changing `PROMPT.md`,
consensus headings, protected human instructions or the normal final answer.
The protocol is engine-neutral; real model verification currently covers Codex.

From the framework directory, inside a cycle:

```sh
python3 scripts/core/cycle_reports.py write \
  --title 'Check duplicate CSV keys' \
  --summary 'Added duplicate-key handling and ran the registered checks.' \
  --phase review --final
```

| CLI field | Contract |
| --- | --- |
| `--title` | 1–60 characters; concise business task, not a completion assertion |
| `--summary` | 1–500 characters; latest factual work description |
| `--phase` | `planning`, `implementing`, `validating`, `blocked`, `review` |
| `--blocker` | Required only when blocked, 1–300 characters; otherwise empty |
| `--final` | This is the cycle's final report, not product acceptance |

All text is trimmed, single-line plain text, in the current product language.
`implementing` describes carrying out the task, including analysis; it does not
independently assert that product code has changed.
The helper supplies `version: 2`, `cycle_id`, `project`, UTC `recorded_at` and
`source: model_report` from the current runtime context. JSON uses `title`,
`summary`, `phase`, `blocker` and boolean `final`
for the user fields. Unknown/missing keys, unsupported versions and wrong cycle
identities are rejected; report input is bounded to 16 KiB. The helper replaces
`logs/<cycle-id>.work.json` atomically; failed validation or replacement preserves
the last valid report. Log rotation removes its paired work report.

No report value is allowed to classify a cycle as successful, unblock governance,
change language/selection, stop execution, or mark tests passed. A blocked work
report can coexist with a normally completed model call; an interrupted cycle
can have a final or partial report. The dashboard keeps these facts separate.
The Dashboard no longer requests, extracts or displays next actions. Existing v1
files are read without modification and projected into v2, discarding their two
retired fields. New writes accept only v2 fields. The consensus used internally
by the autonomous loop and original diagnostic documents remain unchanged.

On a missing/invalid report the page explicitly falls back to the existing
report. If no final update arrives, it shows the last valid update as unfinished.
The optional prompt helper failing does not prevent the loop from running.
Report failure does not create automatic model retries; the coordinator may
correct input once before continuing its original task. This is validated local
tool input, not provider-level constrained decoding: models can omit reporting.
Single coordinator ownership is a workflow contract, not a filesystem security
boundary; an agent with direct file access can still edit its own report.
