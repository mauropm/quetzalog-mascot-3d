"""Perspective coherence test renders (spec section 26)."""
import bpy
import os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output")
REN = os.path.join(OUT, "renders")
os.makedirs(REN, exist_ok=True)

sc = bpy.context.scene
ob = (bpy.data.objects.get("QUETZALOG_PRINT_READY") or
      bpy.data.objects.get("QUETZALOG_BODY"))
assert ob, "no model"
bb = [Vector(c) for c in ob.bound_box]
C = Vector((sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8,
            sum(v.z for v in bb) / 8))

sc.render.resolution_x = 1100
sc.render.resolution_y = 1100
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.film_transparent = False
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 48
except Exception:
    sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'

w = bpy.data.worlds.get("CMPW") or bpy.data.worlds.new("CMPW")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.97, 0.97, 0.98, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

lc = bpy.data.collections.get("LIGHTS") or bpy.data.collections.new("LIGHTS")
if lc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(lc)
for o in list(lc.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for nm, loc, e in (("Key", (300, -380, 340), 3.0), ("Fill", (-380, -200, 120), 1.2),
                   ("Rim", (60, 400, 260), 1.6), ("Up", (0, -40, -400), 0.7)):
    ld = bpy.data.lights.new(nm, 'SUN')
    ld.energy = e
    ld.angle = 0.25
    o = bpy.data.objects.new(nm, ld)
    o.location = loc
    o.rotation_euler = (C - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(o)

cc = bpy.data.collections.get("CAMERAS") or bpy.data.collections.new("CAMERAS")
if cc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(cc)
for o in list(cc.objects):
    bpy.data.objects.remove(o, do_unlink=True)

D = 430.0
VIEWS = {
    "persp_front34": Vector((0.72, -1.0, 0.42)),
    "persp_back34": Vector((-0.66, 1.0, 0.46)),
    "persp_high34": Vector((0.85, -0.85, 1.15)),
    "persp_low34": Vector((0.90, -0.90, -0.42)),
}
for name, d in VIEWS.items():
    d = d.normalized()
    cd = bpy.data.cameras.new("C_" + name)
    cd.type = 'PERSP'
    cd.lens = 80
    cam = bpy.data.objects.new("C_" + name, cd)
    cam.location = C + d * D
    cam.rotation_euler = (C - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(REN, name + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)

print("PERSPECTIVE RENDERS DONE")
