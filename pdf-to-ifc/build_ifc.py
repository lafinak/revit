#!/usr/bin/env python3
"""Build an IFC4 file from extract.py's geometry JSON.

Builds the verified exterior building envelope (4 perimeter walls at the
human-verified dimensions) as real IfcWall entities via the ifc-lite CLI,
then merges them into one file.

Honest scope note: this builds the EXTERIOR ENVELOPE ONLY (4 walls forming
the building footprint), not a full room-by-room reconstruction of every
interior partition. See extract.py's docstring for why: the interior wall
geometry in these PDFs is only recoverable via fragile automated
line-classification on dense hatch-pattern vector soup, which was judged too
likely to produce incorrect geometry under the time constraint for a live
demo. The envelope dimensions (width/depth/wall thickness) ARE verified
ground truth, so this produces a correct, real building shell -- not a
complete floor plan, but not fabricated either.

Wall height is not given anywhere in a 2D plan view, so a standard 2800mm
(2.8m) interior height is assumed and labeled as an assumption, not a
measurement.
"""
import sys
import json
import subprocess
import os


def mm_to_m(mm):
    return mm / 1000.0


def run(cmd):
    print(f"  $ {' '.join(cmd)}", file=sys.stderr)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FAILED: {r.stderr}", file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{r.stderr}")
    print(f"  {r.stdout.strip()}", file=sys.stderr)
    return r.stdout


def build(geom_path, out_path, tmp_dir):
    with open(geom_path) as f:
        geom = json.load(f)

    dims = geom["verified_dimensions"]
    if not dims:
        raise ValueError(f"no verified dimensions for {geom['source_pdf']}")

    width_m = mm_to_m(dims["width_mm"])
    depth_m = mm_to_m(dims["depth_mm"])
    thickness_m = mm_to_m(dims["wall_thickness_mm"])
    height_m = 2.8  # assumed, not measured -- 2D plan has no height info

    os.makedirs(tmp_dir, exist_ok=True)
    wall_files = []

    # 4 perimeter walls, centerlines on the envelope rectangle
    segments = [
        ("south", (0, 0, 0), (width_m, 0, 0)),
        ("east", (width_m, 0, 0), (width_m, depth_m, 0)),
        ("north", (width_m, depth_m, 0), (0, depth_m, 0)),
        ("west", (0, depth_m, 0), (0, 0, 0)),
    ]

    for name, start, end in segments:
        wf = os.path.join(tmp_dir, f"wall_{name}.ifc")
        run([
            "ifc-lite", "create", "wall",
            "--start", f"{start[0]},{start[1]},{start[2]}",
            "--end", f"{end[0]},{end[1]},{end[2]}",
            "--height", str(height_m),
            "--thickness", str(thickness_m),
            "--out", wf,
        ])
        wall_files.append(wf)

    run(["ifc-lite", "merge"] + wall_files + ["--out", out_path])

    return {
        "source_pdf": geom["source_pdf"],
        "envelope_m": {"width": width_m, "depth": depth_m,
                        "wall_thickness": thickness_m, "height_assumed": height_m},
        "walls_created": len(segments),
        "out": out_path,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: build_ifc.py <geom.json> <out.ifc>", file=sys.stderr)
        sys.exit(1)
    result = build(sys.argv[1], sys.argv[2], "/tmp/pdf-to-ifc-walls")
    print(json.dumps(result, indent=2))
