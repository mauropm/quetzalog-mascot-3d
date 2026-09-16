# Quetzalog Mascot — 3D Printable Reconstruction

Watertight, manifold, 3D-printable reconstruction of the **Quetzalog** mascot,
built in Blender from the six orthographic reference views in `views/` and
matched against the target design `image2.png`.

![Quetzalog](hero.png)

---

## 1. Reconstruction methodology

The model is generated procedurally from **measured cross-sections**, not by
extruding or displacing the reference images.

**Measured first.** The references are composited onto white, colour-segmented,
grid-overlaid and profiled row-by-row (`scripts/analyze_regions.py`,
`scripts/grid_refs.py`). Landmarks are read off in millimetres
(`scripts/SPEC.md`), and `scripts/profile_compare.py` diffs reference vs model
silhouette per row so every change is driven by numbers.

**Technique per feature** (spec section 7):

| feature | method |
|---|---|
| torso / head / snout / neck / limbs | super-elliptical cross-section **lofts** from measured section stacks |
| tail | Catmull-Rom spline core + tapering tube with radial feather rings |
| wing arms | tapering tubes between measured joint positions |
| crest / wings / tail / spine feathers | reusable flat "leaf" blade (curvable) with a LEGO stud |
| head mane | layered feather rows rooted on the skull surface |
| eyes | one smooth eyeball + painted material regions |
| claws / nostrils | tapered ellipsoids |
| red forehead crest | beveled brick |

**Unified solid.** All parts are joined and voxel-remeshed at **0.45 mm**, which
preserves the feather plates and studs while guaranteeing a single watertight
shell. Degenerate geometry left by the remesh is removed, the base is bisected
flat at the feet, and the model is scaled to exactly 100 mm tall.

**Materials** — 11 flat colours assigned per face from a procedural region
registry (capsules/ellipsoids). Region predicates are re-mapped through the same
flatten+scale transform as the geometry, so colour borders stay locked to the
surfaces.

## 2. Progression across passes

| | pass 1 | pass 2 | pass 3 | **pass 4 (current)** |
|---|---|---|---|---|
| posture | upright "teddy" sit | upright sit, refined | sphinx-sit, chest raised | sphinx-sit |
| neck | none (head on body) | none | distinct lofted neck | neck |
| head | oversized, low | measured | smaller, raised, longer snout | **sockets, brow, temples** |
| eyes | sphere + sphere iris + sphere pupil + sphere highlight | same | same | **1 smooth eyeball, iris/pupil/highlight painted** |
| crest | chaotic ball | radial petal halo | swept-back layered fan | **continuous mane rooted on the skull** |
| wings | spiky fans | sideways fans | big back-swept folded wings | back-swept wings |
| tail | short blob | spline + rings | longer, higher, thicker | tail |
| dims (W×D×H) | 134 × 95 × 100 | 120 × 104 × 100 | 116 × 108 × 100 | **114 × 103 × 100** |

**Pass 3** was driven by `image1.png` (previous model) vs `image2.png` (target
design): the target is a **sphinx-sit** with the head raised on a neck, large
wings folded back along the body, a long tail and a swept crest.

**Pass 4** was a face + mane refinement pass. Three defects were fixed:

1. **Eyes popped out.** The eyeballs were spheres sitting proud of the skull
   with no facial volume around them. The head now carries a **brow ridge, a
   temple/cheek mass and eye sockets**, and the eyeballs are pulled in so they
   protrude only ~2 mm and never break the head silhouette.
2. **Protruding white highlight.** The highlight (and the iris and pupil) were
   separate *geometry* — a small sphere stuck on the eyeball. All three are now
   **material regions painted onto one smooth eyeball**, so nothing protrudes and
   the highlight cannot catch a physical specular bump. Region predicates are
   sized from the reference (iris ≈ 68 % of the eye, pupil ≈ 36 %).
3. **Bald crown.** The head was a bare dome with a feather ring behind it. The
   crest is replaced by a **continuous mane**: six layered rows of feathers
   rooted *inside* the skull surface, starting immediately above the brow and
   running over the crown and down the nape. Row flow rotates from up-and-back
   at the forehead to back-and-down at the nape, and the blade primitive gained
   a **curvature** parameter so the feathers sweep rather than spike. The bare
   forehead band is now ~4 mm.

