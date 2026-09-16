"""Quetzalog mascot - second-pass reconstruction (v2).

Forms are built from measured cross-sections taken off the six orthographic
references (see scripts/SPEC.md).  Coordinate system: Z up, character FRONT
faces -Y, +X = character's left.  Units: 1 BU = 1 mm, ground plane at z = 0.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

PROJ = "/Users/mauro/Documents/Code/3D-Quetzalog"
VIEWS = os.path.join(PROJ, "views")
OUT = os.path.join(PROJ, "output")
os.makedirs(OUT, exist_ok=True)

VOXEL = 0.55
SMOOTH_ITERS = 2
TARGET_H = 100.0
D2R = math.radians

# ---------------------------------------------------------------- palette ----
MAT_DEFS = {
    "Body_Teal":  (0.020, 0.430, 0.360),
    "Teal_Dark":  (0.015, 0.300, 0.255),
    "Cream":      (0.850, 0.720, 0.500),
    "Red":        (0.720, 0.070, 0.050),
    "Orange":     (0.880, 0.300, 0.020),
    "Yellow":     (0.930, 0.660, 0.050),
    "Green":      (0.140, 0.520, 0.090),
    "Blue":       (0.050, 0.290, 0.700),
    "Purple":     (0.330, 0.140, 0.540),
    "Eye_White":  (0.930, 0.930, 0.930),
    "Eye_Iris":   (0.040, 0.280, 0.580),
    "Eye_Pupil":  (0.010, 0.010, 0.015),
}
MATS = {}

# ------------------------------------------------------- region registry -----
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


# --------------------------------------------------------------- helpers -----
BLOCK = None
DETAIL = None


def clear_scene():
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                  bpy.data.cameras, bpy.data.lights, bpy.data.curves):
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


def build_materials():
    for name, rgb in MAT_DEFS.items():
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
        b.inputs["Roughness"].default_value = 0.55
        if "Specular IOR Level" in b.inputs:
            b.inputs["Specular IOR Level"].default_value = 0.25
        m.diffuse_color = (rgb[0], rgb[1], rgb[2], 1.0)
        MATS[name] = m


def add_box(loc, dims, bevel=0.0, rot=None, col=None, name="box"):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = dims
    if rot:
        ob.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        m = ob.modifiers.new("bev", 'BEVEL')
        m.width = bevel
        m.segments = 3
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
    ob.scale = scale
    if rot:
        ob.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    to_col(ob, col or BLOCK)
    return ob


def add_cyl(a, b, r, col=None, name="cyl", verts=20):
    a = Vector(a); b = Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length,
                                        location=(a + b) * 0.5)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    to_col(ob, col or BLOCK)
    return ob


def loft(sections, bevel, col=None, name="loft"):
    """sections: list of (z, half_x, half_y, centre_y).  Stacked rounded boxes
    that blend into a smooth lofted volume after remeshing."""
    out = []
    for i, (z, hx, hy, cy) in enumerate(sections):
        out.append(add_box((0, cy, z), (hx * 2, hy * 2, 2.0), bevel,
                           col=col, name=f"{name}_{i}"))
    return out


# ----------------------------------------------------------------- leaves ----
def make_leaf(length, width, thickness, name="leaf", us=20, vs=11,
              base_w=0.16, stud=True, stud_r=1.7, stud_h=1.3):
    """Flat rounded blade (super-elliptical cross-section) with an optional
    LEGO-style stud on the outer face."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=us, v_segments=vs, radius=1.0)
    n = 2.0 / 3.0
    for v in bm.verts:
        t = (v.co.z + 1.0) * 0.5
        f = math.sqrt(max(0.0, 1.0 - (2.0 * t - 1.0) ** 4)) * (0.66 + 0.34 * t)
        f = max(f, base_w)
        cx, cy = v.co.x, v.co.y
        if abs(cx) > 1e-9:
            cx = math.copysign(abs(cx) ** n, cx)
        if abs(cy) > 1e-9:
            cy = math.copysign(abs(cy) ** n, cy)
        v.co.x = cx * (width * 0.5) * f
        v.co.y = cy * (thickness * 0.5)
        v.co.z *= (length * 0.5)
    if stud:
        res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False,
                                    segments=12, radius1=stud_r, radius2=stud_r * 0.92,
                                    depth=stud_h)
        for v in res["verts"]:
            v.co.y += thickness * 0.5 + stud_h * 0.35
            v.co.z += length * 0.14
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


