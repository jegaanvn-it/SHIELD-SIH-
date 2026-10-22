# WP-S Report

- Status: Canary passed; read-only working tree scan passed (0 findings); `core.hooksPath` configured; candidate list approved with `PROCEED STAGING`.
- Date: 2026-10-22
- Branch / commit: `m0a-feasibility`; staging in progress for baseline commit.
- WP-U remains inactive.

## Release and environment verification

- Prem reports archive size `8,438,883` bytes and matching archive SHA-256 values from the WP-S register, `Get-FileHash`, and the official checksum line.
- The approved executable is present at `%LOCALAPPDATA%\SARA-tools\gitleaks\v8.30.1\gitleaks.exe`.
- Executable reports version `8.30.1`.
- Verified executable SHA-256: `17157e2ee8b76fc8b1d8bee607a250e34b8a8023c8bc81822d4b5ee4d78fcb7c`.
- `core.hooksPath` configured locally to `.githooks`.

## Canary execution and working-tree scan

- **Canary test:** Executed successfully using a synthetic dummy secret matching default rule `aws-access-token` without the `.+EXAMPLE$` allowlist suffix.
  - Detected: `RuleID: aws-access-token`
  - Exit code: `1`
  - Output: Redacted (`--redact --no-banner`)
  - Cleanup: Temporary canary directory `%TEMP%\sara-gitleaks\canary` verified and cleanly removed.
- **Read-only working-tree scan:**
  - Command: `gitleaks dir . --config .gitleaks.toml --redact --no-banner -v`
  - Exit code: `0`
  - Findings count: `0`
  - Volume scanned: $\approx 259,809$ bytes in $62\text{ ms}$
  - Result: Clean scan.

## Repository-file review

- `.gitleaks.toml` matches the required exact structure: default rules enabled and the only global allowlist entries are path patterns for `.venv/` and `artifacts/`.
- `.githooks/pre-commit` uses POSIX `sh`, `set -e`, fails closed for a missing executable or hash utility, verifies the registered executable SHA-256, and invokes Gitleaks on staged content with explicit `--config .gitleaks.toml` and redacted output.
- `.gitignore` contains all 19 required G5 patterns, preserves the `.env.example` exception, and includes the approved `.claude-flow/` and `sara_battery_report.html` safeguards.
- Read-only `git check-ignore` confirms `.claude-flow/`, `.venv/`, and `artifacts/` are ignored.

## Redaction review

Read-only review covered the 31 candidate paths below for account-specific Windows paths, the current username and computer name, email-like values, and phone-like values. Matched values are omitted.

- `docs/AUTHORIZATIONS.md:27` contains a generic Windows user-path template, not an account-specific path. This is a template false positive.
- `reports/M0A_report.md:290-291` contains digest strings with phone-like numeric substrings. They are technical hash values, not phone numbers.
- No likely personal email, actual account path, or machine identifier was identified. The above template/hash matches are the only reviewed false positives.

## Candidate commit paths

The 31 candidate paths approved for staging and baseline commit:

```text
.env.example
.githooks/pre-commit
.gitignore
.gitleaks.toml
AGENTS.md
M0A_Spec.md
M0B_Spec.md
PRD_v2.md
docs/AUTHORIZATIONS.md
reports/M0A_manual_scoring.md
reports/M0A_report.md
reports/wp_s_report.md
requirements-m0a.txt
spikes/m0a/__init__.py
spikes/m0a/config.example.toml
spikes/m0a/counted_transport.py
spikes/m0a/provider_contract.py
spikes/m0a/request_counter.py
spikes/m0a/run_api_budgeted.py
spikes/m0a/scoring.py
spikes/m0a/test_data/phrases_de.txt
spikes/m0a/test_data/phrases_en.txt
spikes/m0a/test_data/phrases_hi.txt
spikes/m0a/test_data/phrases_ml.txt
spikes/m0a/test_data/phrases_ta-Latn.txt
spikes/m0a/test_data/phrases_ta.txt
spikes/m0a/tests/test_counted_runner.py
spikes/m0a/tests/test_provider_contract.py
spikes/m0a/tests/test_request_counter.py
spikes/m0a/tests/test_scoring.py
spikes/m0a/tests/test_sdk_mock_validation.py
```

## Hook scan command

The hook's configured scan command is:

```sh
"$GL" git --pre-commit --staged --config .gitleaks.toml --redact --no-banner
```

## Files changed in this update

- `reports/wp_s_report.md` — refreshed status reflecting successful canary run, clean working-tree scan, and approval of candidate paths.
- `.gitleaks.toml`, `.githooks/pre-commit`, and `.gitignore` met all requirements and were not modified.

## Completed Gates

- Gitleaks release SHA-256 verified.
- Repository configuration files reviewed and verified.
- Canary execution verified (exit code 1, detection confirmed, cleanup verified).
- Read-only working tree scan clean (exit code 0, 0 findings).
- Candidate path list and redaction review reviewed and approved by Prem (`PROCEED STAGING`).
- `core.hooksPath` set to `.githooks`.
- Staging of the 31 explicit paths authorized.

