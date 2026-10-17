# Language settings

[中文](../README.md) · [Project guide](../../README.md)

The product center saves its interface language separately from the default product language for new work. The initial interface default follows the computer's display language: Chinese selects `zh-CN`; other languages select `en`. WSL first checks the Windows display language and uses its Linux locale if Windows cannot be queried. A newly created center can initialize new-work defaults from existing installation configuration; center preferences are saved independently thereafter.

## Choose languages in the product center

Open the center's Settings: the interface language controls the center, product-detail labels and local help pages; the default product language applies to new work. These are separate choices. Confirm the product language when creating work; configuration templates can also specify it. Existing products retain their locked language. Product details show the recorded product language without a separate language selector.

## Language settings for lower-level standalone loops

The following commands configure the loop in the selected run directory. They do not change saved center preferences or replace the center's work creation and product management. Run from the standalone loop's repository root:

```bash
make language LANGUAGE=en
make language LANGUAGE=zh-CN
```

On Windows without make:

```powershell
python scripts/core/localization.py set --language en
```

Windows `start-win.ps1 -Language en` also saves that run directory's loop language preference. For these lower-level loops, a saved choice takes precedence over an old service's `AUTONOMOUS_COMPANY_LANGUAGE` environment variable; that variable only supplies the initial choice when no preference exists. Center preferences and lower-level loop configuration do not synchronize with each other.

## Keep one language throughout a product cycle

A product cycle covers one product from startup to delivery and may include many AI iterations. Its language is fixed when it first starts and survives pauses, restarts and recovery.

| Action | Result |
|---|---|
| Choose English as the center interface language | Center and detail labels and local help use English; product content keeps its original language |
| Choose English as the default product language for new work | New work defaults to English, subject to the configuration confirmed at creation |
| Change a standalone loop's language preference to English | English is saved for the next product cycle; the current product keeps its original language |
| Pause or restart the same product | Its original language continues |
| Explicitly begin the next product cycle in a standalone loop | That run directory's latest saved language preference takes effect |

The center's interface language can change independently. Changing the new-work default language does not change an existing product's instructions, generated content or historical records.

For lower-level standalone loops only: when ready for the next product, stop a foreground loop with `make stop` or pause a background service with `make pause`, then run:

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
| Product center, detail labels and local help pages | Center interface language |
| Common lower-level loop operational guidance | That run directory's language settings |
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

### Recover after a standalone loop configuration writer is interrupted

If a standalone loop's configuration remains busy or an interactive-session marker remains after a crash, stop the foreground loop or pause its background service. Close every `make team` session and its descendants and any commands writing that run's configuration. After confirming that all of these processes have stopped, run from the repository root:

```bash
python3 scripts/core/localization.py recover-lock --confirm RECOVER
```

On Windows, use `python` instead of `python3`. `RECOVER` attests that all relevant processes are stopped; never use it against a live writer. Recovery finishes an interrupted language-preference save and clears abandoned operation markers. It preserves the current product language and history. If it reports a running loop or unexpected lock-directory contents, resolve that cause instead of deleting configuration or governance backups.