def place(ob, base, tip, up_hint, col=None):
    base = Vector(base); tip = Vector(tip)
    z = tip - base
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
    ob.matrix_world = Matrix((
        (x.x, y.x, z.x, base.x + z.x * L * 0.5),
        (x.y, y.y, z.y, base.y + z.y * L * 0.5),
        (x.z, y.z, z.z, base.z + z.z * L * 0.5),
        (0, 0, 0, 1)))
    to_col(ob, col or DETAIL)
    return ob


def leaf(base, tip, width, thickness, mat, up_hint, prio=50, col=None,
         stud=True):
    L = (Vector(tip) - Vector(base)).length
    ob = make_leaf(L, width, thickness, stud=stud)
    place(ob, base, tip, up_hint, col=col)
    reg(prio, mat, t_capsule(base, tip, max(width, thickness) * 0.52))
    return ob


# ------------------------------------------------------------- references ----
def build_references(col):
    specs = [
        ("REF_FRONT", "front", (0, -260, 52), (D2R(90), 0, 0)),
        ("REF_BACK", "back", (0, 260, 52), (D2R(90), 0, D2R(180))),
        ("REF_LEFT", "left", (-260, 0, 52), (D2R(90), 0, D2R(-90))),
        ("REF_RIGHT", "right", (260, 0, 52), (D2R(90), 0, D2R(90))),
        ("REF_TOP", "top", (0, 0, 290), (0, 0, 0)),
        ("REF_BOTTOM", "bottom", (0, 0, -200), (D2R(180), 0, 0)),
    ]
    for name, fn, loc, rot in specs:
        p = os.path.join(VIEWS, fn + ".png")
        if not os.path.exists(p):
            continue
        img = bpy.data.images.load(p)
        e = bpy.data.objects.new(name, None)
        e.data = img
        e.empty_display_type = 'IMAGE'
        e.empty_display_size = TARGET_H * 1.10
        e.location = loc
        e.rotation_euler = rot
        e.hide_render = True
        col.objects.link(e)


# ================================================================== BODY =====
def build_legs():
    for sx in (-1, 1):
        # front leg + foot
        add_box((sx * 12.5, -13, 21), (15, 16, 25), 7, name="fleg")
        add_box((sx * 12.5, -20, 6.5), (16, 21, 13), 5, name="ffoot")
        for i in (-1, 0, 1):
            c = Vector((sx * 12.5 + i * 5.3, -29.5, 5.6))
            add_ellipsoid((c + Vector((0, -5.0, 0.6))), (3.0, 4.8, 3.0),
                          col=DETAIL, name="claw")
            reg(90, "Cream", t_ellip(c + Vector((0, -2.4, 0.4)), (3.4, 5.4, 3.4)))
        # rear haunch + splayed foot
        add_box((sx * 17.5, 10, 18), (18, 22, 26), 8, name="bleg")
        add_box((sx * 21.5, 16, 6.5), (17, 20, 13), 5,
                rot=(0, 0, sx * D2R(-16)), name="bfoot")
        for i in (-1, 0, 1):
            c = Vector((sx * 24.0 + i * 5.2, 25.5, 5.6))
            add_ellipsoid(c + Vector((sx * 1.6, 4.6, 0.6)), (3.0, 4.8, 3.0),
                          col=DETAIL, name="claw")
            reg(90, "Cream", t_ellip(c + Vector((sx * 1.0, 2.2, 0.4)),
                                     (3.4, 5.4, 3.4)))


BODY_SECTIONS = [
    (13.5, 15.0, 15.0, 0.0),
    (19.0, 16.8, 16.5, 0.0),
    (26.0, 17.4, 17.2, -0.4),
    (33.0, 17.0, 17.0, -1.0),
    (40.0, 15.8, 16.0, -1.6),
    (46.0, 13.6, 14.4, -1.8),
    (51.5, 10.6, 12.0, -1.8),
]


def build_body():
    loft(BODY_SECTIONS, 9.0, name="torso")
    # raised cream belly panel
    add_box((0, -15.5, 27), (15.5, 7.0, 25.0), 3.0, col=DETAIL, name="belly")
    reg(60, "Cream", t_ellip((0, -15.0, 27), (8.6, 8.5, 13.6)))
    # chest plate (slightly proud, teal)
    add_box((0, -12.5, 43), (22.0, 8.0, 14.0), 5.0, name="chest")


def build_neck():
    add_box((0, -3, 50), (19.0, 22.0, 13.0), 6.5, name="neck")


