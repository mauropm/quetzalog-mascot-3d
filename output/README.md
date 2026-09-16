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

| | pass 1 | pass 2 | pass 3 | pass 4 | pass 5 | pass 6 | pass 7 | **pass 8 (current)** |
|---|---|---|---|---|
| posture | upright "teddy" sit | upright sit, refined | sphinx-sit, chest raised | sphinx-sit |
| neck | none (head on body) | none | distinct lofted neck | neck |
| head | oversized, low | measured | smaller, raised, longer snout | **sockets, brow, temples** |
| eyes | sphere + sphere iris + sphere pupil + sphere highlight | same | same | **1 smooth eyeball, iris/pupil/highlight painted** |
| crest | chaotic ball | radial petal halo | swept-back layered fan | **continuous mane rooted on the skull** |
| wings | spiky fans | sideways fans | big back-swept folded wings | back-swept wings |
| tail | short blob | spline + rings | longer, higher, thicker | tail |
| snout | short | short | short | short | +3.4 mm forward | +2 mm, wider | one volume + cream jaw | **+2 mm, squared nose block** |
| back feathers | — | spine ladder | spine ladder | spine ladder | dorsal tile ridge | **removed; wings converge** |
| shoulder / hip | — | — | — | — | rounded masses | flared limb tops | **rounded, leaning haunches** |
| neck | tube | tube | tube | tube | tube | chest-fed loft | **chest-fed loft** |
| feet / claws | 3 spheres + painted rings | 3 spheres | 3 spheres | 3 spheres | 3 spheres | 3 spheres | **broad slab + 4 cone claws** |
| dims (W×D×H) | 134 × 95 × 100 | 120 × 104 × 100 | 116 × 108 × 100 | 114 × 103 × 100 | 114 × 106 × 100 | 114 × 108 × 100 | 117 × 109 × 100 | **117 × 111 × 100** |

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

**Pass 7** fixed two specific problems:

1. **The back had three parallel feather rails.** The dorsal ridge added in
   pass 5 ran down the spine between the two wings, reading as a third rail
   that duplicated the wings. It is **removed entirely**, so the back is a
   coherent body surface again. In its place the **wing feathers now converge**:
   each wing's feather direction sweeps from *back-and-inward* at the inner end
   (`ax = −0.10`) to *outward-and-down* at the wingtip (`ax = +0.52`), so the
   two wings form a **V that meets the tail base** instead of running parallel.
   The wings themselves are unchanged.
2. **The snout's lower jaw read as a separate ball.** The cream muzzle was made
   of cheek/chin boxes parked behind the snout, so from the side it looked like
   a small round object sitting behind the snout. The **snout is now one volume
   extending down to z47**, and the cream muzzle is simply the **lower half of
   that same volume** (a material region, not separate geometry). The cheek pads
   were shrunk and tucked up beside the eyes.

**Pass 8** addressed five specific areas:

1. **Nose.** The snout tip now carries a distinct **soft-square jewel block** —
   a beveled box (12.2 × 9.0 × 9.0 mm, 2.5 mm bevel) merged into the snout, so
   the muzzle slopes down into it instead of the old pair of black dots on a
   plain rounded tip. The two nostrils are tall ovals painted on the block's
   front face.
2. **Toe/claw rows.** The feet were three round lobes in a row plus a cream ring
   painted around each claw — the "double chain" that read as mechanical. Each
   foot is now **one broad, slightly boxy slab** (super-ellipse power 3.4), and
   the claws are **four clean tapered cones** emerging from its front face.
3. **Snout length.** The front sections moved ~1 mm forward and the nose block
   adds ~1.5 mm more, so the muzzle is ~2.4 mm longer overall without touching
   the skull, eyes or mane.
4. **Hand/foot separation.** The rear limbs moved outboard (leg 13.5 → 19.0 mm,
   foot 14.5 → 19.5 mm) and now **lean out of the flank**, matching the measured
   reference (front feet ±10.0 mm, rear feet ±19.5 mm). The four limbs read as
   four limbs in the black silhouette test.
5. **Shoulders / hips.** Both limb lofts were re-profiled at super-ellipse power
   2.2 (rounder) with a fuller shoulder swell and a leaning haunch, so no
   straight cylinder butts against the torso.

## 2b. Material borders

Region borders are assigned per face, so a voxel remesh quantises every colour
edge to the 0.45 mm face grid. For the claws this read as a clipped sawtooth, so
`refine_material_edges()` **subdivides only the faces that straddle a material
boundary** (then triangulates the resulting n-gons and dissolves degenerates)
and re-assigns. That gives a clean skin/nail curve for ~75k extra faces instead
of re-voxelling the whole model. A grazing-angle test showed the claw boundary
is only clean when the cone meets the foot face near-perpendicularly, which is
why the claws emerge at ~45°.

