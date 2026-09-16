"""Quetzalog mascot - procedural reconstruction from orthographic references.

Coordinate system:  Z up, character FRONT faces -Y, +X = character's right.
Units: 1 Blender unit = 1 millimetre.  Ground plane at z = 0.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
VIEWS = os.path.join(PROJ, "views")
OUT = os.path.join(PROJ, "output")
os.makedirs(OUT, exist_ok=True)

VOXEL = 0.75
TARGET_H = 100.0
D2R = math.radians


# ----------------------------------------------------------------------------
# scene / collection helpers
# ----------------------------------------------------------------------------

def clear_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                  bpy.data.cameras, bpy.data.lights):
        for b in list(block):
            block.remove(b)


def get_col(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    holder = parent if parent is not None else bpy.context.scene.collection
    if col.name not in [c.name for c in holder.children]:
        holder.children.link(col)
    return col


def to_col(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    return ob


# ----------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------

MAT_DEFS = {
    "Body_Teal":  (0.030, 0.470, 0.390),
    "Cream":      (0.850, 0.730, 0.520),
    "Red":        (0.740, 0.080, 0.060),
    "Orange":     (0.880, 0.330, 0.030),
    "Yellow":     (0.930, 0.680, 0.060),
    "Green":      (0.170, 0.560, 0.110),
    "Blue":       (0.060, 0.330, 0.720),
    "Purple":     (0.360, 0.160, 0.560),
    "Eye_White":  (0.930, 0.930, 0.930),
    "Eye_Iris":   (0.050, 0.300, 0.600),
    "Eye_Pupil":  (0.015, 0.015, 0.020),
}
MATS = {}


def build_materials():
    for name, rgb in MAT_DEFS.items():
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.25
        m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
        MATS[name] = m


# ----------------------------------------------------------------------------
# region registry for material assignment after remesh
# ----------------------------------------------------------------------------
REG = []


def reg(prio, mat, test):
    REG.append((prio, mat, test))


def t_ellip(c, s):
    c = Vector(c); s = Vector(s)
    return lambda p: (((p - c).x / s.x) ** 2 + ((p - c).y / s.y) ** 2 +
                      ((p - c).z / s.z) ** 2) <= 1.0


def t_capsule(a, b, r):
    a = Vector(a); b = Vector(b)
    ab = b - a
    L2 = ab.length_squared or 1e-9
    def f(p):
        t = max(0.0, min(1.0, (p - a).dot(ab) / L2))
        return (p - (a + ab * t)).length <= r
    return f


# ----------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------

BLOCK = None
DETAIL = None


def add_box(loc, dims, bevel=0.0, rot=None, col=None, name="box"):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (dims[0], dims[1], dims[2])
    if rot:
        ob.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        m = ob.modifiers.new("bev", 'BEVEL')
        m.width = bevel
        m.segments = 2
        m.limit_method = 'ANGLE'
        m.angle_limit = D2R(30)
        bpy.ops.object.modifier_apply(modifier=m.name)
    to_col(ob, col or BLOCK)
    return ob


def add_ellipsoid(loc, scale, col=None, name="ell", rot=None, seg=24, ring=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring,
                                         radius=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = (scale[0], scale[1], scale[2])
    if rot:
        ob.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    to_col(ob, col or BLOCK)
    return ob


def add_cyl(a, b, r, col=None, name="cyl", verts=16):
    a = Vector(a); b = Vector(b)
    d = b - a
    L = d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=L,
                                        location=(a + b) * 0.5)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    to_col(ob, col or BLOCK)
    return ob


def make_leaf(length, width, thickness, name="leaf", us=24, vs=12, base_w=0.20):
    """Broad rounded feather blade: narrow stem, wide rounded tip.

    Cross section is remapped to a superellipse so each feather is a flat
    blade with soft edges (LEGO-plate feel) rather than a smooth ellipsoid.
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=us, v_segments=vs, radius=1.0)
    n_exp = 2.0 / 3.0
    for v in bm.verts:
        t = (v.co.z + 1.0) * 0.5
        u = 2.0 * t - 1.0
        f = math.sqrt(max(0.0, 1.0 - u ** 4))
        f = max(f, base_w)
        cx, cy = v.co.x, v.co.y
        if abs(cx) > 1e-9:
            cx = math.copysign(abs(cx) ** n_exp, cx)
        if abs(cy) > 1e-9:
            cy = math.copysign(abs(cy) ** n_exp, cy)
        v.co.x = cx * (width * 0.5) * f
        v.co.y = cy * (thickness * 0.5) * (0.75 + 0.25 * f)
        v.co.z *= (length * 0.5)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    return ob


