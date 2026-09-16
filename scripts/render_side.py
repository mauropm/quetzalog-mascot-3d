import bpy, os
from mathutils import Vector
PROJ="/Users/mauro/Documents/Code/3D-Quetzalog"; CMP=os.path.join(PROJ,"output","comparison")
sc=bpy.context.scene
ob=bpy.data.objects.get("QUETZALOG_PRINT_READY") or bpy.data.objects.get("QUETZALOG_BODY")
bb=[Vector(c) for c in ob.bound_box]
C=Vector((sum(v.x for v in bb)/8,sum(v.y for v in bb)/8,sum(v.z for v in bb)/8))
sc.render.resolution_x=1375; sc.render.resolution_y=1144; sc.render.film_transparent=True
sc.view_settings.view_transform='Standard'
try:
    sc.render.engine='BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples=32
except Exception: sc.render.engine='BLENDER_EEVEE'
w=bpy.data.worlds.get("CMPW") or bpy.data.worlds.new("CMPW"); sc.world=w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(1,1,1,1)
w.node_tree.nodes["Background"].inputs[1].default_value=0.9
cc=bpy.data.collections.get("CAMERAS") or bpy.data.collections.new("CAMERAS")
if cc.name not in [c.name for c in sc.collection.children]: sc.collection.children.link(cc)
span=max(bb[i][k] for i in range(8) for k in (1,2)) - min(bb[i][k] for i in range(8) for k in (1,2))
for name, loc in (("sideR", Vector((-700, C.y, C.z))), ("sideL", Vector((700, C.y, C.z))),
                  ("frontO", Vector((0,-700,C.z)))):
    cd=bpy.data.cameras.new("C_"+name); cd.type='ORTHO'; cd.ortho_scale=150.0
    cam=bpy.data.objects.new("C_"+name, cd); cam.location=loc
    cam.rotation_euler=(C-loc).to_track_quat('-Z','Y').to_euler()
    cc.objects.link(cam); sc.camera=cam
    sc.render.filepath=os.path.join(CMP,"v5_%s.png"%name)
    bpy.ops.render.render(write_still=True)
    cc.objects.unlink(cam); bpy.data.objects.remove(cam, do_unlink=True)
print("SIDE RENDERS DONE")
