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

| | pass 1 | pass 2 | pass 3 | pass 4 | pass 5 | **pass 6 (current)** |
|---|---|---|---|---|
| posture | upright "teddy" sit | upright sit, refined | sphinx-sit, chest raised | sphinx-sit |
| neck | none (head on body) | none | distinct lofted neck | neck |
| head | oversized, low | measured | smaller, raised, longer snout | **sockets, brow, temples** |
| eyes | sphere + sphere iris + sphere pupil + sphere highlight | same | same | **1 smooth eyeball, iris/pupil/highlight painted** |
| crest | chaotic ball | radial petal halo | swept-back layered fan | **continuous mane rooted on the skull** |
| wings | spiky fans | sideways fans | big back-swept folded wings | back-swept wings |
| tail | short blob | spline + rings | longer, higher, thicker | tail |
| snout | short | short | short | short | +3.4 mm forward | **+2 mm, wider** |
| back feathers | — | spine ladder | spine ladder | spine ladder | **dorsal tile ridge** |
| shoulder / hip | — | — | — | — | rounded masses | **flared limb tops** |
| neck | tube | tube | tube | tube | tube | **chest-fed loft** |
| dims (W×D×H) | 134 × 95 × 100 | 120 × 104 × 100 | 116 × 108 × 100 | 114 × 103 × 100 | 114 × 106 × 100 | **114 × 108 × 100** |

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

**Pass 5** was a structural refinement pass on three specific problems:

1. **Snout too short.** The snout cross-sections were pushed forward
   (`cy −28.0 → −31.5` at the widest section), so the tip now sits at
   `Y = −39.2` instead of `−35.9` — **3.4 mm more forward projection** with the
   same width, height and rounded profile. The nostrils moved with it.
2. **Tail↔back feather bridge.** The dorsal feathers were a sparse diagonal
   ladder pointing up-and-back, which read as a loop climbing from the tail
   into the upper back and left the back bare between the wings. They are now a
   **roof-tile dorsal ridge**: roots measured on the actual back surface, flowing
   *down-and-back* from the nape to the tail base, wide central tiles with
   staggered flanking tiles so the whole back is covered wing to wing. The
   reference (`views/back.png`) shows one continuous feather column from the
   head to the tail, so continuity was kept — as a deliberate mane, not a loop.
3. **Tubular limbs.** The front legs and rear haunches butted into the torso as
   near-constant cylinders. Each now ends in a **rounded shoulder / hip mass**
   (`add_ellipsoid`) that overlaps the torso and carries the leg's top section,
   and the leg lofts are tapered rather than constant-width. No cylinder-to-body
   intersection remains.

**Pass 6** was a soft-cartoon-anatomy pass. Everything was verified against
**neutral gray clay renders** (`output/refinement04/clay_*.png`) so the shapes
were judged without colour.

1. **Snout larger and longer.** The sections moved forward again
   (`cy −31.5 → −33.5`) and grew slightly (`hx 7.3 → 7.6`, `hy 7.8 → 8.2`), so
   the tip is now at `Y = −41.2` (from `−39.2`) and the snout reads chunkier.
   The nostrils moved with it.
2. **Neck rebuilt as a chest-fed loft.** The neck used to be a *tube* starting
   inside the torso: its front sat at `y ≈ −5.6` while the cream chest plate was
   at `y ≈ −19`, so the neck was recessed 13 mm behind the chest and read as a
   separate object sitting on the body. It is now an 8-section loft whose
   **front contour is carried straight up from the chest plate** (−18.5 → −20.0
   → −19.2) and only steps back under the jaw. A small throat mass fills the
   notch between the jaw overhang and the neck. The top of the neck stays
   narrower than the head, so the **intentional sharp jaw edge is preserved**.
3. **Shoulders and hips are now flared limb tops, not bolted-on spheres.** The
   pass-5 ellipsoids were removed. Each leg's loft now widens continuously into
   the torso (`hx 6.6 → 9.4` front, `8.0 → 9.8` rear) and then **shrinks back
   inside the body** (`→ 4.2`), so the cap is buried and there is no exposed
   flat edge. The limbs were also pulled back (front `y −12 → −11`, rear
   `y 15 → 12.5`) so their fronts sit flush with the chest instead of hanging
   out in front of it.

## 3. Final dimensions

```
Width  (X)  113.63 mm
Depth  (Y)  108.14 mm
Height (Z)  100.00 mm
Base contact area  1237.2 mm^2
```

## 4. Validation results

```
Vertices                280,744
Edges                   561,540
Faces                   280,776
Connected components    1
Non-manifold edges      0
Boundary edges          0
Wire edges              0
Loose vertices          0
Degenerate faces        0
Invalid / inverted normals  0
Bounding box            (-56.81, -41.16, 0.00) -> (56.81, 66.98, 100.00) mm
Thickness samples       6,038
Min thickness           0.36 mm   (feather silhouette edge, grazing ray)
5th percentile          2.72 mm
Median thickness        11.47 mm
Materials               11
STATUS                  PASS — watertight, manifold, single shell
```

The exported STL was re-imported and independently re-checked: 280,744 verts /
561,528 tris, 0 non-manifold, 0 boundary, 113.63 × 108.14 × 100.00 mm. The 3MF
is a valid OPC package with 11 basematerials and `unit="millimeter"`.

## 5. Print recommendations

- **Print upright as modelled** — the flat base (four feet) on the build plate,
  `+Z` up, marked by the `PRINT_ORIENTATION` empty.
- **Resin (SLA/DLP)** gives the best result and reproduces the feather tips and
  studs cleanly.
- **FDM**: 0.4 mm nozzle, 0.10–0.14 mm layers, supports under the wing, crest
  and tail overhangs.
- **Thickness**: median 11.5 mm, 5th percentile 2.67 mm. The sub-millimetre
  reading is a grazing ray at a feather silhouette edge, not a wall — the plates
  themselves are ~3.4 mm thick.
- **Stability**: 1237 mm² of base contact — no raft needed.

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
  refinement/                          head close-ups (face/mane pass)
    head_front.png head_3quarter.png head_side.png head_top.png head_back34.png
  refinement03/                        body renders (structural pass)
    front.png side.png back.png top.png 3quarter.png
  refinement04/                        clay + close-ups (soft-anatomy pass)
    head_side.png head_3quarter.png neck_front.png
    body_front.png body_3quarter.png body_side.png  clay_*.png
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
3. **The dorsal ridge is denser than the reference.** `views/back.png` shows a
   narrower feather column with more bare teal flanking it; the ridge here covers
   the full back to avoid the empty cavity the brief called out.
4. **The mane is a compromise.** The six-view references show the crest as a
   flat radial fan behind the head, whereas the refinement brief asked for a
   continuous swept-back mane covering the crown. The model follows the brief
   (no bald patch), so its crest is taller and more swept than `views/front.png`.
5. **The wings are less spread** in the front view than the reference; this was
   carried over unchanged from pass 3 and is not part of this pass.
6. **The neck is thicker than the reference.** `views/right.png` shows a
   narrower neck column; feeding the front contour straight up from the chest
   (so the neck stops reading as a separate object) necessarily makes it wider.
7. **LEGO studs / brick seams** are represented only as small studs on the
   feather plates and the belly panel. Modelling every 1×1 plate seam would add
   sub-millimetre noise that would not print.
8. **Crest colours** vary per leaf in the references with no strict pattern; a
   repeating rainbow sequence is used.
9. **No physical scale was given**; 100 mm overall height was assumed.
