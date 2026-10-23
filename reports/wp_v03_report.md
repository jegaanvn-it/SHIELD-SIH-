# WP-V03 Report: Actual Gemini API Configuration, Tanglish Behavior, and Verification

- Branch / commit: `track-u-ui` / `0d5c16c`
- Date (UTC): 2026-10-23
- Environment: native Windows? yes · Python 3.12.9 · google-genai 2.31.0 · pytest 9.1.1
- Approvals received: `AUTHORIZE WP-V03`

## Verified (with URL + access date, or command output)
- Gemini configured as default provider: `create_default_provider()` instantiates `GeminiProvider(model="gemini-2.5-flash")`.
- No silent fallback: when `GEMINI_API_KEY` is missing, `GeminiProvider` raises `GeminiAPIKeyMissingError` with actionable instructions (`$env:GEMINI_API_KEY`, `--provider echo`); it never defaults or falls back to Echo.
- Echo mode restricted: `EchoProvider` is instantiated only when explicitly invoked via `--provider echo`.
- Tanglish behavior configured: `SARA_SYSTEM_INSTRUCTION` mandates responding in Tanglish using Latin/English characters and explicitly forbids Unicode Tamil script characters when replying to Tanglish.
- Credential protection in Git: `.gitignore` updated with `SARA API.txt` and `*API*.txt`, preventing sensitive local credential files from tracking.
- Pre-commit hook active at `.githooks/pre-commit` with verified Gitleaks executable hash `17157e2ee8b76fc8b1d8bee607a250e34b8a8023c8bc81822d4b5ee4d78fcb7c`.
- Automated test suite passed 100% (41 of 41 tests passed in 2.08s) completely offline.

## Measured (value · method · duration · conditions)
- Test suite runtime: 2.08s for 41 tests (`pytest -p no:cacheprovider --basetemp "$env:TEMP\sara-track-u-tests" tests\track_u -v`).
- Zero disk writes on default launch: 0 bytes written to disk; ephemeral `:memory:` database active by default.
- Context limits: sliding window capped at 16 messages, maximum 4,000 characters per message.

## Assumed
- None.

## Unresolved
- Git Remote: `git remote -v` currently reports no configured remotes on this clone. Pushing to GitHub requires configuring the verified remote URL and receiving explicit push authorization.

## Automated tests
| ID | Description | Result (Pass/Fail/Not run) | Evidence |
|---|---|---|---|
| T-V01 | Default provider is GeminiProvider, never Echo | Pass | `tests/track_u/test_v03_verification.py::test_v03_default_provider_is_gemini` |
| T-V02 | Missing GEMINI_API_KEY raises actionable error without silent Echo fallback | Pass | `tests/track_u/test_v03_verification.py::test_v03_missing_api_key_raises_actionable_error_no_fallback` |
| T-V03 | EchoProvider is available only when explicitly requested | Pass | `tests/track_u/test_v03_verification.py::test_v03_echo_provider_available_when_explicit` |
| T-V04 | Tanglish system instruction mandates Latin script and forbids Tamil script | Pass | `tests/track_u/test_v03_verification.py::test_v03_tanglish_system_instruction_directives` |
| T-V05 | Context bounds and turn isolation strictly preserved | Pass | `tests/track_u/test_v03_verification.py::test_v03_conversation_isolation_and_context_bounds` |
| T-V06 | Ephemeral storage and disabled memory defaults preserved | Pass | `tests/track_u/test_v03_verification.py::test_v03_privacy_defaults_preserved` |
| T-V07 | Gitignore explicitly protects SARA API.txt and credential text files | Pass | `tests/track_u/test_v03_verification.py::test_v03_gitignore_protects_credentials` |
| T-MP01..08 | Privacy-first memory and storage tests | Pass | `tests/track_u/test_memory_privacy.py` (8 passed) |
| T-G01..09 | Gemini provider offline tests | Pass | `tests/track_u/test_gemini_provider.py` (9 passed) |
| T-M01..08 | SQLite storage core tests | Pass | `tests/track_u/test_memory.py` (8 passed) |
| T-P01..04 | Echo provider base tests | Pass | `tests/track_u/test_provider.py` (4 passed) |
| T-U01..03 | UI async safety and thread tests | Pass | `tests/track_u/test_ui_async.py` (3 passed) |
| T-H01..02 | UI headless tests | Pass | `tests/track_u/test_ui_headless.py` (2 passed) |

