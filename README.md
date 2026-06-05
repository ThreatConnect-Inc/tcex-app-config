# tcex-app-config

A [TcEx](https://github.com/ThreatConnect-Inc/tcex) submodule providing read, write, update, validate,
schema-generation, and Pydantic-model support for every ThreatConnect App configuration file.

## Overview

ThreatConnect Apps are described by a set of JSON/YAML configuration files that define their inputs,
outputs, runtime behavior, and UI layout. This submodule owns the authoritative Python representation of
those files — parsers, Pydantic **v2** models, in-place updaters, validators, and a permutation engine.
It is consumed by the framework at runtime (loading the running App's config) and by developer tooling at
build time (the CLI's `package`/`validate`/`update` commands and the test harness).

Each config file is fronted by a small reader class that lazily parses the file into a Pydantic model
exposed as `.model`, with optional `.update` / `.validate` sub-objects. Some of these readers compose the
others:

```
AppSpecYml                 # app_spec.yml — the human-authored source of truth
├── InstallJson  (self.ij) #   install.json reader
└── TcexJson     (self.tj) #   tcex.json reader → also builds its own InstallJson

Permutation                # enumerates valid input/output combinations
├── InstallJson  (self.ij)
└── LayoutJson   (self.lj)

InstallJson                # install.json
├── .model    → InstallJsonModel
├── .update   → InstallJsonUpdate
└── .validate → InstallJsonValidate
```

## Configuration Files Covered

| File | Reader class | Purpose |
|---|---|---|
| `install.json` | `InstallJson` | Primary App manifest: runtime level, input params, features, playbook outputs, SDK version |
| `app_spec.yml` | `AppSpecYml` | Human-authored App specification (source of truth for tooling); migrates and feeds `install.json` |
| `layout.json` | `LayoutJson` | UI layout: ordered input sections with display expressions, plus an outputs list |
| `tcex.json` | `TcexJson` | TcEx CLI project configuration: package name and build/packaging settings |
| `job.json` | `JobJson` | Job (Organization) App configuration |

## Module Layout

```
tcex/app/config/
├── install_json.py            # InstallJson + _InstallJsonSchemaGenerator
├── install_json_update.py     # InstallJsonUpdate
├── install_json_validate.py   # InstallJsonValidate
├── app_spec_yml.py            # AppSpecYml (+ 1.0.0 → 1.1.0 migration)
├── layout_json.py             # LayoutJson + LayoutJsonUpdate
├── tcex_json.py               # TcexJson
├── tcex_json_update.py        # TcexJsonUpdate
├── job_json.py                # JobJson
├── permutation.py             # Permutation + InputModel
└── model/                     # Pydantic v2 models (one per config file)
    ├── install_json_model.py
    ├── app_spec_yml_model.py
    ├── layout_json_model.py
    ├── tcex_json_model.py
    └── job_json_model.py
```

The package re-exports `AppSpecYml`, `InstallJson`, `JobJson`, `LayoutJson`, `Permutation`, and `TcexJson`
from `__init__.py`; all five top-level models are re-exported from `model/__init__.py`.

## Module Reference

### `InstallJson`

Reads and writes `install.json` and exposes it as an `InstallJsonModel`. Beyond parsing, it builds
TC-style output-variable strings, expands macro valid-value tokens, filters params, converts params to
CLI-argument dicts for test harnesses, and can emit a JSON Schema for the model.

`InstallJson(filename='install.json', path=Path.cwd(), logger=None)`

**Deliberately not a singleton** — the CLI `package` command constructs multiple `InstallJson` instances
to write `install.json` files into build directories, so each instance is independent.

| Member | Kind | Description |
|---|---|---|
| `contents` | `@cached_property` | Parsed file as an `OrderedDict`. **If the file does not exist it silently returns a hard-coded "External App" default dict** (it does not raise). Read once, cached for the instance's life. |
| `model` | `@cached_property` | `InstallJsonModel(**self.contents)`. |
| `is_external_app` | `@cached_property` | `True` when no `install.json` file is present. |
| `update` | `@property` | A fresh `InstallJsonUpdate` bound to this instance. |
| `validate` | `@property` | A fresh `InstallJsonValidate` bound to this instance. |
| `params_dict` | `@property` | `name → ParamsModel` map (used by the test harness for output generation). |
| `tc_playbook_out_variables` / `_csv` | `@property` | Playbook output-variable list / CSV string. |
| `app_prefix` / `app_prefixes` | `@property` | Output-var prefix for the App's runtime level (e.g. `TCPB_-_` for playbook). |
| `has_feature(feature)` | method | Case-insensitive feature check. |
| `create_variable(var_name, var_type, job_id=1234)` | method | Builds a TC variable string, e.g. `#App:9876:app.data.count!String`. |
| `create_output_variables(output_variables, job_id=9876)` | method | `create_variable` over a list of outputs. |
| `expand_valid_values(valid_values)` | `@staticmethod` | Expands `${GROUP_TYPES}` to the full 16-type group list and strips `${OWNERS}` / `${USERS}`. **Mutates the passed list in place** (uses `.remove()` / `.extend()`) and returns it. |
| `params_to_args(name, hidden, required, service_config, _type, input_permutations)` | method | Builds a CLI-arg dict with type-aware defaults (used by `tcex-app-testing`). |
| `write()` | method | Serializes `model` via `model_dump_json(by_alias=True, exclude_defaults=True, exclude_none=True, indent=2)` back to `fqfn`. |
| `write_schema(path=None)` | method | Writes the install.json JSON Schema (default `install_json.schema.json` beside the file) and returns its `Path`. Uses a custom generator that renders `semantic_version.Version` fields as `string`, and suppresses Pydantic warnings during generation. |

#### `InstallJsonUpdate`

Applies a batch of standard normalizations to an open `InstallJson`, then writes the file. Mutates
`ij.model` in place.

`multiple(features=True, sequence=True, valid_values=True, playbook_data_types=True, sdk_version=True)`
runs the selected steps and calls `ij.write()`:

- `update_sequence_numbers()` — renumbers params `1..n` in order.
- `update_valid_values()` — for `String` / `KeyValueList` params, sets the correct keychain/text store
  token by App type: `${USER:<store>}` / `${ORGANIZATION:<store>}` for organization/service-config
  inputs, `${<store>}` for playbook inputs (removing the tokens that belong to the other App type), where
  `<store>` is `KEYCHAIN` when `encrypt` is set, otherwise `TEXT`.
- `update_playbook_data_types()` — backfills `playbookDataType: ['String']` on `String` params (playbook
  Apps only).
- `update_sdk_version()` — stamps `sdkVersion` from the installed `tcex` package version, **best-effort:
  `ImportError` / `ValueError` are suppressed** (left unchanged if `tcex` can't be resolved).

#### `InstallJsonValidate`

Integrity checks. **Each method returns a list of the offending values rather than raising** — the caller
decides how to report them.

| Method | Returns |
|---|---|
| `validate_duplicate_input()` | Input names that appear more than once. |
| `validate_duplicate_output()` | Output names that appear more than once **keyed on `name-type`** (the same name with a different type is allowed). |
| `validate_duplicate_sequence()` | Duplicate param sequence numbers. |

### `AppSpecYml`

Reads and writes `app_spec.yml`, the human-authored specification that is the source of truth for App
tooling. Uses libyaml (`CLoader`/`CDumper`) when available, falling back to the pure-Python loader.

`AppSpecYml(filename='app_spec.yml', path=Path.cwd(), logger=None)` — its `__init__` also constructs an
`InstallJson` (`self.ij`) and a `TcexJson` (`self.tj`).

**Non-obvious behaviors:**

- **Reading `contents` rewrites the file on disk.** `contents` (`@cached_property`) loads the YAML, and if
  `schemaVersion` is `1.0.0` (the default when absent) it runs the full `1.0.0 → 1.1.0` migration, then
  **writes the canonicalized document back to `app_spec.yml`** and re-reads it. Simply accessing
  `.contents` or `.model` therefore has a file-write side effect for legacy specs.
- The `1.0.0 → 1.1.0` migration is extensive: it lifts `app.*` to the top level, moves
  `feeds`/`repeatingMinutes`/`publishOutFiles` under `organization`, renames `inputGroups → sections` and
  `outputGroups → outputData`, converts `notes → notePerAction`, `playbookType → category`, `jira →
  internalNotes`, reshapes `releaseNotes`, moves `retry` under `playbook`, and defaults
  `minServerVersion` to `6.0.0`.
- **`model` enforces the `advancedRequest` feature contract.** When `advancedRequest` is in `features`, it
  **requires a `Configure` section and raises `RuntimeError` if one is missing**; otherwise it appends the
  standard Advanced Request inputs to the `Configure` section, adds the Advanced Request outputs, and adds
  `'Advanced Request'` to the `tc_action` valid values.
- `fix_contents()` fills defaults (`packageName` from `tcex.json`, `programMain` → `run.py`,
  `outputPrefix`, API-service `displayPath`, empty `labels`/`deprecatesApps`).

Other members: `has_spec`, `write(contents)`, `dict_to_yaml(data)` (block style, `sort_keys=False`), and
`write_schema(path=None)` (default `app_spec_yml.schema.json`, Version-as-string generator).

### `LayoutJson`

Reads and writes `layout.json`, which models the two-part layout structure — ordered input sections that
each carry a display expression, plus an outputs list.

`LayoutJson(filename='layout.json', path=Path.cwd(), logger=None)`

**This class is a singleton** (`metaclass=Singleton`): one instance per process, with the parsed model
cached for the process lifetime. Be aware of this shared, cached state when a process needs to read more
than one `layout.json`.

| Member | Kind | Description |
|---|---|---|
| `contents` | `@cached_property` | Parsed file; **logs an error and returns `{}` if the file is missing** (does not raise). |
| `model` | `@cached_property` | `LayoutJsonModel`. |
| `has_layout` | `@property` | `True` when a `layout.json` file exists. |
| `create(inputs, outputs)` | method | Generates a new `layout.json` with `Action` / `Connection` / `Configure` / `Advanced` sections — routes `tc_action` to `Action`, hidden inputs to `Configure` with a `"'hidden' != 'hidden'"` display — and writes it. |
| `update` | `@property` | A `LayoutJsonUpdate`. |
| `write(data)` | method | Writes a JSON string to disk. |
| `write_schema(path=None)` | method | Writes `layout_json.schema.json` (default) and returns its `Path`. |

#### `LayoutJsonUpdate`

`multiple()` calls `update_sort_outputs()` — which **sorts the outputs list alphabetically by name** to
enforce stable diffs — and writes the file.

### `TcexJson`

Reads and writes `tcex.json`, the TcEx CLI project file, as a `TcexJsonModel` (package and build
metadata). Its `__init__` also constructs an `InstallJson` (`self.ij`), used when deriving the package
name. Note `write()` serializes **without** `by_alias` (the `tcex.json` field names are not camelCased).
`write_schema(path=None)` emits `tcex_json.schema.json`.

#### `TcexJsonUpdate`

`multiple(template=None)` runs:

- `update_package_app_name()` — if the package name is unset (or equals a bare App prefix), derives it
  from the **current working directory name**, title-cased with `_` separators, prefixed with the App
  prefix (e.g. `TCPB_-_`).
- `update_deprecated_fields()` — clears the deprecated `lib_versions`.
- `update_package_excludes()` — ensures `.gitignore`, `.pre-commit-config.yaml`, `app_spec.yaml`,
  `local-*`, and `pyproject.toml` are in the package `excludes`.
- optional `template_name`, then `tj.write()`.

### `JobJson`

Reads `job.json` for Job (Organization) App configuration and exposes it as a `JobJsonModel`. **Read-only**
— there is no `update`/`validate`/`write`.

**This class is a singleton** (`metaclass=Singleton`). Caveat: its constructor's default `filename` is
`'tcex.json'`, **not `'job.json'`** (a copy-paste artifact carried in the source, also reflected in its
log messages) — pass an explicit `filename='job.json'` if you rely on the default location.

### `Permutation`

Calculates every valid combination of input values, and the corresponding set of active outputs, for an
App — driven by the display expressions in `layout.json` and the param definitions in `install.json`.
This lets test harnesses and CLI tooling enumerate all valid App states without running the App. Its
`__init__` constructs an `InstallJson` (`self.ij`) and `LayoutJson` (`self.lj`); no arguments.

**How it works (and the caveats):**

- It uses an **in-memory `sqlite3`** database. A single-row table holds the current input values, and each
  `layout.json` display expression is evaluated as that row's SQL `WHERE` clause
  (`SELECT count(*) ... WHERE <display>` → visible when the count is `> 0`). Display expressions are
  therefore expected to be valid SQL conditions.
- `_gen_permutations()` walks the layout param order recursively, branching on every value of `Boolean`
  (`True`/`False`) and `Choice`/`EditChoice` (each expanded valid value) inputs, so **the permutation count
  grows combinatorially** with the number and cardinality of such inputs.
- **Requires a Python built with the `sqlite3` module** — `permutations()` fails fast with a rendered
  panel if `sqlite3` is not importable. **Only Apps that have a `layout.json` are supported.**
- `db_conn` is a `@cached_property` from `tcex.pleb.cached_property` (the project descriptor, resettable in
  tests) rather than `functools.cached_property`.

| Member | Kind | Description |
|---|---|---|
| `action_configurations` | `@cached_property` | `action → {'inputs': [...], 'outputs': [...]}` for every `tc_action` value, deduplicated and name-sorted. |
| `input_permutations` / `output_permutations` | `@property` | Lazily generated lists-of-lists of valid input / output permutations. |
| `input_names` | `@cached_property` | Per-permutation lists of input names. |
| `get_action_inputs(action)` / `get_action_outputs(action)` | method | Inputs / outputs for an action. |
| `get_action_input_names(action)` / `get_action_output_names(action)` | method | The name lists for the above. |
| `get_input_applies_to_all(input_name)` | method | `True` if the input appears in every action configuration. |
| `inputs_ordered` | `@property` | Params in layout order (falls back to `install.json` order when no layout). |
| `inputs_by_action(action, include_hidden=True)` | method | Yields `{'applies_to_all', 'input'}` per applicable input. |
| `outputs_by_action(action)` / `outputs_by_inputs(inputs)` | method | Yields the outputs visible for a given action / input set. |
| `input_dict(permutation_id)` | method | `name → value` for one permutation index. |
| `validate_input_variable(input_name, inputs, display=None)` | method | `True` if the display clause matches the provided inputs. |
| `validate_layout_display(table, display_condition)` | method | Evaluates a display clause against a DB table. |
| `permutations()` | method | Generates permutations and writes them to `permutations.json` in the CWD. |
| `write_permutations_file()` | method | Writes the `permutations.json` artifact. |

`InputModel` (a `ParamsModel` subclass used internally) adds a `value` field and a name-based `__hash__`
so permutation inputs can be collected into sets.

## Models (`model/`)

Each config file has a corresponding **Pydantic v2** model that enforces the schema, documents fields, and
handles camelCase ↔ snake_case aliasing. Every model sets
`model_config = ConfigDict(alias_generator=to_camel, validate_assignment=True)` (one variant adds
`arbitrary_types_allowed=True` for `semantic_version.Version`). Version fields (`languageVersion`,
`minServerVersion`, `programVersion`, `sdkVersion`) are coerced to `semantic_version.Version` via
`@field_validator(..., mode='before')`.

| Model | Config file | Notes |
|---|---|---|
| `InstallJsonModel` | `install.json` | Composed via multiple inheritance (`InstallJsonCommonModel` + `InstallJsonOrganizationModel`). |
| `AppSpecYmlModel` | `app_spec.yml` | Extends `InstallJsonCommonModel`; its sub-models extend the install.json sub-models — this is the source-of-truth model that maps onto `install.json`. |
| `LayoutJsonModel` | `layout.json` | `InputsModel` (sections) → `ParametersModel`, plus `OutputsModel`. |
| `TcexJsonModel` | `tcex.json` | Wraps a `PackageModel`. |
| `JobJsonModel` | `job.json` | Extends `JobJsonCommonModel`. |

`InstallJsonModel` is the workhorse and exposes a wide helper surface beyond its fields, including
`is_api_service_app` / `is_feed_app` / `is_job_app` / `is_organization_app` / `is_playbook_app` /
`is_service_app` / `is_trigger_app` / `is_webhook_trigger_app` properties, `filter_params(...)`,
`get_param(name)`, `get_output(name)`, `param_names`, `app_output_var_type`, and `updated_features`.

## Project Structure Note — No `pyproject.toml` or `.pre-commit-config.yaml`

This submodule intentionally ships **without** a `pyproject.toml` or `.pre-commit-config.yaml`.
All linting (`ruff`), type-checking (`ty`), and pre-commit hooks are configured in the **parent
projects** (`tcex`, `tcex-app-testing`, `tcex-cli`), each of which scans this submodule as part of
its own workspace. Running `pre-commit run --all-files` or `ty check` from the parent repo
root covers this code automatically — there is no need for (and no benefit to) duplicating
that configuration here.

## Used By

- [tcex](https://github.com/ThreatConnect-Inc/tcex) — runtime App config loading.
- [tcex-app-testing](https://github.com/ThreatConnect-Inc/tcex-app-testing) — test-harness param/output generation and permutations.
- [tcex-cli](https://github.com/ThreatConnect-Inc/tcex-cli) — the `package`, `validate`, and `update` commands.

## License

Apache 2.0 — see [LICENSE](LICENSE).
