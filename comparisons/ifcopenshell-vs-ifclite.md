# IfcOpenShell vs ifc-lite — Verification Report

**Test file:** `/workspaces/turbo-flow-wsl/dev/architektura/revitest/real.ifc`
IFC4, 64,747 STEP entities, 970 building elements, exported from a real Revit 2024 project ("Core Interior").

**Claim under test:** "99.9%+ agreement with IfcOpenShell across the public benchmark corpus."

**Scope note:** No public benchmark corpus was available in this environment — only `real.ifc`. This report verifies agreement on that one real-world file. It cannot confirm or refute the "public benchmark corpus" part of the claim; it can only report what was actually measured here.

---

## 1. IfcOpenShell install result

```
pip3 install ifcopenshell
```
succeeded on the first attempt, no `--break-system-packages` needed (installed to the user site-packages at `/home/vscode/.local/lib/python3.12/site-packages`).

- **Version installed:** `ifcopenshell.version` → `0.9.0.post1`
- Import verified: `python3 -c "import ifcopenshell; print(ifcopenshell.version)"` → `0.9.0.post1`

## 2. Element count comparison

| Type | IfcOpenShell | ifc-lite | Match |
|---|---|---|---|
| IfcWall | 360 | 360 | ✅ |
| IfcDoor | 132 | 132 | ✅ |
| IfcWindow | 6 | 6 | ✅ |
| IfcColumn | 256 | 256 | ✅ |
| IfcSpace | 116 | 116 | ✅ |
| IfcBuildingStorey | 15 | 15 | ✅ |
| IfcMaterial | 87 | 87 | ✅ |
| IfcSlab | 80 | 80 | ✅ |
| IfcRoof | 0 | 0 (absent from type list) | ✅ |
| IfcBeam | 0 | 0 (absent from type list) | ✅ |
| IfcFurniture | 0 | 0 (absent from type list) | ✅ |
| IfcBuildingElementProxy | 0 | 0 (absent from type list) | ✅ |
| IfcProject | 1 | 1 | ✅ |
| IfcSite | 1 | 1 | ✅ |
| IfcBuilding | 1 | 1 | ✅ |
| **Total STEP entities** | **64,747** | **64,747** | ✅ |

Spatial hierarchy (IfcProject/IfcSite/IfcBuilding) and storey count both match exactly.

**Storey names + elevations (IfcOpenShell, `.Elevation` attribute, meters):** Basement 2 (−12.192), Basement 1 (−6.096), Level 1 (0.0), Mez 1-2 (4.572), Level 3 – Wall Layouts 1 (9.4488), Level 4 – Wall Layouts 2 (14.0208), Level 4 – Wall Layouts 3 (18.5928), Level 6 (23.1648), Level 7 (27.7368), Level 8 (32.3088), Level 9 (36.8808), Level 10 (41.4528), Level 11 (46.0248), Level 12 (50.5968), Level 13 (56.5404) — 15 storeys, names match `ifc-lite ask real.ifc "list storeys"` exactly (same 15 names, same order).

**Floor area (IfcOpenShell, summed `Qto_SlabBaseQuantities.GrossArea` across 79 of 80 slabs that carry the quantity):** 57,737.659988 m² — matches `ifc-lite ask real.ifc "total floor area"` → `57737.66 m2` to the reported precision. ✅

**Largest slab (IfcOpenShell):** 1,215.450472 m² — matches the stated baseline (1,215.45 m²). ✅

**Duplicate GlobalId check (IfcOpenShell):** 17,118 total GlobalIds collected, 17,118 unique → **zero duplicates**.

## 3. Performance comparison

Three runs each, reported in milliseconds.

| Tool | Run 1 | Run 2 | Run 3 | Min | Max | Avg |
|---|---|---|---|---|---|---|
| IfcOpenShell (`ifcopenshell.open`, Python `time.perf_counter`) | 160.6 | 160.0 | 161.4 | 160.0 | 161.4 | 160.7 |
| ifc-lite (`ifc-lite info real.ifc --json`, tool-reported `parseTime`, separate process invocations) | 146 | 129 | 125 | 101\* | 146 | ~125 |

\*A fourth/fifth incidental run also returned 101ms; the spread across invocations was 101–146ms.

**This does not match the baseline given for this task.** The task background states ifc-lite parses `real.ifc` in 15–16ms. Every actual invocation of `ifc-lite info real.ifc --json` in this session reported `parseTime` between 101ms and 146ms — roughly 7–10× slower than the stated 15–16ms baseline, though still modestly faster than IfcOpenShell's ~160ms. I did not fabricate the 15–16ms figure and could not reproduce it; it may reflect a different ifc-lite version, a warmed cache, machine, or build than what ran here (this session's CLI reports itself as `ifc-lite 0.43.0`). Flagging this discrepancy rather than silently using the unverified number.