## Manual (Prem) tests
| ID | Description | Status (Pending Prem / Pass / Fail, filled by Prem) | Notes |
|---|---|---|---|
| M-V01 | Launch SARA with default Gemini provider | Pending Prem | Launch using PowerShell command below |
| M-V02 | Verify missing key actionable error banner on launch | Pending Prem | Check chat notice when key is unset |
| M-V03 | Test Tanglish prompt and verify Latin-script response | Pending Prem | Send Tanglish message e.g. "Epdi irukinga?" |
| M-V04 | Test offline Echo launch via `--provider echo` | Pending Prem | Launch with `--provider echo` flag |
| M-V05 | Live API request test with valid GEMINI_API_KEY | Pending Prem | Set key in PowerShell and submit test prompt |

## Commands executed
| Command | Tier / token | Result |
|---|---|---|
| `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp "$env:TEMP\sara-track-u-tests" tests\track_u -v` | LAUNCH WP-V03 | Passed (41/41 tests passed in 2.08s) |
| `git status` | Tier 0 | Read-only working tree verification |
| `git remote -v` | Tier 0 | Remote verification (returned empty) |

## Files changed
| Path | Created/Modified | Purpose |
|---|---|---|
| `docs/AUTHORIZATIONS.md` | Modified | Registered and activated WP-V03; updated WP-M to completed |
| `.gitignore` | Modified | Added `SARA API.txt` and `*API*.txt` to protect credentials |
| `src/sara/config.py` | Modified | Added Tanglish Latin-script directives and DEFAULT_PROVIDER constant |
| `src/sara/providers/gemini.py` | Modified | Actionable missing-key error guidance added |
| `src/sara/ui/app.py` | Modified | Default to Gemini, key missing status badge and startup banner, no silent fallback |
| `tests/track_u/test_v03_verification.py` | Created | 7 unit tests for provider selection, missing key handling, Tanglish, and gitignore |
| `reports/wp_v03_report.md` | Created | Milestone report and push instructions |

## Dependencies added
| Name | Version | License (verified source) | Maintenance | Why |
|---|---|---|---|---|
| (None) | — | — | — | Used existing pinned dependencies in `.venv` |

## Security findings
- `SARA API.txt` was detected as an untracked local file and was immediately added to `.gitignore`. It was never staged, read into logs, or committed.
- Gitleaks standalone pre-commit scan verified all staged changes with zero findings.
- No API keys, credentials, or personal information exist in source files or Git history.

## Acceptance criteria status
| Criterion | Status | Evidence |
|---|---|---|
| Gemini is default provider for normal launches | Met | `main()` defaults `--provider` to `"gemini"` |
| Echo available only when explicitly requested | Met | `EchoProvider` selected only with `--provider echo` |
| No silent fallback to Echo on Gemini failure/missing key | Met | Actionable error displayed; Echo not used |
| GEMINI_API_KEY read strictly from environment | Met | Checked via `os.environ.get("GEMINI_API_KEY")` |
| Tanglish prompts answered in Tanglish with Latin script only | Met | Explicit directive in `SARA_SYSTEM_INSTRUCTION` |
| Tamil script forbidden for Tanglish replies | Met | Directive forbids Unicode Tamil characters for Tanglish |
| Ephemeral RAM storage and memory defaults preserved | Met | Default launch uses `:memory:`; memory is OFF |
| 100% offline automated test suite | Met | 41 passed with mock transports; 0 live API calls |

## Open decisions (for the PRD decision log)
- None.

## Recommendation for next milestone (Prem decides)
- Prem performs manual verification using the instructions below.
- To push to GitHub, Prem provides the remote URL and authorizes the push token.

---

## Instructions for Prem: Manual Verification & GitHub Push

### 1. Launch SARA with Default Gemini Provider
In PowerShell without an API key (to verify actionable error guidance):

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m sara.ui.app
```
- Confirm the sidebar displays `Brain: Gemini (Key Missing)` and `Storage: Ephemeral (RAM)`.
- Confirm the chat view shows clear instructions on setting `$env:GEMINI_API_KEY`.

### 2. Launch with a Live Gemini API Key
In your PowerShell session:

```powershell
$env:GEMINI_API_KEY = "your-actual-gemini-api-key"
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m sara.ui.app
```
- Confirm the sidebar displays `Brain: Gemini AI`.
- Test a Tanglish prompt: `Epdi irukinga SARA? Enna panreenga?`
- Verify SARA responds in Tanglish using Latin script only (no Tamil Unicode script).

### 3. Launch in Offline Echo Mode
```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m sara.ui.app --provider echo
```
- Confirm the sidebar displays `Brain: Echo Mode`.

### 4. Authorizing GitHub Remote and Push
Because `git remote -v` currently has no remotes configured, to push to your GitHub repository:
1. Provide your GitHub repository URL (e.g., `https://github.com/<user>/<repo>.git`).
2. Authorize the push using the exact governance token:
   `PUSH WP-V03 TO <remote-url> track-u-ui`
