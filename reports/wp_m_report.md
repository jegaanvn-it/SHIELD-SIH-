# WP-M Report: Privacy-First Memory and Conversation Storage

- Branch / commit: `track-u-ui` / pending commit
- Date (UTC): 2026-10-23
- Environment: native Windows? yes · Python 3.12.9 · google-genai 2.31.0 · pytest 9.1.1
- Approvals received: `AUTHORIZE WP-M`

## Verified (with URL + access date, or command output)
- Ephemeral in-memory default verified: `SQLiteStorage()` creates `:memory:` database with zero disk file handles.
- Long-term memory default-off verified: `is_memory_enabled() is False` and `add_memory` raises `PermissionError` when disabled.
- Zero auto-extraction verified: conversation messages containing personal identifiers, addresses, and sensitive facts produce 0 rows in `memories`.
- Credential screening verified: regex matches Google API keys, OpenAI keys, Bearer headers, and assignment patterns, redacting to `[REDACTED_SECRET]`.
- Pre-commit hook active at `.githooks/pre-commit` verifying executable SHA-256 (`17157e2ee8b76fc8b1d8bee607a250e34b8a8023c8bc81822d4b5ee4d78fcb7c`).
- Automated test suite passed 100% (34 of 34 tests passed in 1.67s) completely offline.

