import bpy
import math
import os
from mathutils import Vector

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output")
RD = os.path.join(OUT, "renders")
os.makedirs(RD, exist_ok=True)

sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in \
    [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
sc.render.resolution_x = 720
sc.render.resolution_y = 720
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'
try:
    sc.eevee.taa_render_samples = 32
except Exception:
    pass

sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.view_settings.exposure = 0.0

world = bpy.data.worlds.new("W") if not bpy.data.worlds else bpy.data.worlds[0]
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.90, 0.92, 0.95, 1.0)
bg.inputs[1].default_value = 0.55

lights = bpy.data.collections.get("LIGHTS")
if lights is None:
    lights = bpy.data.collections.new("LIGHTS")
    bpy.context.scene.collection.children.link(lights)

def add_sun(name, direction_from, energy, angle=0.15):
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = energy
    ld.angle = angle
    ob = bpy.data.objects.new(name, ld)
    ob.location = Vector(direction_from)
    lights.objects.link(ob)
    ob.rotation_euler = (Vector((0, 6, 45)) - Vector(direction_from)).to_track_quat('-Z', 'Y').to_euler()
    return ob

for o in list(lights.objects):
    bpy.data.objects.remove(o, do_unlink=True)
add_sun("Key", (260, -320, 300), 3.2)
add_sun("Fill", (-340, -160, 90), 1.3)
add_sun("Rim", (40, 360, 220), 1.6)

cams = bpy.data.collections.get("CAMERAS")
if cams is None:
    cams = bpy.data.collections.new("CAMERAS")
    bpy.context.scene.collection.children.link(cams)

target = Vector((0, 6, 45))
specs = {
    "front": (Vector((0, -420, 45)), 150),
    "back": (Vector((0, 430, 45)), 150),
    "left": (Vector((420, 0, 45)), 150),
    "right": (Vector((-420, 0, 45)), 150),
    "top": (Vector((0, 6, 430)), 150),
    "bottom": (Vector((0, 6, -420)), 150),
    "persp": (Vector((250, -330, 230)), 170),
}

for name, (loc, oscale) in specs.items():
    cd = bpy.data.cameras.new("CAM_" + name)
    cd.type = 'ORTHO' if name != "persp" else 'PERSP'
    if cd.type == 'ORTHO':
        cd.ortho_scale = oscale
    else:
        cd.lens = 55
    cam = bpy.data.objects.new("CAM_" + name, cd)
    cam.location = loc
    cam.rotation_euler = (target - loc).to_track_quat('-Z', 'Y').to_euler()
    cams.objects.link(cam)
    sc.camera = cam
    sc.render.filepath = os.path.join(RD, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)

print("RENDER DONE")
