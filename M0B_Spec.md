# M0B Specification — Hardware Telemetry, Game Detection, Time Accounting, SQLite Design, KDE Connect

Version 2.0 · 2026-10-20 · Owner: Prem · Branch: `m0b-telemetry`

**Authority.** `AGENTS.md` governs; rule IDs (R1, S1, H5, ...) refer to it. If anything here conflicts with it, the stricter rule wins. This spec authorizes **M0B only**. M0A approval does not authorize M0B; M0B approval does not authorize the MVP (R1). M0B may start only after every M0A acceptance criterion has evidence and a status, any pending/unresolved/not-met items are honestly listed, and Prem has reviewed the report. If there are open items to carry forward, Prem must explicitly acknowledge them with `ACCEPT M0A OPEN ITEMS`; that acknowledgment does not mark any result as passed. Prem must separately type `APPROVE M0B` to start M0B.

**Nothing in this file is a result.** Whether any sensor, counter, or Windows interface works on this laptop is **unknown** until measured. Do not present expectations below as findings.

---

## 1. Objective

Produce **evidence** for each of the following, on this laptop, in **native Windows**, **without administrator rights**:
1. Which health metrics are reliably readable (Available / Unavailable-without-admin / Unknown).
2. Whether allowlisted game processes and the foreground window can be detected safely.
3. How session time should be accounted across sleep, resume, restart, crash, DST, and time-zone changes.
4. A SQLite design with migrations, backup, and crash-safety evidence.
5. What KDE Connect can do with Prem's actual phone and network.
6. A resource baseline for light polling.
7. Inputs for decisions D-1, D-6, D-7 (PRD §15).

## 2. Hard limits recap

- **Native Windows only (S1).** If WSL or non-Windows is detected, stop; do not claim these tests passed.
- **Never elevate.** Access denied → record **Unavailable without elevation**; do not retry with admin; do not install third-party sensor tools or drivers in M0B (listing them as a *decision* is allowed).
- No registry writes, no hooks, no keylogging, no webcam/microphone, no changes to Defender/Firewall/UAC.
- No Gemini calls in M0B. No personal data in files or reports; redact usernames/paths.
- Codex must not claim results of Manual (Prem) tests, physical-device tests, or Prem's visual comparisons (H5).

## 3. Approval tokens needed

| Token | Used for |
|---|---|
| `APPROVE M0B` | Start M0B; authorizes its Tier 0 read-only inspection, but no other token-scoped action |
| `ACCEPT M0B OPEN ITEMS` | Acknowledge only the pending, unresolved, unavailable, or not-met items listed in the M0B report before any later milestone; does not mark them passed or authorize that milestone |
| `FILES M0B` | Create files **only** in: `spikes/m0b/`, `reports/`, `artifacts/m0b/` (git-ignored), `docs/m0b/`, `requirements-m0b.txt`; create branch `m0b-telemetry`; commits |
| `INSTALL M0B` | Create/refresh `.venv`; install pinned packages in §6.1 |
| `LAUNCH M0B` | Start/stop **Notepad** (as the stand-in "game") and child Python processes that Codex itself starts for tests (SQLite crash test, harnesses) |
| `EXTERNAL M0B` | Read-only fetch of official docs/package pages (`learn.microsoft.com`, `docs.python.org`, `pypi.org`, `github.com` repos of candidates, `kdeconnect.kde.org`, `developer.nvidia.com`). **Also** needed before any query that contacts Windows Update services |

`FILES M0B` does not permit editing `.gitignore`. M0A must establish all AGENTS.md G5 patterns before the M0B gate; M0B verifies those patterns under BC-15. These patterns and the G4-scanned final redacted M0A report commit are non-waivable M0B prerequisites; `ACCEPT M0A OPEN ITEMS` cannot waive them. The M0B branch is created from the `m0a-feasibility` commit containing the final redacted M0A report, so that report is present in its history. If the M0A report could not be committed under AGENTS.md G4, M0B does not start until the handoff is resolved.

