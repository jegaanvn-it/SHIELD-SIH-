# M0A Specification — Environment, Gemini Verification, and Language/Voice Feasibility

Version 2.0 · 2026-10-20 · Owner: Prem · Branch: `m0a-feasibility`

**Authority.** `AGENTS.md` governs. Rule IDs (R1, E2, H5, ...) refer to it. If anything here conflicts with `AGENTS.md`, the stricter rule wins. This spec authorizes **M0A only** (R1); it does not authorize M0B, the MVP, or any application code.

**Nothing in this file is a result.** No model, price, quota, free-tier status, language quality, or hardware fact has been verified. Do not copy claims from this file into the report as Verified.

---

## 1. Objective

Produce **evidence** (not an application) for:
1. The state of the repo, Git, Python, and installed packages.
2. The current official Gemini SDK, models, pricing, quotas, free-tier eligibility, and data-handling terms.
3. Whether Gemini (and local options reviewed on paper) can handle **English, Tamil, Tanglish, Malayalam, Hindi, German** for transcription, language identification, response-language consistency, and speech synthesis, each measured separately.
4. Latency and API-usage observations.
5. Inputs for decisions D-2, D-3, D-4, D-8, D-9 (PRD §15).

## 2. Hard limits recap (from AGENTS.md)

- Native Windows only (S1). If WSL or non-Windows, **stop and report**.
- No elevation, no billing, no installs without `INSTALL M0A`, and no M0A project-file writes outside the paths listed for `FILES M0A`. The one-time backup and Git initialization preparation tokens in §3 and `AGENTS.md` §2 authorize only their specifically defined operations; they do not expand the `FILES M0A` project-file allowlist. Before an API request, verify the selected model's current free-tier eligibility from approved official sources and obtain Prem's confirmation that billing is disabled for the API project. If either cannot be verified, make no API requests.
- **No Gemini request** until: `API M0A` token + approved model IDs + Prem has read the data-handling summary (E1, E5).
- **Hard cap: 30 API attempts** including failures, timeouts, and separately approved retests; no automatic retries (E2).
- **Synthetic data only.** No personal documents, screenshots, clipboard, notifications, private recordings (E3). **M0A does not use the microphone at all.**
- Codex must not claim results of Manual (Prem) tests (H5).

## 3. Approval tokens needed

| Token | Used for |
|---|---|
| `APPROVE M0A` | Start M0A; authorizes its Tier 0 read-only inspection, but no other token-scoped action |
| `BACKUP M0A SARA TO <absolute-path>` | One-time, non-destructive copy of the entire SARA workspace, including hidden files, to the exact absolute destination named in the token. Before approval, resolve and display the destination; verify it is outside both the SARA workspace and OneDrive and has sufficient free space. Prem must issue the token naming that verified destination. Treat the source and backup as sensitive. Do not overwrite an existing destination or move, delete, or alter source files. Verify the copied inventory and file hashes without displaying file contents. If the destination exists, is unavailable, any check fails, or verification fails, stop. This token authorizes no other write. Any retry requires a new token. See `AGENTS.md` §2. |
| `INIT GIT SARA` | One-time authorization for exactly one ordinary non-bare `git init` in the canonical workspace `C:\Users\<user>\OneDrive\Documents\SARA`, where `<user>` is the current Windows profile directory name. Before running it, verify the resolved current directory exactly matches that path and that `.git` is absent. It authorizes creation of Git metadata in `.git` only, including the initial unborn `HEAD` state inherent to `git init`. It does not authorize modifying project files, creating a branch ref, checking out or switching branches, staging, committing, pushing, or any other Git operation. If the command fails, stop; any retry requires a new token. See `AGENTS.md` §2. |
| `ACCEPT M0A OPEN ITEMS` | Acknowledge only the pending, unresolved, unavailable, or not-met items listed in the M0A report; does not mark them passed or authorize M0B |
  | `FILES M0A` | Create files **only** in: `spikes/m0a/`, `reports/`, `artifacts/m0a/` (git-ignored), `.gitignore`, `.env.example`, and `requirements-m0a.txt` |
