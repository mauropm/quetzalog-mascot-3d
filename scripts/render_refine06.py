"""Diagnostics for the nose/snout/limb/nail pass.  Also emits a silhouette."""
import bpy, os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output", "refinement06")
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
    ("front",              'ORTHO', Vector((0, -D, 50)),        Vector((0, 12, 50)), 150),
    ("side",               'ORTHO', Vector((-D, 12, 50)),       Vector((0, 12, 50)), 150),
    ("back",               'ORTHO', Vector((0, D, 50)),         Vector((0, 12, 50)), 150),
    ("front_3quarter",     'PERSP', Vector((-300, -330, 200)),  Vector((0, 8, 48)), 0),
    ("back_3quarter",      'PERSP', Vector((280, 330, 210)),    Vector((0, 12, 48)), 0),
    ("hands_feet_closeup", 'PERSP', Vector((-210, -250, 130)),  Vector((8, -10, 8)), 0),
    ("snout_closeup",      'PERSP', Vector((-190, -250, 95)),   Vector((0, -34, 60)), 0),
]
for name, kind, loc, tgt, oscale in SHOTS:
    cd = bpy.data.cameras.new("C_" + name)
    cd.type = kind
    if kind == 'ORTHO':
        cd.ortho_scale = oscale
    else:
        cd.lens = 90
    cam = bpy.data.objects.new("C_" + name, cd)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)

SIL = [s for s in SHOTS if s[0] in ("front", "side", "back")]

# ---- flat black silhouette (limb readability test) --------------------------
sil = bpy.data.materials.new("SIL")
sil.use_nodes = True
nt = sil.node_tree
for n in list(nt.nodes):
    if n.type != 'OUTPUT_MATERIAL':
        nt.nodes.remove(n)
em = nt.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (0, 0, 0, 1)
em.inputs[1].default_value = 0.0
nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs[0])
old = [sl.material for sl in ob.material_slots]
for sl in ob.material_slots:
    sl.material = sil
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
for name, kind, loc, tgt, oscale in SIL:
    cd = bpy.data.cameras.new("S_" + name)
    cd.type = kind
    cd.ortho_scale = oscale
    cam = bpy.data.objects.new("S_" + name, cd)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, "silhouette_" + name + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)
for sl, m in zip(ob.material_slots, old):
    sl.material = m
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.57, 1)

print("REFINE06 RENDERS DONE")
