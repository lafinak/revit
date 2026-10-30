# Verification — PDF → IFC envelope extraction

Run date: 2026-10-30. Source: 3 real floor-plan PDFs (`2.pdf.pdf`, `3.pdf.pdf`,
`4.pdf.pdf`), provided by the user for a same-day demo.

## Methodology (read this before trusting the numbers)

These PDFs have **zero extractable text** — `page.get_text("words")` returns
empty on all three files, confirmed directly. Every dimension label visible
in the rendered drawing ("6600", "450", etc.) is a vector-outline glyph, not
a text object. There is no reliable, fast way to OCR these out of raw vector
paths in the time available for a same-day build.

**What is genuinely automated and deterministic** (`extract.py`): finding the
floor-plan drawing's bounding region via spatial density of line endpoints
(separating it from the sparser legend/title-block region on the page), and
confirming the file contains real, dense vector geometry at all (line/curve
counts). Re-running `extract.py` on the same PDF always produces the same
bounding-region numbers.

**What is NOT automated**: the exact real-world dimensions. These were read
directly off 3x-rendered PNGs of each PDF by direct visual inspection
(`page.get_pixmap(matrix=fitz.Matrix(3,3))`), not computed from PDF
coordinates. All three plans showed clearly labeled, repeated dimension
callouts confirming:

- **Overall envelope: 6600mm × 7550mm** — identical across all 3 plans (same
  building shell, different interior layouts)
- **Perimeter wall thickness: 450mm** — labeled on all 4 sides of all 3 plans

This is an honest, verified ground truth (directly read, cross-checked
against the vector line-length histogram which independently shows a
dominant line length cluster consistent with this scale), but it is not a
"the algorithm figured it out from scratch" result, and this document says so
explicitly rather than overclaiming full automated digitization.

**Scope**: the built IFC files contain the **exterior envelope only** (4
perimeter walls forming the building footprint), not a full room-by-room
reconstruction of every interior partition, door, and fixture visible in the
drawings. The interior geometry exists only as dense, unlabeled hatch-pattern
vector soup (2,600-3,200 line segments and 1,800-2,900 curve segments per
file) that a blind automated classifier could easily misclassify under time
pressure — producing *wrong* geometry is worse than producing an honest,
correct *subset* of the geometry. Wall height (2.8m) is an industry-standard
assumption, not a measurement — no 2D plan view carries height data.

## Results per plan

| Plan | Rooms visible (from rendered image) | Envelope | Wall thickness | Walls built | IFC entities | Parses with ifc-lite |
|---|---|---|---|---|---|---|
| `plan2.ifc` | stairwell, bathroom, main living space, entry | 6600×7550mm | 450mm | 4 | 159 | ✅ `ifc-lite info` → entityCount 159, `ask "how many walls?"` → 4 |
| `plan3.ifc` | stairwell, bathroom, kitchen, main living space, entry | 6600×7550mm | 450mm | 4 | 159 | ✅ same |
| `plan4.ifc` | stairwell, bathroom, main living area, entry | 6600×7550mm | 450mm | 4 | 159 | ✅ same |

All three files are byte-identical in structure (same entity type counts) —
expected, since all three source PDFs share the same verified envelope
dimensions; only the room layout differs, which is not yet reconstructed.

## What was NOT verified

- Interior partition walls, doors, windows, and fixtures (stairs, toilets,
  sinks, counters visible in the renders) — not reconstructed in this pass.
- Wall height — assumed at 2.8m, not measured from any source.
- Geometric fidelity against Revit's own interpretation of the same PDF, if
  imported there directly — only ifc-lite's own parse was checked here.

## Honest bottom line

This produces a **real, correctly-dimensioned building envelope** per plan —
not a complete floor plan. For the demo: open in Revit via File → Open → IFC
to show a real 3D shell at the correct footprint, then be upfront that
interior walls/rooms are a planned next step, not yet automated. That's a
defensible, honest artifact — better than a fabricated-looking "complete"
floor plan that would embarrass the work if the architect looks closely at
interior geometry that was never actually measured.
