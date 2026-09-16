"""Diagnostic renders for the back feather-flow + snout jaw pass."""
import bpy, os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output", "refinement05")
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
    ("back",       'ORTHO', Vector((0, D, 50)),        Vector((0, 12, 50)), 150),
    ("top",        'ORTHO', Vector((0, 12, D + 60)),   Vector((0, 12, 50)), 155),
    ("rear34",     'PERSP', Vector((250, 320, 210)),   Vector((0, 12, 48)), 0),
    ("snout_side", 'ORTHO', Vector((-400, -25, 62)),   Vector((0, -25, 62)), 46),
    ("snout_34",   'PERSP', Vector((-150, -240, 120)), Vector((0, -22, 62)), 0),
    ("front",      'ORTHO', Vector((0, -D, 50)),       Vector((0, 12, 50)), 150),
]
for name, kind, loc, tgt, oscale in SHOTS:
    cd = bpy.data.cameras.new("C_" + name)
    cd.type = kind
    if kind == 'ORTHO':
        cd.ortho_scale = oscale
    else:
        cd.lens = 80
    cam = bpy.data.objects.new("C_" + name, cd)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)

print("REFINE05 RENDERS DONE")