## 3. Final dimensions

```
Width  (X)  113.63 mm
Depth  (Y)  102.79 mm
Height (Z)  100.00 mm
Base contact area  1228.6 mm^2
```

## 4. Validation results

```
Vertices                283,185
Edges                   566,423
Faces                   283,212
Connected components    1
Non-manifold edges      0
Boundary edges          0
Wire edges              0
Loose vertices          0
Degenerate faces        0
Invalid / inverted normals  0
Bounding box            (-56.81, -35.81, 0.00) -> (56.81, 66.98, 100.00) mm
Thickness samples       6,025
Min thickness           0.15 mm   (feather silhouette edge, grazing ray)
5th percentile          2.70 mm
Median thickness        11.38 mm
Materials               11
STATUS                  PASS — watertight, manifold, single shell
```

The exported STL was re-imported and independently re-checked: 283,185 verts /
566,422 tris, 0 non-manifold, 0 boundary, 113.63 × 102.79 × 100.00 mm. The 3MF
is a valid OPC package with 11 basematerials and `unit="millimeter"`.

## 5. Print recommendations

- **Print upright as modelled** — the flat base (four feet) on the build plate,
  `+Z` up, marked by the `PRINT_ORIENTATION` empty.
- **Resin (SLA/DLP)** gives the best result and reproduces the feather tips and
  studs cleanly.
- **FDM**: 0.4 mm nozzle, 0.10–0.14 mm layers, supports under the wing, crest
  and tail overhangs.
- **Thickness**: median 11.4 mm, 5th percentile 2.70 mm. The sub-millimetre
  reading is a grazing ray at a feather silhouette edge, not a wall — the plates
  themselves are ~3.4 mm thick.
- **Stability**: 1229 mm² of base contact — no raft needed.

## 6. Files

```
output/
  quetzalog_mascot_print_ready.blend   full Blender project
  quetzalog_mascot_print_ready.stl     binary STL, millimetres (27.3 MB)
  quetzalog_mascot_print_ready.3mf     3MF with per-face colours (6.8 MB)
  validation_report.txt                mesh audit
  hero.png                             hero render
  comparison/
    front.png back.png left.png right.png top.png bottom.png
                                         REFERENCE | MODEL | OVERLAY sheets
    target_vs_model.png                  image2 vs model from the matching camera
    perspective_test.png                 four perspective coherence renders
    clay_*.png                           neutral gray-clay renders (geometry only)
    head_front.png head_clay.png         head close-ups
  refinement/                          head close-ups for the face/mane pass
    head_front.png head_3quarter.png head_side.png head_top.png head_back34.png
  renders/                             orthographic + perspective PNGs
```

## 7. Known deviations from the target

1. **The reference set is internally inconsistent.** The tail appears on the
   *image-left* in both the front **and** the back view, which is impossible for
   one object. The top and bottom views put the tail toward the character's
   **left (+X)**, so the model follows the 3-of-4 majority; the model's front
   view is therefore mirrored relative to `views/front.png` with respect to the
   tail only.
2. **`left.png` / `right.png` are three-quarter perspective renders**, not true
   orthographic side views. `image2.png` is the same kind of view. They were
   used qualitatively (crest sweep, tail depth, wing fold); the model's true
   orthographic side views therefore show less face than those references.
3. **The mane is a compromise.** The six-view references show the crest as a
   flat radial fan behind the head, whereas the refinement brief asked for a
   continuous swept-back mane covering the crown. The model follows the brief
   (no bald patch), so its crest is taller and more swept than `views/front.png`.
4. **The wings are less spread** in the front view than the reference; this was
   carried over unchanged from pass 3 and is not part of this pass.
5. **LEGO studs / brick seams** are represented only as small studs on the
   feather plates and the belly panel. Modelling every 1×1 plate seam would add
   sub-millimetre noise that would not print.
6. **Crest colours** vary per leaf in the references with no strict pattern; a
   repeating rainbow sequence is used.
7. **No physical scale was given**; 100 mm overall height was assumed.