| `EXTERNAL M0A` | Read-only fetch of official docs from: `ai.google.dev`, `github.com/googleapis/python-genai`, `pypi.org`, `learn.microsoft.com`, `docs.python.org`, plus the official repos/PyPI pages of local candidates reviewed in task M0A-11 |
| `INSTALL M0A` | Create `.venv`; install pinned packages in §7 into it |
| `API M0A` | The planned Gemini run in §8 (25 planned attempts only), after model IDs are approved, billing/free-tier status is verified, and the E5 summary is read |
| `APPROVE RETEST M0A <request-ID>` | One additional API attempt for the specific request ID shown to Prem, within the five-attempt reserve; each retest needs its own token before the request |

`BACKUP M0A SARA TO <absolute-path>` and `INIT GIT SARA` are one-time workspace-preparation tokens, not milestone-start approvals. Neither starts M0A or authorizes unrelated milestone actions, and neither implies `FILES M0A`, `INSTALL M0A`, `EXTERNAL M0A`, or `API M0A`. `INIT GIT SARA` does not create a branch ref or the `m0a-feasibility` branch; branch creation remains a separate `FILES M0A` action after `git status` review. The initial unborn `HEAD` state inherent to ordinary non-bare `git init` is permitted as Git metadata only.

## 4. Tier 0 commands for this milestone (no separate command token)

`APPROVE M0A` is required before Tier 0 work begins; no separate token is needed for each Tier 0 command. Use the master list in `AGENTS.md` §3.1. M0A uses: platform checks, `python --version`, `py -0p`, `where.exe python`, `pip --version`, `pip list`, `git status`, `git branch --show-current`, `git log -5 --oneline`, `git diff --stat`, the `GEMINI_API_KEY` presence check, and the installed-voices command. Do **not** run `Get-ChildItem Env:`.

## 5. Needs-approval commands (examples)

```powershell
git switch -c m0a-feasibility                  # FILES M0A (branch creation); only after git status shows no foreign changes (G1, G2)
python -m venv .venv                           # INSTALL M0A
.\.venv\Scripts\python -m pip install -r requirements-m0a.txt   # INSTALL M0A
.\.venv\Scripts\python -m pytest spikes\m0a\tests               # FILES M0A (tests exist), mocks only, no network
.\.venv\Scripts\python spikes\m0a\run_api_budgeted.py --dry-run # FILES M0A; dry run prints the plan and makes NO request
.\.venv\Scripts\python spikes\m0a\run_api_budgeted.py --execute # API M0A only
```

## 6. Tasks

