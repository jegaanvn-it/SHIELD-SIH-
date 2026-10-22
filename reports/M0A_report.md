# M0A Feasibility Research Report

**Status:** Partial. The official-source research and local-alternative desk review authorized by EXTERNAL M0A are recorded below. M0A is not complete; unresolved findings and unrun acceptance criteria remain open.

**Research access date:** 2026-10-20 UTC  
**Workspace branch / commit at research time:** Unborn master with no commit. The earlier m0a-feasibility branch creation failed because Git could not create .git/HEAD.lock. No Git operation was performed during that research batch. See the current workspace follow-up below for the later verified branch state.  
**Scope performed:** Official documentation research, review of official candidate repositories and PyPI metadata, and a read-only System.Speech installed-voice enumeration under EXTERNAL M0A; later installation and test work is recorded in the dedicated INSTALL M0A section below.  
**Scope not performed:** No Gemini/API request, real API-key value access, billing change, model download, Git metadata operation, or microphone/audio test. The approved pins are now installed in `.venv`; the existing tests and local SDK retry checks are recorded below.

Evidence labels follow AGENTS.md: **Verified** = official-source statement; **Measured** = local command output; **Assumed** = explicit assumption; **Unresolved** = unknown or requiring Prem's decision. Official web sources below were accessed on 2026-10-20 UTC unless otherwise stated.

## Verified

### Gemini SDK and proposed pins

- The official Python package is google-genai. PyPI showed version 2.31.0, released 2026-10-14, Apache-2.0, Python >=3.10, and a Python 3.12 classifier. Google's current TTS guide requires google-genai >=2.25.0 for Python. **Proposed pin:** google-genai==2.31.0.
- PyPI showed pytest 9.1.1, released 2026-06-19, MIT, Python >=3.10. **Proposed pin:** pytest==9.1.1.
- At the time of the EXTERNAL M0A research, these were proposals. During the later INSTALL M0A batch they were reviewed and written into `requirements-m0a.txt`; the first installation attempts failed, but a subsequent authorized retry-disabled install succeeded (see installation results below).
- **Important no-retry finding:** In google-genai v2.31.0, Interactions defaults to retries. A local mock test found that public `HttpRetryOptions(attempts=0)` still produced two transport attempts for a synthetic 503. A private generated-client setting of `retry_config=None` produced one attempt, but is not a verified public production configuration. A supported no-retry strategy remains required before API M0A; do not assume the SDK default or public zero-attempt setting complies.

### Model, modality, and language findings

- The current model catalog lists stable Gemini 3.8 Flash (gemini-3.8-flash), Gemini 3.8 Live (gemini-3.8-live), Gemini 3.8 Flash TTS (gemini-3.8-flash-tts), Gemini 3.8 Flash-Lite TTS (gemini-3.8-flash-lite-tts), and Gemini 3.5 Transcribe (gemini-3.5-transcribe). The catalog says Gemini 2.5 model access is limited to users who actively used those models previously and recommends newer models for new projects.
- The Gemini 3.8 Flash model page lists text, image, video, audio, and PDF input with text output. It does not generate audio and does not support Live API. This is a candidate for the text/provider path, not a voice engine.
- Gemini 3.5 Transcribe advertises automatic language detection, speaker diarization, word timestamps, and custom vocabulary. Its current supported-language table lists English, German, Hindi, and Malayalam among the requested languages, but does not list Tamil. Tanglish is not listed. A missing language from the public table is not evidence of reliable support; Tamil/Tanglish transcription remains unresolved and must not be claimed as supported.
- The Gemini 3.8 Flash TTS and Flash-Lite TTS language table lists English, German, Hindi, Malayalam, and Tamil. The guide says these models automatically detect input language. Tanglish is not explicitly listed. Published language coverage is not a quality or naturalness result; no SARA audio output has been generated or listened to.
- Gemini Live's official language list includes English, German, Hindi, Malayalam, and Tamil among its 99 languages. Live is a separate real-time audio-to-audio path; this listing does not prove Tanglish behavior or the quality of a proposed SARA voice pipeline.
- No current official per-language quality matrix for Gemini 3.8 Flash text responses was found in the model pages reviewed. M0A's language identification and response-language checks remain necessary.
- The deprecation page showed no announced shutdown date for Gemini 3.8 Flash, Live, Flash TTS, Flash-Lite TTS, or 3.5 Transcribe as of access date. Preview/experimental models can have more restricted quotas and lifecycle limits; the M0A candidate list should prefer stable IDs.

### Free tier, pricing, quotas, and billing

- The official pricing table lists Standard free-tier input/output as free of charge for Gemini 3.8 Flash, Gemini 3.5 Transcribe, Gemini 3.8 Flash TTS, and Gemini 3.8 Flash-Lite TTS. The same table marks free-tier content as used to improve Google's products; paid-tier content is marked not used for product improvement.
- Public paid prices shown on 2026-10-20 (not a forecast of use or permission to pay):
  - Gemini 3.8 Flash Standard: $0.75 per 1M input tokens and $3.75 per 1M output tokens through 2026-12-31; scheduled to become $1.50 and $7.50 on 2027-01-01.
  - Gemini 3.5 Transcribe Standard: $2.00 per 1M audio input tokens (about $0.003/minute) and $12.00 per 1M text output tokens (about $0.002/minute); the page estimates a blended rate of about $0.005/minute.
  - Gemini 3.8 Flash TTS Standard: $0.50 per 1M text input tokens and $9.00 per 1M audio output tokens (about $0.00225 per 10 seconds) through 2026-12-31; scheduled to double on 2027-01-01.
  - Gemini 3.8 Flash-Lite TTS Standard: $0.50 per 1M text input tokens and $6.00 per 1M audio output tokens (about $0.0015 per 10 seconds) through 2026-12-31; scheduled to double on 2027-01-01.
