# AGENTS.md

Agent guidance for `fault`, the StarlingX **Fault Management (FM)** repository:
the alarm/event framework used across StarlingX, and the `fm` CLI. It is not
built standalone; it is one project in a full StarlingX manifest checkout.
Companion to `README.rst`.

## Major packages

- `fm-api/` — Python library for raising/clearing alarms and logging events;
  imported by other StarlingX services.
- `fm-common/` — shared C/C++ FM library plus the event-suppression helper.
- `fm-mgr/` — the FM manager daemon (runs on controllers).
- `fm-rest-api/` — the FM REST API service (queries alarms/events).
- `python-fmclient/` — the `fm` CLI client.
- `fm-doc/` — the alarm/event catalog (`fm_doc/events.yaml`) and its tooling.

## Build, test, lint

Two levels. At the repo root, `tox` runs lint/style and a catalog consistency
check:

```bash
tox -e pep8        # flake8 style/lint; source of truth for style
tox -e pylint      # static analysis of the Python packages
tox -e linters     # bashate + yamllint + checkEventYaml
```

`linters`' **`checkEventYaml`** validates `fm-doc`'s `events.yaml` against the
alarm/event IDs declared in `fm-api` (`constants.py`) and `fm-common`
(`fmAlarm.h`); a mismatch fails the gate, so keep those three in sync when adding
or changing an alarm. The `-py313` variants (`pep8-py313`, `pylint-py313`) run
the same checks under the Trixie interpreter.

The **unit-test suite for `fm-rest-api` lives in its own subdirectory tox**
(`fm-rest-api/fm/`, `envlist = flake8,py39,bandit,pylint`); run it from there:

```bash
cd fm-rest-api/fm && tox -e py39   # stestr unit tests (Python 3.9)
```

That env installs sibling repos (sysinv/tsconfig/cgts-client from `config`,
fm-api from this repo, platform-util from `utilities`) as editable deps, so a
full StarlingX checkout must be present.

`fm-rest-api` uses **Alembic** for DB schema migrations: add new revisions under
`fm-rest-api/fm/fm/db/sqlalchemy/migrations/versions/`. It has fully replaced
sqlalchemy-migrate (numeric migrate versions are rejected); the legacy
`migrate_repo/` is retained only to bridge a pre-existing schema onto its first
Alembic revision.

## Boundaries / do-not-touch

- Keep `events.yaml`, `fm-api`'s `constants.py`, and `fm-common`'s `fmAlarm.h`
  consistent — `checkEventYaml` enforces it.
- The `fm-rest-api` unit suite needs the editable sibling deps above; a
  standalone `fault` clone cannot run it.

## Contributing

StarlingX process; full detail in the StarlingX docs (Development Process; Code
Submission Guidelines).

- Reviews go through Gerrit (`review.opendev.org`) via `git review`.
- Sign off every commit (`git commit -s`); a `Signed-off-by` header is required.
- If an AI tool materially shaped the change, add an `Assisted-By:` trailer (or
  `Generated-By:` when a substantial portion was tool-generated) in addition to
  `Signed-off-by`, and note what the tool contributed. You remain the
  accountable author, and the same quality/correctness/security/licensing bar
  applies (per the OpenInfra AI-generated-content policy).
- Link the change: `Story:`/`Task:` (StoryBoard) or `Closes-Bug:`/`Partial-Bug:`/
  `Related-Bug:` (Launchpad).
- Include a **Test Plan** section in the commit message listing the test-case
  titles you ran (`PASS:`/`FAIL:`).
- Run the relevant `tox` envs (root `pep8`/`pylint`/`linters`; `py39` in
  `fm-rest-api/fm/` for service changes) and add or update unit tests before
  posting.
- Land on master first, then cherry-pick to a release branch with
  `git cherry-pick -x`.
