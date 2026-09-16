# Quetzalog Mascot 3D Model

## Source
Six orthographic reference images from `views/` (`front.png`, `back.png`,
`left.png`, `right.png`, `top.png`, `bottom.png`). All are 1375 x 1144 px,
white background. They depict a chibi teal dragon mascot ("Quetzalog") in a
LEGO-style blocky/studded aesthetic: oversized head, big cartoon eyes, cream
muzzle and belly, a rainbow feather crest, feathered wings, a feathered curled
tail, a red forehead crest piece and four stubby clawed feet.

The references are AI-generated "views" and are not perfectly mutually
consistent (e.g. the tail curls to the opposite side between front and back
views). They were therefore used as **constraints on silhouette, proportion and
character features**, and a single coherent 3D volume was inferred rather than
projecting each view independently.

## Model
Reconstruction approach (fully procedural, Blender Python via MCP):

1. **Reference setup** - the six images were imported as aligned image-empties
   in the `REFERENCES` collection in an orthographic environment
   (`X` = left/right, `Y` = front/back, `Z` = up, front = `-Y`), scaled so the
   mascot maps to a 100 mm tall volume.
2. **Blockout** - primary volumes built from beveled boxes, ellipsoids and
   cylinders: torso, hips, chest, neck, head, mane base, snout, chin, cheeks,
   four legs and feet.
3. **Character details** - eyes (sclera / iris / pupil / highlight spheres),
   cream muzzle and belly, cream claws, red forehead crest piece, nostril bar.
4. **Feathers** - a reusable procedural "blade" primitive (narrow stem, broad
   rounded tip, super-elliptical cross-section so each feather reads as a flat
   LEGO-style plate). Used to build:
   - the rainbow **crest** (5 concentric layers over a dome around the head),
   - the **spine ridge**,
   - the two **wings** (a green segmented arm plus two fanned rows of primaries
     and coverts),
   - the **tail** (a Catmull-Rom spline core with rings of radial feathers).
5. **Union** - all parts were joined and a **voxel remesh** (0.75 mm) produced a
   single watertight, self-intersection-free solid; a light smooth pass and a
   flat base cut followed.
6. **Materials** - 11 materials (teal body, cream, red, orange, yellow, green,
   blue, purple, eye white, iris, pupil) are assigned per-face from the
   procedural region registry (capsules/ellipsoids for feathers, eyes, claws,
   muzzle and belly), so the colour regions are baked into the geometry rather
   than relying on textures.
7. **Scale** - the model was uniformly scaled so the overall height is exactly
   100 mm.

### Structure
```
QUETZALOG
├── REFERENCES   (6 aligned orthographic image-empties)
├── BLOCKOUT     (empty - merged into the final solid)
├── DETAIL       (empty - merged into the final solid)
├── PRINT_READY  (QUETZALOG_PRINT_READY - the single printable mesh)
└── VALIDATION   (ANNOTATION_QUETZALOG + QUETZALOG_INFO text)
CAMERAS  (front/back/left/right/top/bottom/persp)
LIGHTS   (Key / Fill / Rim)
PRINT_ORIENTATION  (empty marking +Z up, base on build plate)
```

## Dimensions
- Width  (X): **134.07 mm** (wing tip to wing tip / tail)
- Depth  (Y): **95.16 mm**
- Height (Z): **100.00 mm**
- Base contact area at z = 0: **~1636 mm²**

## Printing
- **Recommended technology:** resin (SLA/DLP) for best detail, or FDM with a
  0.4 mm nozzle and 0.12-0.16 mm layers.
- **Recommended orientation:** print **upright as modelled** - the flat base
  (the four feet, cut flat at z = 0) sits on the build plate, `+Z` is up.
  `PRINT_ORIENTATION` marks this orientation.
- **Supports:** the body is self-supporting, but supports are recommended
  under the horizontally-projecting **wing feathers**, the outer **crest**
  feathers and the **tail** overhangs.
- **Wall / feature thickness:** the solid is solid (no hollow shells); the
  thinnest features are feather tips and blades. Measured inward ray-cast
  thickness: minimum **1.37 mm**, 5th percentile **2.76 mm**, median
  **11.03 mm**. This is comfortably printable in resin and acceptable in FDM.
- **Base:** flat and stable; no extra raft/platform is required.

## Validation
```
Vertices:               123,286
Edges:                  246,283
Faces:                  122,989
Object count:           1 printable mesh (plus references/cameras/lights)
Connected components:   1
Non-manifold edges:     0
Boundary edges:         0
Loose geometry:         0  (0 loose verts, 0 wire edges)
Degenerate faces:       0
Invalid/inverted normals: 0
Bounding box:           (-70.14, -41.59, 0.00) -> (63.93, 53.57, 100.00) mm
Dimensions:             134.07 x 95.16 x 100.00 mm
Min feature thickness:  1.37 mm (5th pct 2.76 mm)
Base contact area:      1636.3 mm²
Materials:              11
STATUS:                 PASS - watertight, manifold, single shell
```
The exported STL was re-imported and re-checked independently:
123,286 verts / 246,588 triangles, 0 non-manifold edges, 0 boundary edges,
1 connected component, dimensions 134.07 x 95.16 x 100.00 mm.

## Files
- BLEND: `output/quetzalog_mascot_print_ready.blend`
- STL:   `output/quetzalog_mascot_print_ready.stl` (binary, 12.3 MB)
- 3MF:   `output/quetzalog_mascot_print_ready.3mf` (3MF core + basematerials, 3.3 MB)
- Report:`output/validation_report.txt`
- Renders: `output/renders/{front,back,left,right,top,bottom,persp}.png`

## Notes
- **Deviations from the references:** the references are AI-generated and
  mutually inconsistent; the reconstruction is a coherent interpretation.
  The LEGO studs / printed part lines are not reproduced as geometry (they are
  sub-millimetre at 100 mm and would not print); the blocky character is
  instead conveyed by flat feather blades, beveled body volumes and the correct
  silhouette. Feather tips are rounded rather than razor-sharp for print
  durability.
- **Assumptions:** no physical scale was given, so a 100 mm overall height was
  assumed (desktop-figurine scale). The tail is modelled curling to the
  character's left, matching the front and bottom views.
- **Single unified solid:** the wings, crest, tail and body are naturally
  connected, so they were unioned into one watertight shell (Option A) rather
  than left as separate parts. This gives the strongest, most printable result
  and needs no assembly.
- The mesh is a voxel-remeshed quad-dominant surface (~123 k verts); it is
  suitable for further editing (sculpting, decimation, re-meshing) if desired.