- These are mutable public prices. The research did not access the user's AI Studio project or billing account, and therefore did not establish account-specific free-tier availability, active billing status, or current account quotas. No API requests may be made until the official account/model eligibility and disabled-billing preflight required by AGENTS.md and M0A_Spec.md is completed and verified. Billing must not be enabled.
- Google's rate-limit documentation says limits are per project and model-dependent, measured across RPM, input TPM, and RPD; RPD resets at midnight Pacific time. Exact active quotas are shown in AI Studio and remain unknown for this project. Preview/experimental model quotas may be tighter.
- The M0A cap remains 30 total API attempts: 25 planned and at most five separately approved retests. Failed requests count. There must be no automatic retries, concurrent runners, or counter bypass. The SDK retry finding above means a verified no-retry configuration is a prerequisite, not a detail to defer.

### Data handling and local data

- Google's terms say unpaid Gemini API content and responses can be used to provide, improve, and develop Google products and machine-learning technologies; human reviewers may process inputs and outputs. Google says not to submit sensitive, confidential, or personal information to unpaid services. M0A's synthetic-only requirement is essential.
- The terms also state that Gemini API use through a project with active billing is a Paid Service, and that Paid Services' prompts/responses are not used to improve products but can be logged for a limited period for abuse monitoring. This is not permission to enable billing or incur paid usage.
- The terms describe Gemini API as intended for developers building with AI models for professional or business purposes, not consumer use. Because SARA is described as a personal AI companion, this appears to create a terms-suitability question. It is not resolved here; Prem must review the applicable terms and determine whether an official clarification is needed before API use.
- The official zero-data-retention guide says Interactions stores state by default and requires store=false to opt out; Live session-resumption handles can retain text/audio/video state for up to 24 hours; File API assets remain stored until deletion or expiry; Search and Maps grounding retain prompts/context/output for 30 days and that storage cannot be disabled. Explicit context caching also persists by its configured expiry. For M0A, avoid grounding, file upload, Live session resumption, and explicit caching; verify the exact request mode's storage behavior before any API call.
- API key values were not inspected. AGENTS.md's GEMINI_API_KEY-only source and secret-redaction rules remain in force.

### Local/offline candidate desk review

| Candidate | Official evidence and requested language coverage | License / Python and Windows notes | Resource, maintenance, and limitations |
|---|---|---|---|
| Windows System.Speech voices | Microsoft documents that GetInstalledVoices enumerates voices currently installed for the specified API and that locale support depends on installed engines. Local read-only enumeration found one enabled voice: Microsoft Zira Desktop, en-US. | Windows built-in/API capability; no separate Python package pin proposed. The measured result covers System.Speech only, not every Windows speech subsystem. | Only English was confirmed on this machine. No audio was generated or judged; other languages and voice quality remain unverified. |
| faster-whisper | Official repo/PyPI review supports a local transcription candidate, but the reviewed candidate pages did not provide a complete requested-language matrix. No English/Tamil/Tanglish/Malayalam/Hindi/German quality claim is made. | PyPI 1.2.1, MIT, Python >=3.9; classifiers list 3.9, 3.10, and 3.11, not 3.12. Python 3.12 compatibility is therefore not established by the package classifiers. | Official README reports one CPU small-model int8 benchmark at 1m42s and 1,477 MB RAM on an Intel i7-12700K; this is not a measurement of the SARA laptop. GPU use requires NVIDIA CUDA 12/cuDNN 9 per README. Model weights are separate and were not downloaded. |
| Piper | Official voice catalogue lists English, German, Malayalam, and Hindi; Tamil is absent from the current catalogue. Tanglish is not listed. | PyPI 1.8.0, GPL-3.0-or-later, Python >=3.9, with Python 3.12 classifier. Each voice model has its own MODEL_CARD license and must be reviewed separately. | Local neural TTS candidate. Voice weights are separate; no download, installation, latency, resource, pronunciation, or naturalness test was performed. GPL and voice-specific terms need Prem review before adoption. |
| openWakeWord | Official repo says pretrained models currently support English only. This candidate is for a later wake-word milestone, not M0A microphone use. | Source code Apache-2.0; included pretrained models CC BY-NC-SA 4.0. PyPI 0.6.0 metadata requires Python >=3.7 but has no Python 3.12 classifier. Windows installation uses ONNX Runtime because modern TFLite support is unavailable. | Latest PyPI release shown was 0.6.0 from 2024-02-11, so maintenance freshness is a risk. Repository gives only broad hardware examples; actual laptop resource and false-accept behavior are unmeasured. |

## Measured

- Command: System.Speech GetInstalledVoices read-only enumeration; result: one enabled voice, Microsoft Zira Desktop, culture en-US. No audio playback, synthesis, microphone capture, or recording occurred.
- Gemini API attempts in this research batch: 0. The persistent API counter was not opened or changed during this batch; the prior report recorded zero attempts.
- Packages installed/downloaded in this research batch: 0.
- Git operations in this research batch: 0.