def place_leaf(ob, base, tip, up_hint, col=None):
    base = Vector(base); tip = Vector(tip)
    z = (tip - base)
    L = z.length
    z.normalize()
    up = Vector(up_hint)
    y = up - z * up.dot(z)
    if y.length < 1e-5:
        up = Vector((0, 0, 1))
        y = up - z * up.dot(z)
        if y.length < 1e-5:
            up = Vector((1, 0, 0))
            y = up - z * up.dot(z)
    y.normalize()
    x = y.cross(z)
    m = Matrix((
        (x.x, y.x, z.x, base.x + z.x * L * 0.5),
        (x.y, y.y, z.y, base.y + z.y * L * 0.5),
        (x.z, y.z, z.z, base.z + z.z * L * 0.5),
        (0, 0, 0, 1),
    ))
    ob.matrix_world = m
    to_col(ob, col or DETAIL)
    return ob


def feather(base, tip, width, thickness, mat, up_hint, prio=50, col=None):
    L = (Vector(tip) - Vector(base)).length
    ob = make_leaf(L, width, thickness, name="feather")
    place_leaf(ob, base, tip, up_hint, col=col)
    reg(prio, mat, t_capsule(base, tip, max(width, thickness) * 0.55))
    return ob


# ----------------------------------------------------------------------------
# reference images
# ----------------------------------------------------------------------------

def build_references(col):
    specs = [
        ("REF_FRONT", "front", (0, -250, 52), (D2R(90), 0, 0)),
        ("REF_BACK", "back", (0, 250, 52), (D2R(90), 0, D2R(180))),
        ("REF_LEFT", "left", (-250, 0, 52), (D2R(90), 0, D2R(-90))),
        ("REF_RIGHT", "right", (250, 0, 52), (D2R(90), 0, D2R(90))),
        ("REF_TOP", "top", (0, 0, 280), (0, 0, 0)),
        ("REF_BOTTOM", "bottom", (0, 0, -190), (D2R(180), 0, 0)),
    ]
    for name, fn, loc, rot in specs:
        path = os.path.join(VIEWS, fn + ".png")
        if not os.path.exists(path):
            continue
        img = bpy.data.images.load(path)
        e = bpy.data.objects.new(name, None)
        e.data = img
        e.empty_display_type = 'IMAGE'
        e.empty_display_size = TARGET_H * 1.10
        e.location = loc
        e.rotation_euler = rot
        e.hide_render = True
        col.objects.link(e)


# ----------------------------------------------------------------------------
# character build
# ----------------------------------------------------------------------------

def build_body():
    add_box((0, 2, 29), (38, 44, 36), 13, col=BLOCK, name="torso")
    add_box((0, 16, 21), (35, 29, 29), 11, col=BLOCK, name="hips")
    add_box((0, -8, 35), (33, 29, 31), 11, col=BLOCK, name="chest")
    add_box((0, -3, 47), (26, 26, 20), 8, col=BLOCK, name="neck")
    reg(60, "Cream", t_ellip((0, -13, 27), (14, 17, 20)))


def build_head():
    add_box((0, -11, 61), (41, 37, 37), 13, col=BLOCK, name="head")
    add_ellipsoid((0, 4, 57), (23, 21, 21), col=BLOCK, name="mane_base")
    add_box((0, -31, 55), (23, 20, 16), 5, col=BLOCK, name="snout")
    add_box((0, -28, 47), (24, 19, 12), 5, col=BLOCK, name="chin")
    for sx in (-1, 1):
        add_box((sx * 11, -27, 51), (17, 19, 17), 7, col=BLOCK, name="cheek")
    reg(72, "Cream", t_ellip((11, -27, 51), (10.5, 13.5, 11)))
    reg(72, "Cream", t_ellip((-11, -27, 51), (10.5, 13.5, 11)))
    reg(72, "Cream", t_ellip((0, -25, 44), (13.5, 14, 8)))
    add_box((0, -23, 78), (13, 11, 18), 3, col=DETAIL, name="crest_red")
    reg(80, "Red", t_ellip((0, -24, 77), (9.5, 9, 12)))
    add_ellipsoid((0, -30, 55), (10, 4, 4), col=DETAIL, name="nostril_bar")


