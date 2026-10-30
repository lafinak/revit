# Apache Tika vs rvt-rs — prior-art verification

**Date:** 2026-10-30
**Test file:** `real.rvt` (33.7 MB, Revit 2024, "2024_Core_Interior", MIT-licensed test dataset), and its IFC export `real.ifc` (4.9 MB)
**Claim under test:** `rvt-rs`'s own `CLEANROOM.md` lists "Apache Tika's Revit metadata extractor" as prior-art for `.rvt` reverse engineering. This report tests whether that extractor does anything Revit-specific.

## 1. Install

- Java: OpenJDK 21.0.12.1 (already present, `/usr/bin/java`) — no install needed.
- Tika: `tika-app-latest.jar` at `https://dlcdn.apache.org/tika/tika-app-latest.jar` **404s** — that convenience alias doesn't exist on the current mirror layout.
  - `dlcdn.apache.org/tika/` only lists two release directories: `3.3.3/` and `4.2.0/`.
  - `4.2.0/` ships only `tika-app-4.2.0.zip` (the standalone fat jar was moved into a zip for the 4.x line).
  - `3.3.3/` still publishes a standalone fat jar directly: `tika-app-3.3.3.jar`.
  - Used: `https://dlcdn.apache.org/tika/3.3.3/tika-app-3.3.3.jar`
- Result: downloaded to `/tmp/tika.jar`, **62 MB**, `java -jar /tmp/tika.jar --version` → `Apache Tika 3.3.3`.

## 2. `--metadata real.rvt` (verbatim)

```
Content-Length: 33718272
Content-Type: application/x-tika-msoffice
X-TIKA:Parsed-By: org.apache.tika.parser.CompositeParser
X-TIKA:Parsed-By: org.apache.tika.parser.microsoft.OfficeParser
resourceName: real.rvt
```

That's the entire output. Five lines, none of them Revit-specific.

## 3. `--text real.rvt`

Output file: **0 lines, 0 bytes.** No stderr errors beyond the standard CLI startup banner. `OfficeParser`'s generic OLE/CFB handling found nothing it recognized as extractable "document text" inside the compound file — Revit's actual payload (the ElemTable/PartitionTable binary streams) isn't text and isn't a format `OfficeParser` knows how to walk.

## 4. `--detect real.rvt`

```
application/x-tika-msoffice
```

This is Tika's generic sniffer for "some OLE2/CFBF compound binary file, unknown exact kind" — the same MIME type you'd get from a corrupted or unrecognized legacy `.doc`/`.xls`/`.ppt`/`.msg` you fed it. There is no `application/vnd.autodesk.revit` or similar.

## 5. `rvt-info real.rvt` (verbatim, for comparison)

```
Revit file · real.rvt
  version:       2024
  build:         20230509_0315(x64)
  locale:        ENU
  file GUID:     2a619b2e-a277-4154-90ff-ca7b37baec5b
  original path: B:\Git\revit-test-datasets\Revit\2024_Core_Interior.rvt
  partition:     Partitions/46
  streams:       20 (33589540 total bytes)

Document ·
  title:          2024_Core_Interior
  last saved:     2023-09-07 12:50:35 UTC
  worksharing:    Not enabled
  save counter:   66
  cloud model:    no

Schema ·
  class names (inferred): 8575

Streams ·
  BasicFileInfo
  Contents
  Formats/Latest
  Global/ContentDocuments
  Global/DocumentIncrementTable
  Global/ElemTable
  Global/History
  Global/Latest
  Global/PartitionTable
  Partitions/46
  Partitions/48
  Partitions/51
  Partitions/53
  Partitions/55
  Partitions/59
  Partitions/61
  Partitions/65
  ProjectInformation
  RevitPreview4.0
  TransmissionData
```

## 6. `--metadata real.ifc` (verbatim, second data point)

```
Content-Encoding: ISO-8859-1
Content-Length: 4879335
Content-Type: text/plain; charset=ISO-8859-1
X-TIKA:Parsed-By: org.apache.tika.parser.CompositeParser
X-TIKA:Parsed-By: org.apache.tika.parser.DefaultParser
X-TIKA:Parsed-By: org.apache.tika.parser.csv.TextAndCSVParser
X-TIKA:encodingDetector: UniversalEncodingDetector
X-TIKA:detectedEncoding: ISO-8859-1
resourceName: real.ifc
```

IFC is an openly published, text-based STEP format (ISO 10303-21) — far easier to parse than Revit's proprietary binary — and Tika still has no IFC-aware parser. It falls through to `TextAndCSVParser`, which detects "it's text with commas in it" and stops there. No `IfcProject` name, no schema version (`IFC4`, `IFC2X3`, etc.), no entity counts.

## 7. Direct comparison