# ================================================================== HEAD =====
def build_head():
    add_box((0, -3, 63), (36.0, 34.0, 34.0), 11.0, name="head")
    # brow / helmet band across the top-front
    add_box((0, -13, 74), (32.0, 18.0, 11.0), 4.5, name="brow")
    # crown block behind the red crest
    add_box((0, 2, 74), (28.0, 20.0, 12.0), 5.0, name="crown")
    # snout
    add_box((0, -21, 54), (16.0, 16.0, 14.0), 4.0, name="snout")
    reg(76, "Body_Teal", t_ellip((0, -22, 55), (9.5, 10.0, 9.0)))
    # cream cheeks + jaw
    for sx in (-1, 1):
        add_box((sx * 9.5, -18, 51), (13.5, 16.5, 15.0), 5.5, name="cheek")
    add_box((0, -17, 45.5), (22.0, 15.0, 10.0), 4.5, name="chin")
    reg(72, "Cream", t_ellip((9.5, -18, 51), (9.6, 12.4, 10.2)))
    reg(72, "Cream", t_ellip((-9.5, -18, 51), (9.6, 12.4, 10.2)))
    reg(72, "Cream", t_ellip((0, -17, 45), (12.0, 12.0, 7.4)))
    # nostrils
    for sx in (-1, 1):
        add_ellipsoid((sx * 4.0, -28.5, 56.5), (1.7, 2.0, 1.7), col=DETAIL,
                      name="nostril")
        reg(95, "Eye_Pupil", t_ellip((sx * 4.0, -28.6, 56.5), (2.0, 2.4, 2.0)))
    # red forehead crest
    add_box((0, -16, 74.5), (9.0, 11.0, 13.5), 2.5, col=DETAIL, name="crest_red")
    add_box((0, -16, 80.5), (6.0, 8.0, 5.0), 1.5, col=DETAIL, name="crest_red2")
    reg(80, "Red", t_ellip((0, -16, 76), (7.0, 8.0, 9.5)))


def build_eyes():
    for sx in (-1, 1):
        ec = Vector((sx * 9.9, -17.0, 61.0))
        add_ellipsoid(ec, (8.4, 7.8, 9.0), col=DETAIL, name="sclera")
        I = ec + Vector((sx * 0.9, -5.2, -0.9))
        add_ellipsoid(I, (6.0, 4.8, 6.3), col=DETAIL, name="iris")
        P = ec + Vector((sx * 1.3, -7.6, -1.3))
        add_ellipsoid(P, (3.7, 3.0, 3.9), col=DETAIL, name="pupil")
        H = P + Vector((-sx * 1.1, -1.9, 1.2))
        add_ellipsoid(H, (1.9, 1.9, 1.9), col=DETAIL, name="hilite")
        reg(100, "Eye_White", t_ellip(ec, (8.9, 8.3, 9.5)))
        reg(101, "Eye_Iris", t_ellip(I, (6.4, 5.2, 6.7)))
        reg(102, "Eye_Pupil", t_ellip(P, (4.1, 3.4, 4.3)))
        reg(103, "Eye_White", t_ellip(H, (2.2, 2.2, 2.2)))