def build_eyes():
    for sx in (-1, 1):
        ec = Vector((sx * 11.0, -24.0, 64.5))
        add_ellipsoid(ec, (9.2, 8.4, 9.8), col=DETAIL, name="sclera")
        I = ec + Vector((sx * 1.2, -5.6, -1.0))
        add_ellipsoid(I, (6.6, 5.2, 6.6), col=DETAIL, name="iris")
        P = ec + Vector((sx * 1.7, -8.2, -1.5))
        add_ellipsoid(P, (4.0, 3.2, 4.0), col=DETAIL, name="pupil")
        H = P + Vector((-sx * 1.2, -1.8, 1.2))
        add_ellipsoid(H, (2.0, 2.0, 2.0), col=DETAIL, name="hilite")
        reg(100, "Eye_White", t_ellip(ec, (9.7, 9.0, 10.3)))
        reg(101, "Eye_Iris", t_ellip(I, (7.0, 5.6, 7.0)))
        reg(102, "Eye_Pupil", t_ellip(P, (4.4, 3.6, 4.4)))
        reg(103, "Eye_White", t_ellip(H, (2.3, 2.3, 2.3)))


def build_legs():
    for sx in (-1, 1):
        add_box((sx * 11, -14, 14), (15, 16, 28), 7, col=BLOCK, name="fleg")
        add_box((sx * 11, -23, 6.5), (17, 23, 13), 5, col=BLOCK, name="ffoot")
        add_box((sx * 15, 14, 15), (18, 20, 30), 8, col=BLOCK, name="bleg")
        add_box((sx * 15, 23, 6.5), (18, 21, 13), 5, col=BLOCK, name="bfoot")
        for i in (-1, 0, 1):
            c = Vector((sx * 11 + i * 5.4, -33.0, 5.5))
            t = c + Vector((0, -5.2, 0.6))
            add_ellipsoid((c + t) * 0.5, (3.0, 4.6, 3.0), col=DETAIL, name="claw")
            reg(90, "Cream", t_ellip((c + t) * 0.5, (3.4, 5.0, 3.4)))
            c2 = Vector((sx * 15 + i * 5.6, 32.5, 5.5))
            t2 = c2 + Vector((0, 5.2, 0.6))
            add_ellipsoid((c2 + t2) * 0.5, (3.0, 4.6, 3.0), col=DETAIL, name="claw")
            reg(90, "Cream", t_ellip((c2 + t2) * 0.5, (3.4, 5.0, 3.4)))


TAIL_CTRL = [
    (0, 18, 20), (2, 28, 19), (-6, 36, 19), (-18, 38, 20),
    (-30, 35, 22), (-40, 28, 25), (-47, 18, 28), (-50, 7, 31),
]


def catmull_rom(ctrl, n):
    P = [Vector(c) for c in ctrl]
    pts = [P[0]] + P + [P[-1]]
    segs = len(P) - 1
    out = []
    for i in range(n):
        t = i / (n - 1.0) * segs
        k = min(int(t), segs - 1)
        lt = t - k
        p0, p1, p2, p3 = pts[k], pts[k + 1], pts[k + 2], pts[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * lt +
                          (2 * p0 - 5 * p1 + 4 * p2 - p3) * lt * lt +
                          (-p0 + 3 * p1 - 3 * p2 + p3) * lt * lt * lt))
    return out


