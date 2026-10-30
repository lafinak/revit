# openbim-ifc-cli vs ifc-lite — Verification Report

Test file: `/workspaces/turbo-flow-wsl/dev/architektura/revitest/real.ifc` (4,879,335 bytes, IFC4, 64,747 STEP entities, 970 building elements, real Revit 2024 export). All commands below were actually run in this devpod on 2026-10-30; nothing is quoted from documentation without being exercised.

## 1. Install result

```
$ cargo install openbim-ifc-cli 2>&1 | tail -40
   Compiling zopfli v0.8.4 ... [36 crates]
   Compiling ifc-schema v0.3.5
   Compiling ifc-model v0.4.5
   Compiling ifc-template-catalog v0.4.3
   Compiling ifc-validate v0.8.2
   Compiling ifc-properties v0.10.2
   Compiling ifc-geometry v0.32.0
   Compiling ifc-step v0.6.2
   Compiling ifc-schedule v0.5.2
   Compiling ifc-spatial v0.6.2
   Compiling ifc-cost v0.5.2
   Compiling ifc-xml v0.5.2
   Compiling openbim-ifc v0.39.4
   Compiling openbim-ifc-cli v0.6.0
    Finished `release` profile [optimized] target(s) in 1m 03s
  Installing /home/vscode/.cargo/bin/openbim-ifc
   Installed package `openbim-ifc-cli v0.6.0` (executable `openbim-ifc`)
```

- **The crate exists and installs cleanly.** `cargo install openbim-ifc-cli` succeeded on the first try, no name mismatch, no yanked version. Install time: **63 seconds** (release build, this devpod).
- Binary: `/home/vscode/.cargo/bin/openbim-ifc`, 10,810,736 bytes (~10.3 MB), ELF executable.
- Pulled in a visible multi-crate workspace from the same org: `openbim-step`, `ifc-schema`, `ifc-model`, `ifc-template-catalog`, `ifc-validate`, `ifc-properties`, `ifc-geometry`, `ifc-step`, `ifc-schedule`, `ifc-spatial`, `ifc-cost`, `ifc-xml`, `openbim-ifc`, `openbim-ifc-cli`. Cloning the GitHub repo (`openbimrs/ifc`, depth 1) and counting adds more crates not needed by the CLI build (`ifc-classification`, `ifc-georef`, `ifc-material`, `ifc-systems`): **~18 crates total**.
- Memory stayed healthy throughout (free never dropped below 1.6 GiB free / 11 GiB "available"); no parallel builds were run.

## 2. Command outputs (verbatim, trimmed where noted)

### `openbim-ifc --version`
```
openbim-ifc 0.6.0
```

### `openbim-ifc --help`
```
The openbim-ifc command: validate, convert, inspect, query and edit IFC files (STEP, ifcXML and ifcZIP), and exchange their values as CSV, TSV or XLSX tables, from a shell or CI.

Commands:
  validate       Validate against the schema each file declares (exit 1 on findings)
  convert        Convert between STEP, ifcXML (native or XSD layout) and ifcZIP
  info           Show the header, the declared schema and entity counts
  psets          Show the property and quantity sets of one entity or type object
  tree           Show the spatial structure: project, site, building, storey, space
  lint           Report products no model viewer will draw (exit 1 on findings)
  select         List the entities a selector selects, with values read by path
  convert-units  Convert the model's length unit, rescaling every length, area and volume, and write it as STEP
  edit           Set values by path on the entities a selector selects, as one checked transaction, into a new file (exit 3 on a refusal)
  export-table   Write the entities a selector selects as a table ...
  import-table   Write a table's edited cells back by key ...
  relations      Show what one entity is related to ...
  materials      Show the material definition of each selected entity ...
  cost           Show every cost schedule with its tree of cost items, values and rolled-up totals
  schedule       Show every work schedule and work plan with its tree of tasks ...
```
This is a real, broad CLI — 15 subcommands, not a toy wrapper. `edit`/`import-table` implement transactional writes with a dedicated refusal exit code (3), matching the "schema-checked construction, transactional editing" claim.

### `openbim-ifc validate real.ifc` (default human format)
```
real.ifc: IFC4: conformant: 0 errors, 0 evaluation errors, 0 warnings; 2 rules not evaluated
```
Timing (cold, first run after install): **1.376s real**. Warm re-run: **0.676s real**.