| ID | Task | Type | Token |
|---|---|---|---|
| M0A-01 | Inspect repo and Git state: branch, status, last commits, existing files. If the tree has foreign changes, **stop** (G2). | Automated (Tier 0) | APPROVE |
| M0A-02 | Inspect Python version(s), `pip list`, whether `.venv` exists, installed google SDKs (note deprecated `google-generativeai` if present). | Automated | APPROVE |
| M0A-03 | Confirm native Windows (not WSL). | Automated | APPROVE |
| M0A-04 | Check `GEMINI_API_KEY` **presence only**. Never print or read the value. | Automated | APPROVE |
| M0A-05 | Verify from **official docs**: current `google-genai` version and requirements; model list and capabilities (text, image, audio input, TTS, Live); free-tier eligibility per model; rate limits; pricing; deprecations/changelog; supported languages for audio/TTS. Record URL + UTC access date for each fact. Do not use third-party blogs as Verified sources. | Automated (docs) | EXTERNAL |
| M0A-06 | Write the **data-handling summary** (E5): current official terms on free-tier vs paid data use, retention, and model-improvement policy, with quotes limited to short excerpts and URLs. Present to Prem; **wait for `API M0A`**. | Automated (docs) → Manual (Prem) approval | EXTERNAL |
| M0A-07 | Build the minimal test harness in `spikes/m0a/` (see §7.2): persistent request counter initialized to zero during harness setup, redaction, no auto-retry, synthetic data only, `--dry-run`. | Automated | FILES, INSTALL |
| M0A-08 | Mock-based tests of provider error handling: invalid key, quota exhaustion (429), timeout, network failure, unsupported model, empty response. **No network.** | Automated | FILES, INSTALL |
| M0A-09 | Unit tests of scoring scripts (CER, label match, script-range check) with fixed inputs. **No network.** | Automated | FILES, INSTALL |
| M0A-10 | Execute the budgeted Gemini run (§8) and save raw outputs to `artifacts/m0a/` (ignored). | Automated | FILES, API |
| M0A-11 | Desk review (no installs, no downloads of models) of local candidates: Windows built-in voices (installed-voices command), `faster-whisper`, Piper, `openWakeWord` (for later): language coverage for the six modes, license (including model/voice licenses), maintenance, Windows/Python 3.12 support, resource needs. | Automated (docs) | EXTERNAL |
| M0A-12 | Record usage metadata returned by the API (tokens/audio seconds if present). Estimate cost **only** if official pricing was verified; label estimate vs provider-reported. | Automated | API |
| M0A-13 | Run automated scoring (§9) and generate the blank manual scoring sheets for Prem. | Automated | FILES |
| M0A-14 | Manual listening/reading tests MT-A1 … MT-A4 (§10). | **Manual (Prem)** | — |
| M0A-15 | Write `reports/M0A_report.md` using the AGENTS.md template plus the M0A tables in §11. | Automated | FILES |

## 7. Harness and dependencies

  ### 7.1 Pinned dependency list (pins verified from PyPI/official source)
  
  Preserve the approved `google-genai==2.31.0` and `pytest==9.1.1` pins in `requirements-m0a.txt`. The proposed pre-commit-specific toolchain pins are withdrawn by Amendment v2.1 and must not be added as M0A requirements. Gitleaks, if separately approved for the Git handoff, is a standalone tool installed outside the repository under its separate work-package authorization; it is not an M0A Python dependency. Any future dependency change requires the applicable `INSTALL` authorization and the X6 review in `AGENTS.md`. No packages for audio playback are installed; Prem plays WAV files with Windows' default player. Optional offline language detector: **not installed** in M0A (desk-review only).

### 7.2 Harness requirements (`spikes/m0a/`)

- Reads the key only from `GEMINI_API_KEY`; refuses to run if unset; never logs it.
- Persistent request counter file in `artifacts/m0a/request_counter.json`; initialize it to zero during FILES-authorized harness setup, before API authorization. One counter covers the entire M0A feasibility run across process restarts and is never reset. It increments **before** every request attempt, including failed attempts. Use an interprocess lock and allow only one API runner at a time. If the initialized counter is missing, corrupt, unreadable, or cannot be locked, fail closed and make no request; do not recreate or reset it.
- SDK method mapping: use the public `client.models.generate_content()` method for the non-streaming groups in §8. Use the public `client.models.generate_content_stream()` method only for API-LAT-TTS, where the measurement is time from dispatch until the first audio data is received.
- Configure the public SDK HTTP retry options with `HttpRetryOptions(attempts=1)` for both methods. Set `automatic_continuation=False` in the public generation config where supported and applicable. If the installed SDK cannot apply these controls to a method, or a local mock shows more than one transport request for one intended request, stop that item and make no API request with that configuration.
- Count at the transport boundary: immediately before each SDK-generated HTTP request is forwarded to the underlying transport, increment and durably persist the shared counter once. Every retry, continuation request, timeout, and failed transport dispatch counts separately. If the increment fails, do not forward that HTTP request. Forward at most one transport request for each planned request: if another is intercepted for the same planned request, count it and reject it before network dispatch, then abort that item. One intended request consumes exactly one counter attempt only when its SDK call produces exactly one intercepted transport request. Hold the interprocess lock for the entire API runner invocation so only one runner can be active; do not run concurrent or overlapping SDK calls.
- No automatic retries; on 429/timeout/network error, records the error and **stops that item**.
- Per-request timeout (e.g., 60 s, configurable); records wall-clock latency (monotonic clock).
- Every request uses only inputs from `spikes/m0a/test_data/` (synthetic phrases in §12). Fails if given any other input path.
- Models come from a config file (`spikes/m0a/config.example.toml`, no secrets), filled after Prem approves IDs (D-8).
- `--dry-run` prints planned requests and counts without any network call.
- Writes redacted logs; saves audio to `artifacts/m0a/audio/` (ignored).