## 4. Tier 0 commands for this milestone (no separate command token)

`APPROVE M0B` is required before Tier 0 work begins; no separate token is needed for each Tier 0 command. Use the master list in `AGENTS.md` §3.1: GPU (`nvidia-smi`, query form), `Win32_Processor`, `Win32_VideoController`, `Win32_OperatingSystem`, `Win32_Battery`, `Get-MpComputerStatus`, `AntivirusProduct`, `Get-HotFix`, `Get-WinEvent` (Application 1000/1001), `powercfg /batteryreport /output "$env:TEMP\sara_battery_report.html"`, git read-only commands, platform checks.

Additional **read-only** commands allowed for M0B (they create no files and contact no external service; if any returns "access denied" or empty, record **Unavailable**):

```powershell
# Performance counters (read-only)
Get-Counter -ListSet 'GPU Engine','GPU Adapter Memory','Thermal Zone Information','Processor Information' -ErrorAction SilentlyContinue | Select-Object CounterSetName
Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction SilentlyContinue
Get-Counter '\Thermal Zone Information(*)\Temperature' -ErrorAction SilentlyContinue

# ACPI/WMI thermal and fan classes (often empty or access-denied without admin; record as found)
Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue
Get-CimInstance -ClassName Win32_Fan -ErrorAction SilentlyContinue
Get-CimInstance -Namespace root/wmi -ClassName BatteryFullChargedCapacity -ErrorAction SilentlyContinue
Get-CimInstance -Namespace root/wmi -ClassName BatteryStaticData -ErrorAction SilentlyContinue

# Disk and memory
Get-PSDrive -PSProvider FileSystem
Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID,Size,FreeSpace
Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory

# Startup apps (read-only listing)
Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location

# Time zone (read-only)
Get-TimeZone

# KDE Connect presence (read-only; installation is done by Prem, not Codex)
Get-Command kdeconnect-cli -ErrorAction SilentlyContinue
Get-AppxPackage -Name '*kde*' | Select-Object Name,Version
```

Output rules: redact usernames, device names, and serials. The raw battery HTML report stays only at `$env:TEMP\sara_battery_report.html` under the Tier 0 exception; do not copy it into the repository or commit it. Write only redacted findings into the permitted report path (G5, G6).

## 5. Needs-approval commands (examples)

```powershell
git switch -c m0b-telemetry                                   # FILES M0B; branch from m0a-feasibility commit containing the final report, after git status shows no foreign changes
python -m venv .venv                                           # INSTALL M0B (skip if .venv from M0A is reused)
.\.venv\Scripts\python -m pip install -r requirements-m0b.txt  # INSTALL M0B
.\.venv\Scripts\python -m pytest spikes\m0b\tests              # FILES M0B; Automated
.\.venv\Scripts\python spikes\m0b\probe_metrics.py             # FILES M0B; read-only probes
.\.venv\Scripts\python spikes\m0b\detect_allowlisted.py --launch-notepad   # LAUNCH M0B
.\.venv\Scripts\python spikes\m0b\sqlite_crash_test.py         # LAUNCH M0B (kills its own child process)
.\.venv\Scripts\python spikes\m0b\poll_harness.py --scenario active --minutes 15   # FILES M0B
```

## 6. Dependencies

### 6.1 Candidate pinned list (Codex verifies and pins after desk review; `INSTALL M0B` required)

`psutil` · `nvidia-ml-py` (NVML bindings; verify package/import name and license) · `pytest`. `ctypes` (stdlib) is used for foreground-window queries; `pywin32` only if `ctypes` proves insufficient and Prem approves. **No** third-party sensor tools, drivers, or services.

### 6.2 Desk review (task M0B-14)