def build_tail():
    N = 22
    pts = catmull_rom(TAIL_CTRL, N)
    radii = [12.0 + (3.6 - 12.0) * (i / (N - 1.0)) ** 0.85 for i in range(N)]
    for p, r in zip(pts, radii):
        add_ellipsoid(p, (r, r, r), col=BLOCK, name="tailseg")
    palette = ["Blue", "Red", "Green", "Yellow", "Orange", "Purple"]
    idx = 0
    for i in range(3, N, 3):
        seg = (pts[min(i + 1, N - 1)] - pts[i - 1])
        if seg.length < 1e-4:
            continue
        seg.normalize()
        ref = Vector((0, 0, 1)) if abs(seg.z) < 0.9 else Vector((1, 0, 0))
        u = seg.cross(ref).normalized()
        w = seg.cross(u).normalized()
        r = radii[i]
        n = 5
        for k in range(n):
            ang = 2 * math.pi * k / n + i * 0.62
            radial = (u * math.cos(ang) + w * math.sin(ang)).normalized()
            base = pts[i] + radial * (r * 0.30)
            L = 17.0 + 5.0 * math.sin(ang * 1.7)
            tip = base + radial * L + seg * (L * 0.35)
            feather(base, tip, 11.0, 3.4, palette[idx % len(palette)],
                    up_hint=seg, col=DETAIL)
            idx += 1


SPINE = [
    (0, 0, 55), (0, 3, 50), (0, 7, 45), (0, 10, 39),
    (0, 12, 33), (0, 12, 27), (0, 12, 21),
]


def build_spine():
    palette = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple"]
    for i, p in enumerate(SPINE):
        d = Vector((0, 0.88, 0.48)).normalized()
        base = Vector(p)
        tip = base + d * (18 - i * 0.6)
        feather(base, tip, 11.0, 3.6, palette[(i + 2) % len(palette)],
                up_hint=(0, -0.45, 0.88), col=DETAIL)


def build_crest():
    C = Vector((0, 0, 58))
    a = Vector((0, math.sin(D2R(24)), math.cos(D2R(24)))).normalized()
    e1 = Vector((1, 0, 0))
    e2 = a.cross(e1).normalized()
    palette = ["Green", "Blue", "Red", "Yellow", "Orange", "Purple",
               "Blue", "Green", "Red", "Orange", "Yellow", "Purple"]
    layers = [
        (22, 13, 30, 16.0, 4.2, 30),
        (45, 14, 26, 15.0, 4.0, 30),
        (68, 15, 22, 15.0, 3.8, 28),
        (91, 16, 15, 14.0, 3.6, 30),
        (114, 17, 12, 13.0, 3.4, 30),
    ]
    ci = 0
    for beta, R, L, W, T, step in layers:
        psi = 0.0
        while psi < 360.0:
            ps = D2R(psi)
            d = (math.cos(D2R(beta)) * a +
                 math.sin(D2R(beta)) * (math.cos(ps) * e1 + math.sin(ps) * e2))
            d.normalize()
            psi += step
            if d.y < -0.55:
                continue
            if d.z < -0.62:
                continue
            base = C + d * R
            tip = base + d * L
            tang = (-math.sin(ps) * e1 + math.cos(ps) * e2).normalized()
            feather(base, tip, W, T, palette[ci % len(palette)],
                    up_hint=tang, col=DETAIL)
            ci += 1


def build_wings():
    palette = ["Blue", "Red", "Green", "Yellow", "Orange", "Purple"]
    for sx in (-1, 1):
        P = Vector((sx * 15, 12, 49))
        arm = [P, Vector((sx * 25, 15, 55)), Vector((sx * 33, 18, 60)),
               Vector((sx * 39, 20, 63))]
        for i in range(len(arm) - 1):
            add_cyl(arm[i], arm[i + 1], 7.5 - i * 0.6, col=BLOCK, name="warm")
        add_ellipsoid(arm[-1], (7.5, 7, 7), col=BLOCK, name="wrist")
        ci = 0
        n = 8
        for i in range(n):
            t = i / (n - 1.0)
            base = arm[1].lerp(arm[3], t)
            ang = D2R(18 - 96 * t)
            d = Vector((sx * math.cos(ang), 0.22, math.sin(ang))).normalized()
            L = 28 + 8 * math.sin(math.pi * (0.18 + 0.72 * t))
            tip = base + d * L
            feather(base, tip, 14.0, 3.8, palette[ci % len(palette)],
                    up_hint=(0, 0, 1), col=DETAIL)
            ci += 1
        n2 = 6
        for i in range(n2):
            t = i / (n2 - 1.0)
            base = arm[0].lerp(arm[2], t)
            ang = D2R(38 - 92 * t)
            d = Vector((sx * math.cos(ang), 0.38, math.sin(ang))).normalized()
            L = 20 + 6 * math.sin(math.pi * (0.15 + 0.70 * t))
            tip = base + d * L
            feather(base, tip, 12.5, 3.6, palette[(ci + 2) % len(palette)],
                    up_hint=(0, 0, 1), col=DETAIL)
            ci += 1


