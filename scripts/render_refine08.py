"""Underside-continuity validation renders: 7 angles + head/neck/chest close-ups."""
import bpy, os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output", "refinement08")
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
ob = (bpy.data.objects.get("QUETZALOG_PRINT_READY") or
      bpy.data.objects.get("QUETZALOG_BODY"))
assert ob, "no model"

sc.render.resolution_x = 900
sc.render.resolution_y = 900
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 64
except Exception:
    sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'

w = bpy.data.worlds.get("CMPW") or bpy.data.worlds.new("CMPW")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.57, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

lc = bpy.data.collections.get("LIGHTS") or bpy.data.collections.new("LIGHTS")
if lc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(lc)
for o in list(lc.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for nm, loc, e in (("Key", (220, -300, 300), 3.2), ("Fill", (-320, -180, 80), 1.3),
                   ("Rim", (40, 320, 220), 1.5)):
    ld = bpy.data.lights.new(nm, 'SUN')
    ld.energy = e
    ld.angle = 0.25
    o = bpy.data.objects.new(nm, ld)
    o.location = loc
    o.rotation_euler = (Vector((0, 12, 50)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(o)

cc = bpy.data.collections.get("CAMERAS") or bpy.data.collections.new("CAMERAS")
if cc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(cc)
for o in list(cc.objects):
    bpy.data.objects.remove(o, do_unlink=True)

D = 460
SHOTS = [
    ("front",         'ORTHO', Vector((0, -D, 50)),       Vector((0, 12, 50)), 150),
    ("rear",          'ORTHO', Vector((0, D, 50)),        Vector((0, 12, 50)), 150),
    ("left_side",     'ORTHO', Vector((-D, 12, 50)),      Vector((0, 12, 50)), 150),
    ("right_side",    'ORTHO', Vector((D, 12, 50)),       Vector((0, 12, 50)), 150),
    ("top",           'ORTHO', Vector((0, 12, D)),        Vector((0, 12, 50)), 150),
    ("front_3quarter", 'PERSP', Vector((-300, -330, 200)), Vector((0, 8, 48)), 0),
    ("rear_3quarter",  'PERSP', Vector((300, 330, 200)),   Vector((0, 12, 48)), 0),
    ("left_3quarter",  'PERSP', Vector((-300, -180, 180)), Vector((0, -6, 52)), 0),
    ("right_3quarter", 'PERSP', Vector((300, -180, 180)),  Vector((0, -6, 52)), 0),
    ("head_neck_chest",       'PERSP', Vector((-190, -330, 110)), Vector((0, -14, 52)), 0),
    ("head_neck_chest_front", 'ORTHO', Vector((0, -400, 55)),     Vector((0, 0, 55)), 95),
]
for name, kind, loc, tgt, oscale in SHOTS:
    cd = bpy.data.cameras.new("C_" + name)
    cd.type = kind
    if kind == 'ORTHO':
        cd.ortho_scale = oscale
    else:
        cd.lens = 85
    cam = bpy.data.objects.new("C_" + name, cd)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)

# ---- clay pass: geometry only, for the tail/back join -----------------------
sil = bpy.data.materials.new("CLAY7")
sil.use_nodes = True
b = sil.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.70, 0.70, 0.70, 1)
b.inputs["Roughness"].default_value = 0.8
old = [sl.material for sl in ob.material_slots]
for sl in ob.material_slots:
    sl.material = sil
save = [o.data.energy for o in lc.objects]
for o in lc.objects:
    o.data.energy *= 0.45
w.node_tree.nodes["Background"].inputs[0].default_value = (0.28, 0.28, 0.30, 1)
CLAY = [
    ("clay_rear",    'PERSP', Vector((150, 330, 90)),  Vector((0, 18, 34)), 0),
    ("clay_side",    'ORTHO', Vector((-D, 12, 50)),    Vector((0, 12, 50)), 150),
    ("clay_top",     'ORTHO', Vector((0, 12, D)),      Vector((0, 12, 50)), 150),
    ("clay_join",    'PERSP', Vector((230, 300, 130)), Vector((0, 16, 40)), 0),
    ("clay_neck",    'ORTHO', Vector((-D, 0, 50)),     Vector((0, 0, 50)), 130),
]
for name, kind, loc, tgt, oscale in CLAY:
    cd = bpy.data.cameras.new("K_" + name)
    cd.type = kind
    if kind == 'ORTHO':
        cd.ortho_scale = oscale
    else:
        cd.lens = 85
    cam = bpy.data.objects.new("K_" + name, cd)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)
for o, e in zip(lc.objects, save):
    o.data.energy = e
for sl, m in zip(ob.material_slots, old):
    sl.material = m
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.57, 1)

print("REFINE08 RENDERS DONE")
