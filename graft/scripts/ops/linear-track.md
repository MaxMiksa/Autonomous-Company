# scripts/ops/linear-track.py · [[linear-workstream-discipline]]

CLI that appends checklist items to a long-lived workstream issue instead of opening separate Linear issues, inverting the cost so filing under an existing track is the cheap default and a new issue requires written justification.

- key · function · L65-L79 — Resolves the Linear API key from env or Keychain, falling back to a Keychain read because GUI-launched shells never export the env var.
- gql · function · L82-L88 — Runs a GraphQL query against Linear with the API key and aborts on any returned errors.
- get_issue · function · L91-L97 — Fetches a single issue by its numeric identifier within the APP team, erroring if it does not exist.
- set_description · function · L100-L102 — One-line mutation wrapper that overwrites an issue's description text.
- cmd_list · function · L105-L120 — Prints each track with open/done counts and its open checklist items, normalizing ticked boxes to uppercase X so done counts are accurate.
- cmd_add · function · L123-L131 — Appends a new unchecked checklist item to a track's description, inserting the checklist heading if the track lacks one.
- cmd_done · function · L134-L145 — Ticks a checklist item by substring match, refusing when the needle matches zero or multiple items to force an unambiguous target.
- cmd_comment · function · L148-L152 — Posts an evidence comment on a track issue rather than creating a task.
- cmd_new · function · L155-L170 — Creates a new Linear issue only when the --why justification is one of the three accepted reasons, otherwise refuses and points the user to --add.
- main · function · L173-L196 — Parses CLI flags and dispatches to the matching subcommand, defaulting to --add's track.