## Assumed

- None.

## Unresolved

1. **Account and model eligibility:** Whether the intended Google AI Studio project has unpaid access for each chosen model, its current quota, and whether billing is disabled. These are account-specific and were not inspected.
2. **Terms suitability:** Google's published professional/business-purpose restriction may not fit a personal companion. Prem must resolve this before any API request; no legal interpretation is made here.
3. **Data-handling approval:** Prem must read and accept or decline the free-tier data-handling summary. Personal or private content must never be sent under unpaid terms.
4. **No-retry compliance:** The public Interactions retry option tested did not enforce one attempt (`attempts=0` yielded two mocked POSTs). A private `retry_config=None` override yielded one mocked POST but is not a production-ready supported configuration. Resolve this before API M0A.
5. **Language decisions:** D-2 (TTS), D-3 (voice architecture), D-4 (STT/language ID), D-8 (model IDs), and D-9 (Tanglish strategy) remain Prem's decisions.
6. **Tamil/Tanglish:** Tamil is absent from the current Gemini Transcribe language table; Tanglish is not explicitly listed by the reviewed Gemini TTS, Transcribe, or Live pages. Do not claim support without the prescribed tests and Prem's review.
7. **Voice quality:** Official language listings do not establish naturalness, pronunciation, interruption, echo, latency, or noisy-speech performance. Manual listening and review have not run.
8. **Local runtime fit:** faster-whisper 3.12 compatibility, language results, Windows install behavior, and SARA-laptop resource use are untested. Piper's voice-specific licenses and resource needs are unresolved. System.Speech enumeration does not cover all Windows voice stacks.
9. **Local data controls:** No local conversation-memory implementation or retention behavior was tested in this research phase. Existing PRD privacy, backup, export, deletion, and access-control requirements remain in force.
10. **No M0A completion:** Tier 0, tests, API run, manual scoring, report acceptance, and open-item acceptance were not completed by this EXTERNAL M0A research batch.

## D-2 / D-3 / D-4 / D-8 / D-9 evidence recommendations

These are recommendations for Prem's consideration, not decision outcomes:

- **D-2 — TTS engine:** Keep Gemini 3.8 Flash TTS and Flash-Lite as candidates for the required five listed languages, subject to data-use, billing, and listening tests. The measured System.Speech option currently provides only en-US in the enumerated API. Piper lists four of the five script languages but not Tamil, and each selected voice needs a license review. No Tanglish TTS recommendation is established.
- **D-3 — Voice architecture:** Preserve the separate STT, LLM, and TTS architecture as the M0A comparison baseline, since the current plan measures those stages separately. Treat Gemini Live as an alternative research candidate, not a selected architecture; its real-time language list does not prove Tanglish or user-specific quality. Do not API-test until retries and storage behavior are controlled.
- **D-4 — STT / language ID:** Keep Gemini Transcribe and a local faster-whisper candidate under comparison, with separate language identification assessed as specified. Record Tamil/Tanglish as a material evidence gap: the Gemini Transcribe table omits Tamil, and faster-whisper language results for this project have not been tested.
- **D-8 — Gemini model IDs:** Candidate stable IDs for later Prem approval are gemini-3.8-flash for general text, gemini-3.5-transcribe for transcription, and one of gemini-3.8-flash-tts or gemini-3.8-flash-lite-tts for TTS. Do not treat public free-tier pricing as confirmation of account eligibility. No ID is approved by this report.
- **D-9 — Tanglish speech strategy:** Keep both specification variants unresolved for the planned comparison: Latin-script Tanglish through an English voice and Tamil-script conversion through a Tamil voice. Public docs do not promise Tanglish support; a decision needs permitted API outputs and Prem's listening scores, or must remain unresolved.

## Automated tests

| ID | Description | Result | Evidence |
|---|---|---|---|
| AC-6 | Provider error-handling mock tests | Passed via pytest 9.1.1 in project venv | The existing provider-contract mocks passed with synthetic callbacks; no network calls or SDK client are used by these tests. |
| AC-7 | Scoring helper tests | Passed via pytest 9.1.1 in project venv | All four scoring tests passed with fixed synthetic inputs. |
| SDK-Retry | SDK Interactions no-automatic-retry check | Partial; see evidence | With local `httpx.MockTransport`, public `HttpRetryOptions(attempts=0)` still produced two mocked attempts. Setting the generated client's retry config to `None` produced exactly one mocked attempt. The latter uses a private SDK field and is not a production-ready public configuration. |

## INSTALL M0A execution