### `openbim-ifc validate real.ifc --format sarif`
```json
{
  "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "openbim-ifc",
          "version": "0.6.0",
          "semanticVersion": "0.6.0",
          "informationUri": "https://openbimrs.github.io/ifc/guide/cli",
          "rules": []
        }
      },
      "invocations": [{ "executionSuccessful": true, "toolExecutionNotifications": [] }],
      "artifacts": [{ "location": { "uri": "real.ifc" } }],
      "results": []
    }
  ]
}
```
Valid, well-formed SARIF 2.1.0 — the "`validate --format sarif`" claim is real and works.

### `openbim-ifc info real.ifc`
```
File                  real.ifc
Format                STEP
Schema                IFC4 (IFC4_ADD2_TC1, bundled)
Description           ViewDefinition [CoordinationView]
Entities              64747
Entity types          63
  29102  IFCPROPERTYSINGLEVALUE
   7062  IFCRELDEFINESBYPROPERTIES
   6528  IFCPROPERTYSET
   6441  IFCCARTESIANPOINT
    360  IFCWALL
    256  IFCCOLUMN
  ... 43 more types (--all-types lists them)
```
Timing: **0.137s** (cold), **0.060s** (warm).

Note (incidental, not evaluated further here — a separate finding is tracking this): the file's own STEP header lists `Author: rvt-rs`, `Preprocessor: rvt-rs 0.10.0`, `Originating system: rvt-rs STEP writer`. That's metadata embedded in the test fixture by whatever generated it, not a claim made by openbim-ifc-cli — surfaced here because the team is separately investigating a `rvt-rs`-derived Rust `.rvt` reader (BIMCraft, see §7).

### Element counts via `select` (cross-checked against ifc-lite)
```
$ openbim-ifc select real.ifc IfcWall --format csv | tail -n +2 | wc -l   -> 360
$ openbim-ifc select real.ifc IfcDoor --format csv | tail -n +2 | wc -l   -> 132
$ openbim-ifc select real.ifc IfcWindow --format csv | tail -n +2 | wc -l -> 6
$ openbim-ifc select real.ifc IfcColumn --format csv | tail -n +2 | wc -l -> 256
$ openbim-ifc select real.ifc IfcSpace --format csv | tail -n +2 | wc -l  -> 116
```
**Exact match** to ifc-lite's previously-verified counts (Wall=360, Door=132, Window=6, Column=256, Space=116). Both tools agree on ground truth for this file.

### ifcXML and ifcZIP conversion
```
$ openbim-ifc convert real.ifc real_converted.ifcxml --force
openbim-ifc: 64747 entities: real.ifc (STEP) -> real_converted.ifcxml (ifcXML (native layout))
real  0.364s

$ openbim-ifc convert real.ifc real_converted.ifczip --force
openbim-ifc: 64747 entities: real.ifc (STEP) -> real_converted.ifczip (STEP in ifcZIP (real_converted.ifc))
real  0.295s
```
Output sizes: `real.ifc` 4,879,335 B → `real_converted.ifcxml` **17,033,359 B** (3.5x larger, expected XML verbosity) → `real_converted.ifczip` **838,476 B** (5.8x smaller than STEP). Both conversions completed without error; ifcXML round-trips the full 64,747-entity count.

## 3. Feature comparison table

| Feature | ifc-lite (`@ifc-lite/cli` 0.43.0) | openbim-ifc-cli 0.6.0 |
|---|---|---|
| Language/runtime | TypeScript/Node, with a `@ifc-lite/wasm` native module dependency (origin language of the wasm module not confirmed — see §7) | Pure Rust, no WASM dependency (confirmed: binary has no wasm runtime, native release build) |
| STEP parse/read | Yes | Yes |
| ifcXML read/write | Via separate `@ifc-lite/ifcx`/export packages (not tested here) | Yes, native + XSD layout, tested — round-trips 64,747 entities |
| ifcZIP | Not tested in this session | Yes, tested — 838 KB output |
| SARIF validation output | Not tested in this session | Yes, tested — valid SARIF 2.1.0 |
| Schema-checked transactional editing | Not part of CLI core; separate `@ifc-lite/mutations` package exists | Yes — dedicated `edit`/`import-table` subcommands with exit code 3 on refusal |
| Query language | `ifc-lite query --type X --count` style | Selector grammar (`IfcWall, Pset_WallCommon.IsExternal=TRUE + IfcSlab`) via `select` |
| Cost/schedule modules | Not evident in CLI | Yes — dedicated `cost` and `schedule` subcommands |
| CLI breadth | Fewer subcommands tested (info, query) | 15 subcommands |
| Package structure | ~26 scoped npm packages (`@ifc-lite/*`) | ~18 Rust crates under one GitHub org |
| Element-count accuracy on real.ifc | Wall=360, Door=132, Window=6, Column=256, Space=116 | **Identical** |