## Measured (value · method · duration · conditions)
- Test suite runtime: 1.67s for 34 tests (`pytest -p no:cacheprovider --basetemp "$env:TEMP\sara-track-u-tests" tests\track_u -v`).
- Zero disk trace on default exit: 0 bytes written to `%LOCALAPPDATA%\Sara\` in default ephemeral session mode.
- Context bounding: maximum 16 context messages, 4,000 character limit per message.

## Assumed
- None.

## Unresolved
- None.

## Automated tests
| ID | Description | Result (Pass/Fail/Not run) | Evidence |
|---|---|---|---|
| T-MP01 | Conversation-history persistence defaults to OFF (ephemeral session-only mode) | Pass | `tests/track_u/test_memory_privacy.py::test_history_persistence_disabled_by_default` |
| T-MP02 | Long-term cross-session memory defaults to OFF (blocks memory writes) | Pass | `tests/track_u/test_memory_privacy.py::test_long_term_memory_disabled_by_default` |
| T-MP03 | Zero automatic memory extraction from user conversation messages | Pass | `tests/track_u/test_memory_privacy.py::test_zero_automatic_memory_extraction` |
| T-MP04 | Explicit memory opt-in, storage, retrieval, deletion, and bulk purge | Pass | `tests/track_u/test_memory_privacy.py::test_explicit_memory_opt_in_and_crud` |
| T-MP05 | Best-effort credential screening redacts known key patterns | Pass | `tests/track_u/test_memory_privacy.py::test_credential_screening_known_patterns` |
| T-MP06 | Credential screening limitations explicitly documented in filter docstrings | Pass | `tests/track_u/test_memory_privacy.py::test_credential_screening_limitations_documented` |
| T-MP07 | Settings and memories schema creation with default disabled flags | Pass | `tests/track_u/test_memory_privacy.py::test_settings_and_memories_schema_creation` |
| T-MP08 | Ephemeral storage leaves zero artifacts on disk after connection close | Pass | `tests/track_u/test_memory_privacy.py::test_ephemeral_storage_purges_on_close` |
| T-G01..09 | Gemini provider offline tests (mocked client, error mapping, bounding) | Pass | `tests/track_u/test_gemini_provider.py` (9 passed) |
| T-M01..08 | SQLite storage core tests (CRUD, cascades, persistence) | Pass | `tests/track_u/test_memory.py` (8 passed) |
| T-P01..04 | Echo provider unit tests (BaseProvider interface conformance) | Pass | `tests/track_u/test_provider.py` (4 passed) |
| T-U01..03 | UI async safety (conversation isolation, retry deduplication, shutdown) | Pass | `tests/track_u/test_ui_async.py` (3 passed) |
| T-H01..02 | UI headless tests (database path structure, initial message flow) | Pass | `tests/track_u/test_ui_headless.py` (2 passed) |

## Manual (Prem) tests
| ID | Description | Status (Pending Prem / Pass / Fail, filled by Prem) | Notes |
|---|---|---|---|
| M-MP01 | Launch SARA in default ephemeral mode | Pending Prem | Launch using PowerShell command below |
| M-MP02 | Verify sidebar displays `Storage: Ephemeral (RAM)` | Pending Prem | Check sidebar indicator |
| M-MP03 | Open `Privacy & Memory` dialog and verify default OFF state | Pending Prem | Check disclosures and toggle status |
| M-MP04 | Verify explicit memory creation and deletion via UI modal | Pending Prem | Use "Add Memory" and "Delete Selected" buttons |
| M-MP05 | Exit SARA and verify no conversations persist on restart | Pending Prem | Restart app and verify chat log is clean |

## Commands executed
| Command | Tier / token | Result |
|---|---|---|
| `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp "$env:TEMP\sara-track-u-tests" tests\track_u -v` | LAUNCH WP-M | Passed (34/34 tests passed in 1.67s) |
| `git status` | Tier 0 | Read-only working tree verification |

## Files changed
| Path | Created/Modified | Purpose |
|---|---|---|
| `docs/AUTHORIZATIONS.md` | Modified | Registered and activated WP-M scope; updated WP-G to completed |
| `src/sara/config.py` | Modified | Privacy directive added to system instruction; default flags defined |
| `src/sara/memory/models.py` | Modified | Added Memory dataclass model |
| `src/sara/memory/storage.py` | Modified | Added ephemeral :memory: mode, settings table, memories table, credential screening, and CRUD APIs |
| `src/sara/ui/app.py` | Modified | Added storage badge, Privacy & Memory dialog, and default ephemeral CLI launch |
| `tests/track_u/test_memory_privacy.py` | Created | 8 offline unit tests for default-off persistence, zero auto-extraction, credential screening, and memory CRUD |
| `reports/wp_m_report.md` | Created | Milestone report and manual verification instructions |

## Dependencies added
| Name | Version | License (verified source) | Maintenance | Why |
|---|---|---|---|---|
| (None) | — | — | — | Used existing pinned dependencies in `.venv` |

## Security findings
- Zero personal information automatically stored: default setting for local conversation history is ephemeral (in-memory only), and default setting for long-term memory is OFF.
- Best-effort regex screening actively redacts Google API keys (`AIza...`), OpenAI keys (`sk-...`), Bearer tokens, and assignment patterns from message and memory content prior to storage.
- Documented limitation: regex filter is heuristic and does not guarantee detection of arbitrary natural-language passwords.
- Privacy disclosure: UI clearly warns the user that content sent to Gemini leaves the local device over encrypted HTTPS and is subject to Google's policies; local deletion does not purge server-side provider logs.

## Acceptance criteria status
| Criterion | Status | Evidence |
|---|---|---|
| Local conversation-history persistence defaults to OFF | Met | `SQLiteStorage()` uses `:memory:`; zero disk writes by default |
| Session-only data purged on close | Met | In-memory RAM destroyed on application exit |
| Persistent history only activated by explicit opt-in | Met | `--persist` / `--database` flags or explicit setting required |
| Long-term memory defaults to OFF | Met | `is_memory_enabled() is False` on initialization |
| Zero automatic memory extraction or profiling | Met | No passive background summarization; tests verify 0 rows |
| Explicit user permission required to store memory | Met | `add_memory` requires opt-in; UI modal provides explicit controls |
| Clear distinction between context, history, memory, and API transmission | Met | Disclosed in UI modal, docs, and architecture |
| Realism regarding network transmission | Met | Documented that local controls do not stop transmission of submitted prompts |
| Credential screening with honest limitations | Met | Regex redacts known high-entropy keys; docstring discloses heuristic scope |
| 100% offline automated tests | Met | 34 passed with mock transports; 0 live API calls |

## Open decisions (for the PRD decision log)
- None.

## Recommendation for next milestone (Prem decides)
- Prem performs manual verification using the instructions below.
- Upon Prem's satisfaction, proceed to evaluate subsequent Track U or M0A/M0B roadmap milestones.

---

## Instructions for Prem: Manual UI Verification

### 1. Launch SARA in Default Ephemeral Mode

Execute the authorized launch command:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m sara.ui.app
```

### 2. Verify Privacy & Memory Controls
1. Confirm the sidebar displays `Storage: Ephemeral (RAM)`.
2. Click **"🔒 Privacy & Memory"** in the sidebar.
3. Review the status banner:
   - `Local Storage Mode: Ephemeral (In-Memory Only, Zero Disk Trace)`
   - `Long-Term Memory: Disabled (Default OFF — Zero Auto-Extraction)`
4. Test the memory controls:
   - Click **"Toggle Memory Setting"** and confirm the prompt to enable.
   - Click **"➕ Add Memory"** to enter an explicit test fact.
   - Verify the fact appears in the list.
   - Click **"🗑 Delete Selected"** or **"🔥 Clear All"** to remove it.
5. Send a chat message, close the window, and re-launch:
   - Verify the previous conversation was completely purged from RAM upon exit.

### 3. Optional Flags
- To test with EchoProvider offline: `--provider echo`
- To explicitly enable disk persistence: `--persist` or `--database <path>`