- Pin review against the official research already recorded above: `google-genai==2.31.0` meets the recorded SDK minimum and PyPI metadata indicates Python 3.12 support; `pytest==9.1.1` is recorded as supporting Python 3.10 and later. The recorded licenses are Apache-2.0 and MIT respectively. These findings were reviewed from the existing source register; no new external research was performed in this installation batch.
- Created `requirements-m0a.txt` with only the two approved direct pins: `google-genai==2.31.0` and `pytest==9.1.1`.
- The first `python -m venv .venv` attempt failed with exit code 1 in `ensurepip`. Retrying with `TEMP` and `TMP` set to the existing Git-ignored `artifacts/m0a` directory created the venv successfully; `pip==24.3.1` is present.
- Installed the approved `requirements-m0a.txt` pins into the existing venv with one command: `python.exe -m pip install --retries 0 --no-cache-dir --disable-pip-version-check -r requirements-m0a.txt`. It exited 0 and installed `google-genai==2.31.0`, `pytest==9.1.1`, and their resolved dependencies. `pip check` reported no broken requirements. No package beyond the approved dependency set was requested.
- The first sandboxed installation attempt failed because DNS resolution for `pypi.org` was unavailable; pip made five automatic package-index connection retries and exited 1. A later install attempt reached PyPI but returned `ResolutionImpossible` in the `google-genai` Pydantic dependency chain. A subsequent no-install resolver diagnostic resolved the same pins on Python 3.12.9, followed by the successful install recorded above. The earlier resolver failure remains unexplained. These were package-index operations, not Gemini/API requests.
- The latest venv contains Python 3.12.9, `google-genai==2.31.0`, and `pytest==9.1.1`; `pip check` is clean. The previous pip-only inventory is superseded by this successful install.
- Ran `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `PYTHONDONTWRITEBYTECODE=1`, `TEMP=TMP=artifacts/m0a`, and `python.exe -m pytest -p no:cacheprovider -q spikes/m0a/tests`: **11 passed, 9 subtests passed**. The provider-contract, request-counter, and scoring tests use in-memory callbacks, local temporary files, and fixed inputs; source inspection found no Gemini client, network transport, or environment-key read in those tests.
- SDK retry check used `genai.Client` with a custom `httpx.MockTransport` returning a synthetic 503 response; the client used a synthetic placeholder credential, and the process did not read `GEMINI_API_KEY`. First, public `HttpRetryOptions(attempts=0)` failed the one-attempt assertion: the transport received 2 requests. Local installed-source inspection explains this behavior: the legacy retry initializer normalizes `attempts=0` to 1, while the Interactions adapter maps `attempts` to its `max_retries`, yielding one retry. A second local-only check set `client.interactions.sdk_configuration.retry_config=None`; it passed with exactly 1 mocked request. This is an internal generated-client override, not a verified public configuration; automatic retries are not yet safely controlled through the public options for Interactions.
- Ran `spikes/m0a/run_api_budgeted.py --dry-run`: it reported `planned=25`, `used=0`, `reserve=5`, `hard_cap=30`, and `remaining=30`. The persistent counter remained at zero. Source inspection confirms `--execute` is guarded as disabled; that mode was not run.
- No Gemini/API request, real API-key value access, billing change, or Git operation occurred in this batch. PyPI package downloads occurred only for the authorized dependency installation. All SDK test requests were intercepted by `httpx.MockTransport`.

## Manual (Prem) tests

| ID | Description | Status | Notes |
|---|---|---|---|
| MT-A1 | Tanglish speech synthesis | Pending Prem | Not run; requires authorized API output and Prem listening. |
| MT-A2 | Per-language speech synthesis | Pending Prem | Not run; requires authorized API output and Prem listening. |
| MT-A3 | Transcript review | Pending Prem | Not run; requires authorized API output and Prem review. |
| MT-A4 | Reply review | Pending Prem | Not run; requires authorized API output and Prem review. |

## Acceptance criteria status

| Criterion | Status | Evidence |
|---|---|---|
| AC-1 | Not run | Current native-Windows, environment, Git, and API-key-presence evidence was not recertified for this acceptance review. Do not infer current facts from older reports. |
| AC-2 | Met | Official SDK, models, prices, quota rules, free-tier statements, deprecation status, and data handling are recorded above with source URLs and access date; account-specific eligibility remains explicitly Unresolved. |
| AC-3 | Pending Prem | The data-handling summary is recorded above. Prem's acknowledgment is not recorded; no API request was made. |
| AC-4 | Not run | Local counter-aware transport and no-retry mock evidence is recorded below, and the persistent counter remains at zero. No API request was made; account/model free-tier eligibility, disabled billing, and real usage remain unverified. |
| AC-5 | Not run | No API payloads were sent and no microphone test was performed. Local mocks used synthetic data only; they do not establish service-test compliance. |
| AC-6 | Met | The full local M0A suite passed: 36 tests, 9 subtests, 0 failures. Provider and SDK transport tests used local mocks; no service request was made. |
| AC-7 | Met | Scoring tests passed within the local suite; the earlier recorded scoring run reports all four scoring tests passed with fixed inputs. |
| AC-8 | Not run | No completed language matrix or API scoring run is recorded. Language quality, including Tanglish quality, remains unverified; manual cells require Prem's results. |
| AC-9 | Pending Prem | MT-A1 through MT-A4 were not run. They require authorized outputs and Prem/reviewer listening or transcript/reply review. |
| AC-10 | Not run | No real-service latency or usage observations were collected. Real latency remains unverified. |
| AC-11 | Met | Local-option desk review and source register are recorded above; this is a documentation-only review and does not establish runtime suitability or compatibility. |
| AC-12 | Not run | `.gitignore` and `.env.example` were not reverified for this acceptance update. No commit was made, so the pre-commit scan condition has not been triggered; the approved scanner remains unavailable and any commit remains blocked until a scan runs. |
| AC-13 | Met | Evidence-based recommendations for D-2, D-3, D-4, D-8, and D-9 are recorded above without deciding them. |
| AC-14 | Accepted for carry-forward by Prem | Prem issued `ACCEPT M0A OPEN ITEMS` on 2026-10-20 for the unresolved items listed below. This acknowledges their carry-forward only; it does not mark them passed or authorize M0B. |

### Latest evidence and accepted carry-forward items

- **Measured — latest local validation:** 36 tests passed, 9 subtests passed, 0 failures. The actual child-process lock-contention test passed separately (1 passed). Counter-aware non-streaming and streaming integration tests used local `httpx.MockTransport` only. This supersedes earlier dated notes that said the child-process test had not yet run.
- **Verified — safety:** No Gemini/API or network requests, credential access, package installation, or persistent-counter changes occurred in the latest validation. The production CLI remains dry-run-only.
- **Unverified:** Real Google TTS/STT service compatibility; language quality (including Tanglish); selected-model/account free-tier eligibility; billing-disabled status; and real-service latency/usage.
- **Open items explicitly accepted for carry-forward by Prem (`ACCEPT M0A OPEN ITEMS`):** AC-1 current environment recertification; AC-3 data-handling acknowledgment; AC-4 API eligibility/billing and service validation; AC-5 service-test data/microphone evidence; AC-8 language matrix and language-quality results; AC-9 MT-A1 through MT-A4; AC-10 real latency/usage; and AC-12 ignore-file/placeholder re-verification. These criteria remain unrun, pending, or unresolved as stated in the matrix; acceptance does not mark them passed or authorize M0B.
- **Git:** The secret scanner remains unavailable. No commit was made; do not commit unless the required pre-commit scan is available and passes.

## Source register

All sources below were accessed on 2026-10-20 UTC. Findings are paraphrased, not claims that SARA has been tested.

| Topic | Official source URL |
|---|---|
| Gemini current model list and modality catalog | https://ai.google.dev/gemini-api/docs/models |
| Gemini 3.8 Flash model modalities | https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash |
| Gemini TTS requirements and language table | https://ai.google.dev/gemini-api/docs/speech-generation |
| Gemini Transcribe capabilities and language table | https://ai.google.dev/gemini-api/docs/transcribe |
| Gemini Live language list | https://ai.google.dev/gemini-api/docs/live-api/capabilities |
| Gemini per-model pricing/free-tier table | https://ai.google.dev/gemini-api/docs/pricing |
| Gemini quota dimensions and current-quota location | https://ai.google.dev/gemini-api/docs/rate-limits |
| Gemini billing tiers and account project checks | https://ai.google.dev/gemini-api/docs/billing |
| Gemini API terms and unpaid/paid data handling | https://ai.google.dev/gemini-api/terms |
| Gemini retention and feature-specific storage | https://ai.google.dev/gemini-api/docs/zdr |
| Gemini model deprecations | https://ai.google.dev/gemini-api/docs/deprecations |
| Gemini API release notes | https://ai.google.dev/gemini-api/docs/changelog |
| Official Python SDK repository | https://github.com/googleapis/python-genai |
| Pinned v2.31.0 Interactions retry implementation | https://github.com/googleapis/python-genai/blob/v2.31.0/google/genai/_gaos/interactions.py |
| google-genai PyPI release and metadata | https://pypi.org/project/google-genai/ |
| pytest PyPI release and metadata | https://pypi.org/project/pytest/ |
| faster-whisper official repository and resource notes | https://github.com/SYSTRAN/faster-whisper |
| faster-whisper PyPI license, version, and Python classifiers | https://pypi.org/project/faster-whisper/ |
| Piper official repository | https://github.com/OHF-Voice/piper1-gpl |
| Piper official voice catalogue and per-model license notice | https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/VOICES.md |
| Piper PyPI release, license, and Python classifiers | https://pypi.org/project/piper-tts/ |
| openWakeWord official repository, language, platform, and license notes | https://github.com/dscripka/openWakeWord |
| openWakeWord PyPI release and metadata | https://pypi.org/project/openwakeword/ |
| Microsoft installed System.Speech voice enumeration API | https://learn.microsoft.com/en-us/dotnet/api/system.speech.synthesis.speechsynthesizer.getinstalledvoices?view=net-10.0-pp |

## Commands and actions recorded

| Action | Authorization | Result |
|---|---|---|
| Read AGENTS.md and M0A_Spec.md | EXTERNAL M0A prerequisites | Completed before research. |
| Official docs/repository/PyPI browsing from the source register | EXTERNAL M0A | Read-only; findings recorded above. |
| System.Speech GetInstalledVoices enumeration | M0A-11 local candidate review | Read-only; one enabled en-US voice recorded above. |
| Review of proposed dependency pins | INSTALL M0A | Both pins match the official metadata recorded in the source register; no new external request. |
| Create `requirements-m0a.txt` | FILES M0A | Created with only `google-genai==2.31.0` and `pytest==9.1.1`. |
| Create `.venv` | INSTALL M0A | First attempt failed in `ensurepip`; one announced retry with `TEMP`/`TMP` set to `artifacts/m0a` succeeded. Venv contains `pip==24.3.1`. |
| Install pinned dependencies | INSTALL M0A | One retry-disabled install command succeeded for the approved pins and dependencies; `pip check` passed. |
| No-install dependency resolver diagnostic | EXTERNAL M0A | `--dry-run`, `--retries 0`, and `--no-cache-dir`; exited 0 and resolved both direct pins plus Pydantic 2.14.1 / pydantic-core 2.50.1. Full verbose output was not retained. |
| `.venv\Scripts\python.exe -m unittest discover -s spikes\m0a\tests -p 'test*.py' -v` | FILES M0A / INSTALL M0A | After directing `TEMP`/`TMP` to `artifacts/m0a`, passed 11/11 existing tests. The first base-Python attempt had failed on sandbox temp-directory permissions. |
| `python.exe -m pytest -p no:cacheprovider -q spikes/m0a/tests` (plugin autoload and bytecode disabled; TEMP/TMP set to `artifacts/m0a`) | FILES M0A / INSTALL M0A | Passed: 11 tests, 9 subtests, 0 failures. |
| SDK Interactions retry check via inline Python and `httpx.MockTransport` | FILES M0A / INSTALL M0A | Public `HttpRetryOptions(attempts=0)` produced 2 mock calls (failed one-attempt assertion). Setting generated `sdk_configuration.retry_config=None` produced 1 mock call. No real network transport was available. |
| Budget runner dry run | FILES M0A | Completed with no network; persistent counter remained zero and execution guard is present. |
| Gemini API request | Not authorized in this batch | Not performed. |
| API-key value access | Prohibited | Not performed. |
| Git metadata / branch / stage / commit / push operations | Not performed | Git state left untouched. |

## Files changed

- reports/M0A_report.md — replaced the preparation-only research placeholders with the dated official-source findings, local candidate review, unresolved items, decision recommendations, source register, and updated criterion statuses.
- requirements-m0a.txt — created with the two reviewed direct dependency pins.
- .venv/ — project virtual environment; contains `pip==24.3.1`, the approved SDK and pytest pins, and their resolved dependencies.
- spikes/m0a/__pycache__/ and spikes/m0a/tests/__pycache__/ — present after local test execution; `.gitignore` excludes `__pycache__/`.

## Dependency installation status

The approved direct pins are installed unchanged in `.venv`. The one-command install used `--retries 0`; `pip check` passed. The earlier `ResolutionImpossible` remains unexplained, but the subsequent resolver and install both succeeded. Pytest passed all 11 existing tests. SDK Interactions retry control remains a blocker: the documented-looking public `HttpRetryOptions(attempts=0)` path generated two mock calls, while a private `retry_config=None` override generated one. Do not rely on that private override in application code without a supported configuration or a project-controlled no-retry transport design.

### Dependency diagnosis follow-up — 2026-10-20

- **Verified:** `.venv\Scripts\python.exe` reports Python 3.12.9 with `google-genai==2.31.0` and `pytest==9.1.1` installed; `pip check` reported no broken requirements.
- **Verified:** pytest command passed 11 tests and 9 subtests. Existing tests call only synthetic provider callbacks, local temp-file counter operations, and scoring functions; they do not instantiate a Gemini client or read `GEMINI_API_KEY`.
- **Measured:** In the SDK Interactions local transport probe, `HttpRetryOptions(attempts=0)` resulted in two intercepted POSTs for a synthetic 503. With the generated SDK configuration's `retry_config` set to `None`, exactly one intercepted POST occurred. No request escaped `httpx.MockTransport`.
- **Unresolved:** The SDK's public retry configuration did not meet the one-attempt requirement. The private override works in this mock but is not an approved production integration strategy. A supported, reliable no-retry configuration or an app-side guard is needed before API M0A.
- **Verified:** the persistent API counter remains at zero. No real API key was read and no Gemini request was sent.

## Open decisions and next authorization

- Prem retains all D-2, D-3, D-4, D-8, and D-9 decisions; none is resolved here.
- D-6 remains open and is not decided by this report.
- Before API M0A, Prem must review the E5 free-tier data-handling and personal-use terms concern, decide whether those terms are acceptable, approve model IDs, and confirm that billing is disabled and free-tier eligibility is currently verified for the selected project/model.
- Dependency installation and the existing pytest suite are complete. Before any API M0A run, resolve the SDK Interactions retry-control blocker using a supported no-retry strategy and repeat only the local mock transport assertion. Account-specific free-tier eligibility, disabled billing, model approvals, Prem's E5 acknowledgment, and `API M0A` remain separate prerequisites. No API approval is requested or inferred by this report.
- If the official terms or account-specific free-tier/billing state cannot be established, stop with no API request.
- M0B is not recommended or authorized by this partial research report.

## Current workspace and local verification follow-up — 2026-10-20

- **Verified — Git status:** `git status --short --branch` reported `## No commits yet on m0a-feasibility`; `git branch --show-current` reported `m0a-feasibility`. The repository remains unborn and the project paths are untracked. Nothing was staged, committed, or pushed.
- **Secret scan:** The requested pre-commit scan could not run. `gitleaks`, `pre-commit`, `detect-secrets`, and `trufflehog` are unavailable in this environment. No scanner was installed. `git check-ignore .env` confirmed `.env` is ignored; its contents were not read. No commit was attempted. Under G4, a commit remains blocked until an approved secret scan is available.
- **Automated local synthetic tests:** Ran `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q spikes/m0a/tests` with pytest plugin autoload and bytecode disabled and temporary paths directed to `artifacts/m0a`. Result: **11 passed, 9 subtests passed, 0 failures**. No Gemini/API request was made.
- **Persistent API counter:** Read only the numeric counter fields in `artifacts/m0a/request_counter.json`; `attempts=0` (schema version 1). No key value was accessed.
- **SDK retry-control review:** The earlier local `httpx.MockTransport` result remains unresolved: public `HttpRetryOptions(attempts=0)` caused two intercepted attempts; a private generated-client `retry_config=None` override caused one. This task did not rerun that separate SDK probe. Do not use the private override as a supported production solution; no API call is permitted until a supported no-retry approach is established.
- **Manual tests:** MT-A1 through MT-A4 remain not run / Pending Prem. They require generated feasibility outputs and Prem's listening or transcript/reply review; none were produced in this task.
- **Files changed in this follow-up:** `reports/M0A_report.md` only. No tests, scan artifacts, Git metadata, or other project files were written by this follow-up.

