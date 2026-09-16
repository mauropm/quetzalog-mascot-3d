# Quetzalog reconstruction specification (2nd pass)

Derived by measuring the gridded references (`output/analysis/*_grid.png`).

Front view scale: mascot spans y 15..1120 px = 1105 px = 100 mm  ->  1 px = 0.09050 mm
Front origin: x0 = 700 px, y0 = 1120 px
    X = (x_px - 700) * 0.0905        Z = (1120 - y_px) * 0.0905
Top view is the same scale; image-up = +Y (back), so it gives depth.

## Landmarks (front view, mm)

| feature                 | px                    | mm                          |
|-------------------------|-----------------------|-----------------------------|
| crest top               | y 15                  | Z 100.0                     |
| head top (teal)         | y ~290                | Z 75.1                      |
| eye centre              | (595,455) (810,455)   | X -9.5 / +10.0, Z 60.2      |
| eye radius              | 85 px                 | 7.7                         |
| snout                   | x 620..790, y 480..600| X -7.2..+8.1, Z 47.1..57.9  |
| cream muzzle            | x 540..870, y 490..690| X -14.5..+15.4, Z 38.9..57.0|
| chin                    | y ~690                | Z 38.9                      |
| head width              | x 505..900            | X -17.6..+18.1              |
| body width              | x 510..890            | X -17.2..+17.2              |
| cream belly             | x 620..790, y 680..960| X -7.2..+8.1, Z 14.5..39.8  |
| front foot centres      | x 555, 845            | X -13.1, +13.1              |
| feet outer extent       | x 387..1032           | X -28.3..+30.0              |
| wing span               | x 50..1353            | X -58.8..+59.1              |
| wing vertical range     | y 370..720            | Z 36.2..67.9                |
| tail feathers (front)   | x 75..420, y 690..950 | X -56.5..-25.3, Z 15.4..38.9|
| red crest piece         | x 660..745, y 230..360| X -3.6..+4.1, Z 68.8..80.5  |

## Depth (top view)

| feature            | approx Y (mm) |
|--------------------|---------------|
| snout tip          | -25 .. -29    |
| eye centres        | ~ -14         |
| back of head       | ~ +13         |
| back of body       | ~ +18         |
| tail tip           | ~ +55 (curving +X) |

## Ratios

    head width  / body width   = 36 / 34.4 = 1.05
    head height / total height = 34 / 100  = 0.34
    body width  / total height = 34.4/100  = 0.34
    leg length  / body height  = 14 / 34   = 0.41
    wing span   / body width   = 118 / 34.4 = 3.4
    foot width  / body width   = 13.6 / 34.4 = 0.40

## Reference inconsistencies (documented)

* The **tail** appears on the image-left in the front *and* back views, which is
  geometrically impossible for a single object (front/back are mirrored).
  The top and bottom views both put the tail toward **+X (character's left)**,
  so the model uses +X; the front view is therefore mirrored relative to the
  model. 3 of 4 views agree.
* `left`/`right` are 3/4 perspective renders, not true orthographic side views;
  they are used qualitatively (crest sweep, tail depth) only.
* Crest colours vary per leaf in no strict pattern; a repeating rainbow
  sequence is used.

## Component classification (pass-1 model -> pass 2)

    Body      REFINE (re-lofted from measured cross sections)
    Head      REBUILD (measured helmet/snout/cheek volumes)
    Crest     REBUILD (uniform layered leaf rosette, not a chaotic ball)
    Wings     REBUILD (green arm + ordered primary/covert rows)
    Tail      REBUILD (Catmull-Rom core + radial leaf rings)
    Legs/feet REBUILD (measured positions, splayed rear feet)
    Eyes      REFINE (measured centres/radii, layered spheres)
    Belly     REBUILD (raised cream panel)
