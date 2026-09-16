"""Quetzalog mascot - sixth pass (v6): face + feather-mane refinement.

Long neck, head forward/up, elongated torso, large folded wings, long tail,
swept-back crest, smaller eyes.

Core volumes are built as clean lofted surfaces with super-elliptical
cross-sections (LEGO rounded-brick feel) rather than stacks of primitives, and
the crest is an orderly layered petal rosette whose petals all lie in their
ring plane.  Units: 1 BU = 1 mm, Z up, FRONT = -Y, +X = character's left.
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

VOXEL = 0.45
TARGET_H = 100.0
D2R = math.radians

MAT_DEFS = {
    "Body_Teal":  (0.020, 0.430, 0.360),
    "Cream":      (0.850, 0.720, 0.500),
    "Red":        (0.720, 0.070, 0.050),
    "Orange":     (0.880, 0.300, 0.020),
    "Yellow":     (0.930, 0.660, 0.050),
    "Green":      (0.140, 0.520, 0.090),
    "Blue":       (0.050, 0.290, 0.700),
    "Purple":     (0.330, 0.140, 0.540),
    "Eye_White":  (0.930, 0.930, 0.930),
    "Eye_Iris":   (0.060, 0.360, 0.720),
    "Eye_Pupil":  (0.010, 0.010, 0.015),
}
MATS = {}

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


# --------------------------------------------------------------- geometry ----
def se(a, p):
    c, s = math.cos(a), math.sin(a)
    x = math.copysign(abs(c) ** (2.0 / p), c) if abs(c) > 1e-12 else 0.0
    y = math.copysign(abs(s) ** (2.0 / p), s) if abs(s) > 1e-12 else 0.0
    return x, y


def _mesh(bm, name, col):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    return to_col(ob, col or BLOCK)


def loft(secs, n=40, power=2.0, name="loft", loc=(0, 0, 0), col=None):
    """secs: [(z, hx, hy, cy)] -> closed super-elliptical lofted solid."""
    bm = bmesh.new()
    rings = []
    for (z, hx, hy, cy) in secs:
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n
            sx, sy = se(a, power)
            ring.append(bm.verts.new((sx * hx, cy + sy * hy, z)))
        rings.append(ring)
    for r in range(len(rings) - 1):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((rings[r][i], rings[r][j], rings[r + 1][j], rings[r + 1][i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    ob = _mesh(bm, name, col)
    ob.location = loc
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return ob


def tube(path, radii, n=20, name="tube", col=None):
    pts = [Vector(p) for p in path]
    bm = bmesh.new()
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        t.normalize()
        ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        u = t.cross(ref).normalized()
        w = t.cross(u).normalized()
        ring = [bm.verts.new(p + u * math.cos(2 * math.pi * k / n) * r +
                             w * math.sin(2 * math.pi * k / n) * r)
                for k in range(n)]
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return _mesh(bm, name, col)


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
    return to_col(ob, col or BLOCK)


def add_ellipsoid(loc, scale, col=None, name="ell", rot=None, seg=28, ring=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring,
                                         radius=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    if rot:
        ob.rotation_euler = rot
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return to_col(ob, col or BLOCK)


def add_cyl(a, b, r, col=None, name="cyl", verts=20):
    a = Vector(a); b = Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length,
                                        location=(a + b) * 0.5)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return to_col(ob, col or BLOCK)


def make_leaf(length, width, thickness, name="leaf", us=20, vs=11,
              base_w=0.10, stud=True, stud_r=1.6, stud_h=1.2, bend=0.0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=us, v_segments=vs, radius=1.0)
    ne = 2.0 / 3.0
    for v in bm.verts:
        t = (v.co.z + 1.0) * 0.5
        f = (math.sin(math.pi * (t ** 0.8)) ** 0.7) if 0.0 < t < 1.0 else 0.0
        f = max(f, base_w)
        cx, cy = v.co.x, v.co.y
        if abs(cx) > 1e-9:
            cx = math.copysign(abs(cx) ** ne, cx)
        if abs(cy) > 1e-9:
            cy = math.copysign(abs(cy) ** ne, cy)
        v.co.x = cx * (width * 0.5) * f
        v.co.y = cy * (thickness * 0.5)
        v.co.z *= (length * 0.5)
    if bend:
        # curl the blade along its length, in the thin-axis direction
        for v in bm.verts:
            t = v.co.z / (length * 0.5) * 0.5 + 0.5
            v.co.y += bend * (t ** 2) * thickness
    if stud:
        res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10,
                                    radius1=stud_r, radius2=stud_r * 0.9,
                                    depth=stud_h)
        for v in res["verts"]:
            v.co.y += thickness * 0.5 + stud_h * 0.3
            v.co.z += length * 0.12
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
    return to_col(ob, col or DETAIL)


def leaf(base, tip, width, thickness, mat, up_hint, prio=50, col=None, stud=True,
         bend=0.0):
    L = (Vector(tip) - Vector(base)).length
    ob = make_leaf(L, width, thickness, stud=stud, bend=bend)
    place(ob, base, tip, up_hint, col=col)
    reg(prio, mat, t_capsule(base, tip, max(width, thickness) * 0.50))
    return ob


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
# Measured from image2: belly bottom z8, chest top z~41, hip z~21, head z52..79
BODY = [
    (8.0, 11.0, 12.0, 6.0),
    (12.0, 13.2, 14.0, 5.0),
    (17.0, 14.8, 15.4, 3.5),
    (23.0, 15.4, 16.0, 1.5),
    (29.0, 15.2, 15.8, 0.0),
    (34.0, 14.4, 15.0, -1.5),
    (38.0, 13.0, 13.8, -3.0),
    (41.0, 11.0, 12.0, -4.5),
    (43.5, 8.4, 9.6, -6.0),
]


def build_body():
    loft(BODY, n=44, power=3.2, name="torso")
    # cream chest + belly panel, segmented with studs
    loft([(10.0, 7.2, 5.0, -11.0), (16.0, 8.4, 5.4, -12.5),
          (23.0, 9.0, 5.6, -13.5), (30.0, 8.6, 5.4, -14.5),
          (36.0, 7.6, 5.0, -15.5), (40.0, 6.2, 4.2, -16.0),
          (43.0, 4.4, 3.2, -16.5)], n=28, power=3.0, col=DETAIL, name="belly")
    reg(60, "Cream", t_ellip((0, -13.5, 26), (10.0, 7.6, 18.5)))
    for zz in (14.0, 21.0, 28.0, 35.0):
        add_cyl((0, -17.0, zz), (0, -17.9, zz), 2.1, col=DETAIL, name="belly_stud")


# ================================================================== HEAD =====
HEAD = [
    (55.0, 11.0, 11.0, -15.0),
    (58.0, 14.0, 13.8, -15.5),
    (61.5, 15.4, 15.2, -16.0),
    (66.0, 15.7, 15.5, -16.0),
    (70.5, 15.3, 15.2, -16.5),
    (74.5, 14.0, 14.0, -17.0),
    (78.0, 10.8, 11.0, -17.5),
    (80.5, 6.4, 7.0, -18.0),
]


def build_head():
    loft(HEAD, n=44, power=3.0, name="head")
    # crown mass the mane grows out of (kept small: the mane covers it)
    add_ellipsoid((0, -8, 71), (13.0, 12.0, 11.0), name="crest_base")
    # brow ridge: overhangs and sockets the eyes
    add_box((0, -22.0, 74.5), (33.0, 13.0, 9.0), 4.5, name="brow")
    # temple / cheek volume flanking the eyes
    for sx in (-1, 1):
        add_box((sx * 13.0, -22.0, 66.0), (10.0, 13.0, 15.0), 5.0, name="temple")
    # snout
    loft([(52.0, 6.6, 7.2, -28.0), (55.5, 7.4, 7.9, -28.0),
          (60.5, 7.4, 7.9, -28.0), (64.5, 6.2, 6.6, -28.0),
          (66.5, 4.0, 4.2, -28.0)], n=32, power=2.6, name="snout")
    reg(76, "Body_Teal", t_ellip((0, -28, 60), (8.6, 9.0, 8.6)))
    # cream cheeks + jaw
    for sx in (-1, 1):
        add_box((sx * 9.4, -25.5, 59.0), (13.0, 13.0, 13.0), 5.6, name="cheek")
    add_box((0, -27.5, 55.5), (18.5, 12.0, 9.5), 4.5, name="chin")
    reg(72, "Cream", t_ellip((9.4, -26.0, 59.0), (9.4, 11.2, 9.2)))
    reg(72, "Cream", t_ellip((-9.4, -26.0, 59.0), (9.4, 11.2, 9.2)))
    reg(72, "Cream", t_ellip((0, -27.5, 55.5), (10.8, 10.4, 7.4)))
    # nostrils
    for sx in (-1, 1):
        add_ellipsoid((sx * 3.6, -34.6, 61.5), (1.3, 1.7, 1.3), col=DETAIL,
                      name="nostril")
        reg(95, "Eye_Pupil", t_ellip((sx * 3.6, -34.7, 61.5), (1.7, 2.1, 1.7)))
    # red forehead crest
    add_box((0, -22.0, 79.0), (8.0, 10.0, 12.5), 2.4, col=DETAIL, name="crest_red")
    add_box((0, -21.0, 85.0), (5.4, 7.0, 5.0), 1.5, col=DETAIL, name="crest_red2")
    reg(80, "Red", t_ellip((0, -22, 80.5), (6.6, 7.4, 9.5)))


def build_eyes():
    """One smooth eyeball per side.  Iris / pupil / highlight are MATERIAL
    regions painted onto that surface - no protruding geometry, so the eye
    stays smooth and the highlight cannot catch a physical specular bump."""
    for sx in (-1, 1):
        ec = Vector((sx * 8.6, -26.0, 68.0))
        add_ellipsoid(ec, (7.2, 6.8, 7.6), col=DETAIL, name="eyeball")
        reg(100, "Eye_White", t_ellip(ec, (7.6, 7.2, 8.0)))
        # iris: front cap of the eyeball
        reg(101, "Eye_Iris",
            t_ellip(ec + Vector((0.0, -3.4, -0.3)), (5.2, 5.2, 5.2)))
        # pupil: smaller front cap
        reg(102, "Eye_Pupil",
            t_ellip(ec + Vector((0.0, -4.9, -0.4)), (2.9, 2.9, 2.9)))
        # highlight: small painted patch on the upper-outer surface
        hd = Vector((sx * 0.34, -0.88, 0.34)).normalized()
        H = ec + hd * 6.9
        reg(103, "Eye_White", t_ellip(H, (1.4, 1.4, 1.4)))


def build_neck():
    path = [Vector((0, 4, 33)), Vector((0, 0, 40)), Vector((0, -4, 46)),
            Vector((0, -8, 51)), Vector((0, -12, 56))]
    tube(path, [9.6, 8.6, 7.9, 7.3, 6.9], n=28, name="neck")


def build_legs():
    for sx in (-1, 1):
        # front leg: vertical column carrying the raised chest
        loft([(0.0, 6.8, 8.2, 0.0), (4.0, 7.8, 9.2, 0.0),
              (10.0, 8.0, 9.4, 0.0), (20.0, 7.8, 9.2, 0.0),
              (28.0, 7.4, 8.8, -0.5), (34.0, 6.6, 8.0, -1.5),
              (38.5, 5.6, 7.0, -2.5)], n=28, power=2.8,
             name="fleg", loc=(sx * 10.5, -12.0, 0))
        loft([(0.0, 6.6, 8.8, 0.0), (3.5, 7.6, 9.8, 0.0),
              (8.0, 7.8, 10.0, 0.0), (12.0, 6.4, 8.4, 0.0)], n=28, power=3.0,
             name="ffoot", loc=(sx * 10.5, -14.0, 0))
        for i in (-1, 0, 1):
            c = Vector((sx * 10.5 + i * 4.9, -22.5, 5.6))
            add_ellipsoid(c + Vector((0, -4.8, 0.7)), (3.0, 4.8, 3.0),
                          col=DETAIL, name="claw")
            reg(90, "Cream", t_ellip(c + Vector((0, -2.3, 0.5)), (3.4, 5.4, 3.4)))
        # rear haunch + foot forward of it
        loft([(6.0, 8.6, 10.2, 0.0), (12.0, 9.4, 11.2, 0.0),
              (19.0, 9.0, 10.6, 0.0), (25.0, 7.6, 9.2, 0.0),
              (30.0, 5.8, 7.0, 0.0)], n=28, power=2.8,
             name="bleg", loc=(sx * 14.5, 15.0, 0))
        loft([(0.0, 6.6, 8.8, 0.0), (3.5, 7.8, 10.0, 0.0),
              (8.0, 8.0, 10.2, 0.0), (12.0, 6.6, 8.6, 0.0)], n=28, power=3.0,
             name="bfoot", loc=(sx * 14.5, 6.0, 0))
        for i in (-1, 0, 1):
            c = Vector((sx * 14.5 + i * 4.9, -2.5, 5.6))
            add_ellipsoid(c + Vector((0, -4.8, 0.7)), (3.0, 4.8, 3.0),
                          col=DETAIL, name="claw")
            reg(90, "Cream", t_ellip(c + Vector((0, -2.3, 0.5)), (3.4, 5.4, 3.4)))


# ================================================================= CREST =====
def build_mane():
    """Continuous feather mane rooted on the skull surface.

    Layered rows run from just above the brow, over the crown, and down the
    nape.  Each row's flow angle rotates from up-and-back at the forehead to
    back-and-down at the nape, so the whole mass reads as one swept mane
    instead of a ring of radial spikes.  Roots are embedded in the skull so
    there is no hard skin/feather boundary and no bald crown."""
    C = Vector((0.0, -14.0, 67.0))
    R = Vector((16.5, 15.5, 14.5))
    pal = ["Green", "Blue", "Red", "Yellow", "Orange", "Purple",
           "Blue", "Green", "Red", "Orange", "Yellow", "Purple"]
    ci = 0
    # (polar_deg, count, length, width, phase_deg, bend)
    rows = [
        (9.0, 6, 26.0, 13.0, 0.0, 0.5),      # crown centre - tall
        (26.0, 9, 22.0, 13.5, 0.0, 0.5),     # forehead - dense
        (44.0, 11, 18.0, 14.0, 18.0, 0.45),  # upper crown
        (62.0, 12, 18.0, 14.0, 0.0, 0.4),    # upper rear
        (80.0, 13, 18.0, 13.5, 15.0, 0.35),  # rear
        (98.0, 13, 18.0, 13.0, 0.0, 0.3),    # nape - long flowing
    ]
    for polar, n, L0, W, ph, bend in rows:
        sp = math.sin(D2R(polar))
        cp = math.cos(D2R(polar))
        # flow rotates from up-and-back (forehead) to back-and-down (nape)
        flow = Vector((0.0, 1.0, 1.15 - 0.013 * polar))
        for k in range(n):
            az = D2R(360.0 * k / n + ph)
            d = Vector((sp * math.sin(az), -sp * math.cos(az), cp))
            if d.y < -0.40:          # leave the face clear
                continue
            if d.z < -0.30:          # nothing under the jaw
                continue
            t = 1.0 / math.sqrt((d.x / R.x) ** 2 + (d.y / R.y) ** 2 +
                                (d.z / R.z) ** 2)
            base = C + d * (t - 1.8)          # root embedded in the skull
            spread = 0.36 + 0.20 * (1.0 - polar / 98.0)
            fdir = (flow + d * spread).normalized()
            L = L0 * (1.0 + 0.18 * (polar / 98.0))
            leaf(base, base + fdir * L, W, 3.4, pal[ci % len(pal)],
                 up_hint=d, bend=bend)
            ci += 1


def build_spine():
    pal = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple"]
    pts = [(0, 8, 41), (0, 14, 38), (0, 19, 35), (0, 23, 32),
           (0, 26, 28), (0, 28, 24), (0, 29, 21)]
    for i, p in enumerate(pts):
        d = Vector((0, 0.85, 0.53)).normalized()
        b = Vector(p)
        leaf(b, b + d * (15 - i * 0.5), 12.0, 3.4,
             pal[(i + 1) % len(pal)], up_hint=(1, 0, 0))


# ================================================================= WINGS =====
def build_wings():
    pal = ["Blue", "Red", "Green", "Yellow", "Orange", "Purple"]
    for sx in (-1, 1):
        # folded wing sweeping out, back and down
        arm = [Vector((sx * 11, 2, 44)), Vector((sx * 23, 8, 50)),
               Vector((sx * 34, 14, 55)), Vector((sx * 44, 20, 58))]
        for i in range(3):
            add_cyl(arm[i], arm[i + 1], 6.4 - i * 0.4, name="warm")
        add_ellipsoid(arm[0], (7.2, 6.8, 6.8), name="shoulder")
        add_ellipsoid(arm[-1], (5.6, 5.4, 5.4), name="wrist")
        ci = 0
        n = 9
        for i in range(n):
            t = i / (n - 1.0)
            base = arm[0].lerp(arm[3], t)
            d = Vector((sx * (0.66 - 0.16 * t), 0.26 + 0.36 * t,
                        -0.62 - 0.14 * t)).normalized()
            L = 25 + 8 * math.sin(math.pi * (0.18 + 0.72 * t))
            leaf(base, base + d * L, 14.5, 3.6, pal[ci % len(pal)],
                 up_hint=(0, 0.76, 0.65))
            ci += 1
        # secondary row (shorter, tucked above)
        for i in range(6):
            t = i / 5.0
            base = arm[0].lerp(arm[2], t)
            d = Vector((sx * (0.58 - 0.12 * t), 0.34 + 0.30 * t,
                        -0.44 - 0.18 * t)).normalized()
            L = 16 + 6 * math.sin(math.pi * (0.2 + 0.7 * t))
            leaf(base, base + d * L, 12.5, 3.5, pal[(ci + 2) % len(pal)],
                 up_hint=(0, 0.76, 0.65))
            ci += 1


# ================================================================== TAIL =====
TAIL_CTRL = [(0, 18, 24), (2, 28, 22), (7, 38, 19), (14, 46, 15),
             (22, 52, 12), (30, 55, 11), (37, 54, 12), (42, 50, 14)]


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
    N = 26
    pts = catmull_rom(TAIL_CTRL, N)
    radii = [10.0 + (3.0 - 10.0) * (i / (N - 1.0)) ** 0.8 for i in range(N)]
    tube(pts, radii, n=22, name="tailcore")
    pal = ["Blue", "Red", "Green", "Yellow", "Orange", "Purple"]
    idx = 0
    for i in range(2, N, 3):
        seg = (pts[min(i + 1, N - 1)] - pts[i - 1]).normalized()
        ref = Vector((0, 0, 1)) if abs(seg.z) < 0.9 else Vector((1, 0, 0))
        u = seg.cross(ref).normalized()
        w = seg.cross(u).normalized()
        r = radii[i]
        for k in range(5):
            ang = 2 * math.pi * k / 5 + i * 0.55
            radial = (u * math.cos(ang) + w * math.sin(ang)).normalized()
            base = pts[i] + radial * (r * 0.22)
            L = (17.0 + 5.0 * math.sin(ang * 1.7)) * (1.0 - 0.42 * i / (N - 1.0))
            leaf(base, base + radial * L + seg * (L * 0.40), 10.0, 3.2,
                 pal[idx % len(pal)], up_hint=(0, 0.76, 0.65))
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
    return ob


def remove_small_components(ob, min_faces=600):
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


def cleanup_degenerate(ob, merge=0.02):
    """Merge coincident verts and dissolve zero-area faces left by the remesh."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge)
    bad = [f for f in bm.faces if f.calc_area() < 1e-7]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context='FACES')
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges)
    loose = [v for v in bm.verts if len(v.link_edges) == 0]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def flatten_base(ob, z_cut=2.0):
    """Cuts the model flat at z_cut and re-seats it on z=0.  Returns the z shift
    that was applied, so the material regions can follow the geometry."""
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
    return -mn