## Models SDK mapping local mock validation — 2026-10-20

- **Verified — dependency availability:** The existing `.venv` already contains `google-genai==2.31.0`, `pytest==9.1.1`, and `httpx==0.28.1`. No package was installed or upgraded.
- **Automated focused test command:** `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q spikes/m0a/tests/test_sdk_mock_validation.py spikes/m0a/tests/test_request_counter.py spikes/m0a/tests/test_provider_contract.py`, with pytest plugin autoload disabled, bytecode disabled, and temporary test files confined to a newly created and removed `spikes/m0a/.test-tmp/` directory.
- **Measured — final result:** **25 passed, 9 subtests passed, 0 failures** in 13.70 seconds. All SDK HTTP traffic in these tests was intercepted by `httpx.MockTransport`; no real network or Gemini API request was possible through the test transport.
- **Coverage:** Mocked `Models.generate_content()` request serialization and response extraction for text, TTS audio, and STT audio/transcript; `Models.generate_content_stream()` audio chunk extraction and monotonic mock time-to-first-audio path; public `HttpRetryOptions(attempts=1)` with `automatic_continuation=False`; HTTP 429, HTTP 503, timeout, and connection failure for both methods; continuation fixtures to detect follow-up requests; per-intercepted-request counter increments; rejection of an additional dispatch before the downstream mock handler; hard-cap blocking; counter persistence and missing/corrupt/unreadable fail-closed behavior.
- **Measured — initial test failures:** The first complete run had **21 passed, 9 subtests passed, 4 failed**. Two failures expected camelCase for nested SDK request fields that this installed serializer emitted as snake_case; two streaming failures used an invalid `ByteStream` construction. A targeted diagnostic run then had **2 failed** for the same field-name expectation. The assertions were corrected to match observed SDK serialization and the SSE mock was corrected to provide bytes. The final focused run above passed.
- **Lock limitation:** The lock-contention test simulates `msvcrt.locking` denial and verifies a second `AttemptCounter` fails closed. No child process was launched; actual cross-process lock contention was not tested. The production API runner remains disabled, and the test-only counting transport is not production integration.
- **Unresolved — model compatibility:** These tests validate local SDK serialization and response parsing against synthetic responses only. They do not prove that `gemini-3.8-flash-tts` or `gemini-3.5-transcribe` accepts the request or response shapes at Google's service. No service requests were made.
- **Counter and credentials:** Tests used only temporary counter files; the persistent M0A counter was not opened or changed. No environment key was read. The test client used a synthetic placeholder string, not a credential.
- **Files changed in this follow-up:** `spikes/m0a/tests/test_sdk_mock_validation.py` (created), `spikes/m0a/tests/test_request_counter.py` (updated), and `reports/M0A_report.md` (updated). No other files were intentionally changed; nothing was staged or committed.

