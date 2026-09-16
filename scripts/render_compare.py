"""Render the model in the exact framing of the reference images and build
reference | model | overlay comparison sheets."""
import bpy
import os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output")
CMP = os.path.join(OUT, "comparison")
os.makedirs(CMP, exist_ok=True)

RW, RH = 1375, 1144
REF_H_PX = 1105.0
ORTHO = (100.0 * RH / REF_H_PX) * (RW / RH)

ob = (bpy.data.objects.get("QUETZALOG_BODY") or
      bpy.data.objects.get("QUETZALOG_PRINT_READY"))
assert ob, "no model"
bb = [Vector(c) for c in ob.bound_box]
BC = Vector((sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8,
             sum(v.z for v in bb) / 8))
print("model bbox centre:", tuple(round(v, 2) for v in BC))

sc = bpy.context.scene
sc.render.resolution_x = RW
sc.render.resolution_y = RH
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.film_transparent = True
try:
    sc.render.engine = 'BLENDER_EEVEE_NEXT'
    sc.eevee.taa_render_samples = 32
except Exception:
    sc.render.engine = 'BLENDER_EEVEE'
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'

w = bpy.data.worlds.get("CMPW") or bpy.data.worlds.new("CMPW")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.85

lc = bpy.data.collections.get("LIGHTS") or bpy.data.collections.new("LIGHTS")
if lc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(lc)
for o in list(lc.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for nm, loc, e in (("K", (260, -320, 300), 2.6), ("F", (-340, -160, 90), 1.1),
                   ("R", (40, 360, 220), 1.3), ("B", (0, 0, -400), 0.8)):
    ld = bpy.data.lights.new(nm, 'SUN')
    ld.energy = e
    ld.angle = 0.3
    o = bpy.data.objects.new(nm, ld)
    o.location = loc
    o.rotation_euler = (BC - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    lc.objects.link(o)

cc = bpy.data.collections.get("CAMERAS") or bpy.data.collections.new("CAMERAS")
if cc.name not in [c.name for c in sc.collection.children]:
    sc.collection.children.link(cc)
for o in list(cc.objects):
    bpy.data.objects.remove(o, do_unlink=True)

VIEWS = {
    "front": Vector((BC.x, -600, BC.z)),
    "back": Vector((BC.x, 600, BC.z)),
    "left": Vector((600, BC.y, BC.z)),
    "right": Vector((-600, BC.y, BC.z)),
    "top": Vector((BC.x, BC.y, 600)),
    "bottom": Vector((BC.x, BC.y, -600)),
}

clay = bpy.data.materials.get("CLAY") or bpy.data.materials.new("CLAY")
clay.use_nodes = True
bs = clay.node_tree.nodes.get("Principled BSDF")
bs.inputs["Base Color"].default_value = (0.55, 0.55, 0.56, 1)
bs.inputs["Roughness"].default_value = 0.7


def render_set(tag, use_clay):
    orig = None
    if use_clay:
        orig = [m for m in ob.data.materials]
        for i in range(len(ob.data.materials)):
            ob.data.materials[i] = clay
    for name, loc in VIEWS.items():
        cd = bpy.data.cameras.new("C_%s_%s" % (name, tag))
        cd.type = 'ORTHO'
        cd.ortho_scale = ORTHO
        cam = bpy.data.objects.new("C_%s_%s" % (name, tag), cd)
        cam.location = loc
        cam.rotation_euler = (BC - loc).to_track_quat('-Z', 'Y').to_euler()
        cc.objects.link(cam)
        sc.camera = cam
        sc.render.filepath = os.path.join(CMP, "%s_%s.png" % (tag, name))
        bpy.ops.render.render(write_still=True)
        cc.objects.unlink(cam)
        bpy.data.objects.remove(cam, do_unlink=True)
    if use_clay:
        for i, m in enumerate(orig):
            ob.data.materials[i] = m


render_set("clay", True)
render_set("model", False)

cd = bpy.data.cameras.new("C_persp")
cd.type = 'PERSP'
cd.lens = 70
cam = bpy.data.objects.new("C_persp", cd)
cam.location = Vector((BC.x + 230, BC.y - 300, 210))
cam.rotation_euler = (BC - cam.location).to_track_quat('-Z', 'Y').to_euler()
cc.objects.link(cam)
sc.camera = cam
sc.render.filepath = os.path.join(OUT, "renders", "persp.png")
bpy.ops.render.render(write_still=True)

print("COMPARE RENDER DONE")

# head close-up (clay + material)
for _tag, _clay in (("head_clay", True), ("head_front", False)):
    if _clay:
        _o = [m for m in ob.data.materials]
        for i in range(len(ob.data.materials)):
            ob.data.materials[i] = clay
    cd = bpy.data.cameras.new("C_" + _tag)
    cd.type = 'ORTHO'
    cd.ortho_scale = 54
    cam = bpy.data.objects.new("C_" + _tag, cd)
    cam.location = Vector((0, -400, 61))
    cam.rotation_euler = (Vector((0, 0, 61)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cc.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(CMP, _tag + ".png")
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam)
    bpy.data.objects.remove(cam, do_unlink=True)
    if _clay:
        for i, m in enumerate(_o):
            ob.data.materials[i] = m
print("HEAD CLOSEUPS DONE")