## 8. Gemini request budget (hard cap 30, E2)

The `API M0A` token authorizes the 25 planned attempts below, not the reserve. The total cap is 30 attempts across the M0A feasibility run and all process invocations. Before each optional reserve attempt, present Prem with its unique request ID, purpose, model, and current counter value; that attempt requires a separate `APPROVE RETEST M0A <request-ID>` token. The token authorizes one attempt only. No retry is automatic, and a failed request consumes one attempt. If the persistent counter cannot be read or locked, stop without making an API request. Apply the §7.2 transport-boundary accounting rule: each intercepted outbound HTTP request consumes one counter attempt before dispatch, including any retry or continuation request. The public retry setting must permit one attempt, and automatic continuation must be disabled where supported; the transport guard rejects any additional dispatch for the same planned request before it reaches the network. If local mocks show that a method cannot be guarded this way, do not make API calls with it.

| Group | Purpose | SDK method | Planned requests |
|---|---|---|---|
| API-00 | Connectivity/model availability check (one minimal call; only after billing and free-tier preflight) | `client.models.generate_content()` | 1 |
| API-LAT | Text-latency probes (short prompts) | `client.models.generate_content()` | 3 |
| API-LID | Language ID + reply generation, **one batched request per mode** (EN, TA, TA-Latn, ML, HI, DE; 10 phrases each) | `client.models.generate_content()` | 6 |
| API-TTS | Speech synthesis of the 10 phrases, **one request per mode** | `client.models.generate_content()` | 6 |
| API-STT | Transcription of the audio produced by API-TTS, one per mode | `client.models.generate_content()` | 6 |
| API-TLX | Tanglish extras: (1) Tamil-script version of the Tanglish phrases through a Tamil voice, (2) Latin Tanglish through an English voice | `client.models.generate_content()` | 2 |
| API-LAT-TTS | Single short sentence; measure time from dispatch to first audio data | `client.models.generate_content_stream()` | 1 |
| **Planned total** | | | **25** |
| Reserve | Retests; each requires `APPROVE RETEST M0A <request-ID>` before the attempt | Same method as the request being retested | 5 |
| **Hard cap** | | | **30** |

This SDK method mapping does not establish that a candidate model supports the planned modality, payload, language, or response. Verify those model-specific capabilities separately using the approved official-source process and local mocks before any API request. Model IDs still require Prem's approval and must come from configuration (E1, E6).

Notes and known limitations of this design (record in the report as **Assumed/Unresolved**):
- Batching 10 phrases per request saves quota but is not the same as single-turn latency; latency is measured separately (API-LAT, API-LAT-TTS).
- STT input is **TTS-generated audio**, which is cleaner than real speech; it does not measure accents or background noise. Real-voice and noisy-audio STT tests are **deferred** to the push-to-talk milestone (Wave 2) and need Prem's consent. Report as **Unresolved**.
- If the chosen audio model cannot take a batch or a long clip, Codex stops and asks; it does not silently split into more requests.

If a request is needed beyond 25 planned, Codex requests approval for each (max 5).