## Counter-aware runner local validation — 2026-10-20

- **Authorization:** FILES M0A. No LAUNCH M0A authorization was provided for starting the child Python process required by the real cross-process contention test.
- **Implemented:** Added `spikes/m0a/counted_transport.py`. It requires an active planned-request scope, increments the already-locked `AttemptCounter` before forwarding to its delegate, blocks and counts a second SDK dispatch within the same scope, and fails closed if counter increment fails. Concurrent/nested request scopes are rejected.
- **Implemented:** Added `dispatch_planned_request()` to `spikes/m0a/run_api_budgeted.py`. Non-stream groups dispatch through `Models.generate_content`; API-LAT-TTS dispatches through `Models.generate_content_stream`, with the streaming request scope held while chunks are consumed. The command-line runner remains dry-run-only; `--execute` remains disabled.
- **Added tests:** `spikes/m0a/tests/test_counted_runner.py` covers non-stream and streaming SDK calls through the production wrapper with `httpx.MockTransport`, synthetic responses, HTTP 429/503 one-attempt behavior, unexpected follow-up accounting/blocking, and hard-cap blocking before downstream dispatch.
- **Added test:** `spikes/m0a/tests/test_request_counter.py` now includes a child process that holds a temporary counter lock while the parent attempts a second lock. This test was **not run** because AGENTS.md §2 requires separate `LAUNCH M0A` approval for a child Python process. Existing mocked lock-denial test remains in the locally run suite.
- **Automated local test command:** `.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q --basetemp=artifacts/m0a/test-run-counted-20261020 spikes/m0a/tests -k 'not real_child_process'`, with pytest plugin autoload and bytecode disabled and `TEMP`/`TMP` directed to `artifacts/m0a`.
- **Measured result:** **35 passed, 1 deselected, 9 subtests passed, 0 failures** in 23.04 seconds. The deselected test is the new actual cross-process contention test. The temporary pytest directory was removed after the run.
- **Network/API and counter safety:** All runner integration HTTP calls used `httpx.MockTransport`; no real network or Gemini request was made. Tests used temporary counter files only. The persistent M0A counter was not accessed or changed, and no credential was read. Packages were not installed or upgraded.
- **Unresolved:** Actual OS-level cross-process contention remains unverified until the child-process test is run with LAUNCH M0A. Google's service-side TTS/STT model compatibility remains unverified; this work uses synthetic mock responses only.
- **Files changed:** `spikes/m0a/counted_transport.py` (created); `spikes/m0a/run_api_budgeted.py` (modified); `spikes/m0a/tests/test_counted_runner.py` (created); `spikes/m0a/tests/test_request_counter.py` (modified); `reports/M0A_report.md` (updated). Nothing was staged or committed.