## 4. Performance comparison

| Operation | ifc-lite | openbim-ifc-cli |
|---|---|---|
| Parse/info, cold | ~191ms *internal* parseTime, 3.26s wall (Node startup dominates) | 137ms wall |
| Parse/info, warm | ~110ms *internal* parseTime, 1.59s wall | 60ms wall |
| Full schema validation | not measured (no equivalent single command tested) | 676ms warm / 1.38s cold |
| ifcXML conversion | not tested this session | 364ms |
| ifcZIP conversion | not tested this session | 295ms |

The honest comparison: ifc-lite's own **internal parse timer** (110–191ms) is in the same range as openbim-ifc's wall-clock `info` time (60–137ms), i.e. roughly comparable parse speed. But ifc-lite's **wall-clock** time is 1.6–3.3s because every invocation pays Node.js startup — a real operational cost for CLI/CI usage that openbim-ifc, as a native binary, does not pay (sub-100ms for simple reads). For a CI pipeline calling the CLI hundreds of times (e.g., `validate` on every file in a batch), this difference compounds.

## 5. Schema coverage — verified vs claimed

**Verified by actually opening the file:** IFC4 (specifically IFC4_ADD2_TC1, which the tool itself reports as "bundled"). This is the only schema in scope for this test, since `real.ifc` is IFC4.

**Claimed but NOT verified in this session:** IFC2x3 TC1, IFC4X1 FINAL, IFC4X2 FINAL, IFC4X3 ADD2. No IFC2x3 or IFC4X3 test file was available in this devpod to exercise those paths. The `--input-layout` flag's help text does reference "IFC4 ADD2 TC1, IFC4X3 ADD2" for XSD ifcXML layouts specifically, which is at least internally consistent with the broader schema claim, but that is still a claim read from `--help` output, not an opened file. **Do not take the full schema list as verified — only IFC4 is confirmed working.**

## 6. Licensing comparison

| | ifc-lite | openbim-ifc-cli |
|---|---|---|
| License | **MPL-2.0** (confirmed from installed package.json) | **(AGPL-3.0-or-later OR LicenseRef-Commercial) AND CC-BY-ND-4.0** (confirmed from Cargo.toml and crates.io API) |
| Commercial-use implications | Permissive-ish copyleft: MPL requires sharing modifications to MPL-covered *files* themselves, but allows linking/combining with proprietary code in a larger work without that work becoming MPL. Low friction for most commercial integrations. | **AGPL-3.0 is a strong copyleft license with network-use provisions**: if a SaaS or any networked product uses openbim-ifc's AGPL code (including as a library dependency, not just the CLI), the operator generally must offer the complete corresponding source to users of that service — this is a materially higher bar than MPL. The dual-license `OR LicenseRef-Commercial` escape hatch exists specifically because the authors know AGPL is commercially unpalatable: a company that doesn't want AGPL obligations has to buy a commercial license from the authors instead. |

This is a real strategic difference worth calling out in the book: openbim-ifc-cli's licensing model (AGPL + paid commercial alternative) is a common strategy for monetizing open-source infrastructure, but it makes the tool **much harder to adopt inside proprietary/commercial BIM pipelines** without either open-sourcing the consuming product or paying for a commercial license — unlike ifc-lite's MPL-2.0, which most commercial users can adopt with minimal legal review.

## 7. Strategic verdict

**Is openbim-ifc-cli a real, credible competitor? Yes, on the evidence gathered here — but a young one, and not necessarily on the specific axis the book's claim depends on.**

