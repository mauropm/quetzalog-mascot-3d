# Quetzalog Mascot — 3D Printable Reconstruction

Watertight, manifold, 3D-printable reconstruction of the **Quetzalog** mascot,
inferred as a real three-dimensional form from the six orthographic reference
views in `views/`.

![Quetzalog](../output/hero.png)

---

## 1. Reconstruction methodology

This is a **second, ground-up reconstruction**. The first pass extruded and
smoothed the reference silhouettes and produced a lumpy, relief-like blob. The
second pass treats the six images as a turnaround sheet and infers one coherent
volume that explains all of them.

**Measured first.** Every reference was composited onto white, segmented by
colour, overlaid with a coordinate grid and profiled row-by-row
(`scripts/analyze_regions.py`, `scripts/grid_refs.py`). Landmarks were read off
in millimetres (`scripts/SPEC.md`):

```
front view scale   1105 px = 100 mm  ->  1 px = 0.0905 mm
eye centre         X +/-9.8   Z 60.2   radius 7.7
head               X +/-18    Z 46..80
body               X +/-17.2  Z 14..48
cream muzzle       X +/-15    Z 39..57
wing span          X +/-59    Z 36..68
feet outer         X +/-29
red crest piece    X +/-4     Z 69..80
top view (depth)   snout tip Y -25 .. tail tip Y ~ +60
```

**Modelled as cross-sections, not primitives.** The torso, head, snout, neck
and all four limbs are lofted surfaces built from explicit
`(z, half-width, half-depth, centre-y)` section stacks with super-elliptical
cross-sections (`power` 2.6–3.2), which gives the LEGO rounded-brick feel and a
smooth, controlled surface — no stacked spheres.

**Appropriate technique per feature** (spec section 7):

| feature | technique |
|---|---|
| torso / head / snout / neck / limbs | super-elliptical cross-section lofts |
| tail | Catmull-Rom spline core + tapering tube, radial feather rings |
| wing arms | tapering tubes between measured joint positions |
| crest / wings / tail / spine feathers | reusable flat "leaf" blade with a LEGO stud |
| eyes | layered spheres: sclera → iris → pupil → highlight |
| claws / nostrils | tapered ellipsoids |
| red forehead crest | beveled brick |

**The crest** is the character's signature. It is built as a layered **petal
rosette**: five rings of leaves on a tilted axis around the head, each ring's
petals lying flat *in* the ring plane (their plate normal is the ring normal),
so they read as a clean sunburst from the front and as overlapping plates from
the side — not as a random ball of spikes.

**Unified solid.** All parts are joined and voxel-remeshed at **0.45 mm**, which
preserves the feather plates and studs while guaranteeing a single watertight
shell. The base is bisected flat at the feet and the model scaled to exactly
100 mm tall.

**Materials** are 11 flat colours assigned per face from a procedural region
registry (capsules/ellipsoids for feathers, eyes, claws, muzzle, belly). Region
predicates are **re-mapped through the same flatten+scale transform** as the
geometry, so colour borders stay locked to the surfaces.

## 2. Major changes from the first pass

| | pass 1 | pass 2 |
|---|---|---|
| body/head | stacked spheres & boxes | measured super-elliptical cross-section lofts |
| crest | chaotic ball of randomly-oriented feathers | 5-ring layered petal rosette, coplanar petals |
| wings | spiky "finger" fans, leaves edge-on | arm + fan of flat plates facing the viewer |
| tail | short blob | spline core with radial feather rings, correct depth |
| eyes | googly spheres, wrong materials | sclera/iris/pupil/highlight, correct proportions |
| feet | undersized | measured splayed rear feet, tapered soles |
| surface | bumpy, over-smoothed | clean; no smoothing modifier at all |
| dimensions | 134 × 95 × 100 mm | **120.2 × 104.2 × 100.0 mm** (ref: 117 × 102 × 100) |

## 3. Final dimensions

```
Width  (X)  120.23 mm
Depth  (Y)  104.19 mm
Height (Z)  100.00 mm
Base contact area  1133.5 mm^2
```

## 4. Validation results

```
Vertices                250,654
Edges                   501,025
Faces                   250,337
Connected components    1
Non-manifold edges      0
Boundary edges          0
Wire edges              0
Loose vertices          0
Degenerate faces        0
Invalid / inverted normals  0
Bounding box            (-60.11, -40.28, 0.00) -> (60.11, 63.92, 100.00) mm
Thickness samples       6,041
Min thickness           0.56 mm   (silhouette-edge ray, see notes)
5th percentile          2.82 mm
Median thickness        12.49 mm
Materials               11
STATUS                  PASS — watertight, manifold, single shell
```

The exported STL was re-imported and independently re-checked: watertight,
single shell, 100 mm tall, 0 non-manifold edges.

## 5. Print recommendations

- **Print upright as modelled.** The flat base (four feet) sits on the build
  plate, `+Z` up. This orientation is marked by the `PRINT_ORIENTATION` empty.
- **Resin (SLA/DLP)** gives the best result and reproduces the feather tips and
  studs cleanly.
- **FDM**: 0.4 mm nozzle, 0.10–0.14 mm layers. Add supports under the wing,
  crest and tail overhangs.
- **Thickness**: median 12.5 mm, 5th percentile 2.82 mm. The single 0.56 mm
  reading is a grazing ray at a feather silhouette edge, not a wall — the plates
  themselves are 3.2 mm thick.
- **Stability**: 1133 mm² of base contact, low centre of gravity — no raft
  needed.

## 6. Files

```
output/
  quetzalog_mascot_print_ready.blend   full Blender project (refs, model, cameras, lights)
  quetzalog_mascot_print_ready.stl     binary STL, millimetres (25.1 MB)
  quetzalog_mascot_print_ready.3mf     3MF with per-face colours (6.2 MB)
  validation_report.txt                mesh audit
  hero.png                             hero render
  comparison/                          six-view REFERENCE | MODEL | OVERLAY sheets
    front.png back.png left.png right.png top.png bottom.png
    perspective_test.png               four perspective coherence renders
    clay_*.png                         neutral gray-clay renders (geometry only)
    head_front.png head_clay.png       head close-ups
  renders/                             orthographic + perspective PNGs
```

## 7. Known deviations from the references

1. **The reference set is internally inconsistent.** The tail appears on the
   *image-left* in both the front **and** the back view, which is geometrically
   impossible (those views are mirrored). The top and bottom views both put the
   tail toward the character's **left (+X)**, so the model follows the majority
   — 3 of 4 views. Consequently the model's **front view is mirrored** relative
   to `views/front.png` with respect to the tail only.
2. **`left.png` / `right.png` are three-quarter perspective renders**, not true
   orthographic side views (the head is turned toward camera and the eye is
   visible). They were used qualitatively for crest sweep and tail depth; the
   model's true orthographic side views therefore show less face than those
   references.
3. **LEGO studs / brick seams** are represented only as the small studs on the
   feather plates and the belly panel. Modelling every 1×1 plate seam would add
   sub-millimetre noise that would not print and would reintroduce the bumpy
   surface this pass was specifically meant to remove.
4. **Crest colours** vary per leaf in the references with no strict pattern; a
   repeating rainbow sequence is used.
5. **No physical scale was given**; 100 mm overall height was assumed.
