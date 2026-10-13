# Language settings

[中文](../README.md) · [Project guide](../../README.md)

One preference controls the Dashboard, documentation links, new AI output and the target language of new products. The initial default follows the computer's display language: Chinese selects `zh-CN`; other languages select `en`. WSL first checks the Windows display language and uses its Linux locale if Windows cannot be queried.

## Choose a language

Use the Dashboard selector or run from the repository root:

```bash
make language LANGUAGE=en
make language LANGUAGE=zh-CN
```

On Windows without make:

```powershell
python scripts/core/localization.py set --language en
```

Windows `start-win.ps1 -Language en` saves the same preference. A saved choice takes precedence over an old service's `AUTONOMOUS_COMPANY_LANGUAGE` environment variable; that variable only supplies the initial choice when no preference exists. The Dashboard no longer keeps a separate browser preference, so there is no second setting to synchronize.

## Keep one language throughout a product cycle

A product cycle covers one product from startup to delivery and may include many AI iterations. Its language is fixed when it first starts and survives pauses, restarts and recovery.

| Action | Result |
|---|---|
| Choose English before the first start | The interface and new product work use English |
| Choose English while a Chinese product is running | English is saved for the next product; the current product and interface stay Chinese |
| Pause or restart the same product | Its original language continues |
| Explicitly begin the next product cycle | The latest saved preference takes effect |

The Dashboard shows both the current and next product language. Saving a preference does not require stopping the product or change its instructions or generated content midway through work.

When ready for the next product, stop a foreground loop with `make stop` or pause a background service with `make pause`, then run:

```bash
make next-product CONFIRM=NEXT
```

On Windows, stop with `./scripts/windows/stop-win.ps1`, then run:

```powershell
python scripts/core/localization.py next-product --confirm NEXT
```

This explicitly advances the product's language record. It does not invoke a model or clear history, budgets, human rules or existing product files. Recover an interrupted iteration through the normal recovery process before advancing the product cycle. Select the new project and set its task through the usual workflow.

## What follows the setting

| Content | Behavior |
|---|---|
| Dashboard, documentation links and common operational guidance | Current product language, or the preference before a product starts |
| New explanations, decisions, delivery reports and consensus prose | AI instructions require the current product language |
| New product interfaces, help and documentation | The product language is a delivery requirement and part of acceptance |
| All bundled skill source files | English; user-facing work still follows the product language |
| Commands, paths, identifiers, protocol headings and raw tool errors | Unchanged |
| Existing products, historical logs, customized sources and human rules | Preserved; not translated retroactively |

Generated content is guided by instructions and still requires a language check during product acceptance. GitHub-hosted pages, third-party tools and user-supplied source material are outside the local setting's control. Use the language links at the top of the GitHub README.

## Resources and maintenance

Localized roles and documents are selected using reviewed hashes in `source-hashes.json`. A packaged translation is used only when its source has not been customized. Customized sources or missing translations fall back to the source; CRLF/LF differences do not count as customization. All skills use the English files under `.claude/skills/` directly.

This directory contains the English loop prompt, all 14 role definitions and English documentation. Resolve resource paths from the repository root. Review both languages' instruction strength, terminology, commands and links before refreshing a changed source hash. Run the affected language, Dashboard and runtime checks; do not refresh hashes just to silence a failing test.

See [common operations and troubleshooting](docs/troubleshooting.md) for operational guidance.

### Recover after a configuration writer is interrupted

If configuration remains busy or an interactive-session marker remains after a crash, stop the foreground loop or pause its background service. Close every `make team` session and its descendants, the Dashboard and any configuration-writing commands. After confirming that all of these processes have stopped, run from the repository root:

```bash
python3 scripts/core/localization.py recover-lock --confirm RECOVER
```

On Windows, use `python` instead of `python3`. `RECOVER` attests that all relevant processes are stopped; never use it against a live writer. Recovery finishes an interrupted language-preference save and clears abandoned operation markers. It preserves the current product language and history. If it reports a running loop or unexpected lock-directory contents, resolve that cause instead of deleting configuration or governance backups.