| | Apache Tika 3.3.3 | rvt-rs (`rvt-info`) |
|---|---|---|
| File type detected | `application/x-tika-msoffice` (generic OLE/CFB) | Revit 2024, specific build string |
| Revit version/build | — | `2024`, `20230509_0315(x64)` |
| Locale | — | `ENU` |
| File GUID | — | `2a619b2e-a277-4154-90ff-ca7b37baec5b` |
| Original save path | — | `B:\Git\revit-test-datasets\Revit\2024_Core_Interior.rvt` |
| Partition / stream layout | — | 20 streams enumerated by name, byte totals |
| Document title | — | `2024_Core_Interior` |
| Last saved timestamp | — | `2023-09-07 12:50:35 UTC` |
| Worksharing state | — | `Not enabled` |
| Save counter | — | `66` |
| Schema / class count | — | 8575 inferred class names |
| Extracted text | 0 lines | N/A (binary element data, not prose) |
| IFC schema/entities | 0 (plain-text/CSV fallback) | N/A (not tested here, but `rvt-ifc*` tools exist for this) |

Tika extracted **zero** Revit-specific facts. Every structured field rvt-rs reports — version, build, GUID, original path, worksharing, stream map, document title, save counter — comes from understanding Revit's internal compound-file layout and binary record formats. Tika only knows "this is some OLE2 container," which is true of thousands of unrelated legacy Microsoft formats.

## 8. Verdict: is Tika's `.rvt` support a real parser?

**No.** Tika's `.rvt` handling is Microsoft Compound File Binary (CFB/OLE2) container detection, not a Revit-aware parser. The evidence:

- `.rvt` files are, structurally, OLE2/CFBF compound documents — the same container format as legacy `.doc`/`.xls`/`.ppt`/`.msi`/`.msg`. Tika's `OfficeParser` recognizes the *container* magic bytes and generic directory structure, which is why it correctly says "yes, this is an OLE2 file" and reports a byte-accurate `Content-Length`.
- It does **not** walk into the container's internal streams (`BasicFileInfo`, `ProjectInformation`, `Global/ElemTable`, etc.) with any Revit-specific logic. There is no `RevitParser` class in Tika, no code path that knows what `BasicFileInfo` means, no code that decodes the element table's binary record format, no code that reads the embedded build-version string.
- `--text` returning 0 lines confirms this: if Tika had any Revit-aware logic, it would at minimum surface the project information text stream (title, address, client name — the kind of thing `ProjectInformation` holds in cleartext-ish form). It surfaces nothing, because `OfficeParser`'s generic CFB handling doesn't know Revit's stream semantics and has no plain-text payload to fall back on.
- The IFC test is the control: IFC is a far *easier*, openly specified, plain-text format, and Tika still has no entity-aware parser for it — reinforcing that Tika's design philosophy is "detect + extract text/metadata via known container/document parsers," not "implement every proprietary CAD/BIM schema." Revit never got one.

So: Tika is a real, general-purpose file-identification and metadata/text-extraction framework (that part is genuine and valuable for its intended scope — office docs, PDFs, images, archives, etc.). But for `.rvt` specifically, its "support" is exactly the shallow case the task description predicted: compound-container recognition without any understanding of Revit's internal structure.

## 9. Strategic implication

**When would someone choose Tika over rvt-rs for `.rvt` files?** Essentially never, for any task that requires actual Revit data. The only legitimate use case is bulk file-type triage in a pipeline that already runs Tika over everything (e.g., an enterprise search/indexing crawler using Tika for hundreds of formats) and only needs to answer "is this an Office-family compound file, roughly how big, what's its name" — i.e., treating `.rvt` exactly like an unidentified legacy binary. The moment the task needs version, worksharing state, project metadata, element data, or anything Revit-specific, Tika has nothing to offer and rvt-rs (or Revit itself, or the Autodesk Forge/APS SDKs) is the only option.

**Does the "prior art" framing in CLEANROOM.md overstate what Tika does?** Yes, somewhat. The CLEANROOM.md line reads: *"Apache Tika's Revit metadata extractor, chuongmep/revit-extractor (Python), the phi-ag/rvt project, and academic papers on Revit forensics are all public sources whose findings can be referenced."* Calling it **"Apache Tika's Revit metadata extractor"** implies Tika has a named, Revit-aware extraction component analogous to its `OfficeParser` for `.doc` or `PDFParser` for PDF. It does not. What exists is generic CFB container detection that happens to fire (without complaint) on `.rvt` files because they share that container format with real Office documents. There is no Tika code, configuration, or detector entry specific to Revit, no Revit MIME type, and no Revit-specific metadata keys in the Tika metadata schema.

The practical effect on the cleanroom argument is small — Tika isn't where any Revit-specific *knowledge* could leak from, since it has none to leak. But as written, the sentence credits Tika with doing more Revit-specific work than it does, and a careful reader (or a hostile one scrutinizing the cleanroom claim) could reasonably call that imprecise. **Recommended fix:** rephrase to something like *"Apache Tika, which detects `.rvt` as a generic OLE2/CFB container but performs no Revit-specific parsing"* — this is still citable as prior art for the container-format observation, without overclaiming a nonexistent "Revit metadata extractor."

## Raw output files

- `/tmp/tika-metadata-rvt.txt` — full `--metadata` output for `real.rvt`
- `/tmp/tika-text-rvt.txt` — `--text` output for `real.rvt` (empty)
- `/tmp/tika-text-rvt.err` — stderr/banner for the `--text` run
- `/tmp/tika.jar` — Tika 3.3.3 app jar (62 MB), reusable for future tests
