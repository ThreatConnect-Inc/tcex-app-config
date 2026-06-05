# tcex-app-config

A [TcEx](https://github.com/ThreatConnect-Inc/tcex) submodule providing read, write, update, validate,
and Pydantic-model support for every ThreatConnect App configuration file.

## Overview

ThreatConnect Apps are described by a set of JSON/YAML configuration files that define their inputs,
outputs, runtime behavior, and UI layout. This submodule owns the authoritative Python representations
of those files — parsers, models, updaters, validators, and a permutation engine — and is consumed
by the framework at runtime as well as by developer tooling at build time.

## Configuration Files Covered

| File | Class | Purpose |
|---|---|---|
| `install.json` | `InstallJson` | Primary App manifest: runtime level, input params, features, playbook outputs, SDK version |
| `app_spec.yml` | `AppSpecYml` | Human-authored App specification (source of truth for tooling); transforms into `install.json` |
| `layout.json` | `LayoutJson` | UI layout: input groupings, display expressions, output ordering |
| `tcex.json` | `TcexJson` | TcEx CLI project configuration: package name, build settings |
| `job.json` | `JobJson` | Job App specific configuration |

## Module Reference

### `InstallJson`

Reads and writes `install.json`. Exposes the parsed file as an `InstallJsonModel` instance and
provides helpers for constructing TC-style output variable strings
(`#App:9876:my.output!String`), expanding macro valid-value tokens (`${GROUP_TYPES}`,
`${OWNERS}`, `${USERS}`), filtering params, and converting params to CLI-argument dicts for
test harnesses.

**Sub-components:**

- `InstallJsonUpdate` — applies a batch of standard normalizations to an open `InstallJson`:
  refreshes the `features` array, renumbers param sequences, updates `validValues` tokens to the
  correct store scope (`${TEXT}` vs `${USER:TEXT}` / `${ORGANIZATION:TEXT}`), backfills
  `playbookDataType` on `String` params, and stamps `sdkVersion` from the installed `tcex` package.
- `InstallJsonValidate` — integrity checks: duplicate input names, duplicate output names, and
  duplicate sequence numbers.

### `AppSpecYml`

Reads and writes `app_spec.yml` (schema versions `1.0.0` and `1.1.0`). Automatically migrates
a `1.0.0` document to the `1.1.0` schema on first read, then rewrites the file in canonical form.
Injects the full set of standard Advanced Request inputs and outputs when the `advancedRequest`
feature is declared, and validates that a `Configure` section is present before doing so.

### `LayoutJson`

Reads and writes `layout.json`. The model represents the two-part layout structure (ordered input
sections with display expressions, and an outputs list). The bundled `LayoutJsonUpdate` helper
sorts the outputs list alphabetically by name to enforce stable diffs.

### `TcexJson`

Reads and writes `tcex.json` (the TcEx CLI project file). Exposes a `TcexJsonModel` with package
and build metadata. `TcexJsonUpdate` applies standard normalizations.

### `JobJson`

Reads `job.json` for Job App specific configuration and exposes it as a `JobJsonModel`.

### `Permutation`

Calculates every valid combination of input values and the corresponding set of active outputs
for an App, driven by the display-expression logic in `layout.json` and the param definitions in
`install.json`. Uses an in-process SQLite database to evaluate display expressions at scale,
which enables test harnesses and CLI tools to enumerate all valid App states without running the
App itself.

## Models (`model/`)

Each configuration file has a corresponding Pydantic v1 model that enforces the schema, provides
field-level documentation, and handles camelCase ↔ snake_case aliasing for JSON serialization.

| Model | Config file |
|---|---|
| `InstallJsonModel` | `install.json` |
| `AppSpecYmlModel` | `app_spec.yml` |
| `LayoutJsonModel` | `layout.json` |
| `TcexJsonModel` | `tcex.json` |
| `JobJsonModel` | `job.json` |

All models are re-exported from `model/__init__.py` for convenient import.

## Project Structure Note — No `pyproject.toml` or `.pre-commit-config.yaml`

This submodule intentionally ships **without** a `pyproject.toml` or `.pre-commit-config.yaml`.
All linting (`ruff`), type-checking (`ty`), and pre-commit hooks are configured in the **parent
projects** (`tcex`, `tcex-app-testing`, `tcex-cli`), each of which scans this submodule as part of
its own workspace. Running `pre-commit run --all-files` or `ty check` from the parent repo root
covers this code automatically — there is no need for (and no benefit to) duplicating that
configuration here.

## Used By

- [tcex](https://github.com/ThreatConnect-Inc/tcex) — runtime App config loading
- [tcex-app-testing](https://github.com/ThreatConnect-Inc/tcex-app-testing) — test harness param/output generation
- [tcex-cli](https://github.com/ThreatConnect-Inc/tcex-cli) — `package`, `validate`, and `update` commands

## License

Apache 2.0 — see [LICENSE](LICENSE).