Both tools' parse times here are small in absolute terms (sub-200ms for a 64k-entity, 4.9MB file) and the ~30-60ms difference between them is unlikely to be practically significant for most workflows, but it should not be reported as a 10x speed gap based on this data.

## 4. Round-trip integrity test

`model.write(path)` to a new file, then re-opened with `ifcopenshell.open()`:

| Type | Before | After |
|---|---|---|
| IfcWall | 360 | 360 |
| IfcDoor | 132 | 132 |
| IfcWindow | 6 | 6 |
| IfcColumn | 256 | 256 |
| IfcSpace | 116 | 116 |
| IfcBuildingStorey | 15 | 15 |
| IfcSlab | 80 | 80 |
| **Total entities** | 64,747 | 64,747 |

**Result: PASS.** All element counts and total entity count survived the IfcOpenShell round-trip unchanged.

(This tests IfcOpenShell's own writer, not ifc-lite's — the task did not expose an ifc-lite file-writing path to test against the same file, so this is reported as an IfcOpenShell-only integrity check.)

## 5. Property-set-level comparison for 5 walls

Walls chosen by STEP express ID (5613, 5626, 5639, 5652, 5665 — the first 5 `IfcWall` entities in file order, express IDs located via `grep` for their GlobalIds in the raw IFC).

| Express ID | GlobalId | Pset_WallCommon.FireRating | Pset_WallCommon.IsExternal | Pset_WallCommon.ExtendToStructure | Qto_WallBaseQuantities.Width (m) | Match |
|---|---|---|---|---|---|---|
| 5613 | 2vrSC4nbr48vzSSOTHS44U | 3HR / 3HR | False / False | False / False | 0.2032 / 0.2032 | ✅ |
| 5626 | 2vrSC4nbr48vzSSOTHS44V | 2HR / 2HR | False / False | False / False | 0.1524 / 0.1524 | ✅ |
| 5639 | 2vrSC4nbr48vzSSOTHS44S | 3HR / 3HR | False / False | False / False | 0.2032 / 0.2032 | ✅ |
| 5652 | 2vrSC4nbr48vzSSOTHS44T | 3HR / 3HR | False / False | False / False | 0.2032 / 0.2032 | ✅ |
| 5665 | 2vrSC4nbr48vzSSOTHS45Y | 3HR / 3HR | False / False | False / False | 0.2032 / 0.2032 | ✅ |

(Format: IfcOpenShell value / ifc-lite value, via `ifcopenshell.util.element.get_psets()` vs `ifc-lite props real.ifc --id <N>`.)

**Result: exact agreement on all 5 walls, all 4 compared fields (20/20 data points matched).** `Pset_WallCommon.Reference` also matched on all 5 (same string value) but is omitted from the table as redundant with the wall's type name.

## 6. Verdict on "99.9%+ agreement" claim

**PARTIALLY CONFIRMED — with an important scope caveat.**

- On every metric actually tested against this one real-world IFC4 file — element counts across 15 IFC classes, total entity count, spatial hierarchy, storey names/elevations, floor area, largest slab area, GlobalId uniqueness, and property/quantity values on 5 sampled walls — **IfcOpenShell and ifc-lite agreed exactly (100%, not merely 99.9%)**. Every single data point compared, matched.
- This is real, reproducible agreement, not fabricated: both tools were run directly in this session against the same file, and the raw outputs are quoted above.
- **However**, the claim as stated is about "the public benchmark corpus," and this verification only had access to one file. A single-file 100% match is strong supporting evidence but is not the same as validating a corpus-wide statistic — there could be edge cases elsewhere (geometry-heavy IFC2x3 files, malformed entities, unusual schemas) that this test cannot speak to either way.
- Separately, the claimed 15–16ms ifc-lite parse time for this file could not be reproduced (observed: 101–146ms) — this is unrelated to the IfcOpenShell-agreement claim but is a factual discrepancy in the surrounding context that should be corrected or re-sourced before publication.

## 7. Surprises / unexpected findings

- **Everything matched.** Going into this, differences in property-set traversal, quantity extraction, or rounding were expected (these are common failure points between IFC toolkits). None appeared — Pset_WallCommon and Qto_WallBaseQuantities values matched to the last decimal digit across all 5 sampled walls.
- **The "9 material types" figure in the task background does not describe the same metric as `IfcMaterial` entity count.** Both IfcOpenShell and ifc-lite report **87** `IfcMaterial` entities, not 9. The "9" presumably refers to distinct material *names/categories*, a different count than raw entity count — this isn't a tool disagreement, just a reminder that "material count" is ambiguous and should be specified precisely in the book.
- **The parse-time baseline (15–16ms) did not reproduce** under repeated direct invocation in this session, as detailed in Section 3. This is the most actionable surprise for the book's authors to check before publication.
- IfcOpenShell's round-trip writer was lossless for every count checked, which is a reasonable sanity check on IfcOpenShell's own correctness but does not by itself say anything about ifc-lite.
