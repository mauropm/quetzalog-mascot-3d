"""Head/neck silhouette check: true ortho side views + 3/4 views.

Run headless:
    /Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/render_headneck.py -- <tag>

Writes to output/<tag>/ .  Also dumps the x=0 cross-section profile (frontmost y
per z) and a filled cross-section PNG, because the side silhouette is the thing
this pass is about and a render is harder to measure than a plot.
"""
import bpy
import os
import sys
import numpy as np
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
TAG = "refinement11"
if "--" in sys.argv:
    rest = sys.argv[sys.argv.index("--") + 1:]
    if rest:
        TAG = rest[0]
OUT = os.path.join(PROJ, "output", TAG)
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
sc.render.resolution_x = 1000
sc.render.resolution_y = 1000
sc.render.image_settings.file_format = 'PNG'
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 64
except Exception:
    sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'

w = bpy.data.worlds.new("WH")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.57, 1)

lc = bpy.data.collections.new("LH")
sc.collection.children.link(lc)
for nm, loc, e in (("K", (220, -300, 300), 3.2), ("F", (-320, -180, 80), 1.3),
                   ("R", (40, 320, 220), 1.5)):
    ld = bpy.data.lights.new(nm, 'SUN')
    ld.energy = e
    ld.angle = 0.25
    o = bpy.data.objects.new(nm, ld)
    o.location = loc
    o.rotation_euler = (Vector((0, 12, 50)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(o)

cc = bpy.data.collections.new("CH")
sc.collection.children.link(cc)
ob = bpy.data.objects.get("QUETZALOG_PRINT_READY") or bpy.data.objects["QUETZALOG_BODY"]

VIEWS = [
    ("side_L",   (-420.0, 0.0, 50.0),  (0.0, 0.0, 50.0), 120.0),
    ("side_R",   (420.0, 0.0, 50.0),   (0.0, 0.0, 50.0), 120.0),
    ("q34_L",    (-300.0, -300.0, 180.0), (0.0, 0.0, 52.0), 130.0),
    ("q34_R",    (300.0, -300.0, 180.0),  (0.0, 0.0, 52.0), 130.0),
    ("q34_low",  (-260.0, -300.0, -60.0), (0.0, 0.0, 46.0), 130.0),
    ("head",     (-230.0, -300.0, 120.0), (0.0, -18.0, 60.0), 74.0),
]
for nm, loc, tgt, osc in VIEWS:
    cd = bpy.data.cameras.new(nm)
    cd.type = 'ORTHO'
    cd.ortho_scale = osc
    cam = bpy.data.objects.new(nm, cd)
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, nm + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)

# ---- x=0 cross-section: frontmost y per z, and a filled plot --------------
dg = bpy.context.evaluated_depsgraph_get()
S = 4.0
ymin, ymax, zmin, zmax = -70.0, 70.0, 0.0, 102.0
W = int((ymax - ymin) * S)
H = int((zmax - zmin) * S)
g = np.zeros((H, W), dtype=bool)
for j in range(W):
    y = ymin + (j + 0.5) / S
    for i in range(H):
        z = zmin + (i + 0.5) / S
        ok, _, _, _ = ob.ray_cast(Vector((-80.0, y, z)), Vector((1, 0, 0)),
                                  distance=200.0, depsgraph=dg)
        if ok:
            g[i, j] = True

print("x=0 cross-section, frontmost y per z  (front = -Y)")
for zi in range(8, 70, 2):
    row = g[int((zi - zmin) * S)]
    idx = np.where(row)[0]
    if len(idx):
        print(f"  z={zi:3d}   front y = {idx.min()/S + ymin:7.2f}")

img = np.zeros((H, W, 4), dtype=np.float32)
img[..., 3] = 1.0
img[..., 0] = 0.13
img[..., 1] = 0.13
img[..., 2] = 0.16
img[g, 0] = 0.47
img[g, 1] = 0.92
img[g, 2] = 0.86
for mm in range(-70, 71, 10):
    X = int((mm + 70) * S)
    if 0 <= X < W:
        img[:, X, :3] = 0.30
for mm in range(0, 103, 10):
    Y = int(mm * S)
    if 0 <= Y < H:
        img[Y, :, :3] = 0.30
bi = bpy.data.images.new("sec", W, H, alpha=True)
bi.pixels.foreach_set(img.reshape(-1))
bi.filepath_raw = os.path.join(OUT, "section_x0.png")
bi.file_format = 'PNG'
bi.save()
print("wrote", OUT)