## 9. Test matrix and pass criteria

Preliminary pass threshold: **≥ 8 of 10 phrases** per language per dimension. A language is **"Supported (preliminary)"** only if all four dimensions pass; otherwise **"Partial"** listing the failed dimensions. Do not claim full support (PRD V-4).

| # | Dimension | How scored | Type | Phrase passes when |
|---|---|---|---|---|
| D1 | **Transcription (STT)** | Normalize (lowercase, strip punctuation/extra spaces), compute character error rate vs reference; Prem judges meaning and script | Automated (CER) **+** Manual (Prem) | CER ≤ 0.20 **and** Prem rates Understanding ≥ 2 and Script/Display = Pass. CER is a *preliminary* proxy; transliteration differences can inflate it, so Prem's judgment decides conflicts and the conflict is reported |
| D2 | **Language identification** | Label returned by the model vs expected tag: `en`, `ta`, `ta-Latn`, `ml`, `hi`, `de` | Automated | Exact match. For Tanglish, `ta-Latn` (or an explicit "Tamil in Latin script/Tanglish" label) passes; `en` fails |
| D3 | **Response-language consistency** | Automated Unicode-script check of the reply (Tamil block, Malayalam block, Devanagari, Latin) as a pre-filter; then Prem reviews language and naturalness | Automated + Manual (Prem) | Script check passes **and** Prem rates Understanding ≥ 2, Naturalness ≥ 2, Script/Display = Pass (Tanglish reply must be Latin-script Tamil, not Tamil script and not plain English) |
| D4 | **Speech synthesis (TTS)** | Prem listens to the audio | Manual (Prem) | Understanding ≥ 2 **and** Naturalness ≥ 2 (pronunciation acceptable) |

Extra honesty check (informational, within D3 review): phrases 3 and 4 in each set are commands (timer, open folder). The model has **no tools** in M0A; replies must **not claim the action was done**. Record pass/fail per language (`H-claim`). A failure is a finding for Sara's honesty design, not an API error.

**Non-assessable languages.** If Prem cannot judge a language (e.g., Malayalam, Hindi, German), he records **"Not assessable by Prem"**, or a trusted reviewer completes the sheet (record reviewer initials only; no personal details). A language without a competent human review cannot be marked Supported; report as **Unresolved**.

## 10. Manual (Prem) tests

Codex prepares the files and blank result sheets; **Prem performs and records results**. Codex must not fill them.

### MT-A1 — Tanglish speech synthesis (Manual (Prem))
1. Open `artifacts/m0a/audio/tanglish_latin_tamilvoice.wav` (Latin-script Tanglish through the Tamil voice).
2. Play all 10 phrases. For each phrase, score Understanding (1–3) and Naturalness (1–3).
3. Repeat for `tanglish_tamilscript_tamilvoice.wav` (API-TLX-1) and `tanglish_latin_englishvoice.wav` (API-TLX-2).
4. Write which variant sounded best and a one-line reason.
**Expected:** a decision-relevant comparison. **Pass:** the variant used for the final recommendation scores ≥ 8/10 phrases with Understanding ≥ 2 and Naturalness ≥ 2. If none pass, the Tanglish speech strategy remains **Unresolved** (D-9).

### MT-A2 — Per-language speech synthesis (Manual (Prem))
1. For EN, TA, ML, HI, DE: play the language's WAV (API-TTS).
2. Score each of the 10 phrases for Understanding and Naturalness.
**Pass:** ≥ 8/10 phrases meet D4 for that language.

### MT-A3 — Transcript review (Manual (Prem))
1. Open the transcript sheet per language (reference next to model transcript).
2. For each phrase, score Understanding (1–3) and Script/Display (Pass/Fail).
**Pass:** ≥ 8/10 phrases meet D1 (with the automated CER).

