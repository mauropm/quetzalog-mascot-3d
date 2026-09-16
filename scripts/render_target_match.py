"""Render the model from the same 3/4 angle as image2.png (target design)."""
import bpy
import os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output")
CMP = os.path.join(OUT, "comparison")
os.makedirs(CMP, exist_ok=True)

sc = bpy.context.scene
ob = (bpy.data.objects.get("QUETZALOG_PRINT_READY") or
      bpy.data.objects.get("QUETZALOG_BODY"))
assert ob, "no model"
bb = [Vector(c) for c in ob.bound_box]
C = Vector((sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8,
            sum(v.z for v in bb) / 8))

sc.render.resolution_x = 942
sc.render.resolution_y = 789
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
w.node_tree.nodes["Background"].inputs[0].default_value = (0.16, 0.16, 0.17, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

lc = bpy.data.collections.get("LIGHTS") or bpy.data.collections.new("LIGHTS")
if lc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(lc)
for o in list(lc.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for nm, loc, e in (("Key", (-320, -330, 330), 3.0), ("Fill", (340, -240, 100), 1.1),
                   ("Rim", (40, 380, 240), 1.5)):
    ld = bpy.data.lights.new(nm, 'SUN')
    ld.energy = e
    ld.angle = 0.3
    o = bpy.data.objects.new(nm, ld)
    o.location = loc
    o.rotation_euler = (C - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(o)

cc = bpy.data.collections.get("CAMERAS") or bpy.data.collections.new("CAMERAS")
if cc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(cc)
for o in list(cc.objects):
    bpy.data.objects.remove(o, do_unlink=True)

d = Vector((-0.80, -0.72, 0.30)).normalized()
cd = bpy.data.cameras.new("C_tmatch")
cd.type = 'PERSP'
cd.lens = 85
cam = bpy.data.objects.new("C_tmatch", cd)
cam.location = C + d * 430.0
cam.rotation_euler = (C - cam.location).to_track_quat('-Z', 'Y').to_euler()
cc.objects.link(cam)
sc.camera = cam
sc.render.filepath = os.path.join(CMP, "target_match.png")
bpy.ops.render.render(write_still=True)
print("TARGET MATCH RENDER DONE")
