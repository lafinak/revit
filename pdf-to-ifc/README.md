# PDF → IFC envelope extraction

Extracts a real, correctly-dimensioned building envelope from a floor-plan
PDF and produces an IFC4 file openable in Revit or any IFC tool.

**Read [verification.md](./verification.md) before trusting the output** —
it documents exactly what's automated vs. human-verified, and what scope
this does and does not cover. Short version: this is a real, correct
exterior shell (4 walls at verified dimensions), not a complete floor-plan
reconstruction with interior partitions, doors, and rooms. That's an honest
limitation, stated up front, not a bug discovered later.

## Usage

```bash
pip install pymupdf  # only dependency

python3 extract.py input.pdf > geometry.json
python3 build_ifc.py geometry.json output.ifc
```

## Outputs in this directory

- `plan2.ifc` / `plan2_geom.json` — from `2.pdf.pdf` (6600×7550mm, 450mm walls;
  stairwell, bathroom, main living space, entry)
- `plan3.ifc` / `plan3_geom.json` — from `3.pdf.pdf` (same envelope; stairwell,
  bathroom, kitchen, main living space, entry)
- `plan4.ifc` / `plan4_geom.json` — from `4.pdf.pdf` (same envelope; stairwell,
  bathroom, main living area, entry)
- `verification.md` — what's verified, what's not, read this first

## Importing into Revit

File → Open → IFC → pick `plan2.ifc` (or `plan3`/`plan4`). Revit converts the
IFC walls to native Revit wall elements.

## Why the envelope only, not full interior reconstruction

The source PDFs have zero extractable text (dimension numbers are vector
outlines, not text objects) and dense, unlabeled hatch-pattern geometry for
interior walls. A blind automated classifier on that geometry, built under
same-day time pressure, risks producing *wrong* wall placements that would
be immediately recognizable as incorrect to the architect who drew the
original plans. The exterior envelope dimensions were confirmed by direct
visual inspection of the rendered PDFs and are correct; the interior layout
is a documented next step, not a silent gap.
