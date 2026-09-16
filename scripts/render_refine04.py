"""Close-up + clay diagnostic renders for the soft-anatomy refinement pass."""
import bpy, os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output", "refinement04")
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
    o.rotation_euler = (Vector((0, 10, 50)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(o)

cc = bpy.data.collections.get("CAMERAS") or bpy.data.collections.new("CAMERAS")
if cc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(cc)
for o in list(cc.objects):
    bpy.data.objects.remove(o, do_unlink=True)

SHOTS = [
    ("head_side",     'ORTHO', Vector((-400, -10, 68)),  Vector((0, -10, 68)), 62),
    ("head_3quarter", 'PERSP', Vector((-190, -260, 120)), Vector((0, -14, 66)), 0),
    ("neck_front",    'ORTHO', Vector((0, -400, 45)),    Vector((0, 10, 45)), 70),
    ("body_front",    'ORTHO', Vector((0, -400, 45)),    Vector((0, 10, 45)), 150),
    ("body_3quarter", 'PERSP', Vector((-300, -330, 200)), Vector((0, 8, 48)), 0),
    ("body_side",     'ORTHO', Vector((-400, 15, 48)),   Vector((0, 15, 48)), 150),
]

def render(name, kind, loc, tgt, oscale):
    cd = bpy.data.cameras.new("C_" + name)
    cd.type = kind
    if kind == 'ORTHO':
        cd.ortho_scale = oscale
    else:
        cd.lens = 70
    cam = bpy.data.objects.new("C_" + name, cd)
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)

for spec in SHOTS:
    render(*spec)

# ---- clay pass: single neutral material over every slot ---------------------
clay = bpy.data.materials.new("CLAY")
clay.use_nodes = True
bsdf = clay.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.62, 0.62, 0.63, 1)
bsdf.inputs["Roughness"].default_value = 0.42
old = [s.material for s in ob.material_slots]
for s in ob.material_slots:
    s.material = clay
for spec in SHOTS:
    name = "clay_" + spec[0]
    render(name, spec[1], spec[2], spec[3], spec[4])
for s, m in zip(ob.material_slots, old):
    s.material = m

print("REFINE04 RENDERS DONE")