# ================================================================= CREST =====
def build_crest():
    C = Vector((0, 2, 69))
    a = Vector((0, math.sin(D2R(24)), math.cos(D2R(24)))).normalized()
    e1 = Vector((1, 0, 0))
    e2 = a.cross(e1).normalized()
    pal = ["Green", "Blue", "Red", "Yellow", "Orange", "Purple",
           "Blue", "Green", "Red", "Orange", "Yellow", "Purple"]
    layers = [
        (18, 13.0, 21.0, 13.0, 3.6, 12),
        (42, 14.0, 19.0, 13.0, 3.5, 13),
        (66, 15.0, 16.5, 12.5, 3.4, 15),
        (90, 16.0, 14.0, 12.0, 3.3, 16),
        (114, 17.0, 12.0, 11.5, 3.2, 16),
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
            if d.y < -0.52 or d.z < -0.62:
                continue
            base = C + d * R
            tip = base + d * L
            tang = (-math.sin(ps) * e1 + math.cos(ps) * e2).normalized()
            leaf(base, tip, W, T, pal[ci % len(pal)], up_hint=tang)
            ci += 1


def build_spine():
    pal = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple"]
    pts = [(0, 4, 56), (0, 8, 50), (0, 12, 44), (0, 15, 38),
           (0, 17, 32), (0, 17, 26), (0, 16, 21)]
    for i, p in enumerate(pts):
        d = Vector((0, 0.86, 0.51)).normalized()
        b = Vector(p)
        leaf(b, b + d * (16 - i * 0.7), 11.0, 3.4,
             pal[(i + 1) % len(pal)], up_hint=(0, -0.45, 0.88))


# ================================================================= WINGS =====
def build_wings():
    pal = ["Blue", "Red", "Green", "Yellow", "Orange", "Purple"]
    for sx in (-1, 1):
        arm = [Vector((sx * 14, 6, 52)), Vector((sx * 22, 9, 55)),
               Vector((sx * 29, 12, 56.5)), Vector((sx * 34, 15, 57.5))]
        for i in range(len(arm) - 1):
            add_cyl(arm[i], arm[i + 1], 6.6 - i * 0.5, name="warm")
        add_ellipsoid(arm[-1], (6.6, 6.2, 6.2), name="wrist")
        add_ellipsoid(arm[0], (7.4, 7.0, 7.0), name="shoulder")
        ci = 0
        n = 8
        for i in range(n):
            t = i / (n - 1.0)
            base = arm[1].lerp(arm[3], t)
            ang = D2R(12 - 84 * t)
            d = Vector((sx * math.cos(ang), 0.20, math.sin(ang))).normalized()
            L = 20 + 10 * math.sin(math.pi * (0.20 + 0.70 * t))
            leaf(base, base + d * L, 12.5, 3.4, pal[ci % len(pal)],
                 up_hint=(0, 0, 1))
            ci += 1
        for i in range(6):
            t = i / 5.0
            base = arm[0].lerp(arm[2], t)
            ang = D2R(34 - 76 * t)
            d = Vector((sx * math.cos(ang), 0.34, math.sin(ang))).normalized()
            L = 14 + 7 * math.sin(math.pi * (0.18 + 0.72 * t))
            leaf(base, base + d * L, 11.0, 3.3, pal[(ci + 3) % len(pal)],
                 up_hint=(0, 0, 1))
            ci += 1


# ================================================================== TAIL =====
TAIL_CTRL = [(0, 15, 21), (3, 25, 20), (7, 34, 20), (12, 43, 21),
             (18, 50, 23), (25, 54, 25), (31, 54, 27), (35, 49, 29)]


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
    N = 24
    pts = catmull_rom(TAIL_CTRL, N)
    radii = [11.5 + (3.4 - 11.5) * (i / (N - 1.0)) ** 0.8 for i in range(N)]
    for p, r in zip(pts, radii):
        add_ellipsoid(p, (r, r, r), name="tailseg")
    pal = ["Blue", "Red", "Green", "Yellow", "Orange", "Purple"]
    idx = 0
    for i in range(3, N, 3):
        seg = (pts[min(i + 1, N - 1)] - pts[i - 1]).normalized()
        ref = Vector((0, 0, 1)) if abs(seg.z) < 0.9 else Vector((1, 0, 0))
        u = seg.cross(ref).normalized()
        w = seg.cross(u).normalized()
        r = radii[i]
        for k in range(5):
            ang = 2 * math.pi * k / 5 + i * 0.55
            radial = (u * math.cos(ang) + w * math.sin(ang)).normalized()
            base = pts[i] + radial * (r * 0.25)
            L = 15.0 + 4.0 * math.sin(ang * 1.7)
            leaf(base, base + radial * L + seg * (L * 0.35), 10.5, 3.3,
                 pal[idx % len(pal)], up_hint=seg)
            idx += 1


# ============================================================== ASSEMBLY =====
def assemble():
    bpy.ops.object.select_all(action='DESELECT')
    objs = list(BLOCK.objects) + list(DETAIL.objects)
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
    s.iterations = SMOOTH_ITERS
    bpy.ops.object.modifier_apply(modifier=s.name)
    return ob


def remove_small_components(ob, min_faces=400):
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


def flatten_base(ob, z_cut=2.2):
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
    s = h / (max(zs) - min(zs))
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


def main():
    global BLOCK, DETAIL
    clear_scene()
    sc = bpy.context.scene
    sc.name = "Quetzalog"
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

    build_legs()
    build_body()
    build_neck()
    build_head()
    build_eyes()
    build_crest()
    build_spine()
    build_wings()
    build_tail()

    ob = assemble()
    remesh(ob)
    ncomp, sizes = remove_small_components(ob)
    flatten_base(ob, 2.2)
    scl = scale_to_height(ob, TARGET_H)
    assign_materials(ob)
    bpy.ops.object.shade_smooth()

    bb = [Vector(c) for c in ob.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    print("BUILD v2 OK")
    print("verts", len(ob.data.vertices), "faces", len(ob.data.polygons))
    print("dims", tuple(round(v, 1) for v in (mx - mn)))
    print("components before cleanup", ncomp, sizes)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "quetzalog_v2.blend"))


main()
