"""Find through-holes in a closed mesh.

A voxel-remeshed union can be perfectly manifold (0 boundary edges, 0
non-manifold edges) and still contain a tunnel -- the surface is a torus, so the
mesh audit passes and only a render from the right angle shows it.  The only
reliable detector is a ray cast: shoot a grid of rays along an axis and look for
rays that MISS the model entirely while all four neighbours hit.  A miss
surrounded by hits is a hole.

Run inside Blender after the build.
"""
import bpy
from mathutils import Vector

ob = bpy.data.objects.get("QUETZALOG_PRINT_READY") or bpy.data.objects["QUETZALOG_BODY"]
dg = bpy.context.evaluated_depsgraph_get()

V = len(ob.data.vertices)
F = len(ob.data.polygons)
E = set()
for p in ob.data.polygons:
    vs = list(p.vertices)
    for i in range(len(vs)):
        a, b = vs[i], vs[(i + 1) % len(vs)]
        E.add((min(a, b), max(a, b)))
chi = V - len(E) + F
print(f"V={V} E={len(E)} F={F}  V-E+F={chi}  genus={(2 - chi) // 2}")


def find_holes(axis, lo=-70, hi=71, step=3, depth=-140.0, reach=400.0):
    idx = {'X': 0, 'Y': 1, 'Z': 2}[axis]
    perp = [p for p in range(3) if p != idx]
    out = []
    for u in range(lo, hi, step):
        for v in range(0, 106, step):
            base = [0.0, 0.0, 0.0]
            base[idx] = depth
            base[perp[0]] = float(u)
            base[perp[1]] = float(v)
            d = Vector([0.0, 0.0, 0.0])
            d[idx] = 1.0

            def hit_at(du, dv):
                b2 = list(base)
                b2[perp[0]] += du
                b2[perp[1]] += dv
                ok, _, _, _ = ob.ray_cast(Vector(b2), d, distance=reach, depsgraph=dg)
                return ok

            if hit_at(0, 0):
                continue
            if hit_at(5, 0) and hit_at(-5, 0) and hit_at(0, 5) and hit_at(0, -5):
                out.append((u, v))
    return out


for ax in ('X', 'Y', 'Z'):
    hs = find_holes(ax)
    print(f"axis {ax}: {len(hs)} enclosed tunnel points")
    for u, v in hs[:30]:
        lab = {'X': f"y={u} z={v}", 'Y': f"x={u} z={v}", 'Z': f"x={u} y={v}"}[ax]
        print("   ", lab)
