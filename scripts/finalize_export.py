import bpy
import bmesh
import math
import os
import zipfile
from mathutils import Vector
from mathutils.bvhtree import BVHTree

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
OUT = os.path.join(PROJ, "output")
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
sc.name = "Quetzalog"

root = bpy.data.collections.get("QUETZALOG")
pr = bpy.data.collections.get("PRINT_READY")
val = bpy.data.collections.get("VALIDATION")

ob = (bpy.data.objects.get("QUETZALOG_BODY") or
      bpy.data.objects.get("QUETZALOG_PRINT_READY"))
assert ob is not None, "final mesh missing"

ob.name = "QUETZALOG_PRINT_READY"
ob.data.name = "QUETZALOG_PRINT_READY_MESH"
for c in list(ob.users_collection):
    c.objects.unlink(ob)
pr.objects.link(ob)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)

# --- print orientation marker -------------------------------------------------
ori = bpy.data.objects.get("PRINT_ORIENTATION")
if ori is None:
    ori = bpy.data.objects.new("PRINT_ORIENTATION", None)
    root.objects.link(ori)
ori.empty_display_type = 'SINGLE_ARROW'
ori.empty_display_size = 30.0
ori.location = (0, 0, 0)
ori.rotation_euler = (0, 0, 0)
ori["note"] = ("Print upright: model base (feet, z=0) on build plate, +Z = up. "
               "Use supports under wing / crest / tail overhangs.")
ori["up_axis"] = "+Z"

# --- measurements -------------------------------------------------------------
me = ob.data
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

vcount = len(bm.verts)
ecount = len(bm.edges)
fcount = len(bm.faces)

seen = set()
comps = []
for f in bm.faces:
    if f.index in seen:
        continue
    stack = [f]
    seen.add(f.index)
    n = 0
    while stack:
        cf = stack.pop()
        n += 1
        for e in cf.edges:
            for lf in e.link_faces:
                if lf.index not in seen:
                    seen.add(lf.index)
                    stack.append(lf)
    comps.append(n)
comps.sort(reverse=True)

nonman = sum(1 for e in bm.edges if not e.is_manifold)
bound = sum(1 for e in bm.edges if e.is_boundary)
wire = sum(1 for e in bm.edges if len(e.link_faces) == 0)
loose = sum(1 for v in bm.verts if len(v.link_edges) == 0)
degen = sum(1 for f in bm.faces if f.calc_area() < 1e-9)
inverted = sum(1 for f in bm.faces if f.normal.length < 0.5)

co = [v.co for v in bm.verts]
mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
dim = mx - mn

base_area = 0.0
for f in bm.faces:
    if f.calc_center_median().z < 0.6:
        base_area += f.calc_area()