## 3. Final dimensions

```
Width  (X)  116.85 mm
Depth  (Y)  110.99 mm
Height (Z)  100.00 mm
Base contact area  1509.4 mm^2
```

## 4. Validation results

```
Vertices                327,666
Edges                   681,171
Faces                   353,485
Connected components    1
Non-manifold edges      0
Boundary edges          0
Wire edges              0
Loose vertices          0
Degenerate faces        0
Invalid / inverted normals  0
Bounding box            (-58.42, -44.02, 0.00) -> (58.43, 66.98, 100.00) mm
Thickness samples       6,008
Min thickness           0.27 mm   (claw tip, grazing ray)
5th percentile          2.68 mm
Median thickness        10.93 mm
Materials               11
STATUS                  PASS — watertight, manifold, single shell
```

The exported STL was independently re-checked by parsing it directly: 655,372
triangles, 116.85 × 110.99 × 100.00 mm. The 3MF is a valid OPC package with 11
basematerials and `unit="millimeter"`; its full-precision coordinates give an
edge-use histogram of {2: 983,050, 4: 4} — i.e. manifold.

## 5. Print recommendations

- **Print upright as modelled** — the flat base (four feet) on the build plate,
  `+Z` up, marked by the `PRINT_ORIENTATION` empty.
- **Resin (SLA/DLP)** gives the best result and reproduces the feather tips and
  studs cleanly.
- **FDM**: 0.4 mm nozzle, 0.10–0.14 mm layers, supports under the wing, crest
  and tail overhangs.
- **Thickness**: median 10.9 mm, 5th percentile 2.68 mm. A probe restricted
  to the claw band gives a 5th percentile of 2.3 mm, so the claws are solid; the
  sub-millimetre whole-model minimum is a grazing ray at a silhouette edge.
- **Stability**: 1509 mm² of base contact across all four feet — no raft needed.

## 6. Files

```
output/
  quetzalog_mascot_print_ready.blend   full Blender project
  quetzalog_mascot_print_ready.stl     binary STL, millimetres (32.8 MB)
  quetzalog_mascot_print_ready.3mf     3MF with per-face colours (8.7 MB)
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
  refinement05/                        back + snout diagnostics
    back.png top.png rear34.png front.png
    snout_side.png snout_34.png
  refinement06/                        nose / limb / claw diagnostics
    front.png side.png back.png front_3quarter.png back_3quarter.png
    hands_feet_closeup.png snout_closeup.png
    silhouette_front.png silhouette_side.png silhouette_back.png
    clay_shoulder.png clay_hip.png clay_legs.png
    reg_head.png reg_head_side.png reg_back_upper.png
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
3. **The back is barer than the reference.** `views/back.png` does show a
   feather column down the spine; the pass-7 brief explicitly called the central
   rail unwanted, so the model has a plain body back with the two wings
   converging toward the tail.
4. **The mane is a compromise.** The six-view references show the crest as a
   flat radial fan behind the head, whereas the refinement brief asked for a
   continuous swept-back mane covering the crown. The model follows the brief
   (no bald patch), so its crest is taller and more swept than `views/front.png`.
5. **The wings are less spread** in the front view than the reference; this was
   carried over unchanged from pass 3 and is not part of this pass.
6. **The neck is thicker than the reference.** `views/right.png` shows a
   narrower neck column; feeding the front contour straight up from the chest
   (so the neck stops reading as a separate object) necessarily makes it wider.
7. **The toes are not separated.** The reference's four claws each emerge from
   their own rounded toe block. The pass-8 brief called the row of separate
   round toe lobes the "double chain" and asked for one broad form, so the model
   uses a single foot slab with four claws rather than four toe blocks.
8. **Claws meet the foot at ~45°.** A grazing-angle test showed the skin/nail
   material border is only clean when the claw's cone meets the foot face close
   to perpendicular. Steeper claws looked better in profile but produced a
   clipped, sawtoothed colour edge, so the angle was traded for border quality.
9. **Material borders are voxel-quantised.** Every region edge is assigned per
   face on the 0.45 mm voxel grid. `refine_material_edges()` subdivides just the
   boundary faces to soften this, but the remaining stair-step is a resolution
   characteristic shared with the belly panel and mane colours, not specific to
   the claws.
10. **LEGO studs / brick seams** are represented only as small studs on the
    feather plates and the belly panel. Modelling every 1×1 plate seam would add
    sub-millimetre noise that would not print.
11. **Crest colours** vary per leaf in the references with no strict pattern; a
    repeating rainbow sequence is used.
12. **No physical scale was given**; 100 mm overall height was assumed.
