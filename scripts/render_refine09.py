"""Flat-material underside test.

Every material is replaced by an unlit emission copy of its base colour, so the
render is pure colour with no shading - a seam or a pinched waist cannot hide
behind a highlight.  Used to find and then verify the pass-11 throat ramp.
"""
import bpy, os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output", "refinement09")
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
    ("flat_front",   'PERSP', Vector((0, -380, 50)),    Vector((0, -6, 52)), 0),
    ("flat_34",      'PERSP', Vector((-190, -330, 110)),Vector((0, -14, 52)), 0),
    ("flat_34b",     'PERSP', Vector((190, -330, 110)), Vector((0, -14, 52)), 0),
    ("flat_side",    'PERSP', Vector((-360, -60, 20)),  Vector((0, -16, 50)), 0),
    ("flat_low",     'PERSP', Vector((-140, -340, -30)),Vector((0, -16, 50)), 0),
    ("fz_throat",    'PERSP', Vector((-230, -130, 46)), Vector((0, -26, 46)), 0),
    ("fz_throat2",   'PERSP', Vector((230, -130, 46)),  Vector((0, -26, 46)), 0),
    ("fz_throat34",  'PERSP', Vector((-150, -250, 80)), Vector((0, -24, 48)), 0),
    ("fz_full34",    'PERSP', Vector((-190, -330, 110)),Vector((0, -14, 52)), 0),
    ("fz_front",     'PERSP', Vector((0, -380, 50)),    Vector((0, -6, 52)), 0),
]

# ---- flat-emission pass: pure colour, no shading -------------------------
flat = {}
for sl in ob.material_slots:
    m = sl.material
    base = None
    if m and m.use_nodes:
        bs = m.node_tree.nodes.get("Principled BSDF")
        if bs:
            base = tuple(bs.inputs["Base Color"].default_value)
    if base is None:
        base = (0.8, 0.8, 0.8, 1)
    fm = bpy.data.materials.new("FLAT_" + m.name)
    fm.use_nodes = True
    nt = fm.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = base
    out_node = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out_node.inputs[0])
    flat[m.name] = fm
old_mats = [sl.material for sl in ob.material_slots]
for sl in ob.material_slots:
    sl.material = flat[sl.material.name]
light_energy = [o.data.energy for o in lc.objects]
for o in lc.objects:
    o.data.energy = 0.0
w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.62, 0.64, 1)

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

for sl, m in zip(ob.material_slots, old_mats):
    sl.material = m
for o, e in zip(lc.objects, light_energy):
    o.data.energy = e
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.55, 0.57, 1)

print("REFINE09 RENDERS DONE")