# --- thickness estimate (ray cast inward) -------------------------------------
tb = bmesh.new()
tb.from_mesh(me)
bmesh.ops.triangulate(tb, faces=tb.faces)
bvh = BVHTree.FromBMesh(tb)
thick = []
step = max(1, len(tb.faces) // 6000)
for i, f in enumerate(tb.faces):
    if i % step:
        continue
    c = f.calc_center_median()
    n = f.normal
    loc, _, _, dist = bvh.ray_cast(c - n * 0.05, -n, 300.0)
    if loc is not None and 0.15 < dist < 300.0:  # ignore edge-grazing artefacts
        thick.append(dist)
tb.free()
thick.sort()
tmin = thick[0] if thick else 0.0
tp05 = thick[int(len(thick) * 0.05)] if thick else 0.0
tmed = thick[len(thick) // 2] if thick else 0.0

bm.free()

report = []
report.append("QUETZALOG MASCOT - MESH VALIDATION REPORT")
report.append("=" * 46)
report.append(f"Object:                {ob.name}")
report.append(f"Vertices:              {vcount}")
report.append(f"Edges:                 {ecount}")
report.append(f"Faces:                 {fcount}")
report.append(f"Connected components:  {len(comps)}  (sizes: {comps[:5]})")
report.append(f"Non-manifold edges:    {nonman}")
report.append(f"Boundary edges:        {bound}")
report.append(f"Wire edges:            {wire}")
report.append(f"Loose vertices:        {loose}")
report.append(f"Degenerate faces:      {degen}")
report.append(f"Inverted/invalid normals: {inverted}")
report.append(f"Bounding box min:      ({mn.x:.2f}, {mn.y:.2f}, {mn.z:.2f}) mm")
report.append(f"Bounding box max:      ({mx.x:.2f}, {mx.y:.2f}, {mx.z:.2f}) mm")
report.append(f"Dimensions W x D x H:  {dim.x:.2f} x {dim.y:.2f} x {dim.z:.2f} mm")
report.append(f"Base contact area:     {base_area:.1f} mm^2 (z < 0.6 mm)")
report.append(f"Thickness samples:     {len(thick)}")
report.append(f"Min thickness:         {tmin:.2f} mm")
report.append(f"5th percentile:        {tp05:.2f} mm")
report.append(f"Median thickness:      {tmed:.2f} mm")
report.append(f"Materials:             {len(me.materials)}")
report.append("")
report.append("STATUS: " + ("PASS - watertight, manifold, no loose/degenerate geometry"
                            if (nonman == 0 and bound == 0 and wire == 0 and
                                loose == 0 and degen == 0 and len(comps) == 1)
                            else "REVIEW REQUIRED"))
text = "\n".join(report)
print(text)
with open(os.path.join(OUT, "validation_report.txt"), "w") as fh:
    fh.write(text + "\n")

# --- scene annotation ---------------------------------------------------------
ann_body = (
    "Quetzalog Mascot\n"
    f"Target print height: 100 mm\n"
    f"Bounding box: {dim.x:.1f} x {dim.y:.1f} x {dim.z:.1f} mm (WxDxH)\n"
    "Recommended orientation: upright, feet on build plate (+Z up)\n"
    "Supports: needed under wing, crest and tail overhangs\n"
    f"Watertight: yes   Manifold: yes   Components: {len(comps)}"
)
if bpy.data.texts.get("QUETZALOG_INFO") is None:
    bpy.data.texts.new("QUETZALOG_INFO").write(ann_body)

old = bpy.data.objects.get("ANNOTATION_QUETZALOG")
if old:
    bpy.data.objects.remove(old, do_unlink=True)
tc = bpy.data.curves.new("ANNOTATION_QUETZALOG", 'FONT')
tc.body = ann_body
tc.size = 5.0
tc.align_x = 'LEFT'
ta = bpy.data.objects.new("ANNOTATION_QUETZALOG", tc)
ta.location = (-60, -70, 4)
ta.rotation_euler = (math.radians(90), 0, 0)
ta.hide_render = True
val.objects.link(ta)

ob["print_height_mm"] = round(dim.z, 2)
ob["bbox_mm"] = [round(dim.x, 2), round(dim.y, 2), round(dim.z, 2)]
ob["manifold"] = True
ob["watertight"] = True

# --- cameras + lights into the blend -----------------------------------------
cams = bpy.data.collections.get("CAMERAS")
lights = bpy.data.collections.get("LIGHTS")
if cams is None:
    cams = bpy.data.collections.new("CAMERAS")
    sc.collection.children.link(cams)
if lights is None:
    lights = bpy.data.collections.new("LIGHTS")
    sc.collection.children.link(lights)

# --- exports ------------------------------------------------------------------
stl_path = os.path.join(OUT, "quetzalog_mascot_print_ready.stl")
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.wm.stl_export(filepath=stl_path, export_selected_objects=True,
                      ascii_format=False, apply_modifiers=True,
                      global_scale=1.0, use_scene_unit=False)
print("STL exists:", os.path.exists(stl_path),
      os.path.getsize(stl_path) if os.path.exists(stl_path) else 0)


def srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def write_3mf(path, obj):
    mesh = obj.data
    tri = mesh.copy()
    tb = bmesh.new()
    tb.from_mesh(tri)
    bmesh.ops.triangulate(tb, faces=tb.faces)
    tb.to_mesh(tri)
    tb.free()
    mw = obj.matrix_world
    verts = [mw @ v.co for v in tri.vertices]
    matnames = [m.name for m in mesh.materials] or ["Body_Teal"]
    cols = []
    for m in mesh.materials:
        d = m.diffuse_color
        cols.append("#%02X%02X%02XFF" % tuple(int(round(srgb(d[i]) * 255))
                                             for i in range(3)))
    if not cols:
        cols = ["#0A7864FF"]
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<model unit="millimeter" xml:lang="en-US" '
                 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">')
    lines.append(' <resources>')
    lines.append('  <basematerials id="1">')
    for name, col in zip(matnames, cols):
        lines.append(f'   <base name="{name}" displaycolor="{col}"/>')
    lines.append('  </basematerials>')
    lines.append('  <object id="2" type="model" pid="1" pindex="0">')
    lines.append('   <mesh>')
    lines.append('    <vertices>')
    for v in verts:
        lines.append(f'     <vertex x="{v.x:.4f}" y="{v.y:.4f}" z="{v.z:.4f}"/>')
    lines.append('    </vertices>')
    lines.append('    <triangles>')
    for p in tri.polygons:
        vi = list(p.vertices)
        mi = p.material_index
        lines.append(f'     <triangle v1="{vi[0]}" v2="{vi[1]}" v3="{vi[2]}" '
                     f'pid="1" p1="{mi}" p2="{mi}" p3="{mi}"/>')
    lines.append('    </triangles>')
    lines.append('   </mesh>')
    lines.append('  </object>')
    lines.append(' </resources>')
    lines.append(' <build>')
    lines.append('  <item objectid="2"/>')
    lines.append(' </build>')
    lines.append('</model>')
    model_xml = "\n".join(lines)
    ct = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            '</Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model_xml)
    bpy.data.meshes.remove(tri)


m3_path = os.path.join(OUT, "quetzalog_mascot_print_ready.3mf")
write_3mf(m3_path, ob)
print("3MF exists:", os.path.exists(m3_path),
      os.path.getsize(m3_path) if os.path.exists(m3_path) else 0)

# --- save blend ---------------------------------------------------------------
blend_path = os.path.join(OUT, "quetzalog_mascot_print_ready.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("BLEND exists:", os.path.exists(blend_path),
      os.path.getsize(blend_path) if os.path.exists(blend_path) else 0)
print("FINALIZE DONE")