### MT-A4 — Reply review (Manual (Prem))
1. Open the reply sheet per language (user phrase, detected label, reply).
2. Score Understanding, Naturalness, Script/Display; mark `H-claim` for phrases 3 and 4.
3. Note whether mixed-language/technical terms (Python, SQL, Flask, pandas) were preserved.
**Pass:** ≥ 8/10 phrases meet D3; `H-claim` passes for both command phrases.

### Scoring rubric (all manual tests)
- **Understanding (1–3):** 1 = meaning lost or wrong · 2 = mostly clear, minor issues · 3 = fully clear.
- **Naturalness (1–3):** 1 = robotic/awkward/wrong register · 2 = acceptable · 3 = natural.
- **Script/Display (Pass/Fail):** Pass = correct script for the mode (Tamil script for `ta`, Latin letters for `ta-Latn`, Devanagari for `hi`, Malayalam script for `ml`, correct German characters), no garbled characters/missing glyph boxes.

### Result-recording template (one row per phrase; copy per language and test)

```markdown
Reviewer: <Prem | initials> · Date: <YYYY-MM-DD> · Test: <MT-A#> · Language/mode: <...>
| Phrase | Understanding (1–3) | Naturalness (1–3) | Script/Display (P/F) | H-claim (P/F, phrases 3–4 only) | Notes |
|---|---|---|---|---|---|
| 01 | | | | | |
| ... | | | | | |
| 10 | | | | | |
Phrases passing: __/10   Result: PASS (≥8/10) | FAIL | Not assessable by reviewer
```

## 11. Report additions (beyond the AGENTS.md template)

Add to `reports/M0A_report.md`:
1. **Official-source table:** fact · value · URL · access date (UTC) · label.
2. **Language matrix:** rows = six modes; columns = D1–D4 with `x/10`, label (Passed/Failed/Pending Prem/Not run/Not assessable); overall = Supported (preliminary) | Partial | Not supported | Unresolved.
3. **API usage ledger:** request ID · group · model ID · latency · usage metadata (provider-reported) · result; total used vs cap.
4. **Latency table:** text probes (min/median/max), TTS first-audio probe; conditions (network, time).
5. **Cost/usage:** provider-reported usage; any estimate clearly labeled with the verified pricing source (or "Not estimated").
6. **Local-option desk review:** engine · languages · license · maintenance · Windows/Py3.12 · notes (all with sources).
7. **Evidence for decisions** D-2, D-3, D-4, D-8, D-9 with a recommendation; **Prem decides** (H7).
8. **Unresolved list** (must include: real-voice and noisy-audio STT, speech interruption/echo, Tanglish if not passed).

## 12. Synthetic test phrases (10 per mode; contain no personal data)

Keep phrase files at `spikes/m0a/test_data/phrases_<mode>.txt`, one phrase per line, in this order. Phrases 3–4 are command-type; phrase 5 contains a technical string kept verbatim.

### English (`en`)
1. What is the difference between a list and a tuple in Python?
2. Explain how a SQL JOIN works with a small example.
3. Set a study timer for twenty five minutes.
4. Can you open the notes folder?
5. Why does my Flask app say "address already in use"?
6. Give me three practice questions on pandas DataFrames.
7. Summarize what gradient descent does in two sentences.
8. What time should I take a break if I started at six?
9. Tell me a joke about programmers, but keep it friendly.
10. Please speak more slowly.