# ----------------------------------------------------------------------------
# assembly
# ----------------------------------------------------------------------------

def assemble():
    bpy.ops.object.select_all(action='DESELECT')
    objs = [o for o in BLOCK.objects] + [o for o in DETAIL.objects]
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.object
    ob.name = "QUETZALOG_BODY"
    to_col(ob, bpy.data.collections.get("BLOCKOUT"))
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return ob


def remesh(ob):
    m = ob.modifiers.new("Remesh", 'REMESH')
    m.mode = 'VOXEL'
    m.voxel_size = VOXEL
    m.adaptivity = 0.0
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    s = ob.modifiers.new("Smooth", 'SMOOTH')
    s.factor = 0.5
    s.iterations = 3
    bpy.ops.object.modifier_apply(modifier=s.name)
    return ob


def remove_small_components(ob, min_faces=300):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    seen = set()
    comps = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]
        comp = []
        seen.add(f.index)
        while stack:
            cf = stack.pop()
            comp.append(cf)
            for e in cf.edges:
                for lf in e.link_faces:
                    if lf.index not in seen:
                        seen.add(lf.index)
                        stack.append(lf)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    kill = [f for c in comps[1:] if len(c) < min_faces for f in c]
    if kill:
        bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(me)
    bm.free()
    return len(comps), [len(c) for c in comps[:6]]


def settle(ob):
    me = ob.data
    mn = min(v.co.z for v in me.vertices)
    for v in me.vertices:
        v.co.z -= mn
    me.update()
    return mn


def flatten_base(ob, z_cut=2.0):
    """Bisect the model with a horizontal plane and cap it -> flat, stable base."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5,
                           plane_co=(0, 0, z_cut), plane_no=(0, 0, 1),
                           clear_inner=True, clear_outer=False)
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    me = ob.data
    mn = min(v.co.z for v in me.vertices)
    for v in me.vertices:
        v.co.z -= mn
    me.update()


def scale_to_height(ob, h):
    me = ob.data
    zs = [v.co.z for v in me.vertices]
    cur = max(zs) - min(zs)
    s = h / cur
    for v in me.vertices:
        v.co *= s
    me.update()
    return s


def assign_materials(ob):
    me = ob.data
    order = []
    mats = {}
    regs = sorted(REG, key=lambda r: -r[0])
    for _, mat, _ in regs:
        if mat not in mats:
            mats[mat] = len(order)
            order.append(mat)
    if "Body_Teal" not in mats:
        mats["Body_Teal"] = len(order)
        order.append("Body_Teal")
    me.materials.clear()
    for name in order:
        me.materials.append(MATS[name])
    teal = mats["Body_Teal"]
    for p in me.polygons:
        c = p.center
        idx = teal
        for prio, mat, test in regs:
            if test(c):
                idx = mats[mat]
                break
        p.material_index = idx
    me.update()


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main():
    global BLOCK, DETAIL
    clear_scene()
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = 'MILLIMETERS'
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'

    root = get_col("QUETZALOG")
    refs = get_col("REFERENCES", root)
    BLOCK = get_col("BLOCKOUT", root)
    DETAIL = get_col("DETAIL", root)
    get_col("PRINT_READY", root)
    get_col("VALIDATION", root)

    build_materials()
    build_references(refs)

    build_body()
    build_head()
    build_eyes()
    build_legs()
    build_tail()
    build_spine()
    build_crest()
    build_wings()

    ob = assemble()
    remesh(ob)
    ncomp, sizes = remove_small_components(ob)
    flatten_base(ob, 2.0)
    scl = scale_to_height(ob, TARGET_H)
    assign_materials(ob)
    bpy.ops.object.shade_smooth()

    bb = [Vector(c) for c in ob.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    dim = mx - mn
    print("BUILD OK")
    print("verts", len(ob.data.vertices), "faces", len(ob.data.polygons))
    print("bbox min", tuple(round(v, 1) for v in mn))
    print("bbox max", tuple(round(v, 1) for v in mx))
    print("dims", tuple(round(v, 1) for v in dim))
    print("components before cleanup", ncomp, "top sizes", sizes)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "quetzalog_build.blend"))


main()