## Final local validation update — 2026-10-20

- **Measured — full M0A suite:** 36 tests passed, 9 subtests passed, 0 failures. The actual child-process lock-contention test also passed separately (1 passed).
- **Verified — counter-aware transport:** Non-streaming and streaming SDK integration tests passed using local `httpx.MockTransport` only.
- **Safety:** No API or network requests, credential access, package installation, or persistent-counter changes occurred. The production CLI remains dry-run-only.
- **Unresolved:** Real Google TTS/STT service compatibility remains unverified. The Git secret scan and commit remain pending; no commit was made.

## Amendment v2.1 note — 2026-10-21

- The ten pre-commit-specific tooling pins were withdrawn by Amendment v2.1. No packages were installed or uninstalled as part of this amendment.

## Proposed pre-commit toolchain pins and artifact hashes — 2026-10-21

- **Verified from published PyPI metadata (2026-10-20 UTC):** The hashes below are PyPI-published SHA-256 digests for the named wheel artifacts. No artifact was downloaded in this task, so none of these hashes has been checked against downloaded file bytes. The PyYAML entry is specifically the CPython 3.12 Windows x64 wheel.
- **Proposed pins added to `requirements-m0a.txt`:**

| Package pin | Proposed wheel | Published SHA-256 (not locally verified) | PyPI metadata |
|---|---|---|---|
| `pre-commit==4.7.0` | `pre_commit-4.7.0-py2.py3-none-any.whl` | `2e229038ad3656081b70c27913157e4b636ef306f643f024a8a8e3f0f7b2f877` | https://pypi.org/pypi/pre-commit/4.7.0/json |
| `cfgv==3.5.0` | `cfgv-3.5.0-py2.py3-none-any.whl` | `a8dc6b26ad22ff227d2634a65cb388215ce6cc96bbcc5cfde7641ae87e8dacc0` | https://pypi.org/pypi/cfgv/3.5.0/json |
| `identify==2.6.20` | `identify-2.6.20-py2.py3-none-any.whl` | `6a16b69b93187244e0548cbfd25b3e4a6f9a7a2ad784625c3bec2b8d27b81aaa` | https://pypi.org/pypi/identify/2.6.20/json |
| `nodeenv==1.11.0` | `nodeenv-1.11.0-py2.py3-none-any.whl` | `edaa16e6c14d7cf395d75d4bbd5a26390f4dc06501a33b4e76282b02cc688a25` | https://pypi.org/pypi/nodeenv/1.11.0/json |
| `PyYAML==6.0.3` | `pyyaml-6.0.3-cp312-cp312-win_amd64.whl` | `5fcd34e47f6e0b794d17de1b4ff496c00986e1c83f7ab2fb8fcfe9616ff7477b` | https://pypi.org/pypi/PyYAML/6.0.3/json |
| `virtualenv==21.14.11` | `virtualenv-21.14.11-py3-none-any.whl` | `b319f8590a84e5de5f8f2c803ecd2237e9bc0ffa7c1e875e3169c107cecb7454` | https://pypi.org/pypi/virtualenv/21.14.11/json |
| `distlib==0.4.3` | `distlib-0.4.3-py2.py3-none-any.whl` | `4b0ce306c966eb73bc3a7b6abad017c556dadd92c44701562cd528ac7fde4d5b` | https://pypi.org/pypi/distlib/0.4.3/json |
| `filelock==4.2.4` | `filelock-4.2.4-py3-none-any.whl` | `301241438c57936ef93f4243a94f2559022268bfcf9b375a9a72eb0f8db8358e` | https://pypi.org/pypi/filelock/4.2.4/json |
| `platformdirs==4.11.10` | `platformdirs-4.11.10-py3-none-any.whl` | `973c4c082b964958c71588448488d2b14fb253893dfbdb82325a14c84e540e8f` | https://pypi.org/pypi/platformdirs/4.11.10/json |
| `python-discovery==1.6.2` | `python_discovery-1.6.2-py3-none-any.whl` | `f0c697f95a3aaec4174a6e5e58f5885e25768684bafc76f1afde384709ebdcf2` | https://pypi.org/pypi/python-discovery/1.6.2/json |

- **Existing dependency:** `packaging==26.3` is already installed and satisfies virtualenv's `packaging>=26.3` requirement. It was not added to `requirements-m0a.txt` as a new install requirement.
- **AGENTS.md X6 review required before installation:** For each of the ten added packages, document maintenance status, license, Windows/Python 3.12 compatibility, and security review in the M0A report. This review is pending; pin selection and published hashes alone do not complete it.
- **Install status:** No packages or artifacts were downloaded or installed for this update. No tests, scans, staging, or commits were performed.