### Tamil (`ta`, Tamil script)
1. பைத்தானில் லிஸ்ட் மற்றும் டூப்பிள் இடையே என்ன வேறுபாடு?
2. SQL JOIN எப்படி வேலை செய்கிறது என்பதை ஒரு சிறிய உதாரணத்துடன் விளக்கு.
3. இருபத்தைந்து நிமிடங்களுக்கு படிப்பு டைமர் வை.
4. குறிப்புகள் கோப்புறையைத் திற.
5. என் Flask செயலி "address already in use" என்று காட்டுகிறது, ஏன்?
6. பாண்டாஸ் டேட்டாஃப்ரேம் பற்றி மூன்று பயிற்சி கேள்விகள் கொடு.
7. கிரேடியன்ட் டிசென்ட் என்ன செய்கிறது என்பதை இரண்டு வாக்கியங்களில் சொல்.
8. ஆறு மணிக்குத் தொடங்கினால் எப்போது இடைவேளை எடுக்கலாம்?
9. புரோகிராமர்களைப் பற்றி ஒரு நட்பான நகைச்சுவை சொல்.
10. தயவுசெய்து மெதுவாகப் பேசு.

### Tanglish (`ta-Latn`, Tamil in Latin letters)
1. Python-la list-ku tuple-ku enna difference?
2. SQL JOIN eppadi work aagum, oru chinna example-oda sollu.
3. Iruvathi anju nimisham study timer vei.
4. Notes folder-ah open pannu.
5. En Flask app "address already in use" nu kaattuthu, yen?
6. Pandas DataFrame pathi moonu practice questions kudu.
7. Gradient descent enna pannum nu rendu sentence-la sollu.
8. Aaru mani-ku start panninaa break eppo edukkalam?
9. Programmers pathi oru friendly joke sollu.
10. Konjam slow-aa pesu please.

### Malayalam (`ml`)
1. പൈത്തണിൽ ലിസ്റ്റും ട്യൂപ്പിളും തമ്മിലുള്ള വ്യത്യാസം എന്താണ്?
2. ഒരു ചെറിയ ഉദാഹരണത്തോടെ SQL JOIN എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്ന് വിശദീകരിക്കൂ.
3. ഇരുപത്തിയഞ്ച് മിനിറ്റിന് ഒരു പഠന ടൈമർ സജ്ജമാക്കൂ.
4. നോട്ട്സ് ഫോൾഡർ തുറക്കൂ.
5. എന്റെ Flask ആപ്പ് "address already in use" എന്ന് കാണിക്കുന്നു, എന്തുകൊണ്ട്?
6. പാണ്ടാസ് ഡാറ്റാഫ്രെയിമിനെക്കുറിച്ച് മൂന്ന് പരിശീലന ചോദ്യങ്ങൾ തരൂ.
7. ഗ്രേഡിയന്റ് ഡിസെന്റ് എന്താണ് ചെയ്യുന്നതെന്ന് രണ്ട് വാക്യങ്ങളിൽ പറയൂ.
8. ആറു മണിക്ക് തുടങ്ങിയാൽ എപ്പോൾ ഇടവേള എടുക്കണം?
9. പ്രോഗ്രാമർമാരെക്കുറിച്ച് സൗഹൃദപരമായ ഒരു തമാശ പറയൂ.
10. ദയവായി പതുക്കെ സംസാരിക്കൂ.

### Hindi (`hi`)
1. पायथन में लिस्ट और ट्यूपल में क्या अंतर है?
2. एक छोटे उदाहरण के साथ समझाओ कि SQL JOIN कैसे काम करता है।
3. पच्चीस मिनट का स्टडी टाइमर लगाओ।
4. नोट्स फ़ोल्डर खोलो।
5. मेरा Flask ऐप "address already in use" दिखा रहा है, क्यों?
6. पांडास डेटाफ़्रेम पर तीन अभ्यास प्रश्न दो।
7. ग्रेडिएंट डिसेंट क्या करता है, दो वाक्यों में बताओ।
8. अगर मैंने छह बजे शुरू किया तो ब्रेक कब लेना चाहिए?
9. प्रोग्रामरों के बारे में एक दोस्ताना चुटकुला सुनाओ।
10. कृपया थोड़ा धीरे बोलो।