For psutil, nvidia-ml-py, pytest, plus candidates for later milestones (`pystray`, a UI framework shortlist for D-1, `argon2-cffi`): license (verified from the project's official page), latest release date and maintenance signs, Python 3.12 + Windows wheel availability, known advisories. Label every line Verified/Unresolved. Licenses recalled from memory are **Assumed** until checked.

## 7. Tasks

| ID | Task | Type | Token |
|---|---|---|---|
| M0B-01 | Confirm native Windows, Python, repo state, power state (AC/battery) and Windows power mode as reported by Prem; record Android phone model/version **as typed by Prem** (device model, not identifiers). | Automated + Manual (Prem) input | APPROVE |
| M0B-02 | **NVIDIA GPU** telemetry: compare `nvidia-smi` query output with NVML (`nvidia-ml-py`): utilization, temperature, memory used/total, clocks, power, fan. Record which fields return values vs N/A on this laptop. | Automated | APPROVE, INSTALL |
| M0B-03 | **AMD iGPU** telemetry: adapter listing and `GPU Engine`/`GPU Adapter Memory` counters; record what is readable (utilization/memory) and what is not (temperature, clocks). | Automated | APPROVE |
| M0B-04 | **CPU/RAM/disk:** psutil vs PowerShell counters; record agreement and cost per sample. | Automated | INSTALL |
| M0B-05 | **CPU temperature and fan sensors** without admin: try `Thermal Zone Information`, `MSAcpi_ThermalZoneTemperature`, `Win32_Fan`. Expect possible **Unavailable**; record exactly what returned. Do not install sensor tools. | Automated | APPROVE |
| M0B-06 | **Battery health:** `powercfg /batteryreport` (parse design vs full-charge capacity and cycle count if present), `psutil.sensors_battery`, WMI `BatteryFullChargedCapacity`. Record availability and reading consistency. | Automated | APPROVE |
| M0B-07 | **Windows Update/security status:** Defender status, Security Center product list, last hotfixes. Record Available/Unknown. Querying pending updates (which contacts Microsoft's update service) is optional and needs `EXTERNAL M0B`; if not approved, mark **Unknown**. | Automated | APPROVE (+EXTERNAL) |
| M0B-08 | **Crash information:** readability of Application-log events 1000/1001 and any Windows Error Reporting data without admin; propose a safe summary format that omits user paths. | Automated | APPROVE |
| M0B-09 | **Game-process + foreground-window detection** feasibility (§8). | Automated + Manual (Prem) | FILES, INSTALL, LAUNCH |
| M0B-10 | **Time-accounting** experiments (§9). | Automated + Manual (Prem) | FILES, LAUNCH |
| M0B-11 | **SQLite design + spike** (§10). | Automated | FILES, LAUNCH |
| M0B-12 | **KDE Connect** compatibility checks (§11). | Manual (Prem) + Automated read-only | APPROVE |
| M0B-13 | **Resource baseline** (§12). | Automated + Manual (Prem) | FILES, INSTALL |
| M0B-14 | Dependency and licensing desk review (§6.2). | Automated (docs) | EXTERNAL |
| M0B-15 | Write `reports/M0B_report.md` (AGENTS.md template + §14 tables). | Automated | FILES |

## 8. Game-process and foreground-window detection (M0B-09)

Design constraints (carry into later milestones):
- Match **allowlisted executable names** only (user-approved). Name matching is spoofable and can miss games that spawn helper/launcher processes; document this.
- Read only: process name, PID, start time; foreground window via `GetForegroundWindow` → process ID with `ctypes`. **No hooks, no injection, no input monitoring, no memory reads.** Use minimal-rights queries; note whether any process refuses to report.
- Anti-cheat caution: inspect only names/PIDs; never attach to or open game memory.
- "Active play" is an **estimate**: allowlisted process present **and** it is the foreground app (optionally excluding locked-session intervals if detectable without hooks).

Automated tests (use **Notepad** as the stand-in game; `LAUNCH M0B`):
- A1: Allowlist contains `notepad.exe` → harness detects within one scan interval after launch and detects exit within one interval after close.
- A2: Foreground change (bring another window forward using only a window the harness itself created, or document that this step is Manual) → measured vs estimated time diverge as expected.
- A3: Non-allowlisted process is ignored; allowlist entry with different case/path variants behaves as specified.
- A4: Scan cost per pass recorded (ms, CPU).

**Manual (Prem) MT-B2 — real game detection.**
1. Prem picks one game he actually plays and tells Codex only the executable name (no accounts, no save data). Codex adds it to a **local, git-ignored** test allowlist.
2. Prem starts the game; runs `detect_allowlisted.py --watch` for 10 minutes while playing normally.
3. Prem minimizes the game for 2 minutes, then returns to it.
4. Prem closes the game.
5. Prem records: detected start within one scan interval (Y/N); foreground/minimize reflected in the estimate (Y/N); exit detected (Y/N); any launcher/helper processes causing confusion; any anti-cheat warning or game problem (Y/N + note).
**Pass:** start and exit detected within one scan interval, foreground change reflected in the estimate, **no game error or anti-cheat warning**. **Fail:** any miss or any game interference (stop using that title for testing).

Result template:
```markdown
Game exe: <name> · Date: <YYYY-MM-DD> · Scan interval: <s>
| Check | Result (Y/N) | Notes |
|---|---|---|
| Start detected within one interval | | |
| Foreground/minimize reflected | | |
| Exit detected within one interval | | |
| Launcher/helper confusion | | |
| Game error or anti-cheat warning | | |
Overall: PASS | FAIL
```

## 9. Time-accounting experiments (M0B-10)

Implements PRD §9 as a spike (no production code).

**Automated (no sleep needed; injected clocks):**
- T1: Durations computed from monotonic deltas, not wall-clock subtraction (changing the injected wall clock by ±1 h does not change measured duration).
- T2: Heartbeat gap > 2× interval closes the session at the last heartbeat with `end_reason=unknown` and `confidence=estimated`.
- T3: Simulated crash (child process killed after N heartbeats) → on recovery the session ends at its last heartbeat with `crash_recovered`, never at "now".
- T4: DST spring-forward and fall-back days (23 h / 25 h) and a time-zone change (e.g., via `zoneinfo`): daily totals bucket by local date correctly; UTC stored values never change.
- T5: Day boundary configurable (default local midnight) works across a session spanning midnight.

**Measurement question (record, do not assume):** on this laptop, does `time.monotonic()` / `time.perf_counter()` advance during sleep? Codex provides `sleep_probe.py` (writes wall clock, monotonic, and perf counter every 5 s to `artifacts/m0b/sleep_probe.csv`) and a result summary script.

**Manual (Prem) MT-B1 — sleep/resume experiment.**
1. Plug in power; close heavy apps.
2. Run `sleep_probe.py`; wait 2 minutes.
3. Put the laptop to sleep (Start → Power → Sleep) for ~5 minutes; wake it.
4. Wait 2 minutes; stop the probe.
5. Optionally repeat with hibernate if enabled.
6. Tell Codex the approximate real sleep duration (minutes) and which method was used.
**Expected output (to be computed from CSV, not assumed):** the gap in wall-clock time vs the gap in each monotonic clock.
**Pass (for the experiment):** the CSV exists, shows a clear gap, and the report states **measured** whether each clock advanced during sleep. This test records a measurement; it does not "pass or fail" the hardware.

Result template:
```markdown
Date: <YYYY-MM-DD> · Mode: sleep | hibernate · Real duration (min): <n>
| Clock | Advanced during sleep? (Y/N/Partial) | Gap seen (s) |
|---|---|---|
| Wall clock (UTC) | | |
| time.monotonic | | |
| time.perf_counter | | |
```

**Unresolved until measured:** whether Windows power events are needed for sleep detection (if monotonic does not advance during sleep, wall-vs-monotonic divergence is the detector; if it advances, power events or heartbeat gaps are required).

## 10. SQLite design and spike (M0B-11)

Deliver `docs/m0b/sqlite_design.md` (design) and `spikes/m0b/sqlite_*` (spike). Use stdlib `sqlite3`; database in a **temp location**, never in the repo (G5).

Design points to document and test:
- **Location:** `%LOCALAPPDATA%\Sara\` in the real app; spike uses `$env:TEMP`.
- **Pragmas:** WAL, `foreign_keys=ON`, `busy_timeout`; evaluate `synchronous=FULL` vs `NORMAL` for durability vs speed (record measured write times).
- **Migrations:** `PRAGMA user_version`; migration v0→v1→v2 runs in a transaction; failed migration leaves the DB at the old version.
- **Backup/export:** SQLite online backup API to a timestamped file, then `PRAGMA integrity_check` on the copy; JSON/CSV export of memory/learning tables.
- **Corruption/unavailable handling:** open failure and `integrity_check` failure produce a clear state (degraded mode: no memory, app still runs) and keep the corrupted file untouched.
- **Retention preview:** a dry-run query that lists exactly which rows (counts by table/date) would be expired; no deletion in M0B.
- **Draft schema:** tables per PRD §8; no secrets columns; consent and settings tables.
- **Encryption:** D-6 remains open for Prem. Record evidence and options; do not assume or implement either no encryption or SQLCipher as the decided choice.

Automated tests:
- S1: Create/migrate/open; `user_version` correct.
- S2: Failed migration rolls back.
- S3: **Crash safety:** a child process writes in a loop inside transactions; the parent **terminates the child mid-write** (`LAUNCH M0B`, own child only); `integrity_check` passes and the last committed rows are present; run ≥ 20 iterations; report pass count.
- S4: Backup produces a database that passes `integrity_check` and matches row counts.
- S5: Opening a deliberately corrupted *copy* (created by the test in temp) triggers degraded mode without crashing.
- S6: Export produces valid JSON/CSV with no secret fields.

## 11. KDE Connect (M0B-12)

**Codex does not install KDE Connect or change firewall/permissions.** Prem installs and pairs. Codex prepares the checklist and, afterwards, runs only the read-only presence commands in §4.

Facts to verify from official sources (`https://kdeconnect.kde.org`): Windows and Android availability and install route, supported features, security/pairing model, whether a command-line or other automation interface exists on Windows. Label Verified/Unresolved with sources.

**Manual (Prem) MT-B3 — KDE Connect checklist** (record phone model, Android version, laptop on Wi-Fi/LAN; no personal data in notes)
1. Install KDE Connect on Windows and Android from the official sources. When Windows Firewall asks, allow **Private** networks only if you are comfortable; do not change other security settings.
2. Put both devices on the same Wi-Fi (note whether your router has client/AP isolation on).
3. Pair from one device; accept on the other. **Expected:** a paired-device indicator on both.
4. Battery: check that the phone battery level appears on the laptop.
5. Clipboard: copy a harmless text (e.g., `hello-sara-test`) on one device; paste on the other.
6. File transfer: send a harmless text file you created for the test, both directions.
7. Media control: play media on the laptop; try pause/next from the phone (and, if offered, the reverse).
8. Notifications: grant Android notification access only if you choose to; send a **test notification** to yourself; check it appears on the laptop. Do not use real private notifications for this test; note which app categories you would exclude.
9. Run commands (if available): define one harmless predefined command (e.g., open Notepad) and trigger it from the phone.
10. Disconnect Wi-Fi on the phone for 1 minute; reconnect; record whether the connection recovers by itself.
11. Record Android permission prompts that appeared and any OEM battery-optimization issues (background drops).
**Pass criteria per feature:** works as expected, repeatably (2 of 2 tries). **Overall M0B-12 status:** list of features Working / Partial / Not working / Not available; no feature is "supported" without a pass.

Result template:
```markdown
Phone: <model> · Android: <version> · Network: <home Wi-Fi | other> · AP isolation: <Y/N/unknown>
| Feature | Try 1 | Try 2 | Result (Working/Partial/Not working/Not available) | Notes |
|---|---|---|---|---|
| Pairing | | | | |
| Battery | | | | |
| Clipboard | | | | |
| File transfer | | | | |
| Media control | | | | |
| Notifications (test only) | | | | |
| Predefined command | | | | |
| Reconnect after Wi-Fi drop | | | | |
```

**Codex follow-up (Automated, read-only):** record whether `kdeconnect-cli` or another automation interface is present (Tier 0 presence commands) and whether any such interface is documented officially; if none, mark **Unresolved** (integration approach for Wave 4 needs a decision).

## 12. Resource baseline (M0B-13)

Targets (to **measure**, not guaranteed): idle CPU < ~2% of total capacity; RAM < ~250 MB; no local AI models.

**Method** (`spikes/m0b/poll_harness.py`, `psutil` + NVML only):
- Conditions: plugged in, Windows power mode recorded, no games, no heavy apps, same network state each run. Prem records conditions and confirms them.
- Scenario **S0 baseline:** harness not running; record whole-system CPU for 5 minutes (context).
- Scenario **S1 active:** metrics every 5 s, process scan every 15 s, for **15 minutes**.
- Scenario **S2 reduced:** metrics every 30 s, process scan every 60 s, for **15 minutes**.
- For S1/S2 record every 10 s: the harness process's CPU as **% of total CPU capacity** (psutil `cpu_percent` ÷ logical-core count; state the formula) and RSS in MB. Report mean, p95, max for CPU and RSS.
- Responsiveness: median and max duration of one sampling pass.

**Manual (Prem) MT-B5 — sanity check.** During S1, open Task Manager, find the harness (`python.exe`), and note its CPU and Memory columns at three moments. Compare with Codex's numbers.
**Pass (preliminary):** S1 mean CPU < 2% and RSS < 250 MB; S2 lower than S1; Task Manager within ~±1 percentage point CPU and ±50 MB of the harness numbers. Deviations are **reported, not hidden**; the harness excludes the UI and Gemini calls, so the MVP/Wave 3 must **re-measure the full app**.

Result template:
```markdown
Conditions: AC/battery · Power mode · Date
| Scenario | Duration | CPU mean/p95/max (%) | RSS mean/max (MB) | Meets target? |
|---|---|---|---|---|
| S1 active | 15 min | | | |
| S2 reduced | 15 min | | | |
Task Manager check (Prem): CPU __% / Mem __ MB at t1/t2/t3
```

## 13. Manual (Prem) test index

| ID | Test | Steps location |
|---|---|---|
| MT-B1 | Sleep/resume clock experiment | §9 |
| MT-B2 | Real game detection | §8 |
| MT-B3 | KDE Connect checklist | §11 |
| MT-B4 | **Sensor sanity check:** while Codex's probe runs, Prem opens Task Manager → Performance and records GPU utilization and temperature (if shown) at 3 moments; compare with probe values. **Pass:** utilization within ±10 percentage points at each moment; temperature within ±3 °C where both exist; anything else is reported as a discrepancy | below |
| MT-B5 | Resource sanity check | §12 |

MT-B4 steps: (1) run `probe_metrics.py --watch 60`; (2) open Task Manager → Performance → GPU 0/1 and CPU; (3) at roughly 10 s, 30 s, 50 s write down shown values; (4) give them to Codex or paste into the sheet; (5) Codex computes differences but does not mark the manual result.

```markdown
| Moment | Task Manager GPU util % | Probe GPU util % | Task Manager temp | Probe temp | Within tolerance (Prem) |
|---|---|---|---|---|---|
| ~10 s | | | | | |
| ~30 s | | | | | |
| ~50 s | | | | | |
```

## 14. Report additions (beyond the AGENTS.md template)

1. **Metric availability matrix:** metric · source tried · value type · Available / Unavailable-without-admin / Unknown · admin needed? · polling cost · label (Measured/Verified).
2. **Sensor sanity results** (from MT-B4) and reading consistency across sources.
3. **Game detection results** (Automated A1–A4 + MT-B2 recorded by Prem).
4. **Time-accounting results** (T1–T5; MT-B1 measurement of clocks across sleep).
5. **SQLite spike results** (S1–S6; crash-test iterations passed/total; write-time comparison for `synchronous` modes).
6. **KDE Connect matrix** (from MT-B3) and automation-interface findings.
7. **Resource baseline** (S0/S1/S2 tables) with deviations from targets.
8. **Dependency/licensing table** (§6.2) and recommendation for D-1, D-6, D-7.
9. **Design implications:** which dashboard tiles must show "Unavailable", recommended polling defaults, alert design, and whether sensors need a decision about third-party tools (separate approval).
10. **Unresolved list** (must include anything not measured, any manual test Pending Prem).

## 15. Acceptance criteria (M0B)

| ID | Criterion | Type |
|---|---|---|
| BC-1 | Native Windows confirmed; no elevation used; no secrets/personal data in outputs | Automated |
| BC-2 | Each metric in PRD H-1 has a row in the availability matrix with evidence and label (no fabricated readings) | Automated |
| BC-3 | NVIDIA and AMD iGPU findings recorded (readable fields vs N/A) | Automated |
| BC-4 | CPU temp/fan: either readable without admin (with evidence) or marked **Unavailable**; no third-party tools installed | Automated |
| BC-5 | Battery-health availability and values (or Unavailable) recorded | Automated |
| BC-6 | Update/security status accessibility recorded; pending-update query only if `EXTERNAL M0B` was given | Automated |
| BC-7 | Notepad detection tests A1–A4 pass; scan cost measured | Automated |
| BC-8 | MT-B2 completed by Prem; result recorded (Pass/Fail/Pending Prem) | Manual (Prem) |
| BC-9 | Time-accounting tests T1–T5 pass; sleep clock behavior **measured** via MT-B1 | Automated + Manual (Prem) |
| BC-10 | SQLite tests S1–S6 pass; crash test ≥ 20 iterations with 0 integrity failures (or failures reported) | Automated |
| BC-11 | KDE Connect checklist MT-B3 completed by Prem; per-feature results recorded; automation-interface status recorded | Manual (Prem) |
| BC-12 | Resource baseline measured for S1 and S2 (15 min each) with method and conditions; deviations reported | Automated + Manual (Prem) |
| BC-13 | MT-B4 sensor sanity completed by Prem (or reported Pending Prem) | Manual (Prem) |
| BC-14 | Dependency/licensing review completed with sources | Automated (docs) |
  | BC-15 | A secret scan satisfying AGENTS.md G4 is run on the exact content before any commit (or no commit is made); verify `.gitignore` contains every AGENTS.md G5 pattern established during M0A. M0B does not edit `.gitignore`. | Automated |
| BC-16 | Report delivered with recommendations for D-1, D-6, D-7 and Wave 3/4 design implications | Automated |
| BC-17 | Every acceptance criterion has evidence and an explicit status. Pending, not-run, not-met, or unresolved outcomes are not passes; any open items must be listed and explicitly acknowledged by Prem with `ACCEPT M0B OPEN ITEMS` before a later milestone. | Automated + Manual (Prem acceptance of open items) |

## 16. Out of scope for M0B

Application code beyond throwaway spikes; Gemini/API calls; UI; installing KDE Connect or sensor tools; changing firewall/Android settings; any deletion/cleanup; L3 logic; wake word; voice; screenshots; auto-start.

## 17. Stop conditions (specific)

Stop and report if: not native Windows; any probe requires admin (record Unavailable and continue other probes); a real game shows errors or anti-cheat warnings during MT-B2; the SQLite crash test reports corruption (report immediately, do not "fix" by weakening checks); KDE Connect prompts for permissions beyond what Prem approved; any step would store or transmit personal notifications or data.
