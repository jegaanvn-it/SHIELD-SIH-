# SARA Work-Package Authorization Register

**Status:** Register entries below are proposals only. None is active. A grant becomes active only when Prem reviews the entry and issues its exact `AUTHORIZE WP-<ID>` token. The grant is limited to the scopes, paths, commands, and Git operations explicitly listed in that entry. Unlisted operations remain unauthorized. A grant expires when its listed final report is delivered or when Prem revokes it, whichever comes first. Any change to an entry requires a new review and authorization.

## WP-S — Git secret-scanning handoff and baseline commit

**Status:** Proposed — inactive. **Activation token:** `AUTHORIZE WP-S`.

### Bundled scopes and exact file paths

- **EXTERNAL WP-S:** Download only the pinned Gitleaks release asset and its official checksum from the official `gitleaks/gitleaks` GitHub release, including only necessary GitHub release asset redirect hosts. Proposed version: `v8.30.1`; archive: `gitleaks_8.30.1_windows_x64.zip`; proposed SHA-256: `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`. Version and hash are unverified in this register. Download to `%TEMP%\sara-gitleaks\`. Stop if the downloaded archive hash does not match both this register and the official checksum.
- **INSTALL WP-S:** Only after successful checksum verification, extract only `gitleaks.exe` from the verified zip and place it at `%LOCALAPPDATA%\SARA-tools\gitleaks\v8.30.1\gitleaks.exe`, outside the repository. Keep the archive outside the repository. Record the extracted executable's SHA-256 in `reports/wp_s_report.md`. If SmartScreen or Defender blocks the binary, stop; never use `Unblock-File` or change security settings.
- **FILES WP-S — exact repository paths only:**
  - `.githooks/**`
  - `.gitleaks.toml`
  - `.gitignore` — add-only; preserve every AGENTS.md G5 pattern and remove none
  - `reports/wp_s_report.md`
  No other path is authorized.
- **LAUNCH WP-S:** Only Gitleaks `--version`, `--help`, the canary test, the configured first candidate-path scan, and the configured hook scan. Before any execution, record the exact commands in `reports/wp_s_report.md`. The canary test must run before the first real scan: create one clearly synthetic dummy-secret file under `%TEMP%\sara-gitleaks\canary\` using a value matching a default Gitleaks rule; scan that folder with the repository `.gitleaks.toml` and redacted output; require a detection. If no detection occurs, stop and report. Afterwards, delete only the canary folder, after verifying its resolved path is exactly `%TEMP%\sara-gitleaks\canary`. No other process launch or temporary-path write is included.
- **Git operations WP-S:** Read-only `git config --get user.name` and `git config --get user.email`; local `git config --local core.hooksPath .githooks`; read-only review of status/diff; stage only individually reviewed explicit paths; create one baseline commit after all gates below. No branch creation, push, merge, history rewrite, or additional commit is authorized.

### Scan, privacy, and commit gates

- `.gitleaks.toml` must contain `[extend]` with `useDefault = true`, followed by a global `[allowlist]` whose only entries are path entries for `.venv/` and `artifacts/`. It must contain no rule exclusions, secret allowlists, or other content. This preserves the default rules while limiting global allowlisting to those two paths.
- The `.githooks/pre-commit` hook must fail closed: if `gitleaks.exe` is missing, cannot run, or returns an error, the hook blocks the commit. It must pass `--config .gitleaks.toml` explicitly and scan staged content. Never bypass the hook.
- Before staging, present Prem with the candidate commit path list and redaction-review results (file/location only, no matched values) and wait for the exact message `PROCEED STAGING`. The first real scan must target exactly those candidate commit paths, by path-scoped scan or staged-content scan; do not scan the whole working tree. Unrelated tool folders such as `.claude-flow/` must neither be scanned nor staged. Report, using read-only checks and without displaying contents, whether `.claude-flow/` is ignored by `.gitignore` or another applicable ignore source. If the staged content differs from the scanned candidate content, scan the exact staged content again.
- Run the read-only personal-data redaction review on candidate commit files for `C:\Users\`, `$env:USERNAME`, `$env:COMPUTERNAME`, email-like patterns, and phone-like patterns. Report file/location only, never matched values. Stop for Prem review if likely personal data is found.
- If either Git identity value is absent, stop and ask Prem. Set identity locally only to values Prem supplies; never invent values.
- Write `reports/wp_s_report.md` before the baseline commit and include it in the commit. Scan the exact final commit content after the report is written. The report must contain no secrets or personal data; a commit hash is not required in the report.
- Stage explicit reviewed paths only after Prem says `PROCEED STAGING`; never use `git add .`. Create exactly one baseline commit only after a clean exact-content scan and completed redaction review. No push.

### Backup prerequisite

Requested one-time backup target: `%USERPROFILE%\SARA-backups\pre-commit-20261021`. No backup is authorized or created by WP-S. It requires a separate destination preflight and the exact one-time `BACKUP M0A SARA TO <absolute-path>` approval after the destination is verified.

## WP-U — Local Tkinter and SQLite echo-provider prototype

**Status:** Proposed — inactive. **Activation token:** `AUTHORIZE WP-U`.

### Bundled scopes and exact paths

- **FILES WP-U — exact paths only:** `src/sara/__init__.py`, `src/sara/ui/**`, `src/sara/memory/**`, `src/sara/providers/**`, `tests/track_u/**`, and `reports/track_u_report.md`.
- Runtime database path: `%LOCALAPPDATA%\Sara\track_u\conversations.sqlite3` only. Tests must use a temporary database under `%TEMP%\sara-track-u-tests\`; tests must not open the runtime database or launch the UI.
- **LAUNCH WP-U — named commands only:**

  Tkinter availability check:

  ```powershell
  .\.venv\Scripts\python.exe -c "import tkinter; print(tkinter.TkVersion)"
  ```

  Automated tests:

  ```powershell
  $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp "$env:TEMP\sara-track-u-tests" tests\track_u
  ```

- **Prem manual UI launch only; Codex must not run this command.** The final `reports/track_u_report.md` must include this exact PowerShell command:

  ```powershell
  $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m sara.ui.app --database "$env:LOCALAPPDATA\Sara\track_u\conversations.sqlite3"
  ```

### Restrictions and Git handoff

- Prototype only a minimal Tkinter UI, SQLite conversation memory, and echo provider. No third-party dependencies for the initial UI prototype; no package installation, network, API, credentials, microphone, or real AI-provider access. Tests may not open the runtime database or launch the UI.
- No unrelated file edits, external requests, or push. Track U supplies no M0A/M0B acceptance credit and does not close either milestone.
- WP-U may begin only after the WP-S baseline commit exists. It may create branch `track-u-ui` from that baseline commit, stage only its own explicitly reviewed WP-U paths, and make commits only through the approved secret-scan hook after scanning the exact content. Never bypass the hook; no push or merge.
- The grant expires after `reports/track_u_report.md` is delivered or upon Prem's revocation.

## WP-G — Gemini AI Brain Integration

**Status:** Active. **Activation token:** `AUTHORIZE WP-G`.

### Bundled scopes and exact paths

- **FILES WP-G — exact paths only:**
  - `docs/AUTHORIZATIONS.md`
  - `src/sara/config.py`
  - `src/sara/providers/base.py`
  - `src/sara/providers/gemini.py`
  - `src/sara/providers/__init__.py`
  - `src/sara/ui/app.py`
  - `tests/track_u/test_gemini_provider.py`
  - `tests/track_u/test_ui_async.py`
  - `reports/wp_g_report.md`
- Runtime database path: `%LOCALAPPDATA%\Sara\track_u\conversations.sqlite3` only. Tests must use a temporary database under `%TEMP%\sara-track-u-tests\`; tests must not open the runtime database or launch the UI.
- **LAUNCH WP-G — named commands only:**

  Automated tests:

  ```powershell
  $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp "$env:TEMP\sara-track-u-tests" tests\track_u
  ```

- **Prem manual UI launch only; Codex must not run this command.** The final `reports/wp_g_report.md` must include this exact PowerShell command:

  ```powershell
  $env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m sara.ui.app --database "$env:LOCALAPPDATA\Sara\track_u\conversations.sqlite3"
  ```

### Restrictions and Git handoff

- Implement Gemini AI provider using official `google-genai` SDK, secure API key handling via `GEMINI_API_KEY`, configurable model via `GEMINI_MODEL`, background threading for UI responsiveness, strict conversation context isolation, error mapping, and retry support without prompt duplication.
- Keep `EchoProvider` available for offline testing.
- Automated tests must run completely offline without internet or real API keys using mock transports.
- No third-party dependencies outside the pinned `requirements-m0a.txt` environment. No voice, animations, Windows automation, phone integration, or PC telemetry.
- Commits must pass the active pre-commit security hook after scanning exact content. Never bypass the hook; no push or merge.
- The grant expires after `reports/wp_g_report.md` is delivered or upon Prem's revocation.