### German (`de`)
1. Was ist der Unterschied zwischen einer Liste und einem Tupel in Python?
2. Erkläre mit einem kleinen Beispiel, wie ein SQL-JOIN funktioniert.
3. Stelle einen Lern-Timer auf fünfundzwanzig Minuten.
4. Öffne bitte den Notizen-Ordner.
5. Meine Flask-App meldet „address already in use“. Warum?
6. Gib mir drei Übungsaufgaben zu pandas-DataFrames.
7. Fasse in zwei Sätzen zusammen, was Gradientenabstieg macht.
8. Wann sollte ich eine Pause machen, wenn ich um sechs angefangen habe?
9. Erzähl mir einen freundlichen Witz über Programmierer.
10. Bitte sprich etwas langsamer.

**Prompt for API-LID (identical neutral Sara instruction for every mode; Codex finalizes wording, no personal data):** for each numbered user message, return JSON with `label` (one of `en`, `ta`, `ta-Latn`, `ml`, `hi`, `de`, `other`) and `reply` (one or two sentences in the language of the message; Tanglish messages get Latin-script Tamil replies); the assistant has **no tools** and must not claim to perform actions.

## 13. Acceptance criteria (M0A)

| ID | Criterion | Type |
|---|---|---|
| AC-1 | Repo/Git/Python/pip facts recorded; native Windows confirmed; key **presence** noted; no secrets printed | Automated |
| AC-2 | Gemini SDK, models, pricing, quotas, free-tier eligibility, deprecations, and data-handling terms each recorded with URL + access date, labeled Verified or Unresolved | Automated (docs) |
| AC-3 | Data-handling summary delivered; `API M0A` explicitly given **before** any request | Manual (Prem) approval |
| AC-4 | API attempts used ≤ 30 across the M0A feasibility run (ledger matches persistent counter); failed requests count; no automatic retries or concurrent API runners; selected model's current free-tier eligibility is verified from official sources; Prem confirms billing is disabled before any request; no paid usage | Automated + Manual (Prem confirmation) |
| AC-5 | Only synthetic phrases/audio sent; no mic used; no personal data in `test_data/` or logs | Automated + review |
| AC-6 | Provider error-handling mock tests pass: invalid key, 429, timeout, network failure, unsupported model, empty response | Automated |
| AC-7 | Scoring-script unit tests pass | Automated |
| AC-8 | Language matrix filled: D2 and automated parts of D1/D3 computed; D1/D3/D4 manual cells **Pending Prem** until Prem records; no fabricated results | Automated + Manual (Prem) |
| AC-9 | MT-A1…MT-A4 completed by Prem/reviewer with the template | Manual (Prem) |
| AC-10 | Latency and usage observations recorded with conditions | Automated |
| AC-11 | Local-option desk review completed with sources (no installs) | Automated (docs) |
  | AC-12 | `.gitignore` contains every required pattern in AGENTS.md G5 and does not ignore `.env.example`; `.env.example` contains placeholders only; a secret scan satisfying AGENTS.md G4 is run on the exact content before any commit (or no commit is made) | Automated |
| AC-13 | Report delivered with Verified/Measured/Assumed/Unresolved sections and recommendations for D-2, D-3, D-4, D-8, D-9 | Automated |
| AC-14 | Every acceptance criterion has evidence and an explicit status. Pending, not-run, not-met, or unresolved outcomes are not passes; any open items proposed to carry forward are listed for Prem's explicit `ACCEPT M0A OPEN ITEMS` before M0B can start. | Automated + Manual (Prem acceptance of open items) |

## 14. Out of scope for M0A

Any application code beyond throwaway spikes; microphone/real-voice tests; screenshots/documents/Vision tests; Live-API streaming build; hardware telemetry; KDE Connect; SQLite design; UI; installing local STT/TTS models; any billing change.

## 15. Stop conditions (specific)

Stop and report if: model requires billing; free-tier terms are unclear or unacceptable to Prem; the request counter would exceed the budget; audio model/voice for a language is unavailable (record **Not available**, continue other languages without exceeding the cap); any request would include non-synthetic data.