def scale_to_height(ob, h):
    me = ob.data
    zs = [v.co.z for v in me.vertices]
    s = h / (max(zs) - min(zs))
    for v in me.vertices:
        v.co *= s
    me.update()
    return s


def assign_materials(ob, dz=0.0, scl=1.0):
    """Regions are registered in build coordinates; the finished mesh has been
    flattened (z -= dz) and uniformly scaled (x*scl).  Re-map the regions the
    same way so material borders stay locked to the geometry."""
    me = ob.data
    order = []
    mats = {}
    regs = []
    for prio, mat, test in sorted(REG, key=lambda r: -r[0]):
        regs.append((prio, mat, _remap(test, dz, scl)))
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


def _remap(test, dz, scl):
    """Wrap a region predicate so it is evaluated in the pre-transform space."""
    def f(p):
        q = Vector((p.x / scl, p.y / scl, p.z / scl - dz))
        return test(q)
    return f


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
    build_body()
    build_neck()
    build_head()
    build_eyes()
    build_legs()
    build_mane()
    build_spine()
    build_wings()
    build_tail()

    ob = assemble()
    remesh(ob)
    ncomp, sizes = remove_small_components(ob)
    cleanup_degenerate(ob)
    dz = flatten_base(ob, 2.0)
    scl = scale_to_height(ob, TARGET_H)
    assign_materials(ob, dz, scl)
    bpy.ops.object.shade_smooth()

    bb = [Vector(c) for c in ob.bound_box]
    mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    print("BUILD v6 OK")
    print("verts", len(ob.data.vertices), "faces", len(ob.data.polygons))
    print("dims", tuple(round(v, 1) for v in (mx - mn)))
    print("components before cleanup", ncomp, sizes)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "quetzalog_v6.blend"))


main()