Facts gathered, not inferred:
- It installs and runs correctly; all tested subcommands (`validate`, `info`, `select`, `convert` to both ifcXML and ifcZIP, SARIF output) work on a real, 4.9 MB, 64,747-entity Revit-exported IFC4 file and produce **correct** results that match ifc-lite's independently-verified element counts exactly.
- The underlying workspace is genuinely large: **418,671 lines of Rust** across the cloned `openbimrs/ifc` repo (all crates, not just the CLI), spread over ~18 crates covering STEP, ifcXML, geometry, properties, spatial structure, cost, schedule, validation, and a template catalog. That is a substantial, real Rust BIM codebase — not a thin wrapper.
- But it is **very young and has very low adoption**: GitHub repo created 2026-08-24 (about 9 weeks before this check), 3 stargazers, 0 forks, 58 open issues (consistent with active, unfinished development rather than a mature, stable tool), and only 94 downloads on crates.io for the CLI crate as of this check. Compare to a project that's been accumulating users and contributors over years — this is a brand-new entrant, however technically serious.
- Licensing (AGPL/commercial dual-license) is a real adoption barrier for the commercial-tooling market this space serves, separate from its technical merits.

**On "ifc-lite is the largest single Rust BIM project":** this needs real qualification, but for a different reason than openbim-ifc-cli's size. Checking ifc-lite's own installed packages in this session surfaced something the book should know about directly: **ifc-lite's CLI package itself is TypeScript/Node** (`"type": "module"`, built with `tsc`, run as `dist/index.js` under Node), depending on ~26 separate `@ifc-lite/*` npm packages. There is a `@ifc-lite/wasm` package (WebAssembly bindings), but this session could not confirm from package metadata alone whether that WASM module's *source* is Rust, C++, AssemblyScript, or something else — `npm view @ifc-lite/wasm` shows only "WebAssembly bindings for IFC-Lite," no source-language signal. **If ifc-lite's core is not itself written in Rust, the claim "ifc-lite is the largest Rust BIM project" may rest on an incorrect premise about ifc-lite's own implementation language, independent of any competitor's size.** This is a bigger problem for the claim than openbim-ifc-cli's 418K LOC is, and it should be checked directly against ifc-lite's own source repository before the book goes to print.

Separately, and likely the more consequential challenge either way: `IPedrax/BIMCraft` (743 GitHub stars, Apache-2.0, pure Rust) is reported to be a full BIM-authoring tool — not just an IFC parser — with desktop apps, MCP support, and its own `.rvt` reader "ported in part from rvt-rs." That star count alone (743 vs. openbim-ifc's 3) dwarfs both tools discussed here and is being verified separately; it is very likely the actual largest/most-adopted Rust BIM project in this space if its Rust-LOC claim holds up, not openbim-ifc-cli.

**Bottom line for the book's specific claim:** "ifc-lite is the largest single Rust BIM project" should not be asserted as-is. At minimum it needs (a) confirmation that ifc-lite's own codebase is actually majority-Rust, which this session could not establish, and (b) a size comparison against both openbim-ifc-cli (418K LOC Rust, verified) and BIMCraft (743 stars, claimed pure Rust, being verified separately). The claim may need to become something narrower and defensible, e.g. about a specific sub-package, feature set, or adoption metric — not an unqualified "largest" claim.

## 8. Recommendation for the book

1. **Do not print "ifc-lite is the largest single Rust BIM project" unqualified.** Verify ifc-lite's own source repo language breakdown (GitHub's own language bar, or `cloc`/`tokei` on a clone) before republishing this claim in any form — this session found enough doubt about ifc-lite's own Rust-ness that the claim needs its premise checked first, before even weighing it against competitors.
2. **Cite openbim-ifc-cli as a genuine, if immature, data point**, not a toy or vaporware: 418K LOC of real Rust, 18 crates, a working 15-subcommand CLI verified against ground truth on a real file. Fair framing: "technically serious, pre-1.0, low-adoption (3 stars, created 2 months ago), AGPL-licensed."
3. **Flag BIMCraft (743 stars) as the claim's actual stress-test**, pending the separate verification in progress — don't let openbim-ifc-cli's modest adoption numbers imply the field is uncontested.
4. **Mention the AGPL/commercial dual-license explicitly** if comparing commercial viability, not just technical capability — this is a material difference from ifc-lite's MPL-2.0 that affects who can actually adopt openbim-ifc-cli downstream.
