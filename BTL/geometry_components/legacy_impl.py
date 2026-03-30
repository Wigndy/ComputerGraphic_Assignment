import OpenGL.GL as GL              # standard Python OpenGL wrapper
import numpy as np
import sys
import os
import ast
from pathlib import Path

# Ensure both project root and BTL package folder are importable after refactor.
_this_file = Path(__file__).resolve()
_btl_dir = _this_file.parent.parent
_project_root = _btl_dir.parent
for _p in (str(_project_root), str(_btl_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from libs.shader import *
from libs import transform as T
from libs.buffer import *
from libs.lighting import LightingManager, Material
from sample_function import LossFunctionType, LossSurfaceMeshGenerator
import ctypes

class Geo2D:
    SHAPES = ["Triangle", "Rectangle", "Pentagon", "Hexagon", "Circle", "Ellipse", "Trapezoid", "Star", "Arrow"]
    
    @staticmethod
    def generate(shape_type, radius=1.0, width=1.0, height=1.0, segments=36):
        vertices = []
        normals = []
        texcoords = []
        
        def add_fan(points_2d):
            # points_2d: CCW polygon vertices (without repeating first point)
            cx = sum(p[0] for p in points_2d) / len(points_2d)
            cy = sum(p[1] for p in points_2d) / len(points_2d)
            vertices.append([cx, cy, 0.0])
            normals.append([0.0, 0.0, 1.0])
            texcoords.append([0.5, 0.5])

            # close loop for triangle fan
            pts = points_2d + [points_2d[0]]
            sx = max(abs(p[0]) for p in points_2d) or 1.0
            sy = max(abs(p[1]) for p in points_2d) or 1.0
            for x, y in pts:
                vertices.append([x, y, 0.0])
                normals.append([0.0, 0.0, 1.0])
                texcoords.append([x / (2.0 * sx) + 0.5, y / (2.0 * sy) + 0.5])

        
        if shape_type in ["Triangle", "Pentagon", "Hexagon", "Circle"]:
            n_sides = 3 if shape_type == "Triangle" else \
                      5 if shape_type == "Pentagon" else \
                      6 if shape_type == "Hexagon" else segments
            
            pts = []
            for i in range(n_sides):
                theta = i * (2 * np.pi / n_sides)
                pts.append([radius * np.cos(theta), radius * np.sin(theta)])
            add_fan(pts)
                
        elif shape_type == "Rectangle":
            hw, hh = width / 2.0, height / 2.0
            pts = [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]]
            add_fan(pts)

        elif shape_type == "Ellipse":
            n = max(12, int(segments))
            a, b = width / 2.0, height / 2.0
            pts = []
            for i in range(n):
                theta = i * (2 * np.pi / n)
                pts.append([a * np.cos(theta), b * np.sin(theta)])
            add_fan(pts)

        elif shape_type == "Trapezoid":
            bw = width
            tw = width * 0.6
            hh = height / 2.0
            pts = [[-bw / 2.0, -hh], [bw / 2.0, -hh], [tw / 2.0, hh], [-tw / 2.0, hh]]
            add_fan(pts)

        elif shape_type == "Star":
            n = 5
            r_outer = radius
            r_inner = radius * 0.45
            pts = []
            for i in range(2 * n):
                r = r_outer if i % 2 == 0 else r_inner
                theta = i * (np.pi / n) - np.pi / 2.0
                pts.append([r * np.cos(theta), r * np.sin(theta)])
            add_fan(pts)

        elif shape_type == "Arrow":
            # Upward arrow polygon (concave, fan still gives a usable filled arrow shape)
            hw = width / 2.0
            hh = height / 2.0
            shaft_w = width * 0.35 / 2.0
            shaft_top = -hh + height * 0.45
            pts = [
                [-shaft_w, -hh],
                [ shaft_w, -hh],
                [ shaft_w, shaft_top],
                [ hw,      shaft_top],
                [ 0.0,      hh],
                [-hw,      shaft_top],
                [-shaft_w, shaft_top],
            ]
            add_fan(pts)

        return np.array(vertices, dtype=np.float32), \
               np.array(normals, dtype=np.float32), \
               np.array(texcoords, dtype=np.float32)
               
               
class Geo3D:
    SHAPES = ["Cube", "Sphere (Lat-Long)", "Sphere (Subdiv)", "Sphere (Grid)", 
              "Cylinder", "Cone", "Truncated Cone", "Tetrahedron", "Torus", "Prism", "Heart"]

    @staticmethod
    def generate(shape_type, radius=1.0, height=2.0, sectors=36, stacks=18, inner_radius=0.3):
        vertices, normals, texcoords = [], [], []

        def norm(v):
            v = np.array(v, dtype=np.float64)
            n = np.linalg.norm(v)
            return (v / n) if n > 1e-12 else v

        def spherical_uv(p):
            p = norm(p)
            u = 0.5 + np.arctan2(p[1], p[0]) / (2.0 * np.pi)
            v = 0.5 - np.arcsin(np.clip(p[2], -1.0, 1.0)) / np.pi
            return [float(u), float(v)]

        def add_tri(v0, v1, v2, n0=None, n1=None, n2=None, t0=None, t1=None, t2=None):
            vv = [np.array(v0, dtype=np.float32), np.array(v1, dtype=np.float32), np.array(v2, dtype=np.float32)]
            if n0 is None or n1 is None or n2 is None:
                fn = norm(np.cross(vv[1] - vv[0], vv[2] - vv[0]))
                n0 = n1 = n2 = fn
            if t0 is None: t0 = spherical_uv(vv[0])
            if t1 is None: t1 = spherical_uv(vv[1])
            if t2 is None: t2 = spherical_uv(vv[2])

            vertices.extend([vv[0].tolist(), vv[1].tolist(), vv[2].tolist()])
            normals.extend([np.array(n0, dtype=np.float32).tolist(),
                            np.array(n1, dtype=np.float32).tolist(),
                            np.array(n2, dtype=np.float32).tolist()])
            texcoords.extend([list(map(float, t0)), list(map(float, t1)), list(map(float, t2))])

        if shape_type == "Cube":
            r = radius
            faces = [
                # +X
                ([[r, -r, -r], [r, r, -r], [r, r, r], [r, -r, r]], [1, 0, 0]),
                # -X
                ([[-r, r, -r], [-r, -r, -r], [-r, -r, r], [-r, r, r]], [-1, 0, 0]),
                # +Y
                ([[-r, r, -r], [r, r, -r], [r, r, r], [-r, r, r]], [0, 1, 0]),
                # -Y
                ([[r, -r, -r], [-r, -r, -r], [-r, -r, r], [r, -r, r]], [0, -1, 0]),
                # +Z
                ([[-r, -r, r], [r, -r, r], [r, r, r], [-r, r, r]], [0, 0, 1]),
                # -Z
                ([[-r, r, -r], [r, r, -r], [r, -r, -r], [-r, -r, -r]], [0, 0, -1]),
            ]
            for quad, n in faces:
                t = [[0, 0], [1, 0], [1, 1], [0, 1]]
                add_tri(quad[0], quad[1], quad[2], n, n, n, t[0], t[1], t[2])
                add_tri(quad[0], quad[2], quad[3], n, n, n, t[0], t[2], t[3])

        elif shape_type == "Sphere (Lat-Long)":
            st = max(3, int(stacks))
            sc = max(3, int(sectors))
            for i in range(st):
                th0 = np.pi * i / st
                th1 = np.pi * (i + 1) / st
                for j in range(sc):
                    ph0 = 2.0 * np.pi * j / sc
                    ph1 = 2.0 * np.pi * (j + 1) / sc

                    p00 = np.array([radius * np.sin(th0) * np.cos(ph0),
                                    radius * np.sin(th0) * np.sin(ph0),
                                    radius * np.cos(th0)])
                    p10 = np.array([radius * np.sin(th1) * np.cos(ph0),
                                    radius * np.sin(th1) * np.sin(ph0),
                                    radius * np.cos(th1)])
                    p11 = np.array([radius * np.sin(th1) * np.cos(ph1),
                                    radius * np.sin(th1) * np.sin(ph1),
                                    radius * np.cos(th1)])
                    p01 = np.array([radius * np.sin(th0) * np.cos(ph1),
                                    radius * np.sin(th0) * np.sin(ph1),
                                    radius * np.cos(th0)])

                    n00, n10, n11, n01 = norm(p00), norm(p10), norm(p11), norm(p01)
                    t00, t10, t11, t01 = [j / sc, i / st], [j / sc, (i + 1) / st], [(j + 1) / sc, (i + 1) / st], [(j + 1) / sc, i / st]

                    add_tri(p00, p10, p11, n00, n10, n11, t00, t10, t11)
                    add_tri(p00, p11, p01, n00, n11, n01, t00, t11, t01)

        elif shape_type == "Sphere (Subdiv)":
            # Icosahedron subdivision sphere
            t = (1.0 + np.sqrt(5.0)) / 2.0
            base = [
                [-1,  t,  0], [1,  t,  0], [-1, -t,  0], [1, -t,  0],
                [0, -1,  t], [0,  1,  t], [0, -1, -t], [0,  1, -t],
                [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1],
            ]
            verts = [norm(v) for v in base]
            faces = [
                [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
                [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
                [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
                [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
            ]

            level = max(0, min(4, int(stacks // 6)))
            for _ in range(level):
                mid_cache = {}
                new_faces = []

                def midpoint(i, j):
                    key = tuple(sorted((i, j)))
                    if key in mid_cache:
                        return mid_cache[key]
                    m = norm((verts[i] + verts[j]) * 0.5)
                    verts.append(m)
                    idx = len(verts) - 1
                    mid_cache[key] = idx
                    return idx

                for i0, i1, i2 in faces:
                    a = midpoint(i0, i1)
                    b = midpoint(i1, i2)
                    c = midpoint(i2, i0)
                    new_faces.extend([
                        [i0, a, c],
                        [i1, b, a],
                        [i2, c, b],
                        [a, b, c],
                    ])
                faces = new_faces

            for i0, i1, i2 in faces:
                p0 = (verts[i0] * radius).tolist()
                p1 = (verts[i1] * radius).tolist()
                p2 = (verts[i2] * radius).tolist()
                n0, n1, n2 = verts[i0], verts[i1], verts[i2]
                add_tri(p0, p1, p2, n0, n1, n2, spherical_uv(n0), spherical_uv(n1), spherical_uv(n2))

        elif shape_type == "Sphere (Grid)":
            # Cube-sphere grid
            g = max(2, int(stacks))
            face_dirs = [
                (np.array([ 1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])),
                (np.array([-1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0,-1])),
                (np.array([ 0, 1, 0]), np.array([1, 0, 0]), np.array([0, 0,-1])),
                (np.array([ 0,-1, 0]), np.array([1, 0, 0]), np.array([0, 0, 1])),
                (np.array([ 0, 0, 1]), np.array([1, 0, 0]), np.array([0, 1, 0])),
                (np.array([ 0, 0,-1]), np.array([1, 0, 0]), np.array([0,-1, 0])),
            ]

            for n, udir, vdir in face_dirs:
                for i in range(g):
                    v0 = -1.0 + 2.0 * i / g
                    v1 = -1.0 + 2.0 * (i + 1) / g
                    for j in range(g):
                        u0 = -1.0 + 2.0 * j / g
                        u1 = -1.0 + 2.0 * (j + 1) / g

                        q00 = norm(n + udir * u0 + vdir * v0) * radius
                        q10 = norm(n + udir * u0 + vdir * v1) * radius
                        q11 = norm(n + udir * u1 + vdir * v1) * radius
                        q01 = norm(n + udir * u1 + vdir * v0) * radius

                        n00, n10, n11, n01 = norm(q00), norm(q10), norm(q11), norm(q01)
                        t00, t10, t11, t01 = [j / g, i / g], [j / g, (i + 1) / g], [(j + 1) / g, (i + 1) / g], [(j + 1) / g, i / g]
                        add_tri(q00, q10, q11, n00, n10, n11, t00, t10, t11)
                        add_tri(q00, q11, q01, n00, n11, n01, t00, t11, t01)

        elif shape_type == "Cylinder":
            sc = max(3, int(sectors))
            h0, h1 = -height / 2.0, height / 2.0

            # side
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                c0, s0 = np.cos(a0), np.sin(a0)
                c1, s1 = np.cos(a1), np.sin(a1)

                p00 = [radius * c0, radius * s0, h0]
                p10 = [radius * c0, radius * s0, h1]
                p11 = [radius * c1, radius * s1, h1]
                p01 = [radius * c1, radius * s1, h0]
                n00 = [c0, s0, 0]
                n10 = [c0, s0, 0]
                n11 = [c1, s1, 0]
                n01 = [c1, s1, 0]
                t00, t10, t11, t01 = [i / sc, 0], [i / sc, 1], [(i + 1) / sc, 1], [(i + 1) / sc, 0]
                add_tri(p00, p10, p11, n00, n10, n11, t00, t10, t11)
                add_tri(p00, p11, p01, n00, n11, n01, t00, t11, t01)

            # bottom cap
            cb = [0, 0, h0]
            nb = [0, 0, -1]
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                p0 = [radius * np.cos(a0), radius * np.sin(a0), h0]
                p1 = [radius * np.cos(a1), radius * np.sin(a1), h0]
                add_tri(cb, p1, p0, nb, nb, nb,
                        [0.5, 0.5],
                        [p1[0] / (2 * radius) + 0.5, p1[1] / (2 * radius) + 0.5],
                        [p0[0] / (2 * radius) + 0.5, p0[1] / (2 * radius) + 0.5])

            # top cap
            ct = [0, 0, h1]
            nt = [0, 0, 1]
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                p0 = [radius * np.cos(a0), radius * np.sin(a0), h1]
                p1 = [radius * np.cos(a1), radius * np.sin(a1), h1]
                add_tri(ct, p0, p1, nt, nt, nt,
                        [0.5, 0.5],
                        [p0[0] / (2 * radius) + 0.5, p0[1] / (2 * radius) + 0.5],
                        [p1[0] / (2 * radius) + 0.5, p1[1] / (2 * radius) + 0.5])

        elif shape_type == "Cone":
            sc = max(3, int(sectors))
            h0, h1 = -height / 2.0, height / 2.0
            tip = [0, 0, h1]

            # side
            k = radius / max(height, 1e-6)
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                c0, s0 = np.cos(a0), np.sin(a0)
                c1, s1 = np.cos(a1), np.sin(a1)
                p0 = [radius * c0, radius * s0, h0]
                p1 = [radius * c1, radius * s1, h0]
                n0 = norm([c0, s0, k])
                n1 = norm([c1, s1, k])
                nt = norm([(c0 + c1) * 0.5, (s0 + s1) * 0.5, k])
                add_tri(p0, tip, p1, n0, nt, n1, [i / sc, 0], [(i + 0.5) / sc, 1], [(i + 1) / sc, 0])

            # base cap
            cb = [0, 0, h0]
            nb = [0, 0, -1]
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                p0 = [radius * np.cos(a0), radius * np.sin(a0), h0]
                p1 = [radius * np.cos(a1), radius * np.sin(a1), h0]
                add_tri(cb, p1, p0, nb, nb, nb,
                        [0.5, 0.5],
                        [p1[0] / (2 * radius) + 0.5, p1[1] / (2 * radius) + 0.5],
                        [p0[0] / (2 * radius) + 0.5, p0[1] / (2 * radius) + 0.5])

        elif shape_type == "Truncated Cone":
            sc = max(3, int(sectors))
            h0, h1 = -height / 2.0, height / 2.0
            r0 = radius
            r1 = float(inner_radius if inner_radius > 0 else radius * 0.5)

            slope = (r0 - r1) / max(height, 1e-6)
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                c0, s0 = np.cos(a0), np.sin(a0)
                c1, s1 = np.cos(a1), np.sin(a1)

                p00 = [r0 * c0, r0 * s0, h0]
                p10 = [r1 * c0, r1 * s0, h1]
                p11 = [r1 * c1, r1 * s1, h1]
                p01 = [r0 * c1, r0 * s1, h0]

                n00 = norm([c0, s0, slope])
                n10 = norm([c0, s0, slope])
                n11 = norm([c1, s1, slope])
                n01 = norm([c1, s1, slope])

                add_tri(p00, p10, p11, n00, n10, n11, [i / sc, 0], [i / sc, 1], [(i + 1) / sc, 1])
                add_tri(p00, p11, p01, n00, n11, n01, [i / sc, 0], [(i + 1) / sc, 1], [(i + 1) / sc, 0])

            # bottom cap
            cb = [0, 0, h0]
            nb = [0, 0, -1]
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                p0 = [r0 * np.cos(a0), r0 * np.sin(a0), h0]
                p1 = [r0 * np.cos(a1), r0 * np.sin(a1), h0]
                add_tri(cb, p1, p0, nb, nb, nb)

            # top cap
            ct = [0, 0, h1]
            nt = [0, 0, 1]
            for i in range(sc):
                a0 = 2.0 * np.pi * i / sc
                a1 = 2.0 * np.pi * (i + 1) / sc
                p0 = [r1 * np.cos(a0), r1 * np.sin(a0), h1]
                p1 = [r1 * np.cos(a1), r1 * np.sin(a1), h1]
                add_tri(ct, p0, p1, nt, nt, nt)

        elif shape_type == "Tetrahedron":
            # regular tetrahedron centered at origin
            base = np.array([
                [ 1,  1,  1],
                [-1, -1,  1],
                [-1,  1, -1],
                [ 1, -1, -1],
            ], dtype=np.float64)
            base = np.array([norm(v) * radius for v in base], dtype=np.float64)
            faces = [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)]
            for i0, i1, i2 in faces:
                p0, p1, p2 = base[i0], base[i1], base[i2]
                fn = norm(np.cross(p1 - p0, p2 - p0))
                add_tri(p0, p1, p2, fn, fn, fn)

        elif shape_type == "Torus":
            sc = max(3, int(sectors))
            st = max(3, int(stacks))
            R = radius
            r = max(1e-6, float(inner_radius))

            for i in range(st):
                th0 = 2.0 * np.pi * i / st
                th1 = 2.0 * np.pi * (i + 1) / st
                cth0, sth0 = np.cos(th0), np.sin(th0)
                cth1, sth1 = np.cos(th1), np.sin(th1)

                for j in range(sc):
                    ph0 = 2.0 * np.pi * j / sc
                    ph1 = 2.0 * np.pi * (j + 1) / sc
                    cph0, sph0 = np.cos(ph0), np.sin(ph0)
                    cph1, sph1 = np.cos(ph1), np.sin(ph1)

                    p00 = np.array([(R + r * cth0) * cph0, (R + r * cth0) * sph0, r * sth0])
                    p10 = np.array([(R + r * cth1) * cph0, (R + r * cth1) * sph0, r * sth1])
                    p11 = np.array([(R + r * cth1) * cph1, (R + r * cth1) * sph1, r * sth1])
                    p01 = np.array([(R + r * cth0) * cph1, (R + r * cth0) * sph1, r * sth0])

                    c00 = np.array([R * cph0, R * sph0, 0.0])
                    c10 = np.array([R * cph0, R * sph0, 0.0])
                    c11 = np.array([R * cph1, R * sph1, 0.0])
                    c01 = np.array([R * cph1, R * sph1, 0.0])

                    n00 = norm(p00 - c00)
                    n10 = norm(p10 - c10)
                    n11 = norm(p11 - c11)
                    n01 = norm(p01 - c01)

                    t00, t10, t11, t01 = [j / sc, i / st], [j / sc, (i + 1) / st], [(j + 1) / sc, (i + 1) / st], [(j + 1) / sc, i / st]
                    add_tri(p00, p10, p11, n00, n10, n11, t00, t10, t11)
                    add_tri(p00, p11, p01, n00, n11, n01, t00, t11, t01)

        elif shape_type == "Prism":
            n = max(3, int(sectors))
            h0, h1 = -height / 2.0, height / 2.0

            # side
            for i in range(n):
                a0 = 2.0 * np.pi * i / n
                a1 = 2.0 * np.pi * (i + 1) / n
                c0, s0 = np.cos(a0), np.sin(a0)
                c1, s1 = np.cos(a1), np.sin(a1)

                p00 = [radius * c0, radius * s0, h0]
                p10 = [radius * c0, radius * s0, h1]
                p11 = [radius * c1, radius * s1, h1]
                p01 = [radius * c1, radius * s1, h0]

                # flat face normal from edge direction
                edge = np.array([p01[0] - p00[0], p01[1] - p00[1], 0.0])
                fn = norm([edge[1], -edge[0], 0.0])

                add_tri(p00, p10, p11, fn, fn, fn, [0, 0], [0, 1], [1, 1])
                add_tri(p00, p11, p01, fn, fn, fn, [0, 0], [1, 1], [1, 0])

            # bottom cap
            cb = [0, 0, h0]
            nb = [0, 0, -1]
            for i in range(n):
                a0 = 2.0 * np.pi * i / n
                a1 = 2.0 * np.pi * (i + 1) / n
                p0 = [radius * np.cos(a0), radius * np.sin(a0), h0]
                p1 = [radius * np.cos(a1), radius * np.sin(a1), h0]
                add_tri(cb, p1, p0, nb, nb, nb)

            # top cap
            ct = [0, 0, h1]
            nt = [0, 0, 1]
            for i in range(n):
                a0 = 2.0 * np.pi * i / n
                a1 = 2.0 * np.pi * (i + 1) / n
                p0 = [radius * np.cos(a0), radius * np.sin(a0), h1]
                p1 = [radius * np.cos(a1), radius * np.sin(a1), h1]
                add_tri(ct, p0, p1, nt, nt, nt)

        elif shape_type == "Heart":
            # Parametric heart surface.
            st = max(8, int(stacks))
            sc = max(12, int(sectors))

            # u wraps around [0, 2pi), v spans [0, 1]
            u_vals = np.linspace(0.0, 2.0 * np.pi, sc, endpoint=False)
            v_vals = np.linspace(0.0, 1.0, st)

            def heart_pos(u, v):
                sv = np.sin(np.pi * v)
                x = sv * (np.sin(u) ** 3)
                y = sv * (13.0 * np.cos(u) - 5.0 * np.cos(2.0 * u) - 2.0 * np.cos(3.0 * u) - np.cos(4.0 * u)) / 16.0
                z = 0.1 * np.cos(np.pi * v)
                # Keep height control intuitive in viewer by scaling z with height.
                z *= max(0.01, float(height))
                p = np.array([x, y, z], dtype=np.float64)
                return p * float(radius)

            def heart_normal(u, v):
                su = np.sin(u)
                cu = np.cos(u)
                sv = np.sin(np.pi * v)
                cv = np.cos(np.pi * v)

                # dP/du
                dx_du = sv * 3.0 * (su ** 2) * cu
                dy_du = sv * (-13.0 * np.sin(u) + 10.0 * np.sin(2.0 * u) + 6.0 * np.sin(3.0 * u) + 4.0 * np.sin(4.0 * u)) / 16.0
                dz_du = 0.0

                # dP/dv
                dx_dv = np.pi * cv * (su ** 3)
                dy_dv = np.pi * cv * (13.0 * np.cos(u) - 5.0 * np.cos(2.0 * u) - 2.0 * np.cos(3.0 * u) - np.cos(4.0 * u)) / 16.0
                dz_dv = -0.1 * np.pi * sv * max(0.01, float(height))

                du = np.array([dx_du, dy_du, dz_du], dtype=np.float64)
                dv = np.array([dx_dv, dy_dv, dz_dv], dtype=np.float64)
                n = np.cross(du, dv)
                nn = np.linalg.norm(n)
                if nn < 1e-10:
                    return np.array([0.0, 0.0, 1.0], dtype=np.float64)
                return n / nn

            for i in range(st - 1):
                v0 = v_vals[i]
                v1 = v_vals[i + 1]
                for j in range(sc):
                    jn = (j + 1) % sc
                    u0 = u_vals[j]
                    u1 = u_vals[jn]

                    p00 = heart_pos(u0, v0)
                    p01 = heart_pos(u1, v0)
                    p10 = heart_pos(u0, v1)
                    p11 = heart_pos(u1, v1)

                    n00 = heart_normal(u0, v0)
                    n01 = heart_normal(u1, v0)
                    n10 = heart_normal(u0, v1)
                    n11 = heart_normal(u1, v1)

                    t00 = [j / sc, i / (st - 1)]
                    t01 = [(j + 1) / sc, i / (st - 1)]
                    t10 = [j / sc, (i + 1) / (st - 1)]
                    t11 = [(j + 1) / sc, (i + 1) / (st - 1)]

                    add_tri(p00, p10, p11, n00, n10, n11, t00, t10, t11)
                    add_tri(p00, p11, p01, n00, n11, n01, t00, t11, t01)

        return np.array(vertices, dtype=np.float32), \
               np.array(normals, dtype=np.float32), \
               np.array(texcoords, dtype=np.float32)


class MeshDrawable:
    """Generic drawable for geometry generated by Geo2D/Geo3D or imported meshes."""

    MODE_FLAT = 0
    MODE_COLOR = 1
    MODE_LIGHTING = 2
    MODE_TEXTURE = 3
    MODE_COMBINED = 4

    def __init__(self, vertices, normals=None, texcoords=None, colors=None, primitive=GL.GL_TRIANGLES):
        self.vertices = np.asarray(vertices, dtype=np.float32)
        if self.vertices.ndim != 2 or self.vertices.shape[1] != 3:
            raise ValueError("vertices must have shape (N, 3)")

        count = self.vertices.shape[0]
        self.normals = np.asarray(normals, dtype=np.float32) if normals is not None else np.zeros((count, 3), dtype=np.float32)
        if self.normals.shape != (count, 3):
            self.normals = np.resize(self.normals, (count, 3)).astype(np.float32)

        self.texcoords = np.asarray(texcoords, dtype=np.float32) if texcoords is not None else np.zeros((count, 2), dtype=np.float32)
        if self.texcoords.shape != (count, 2):
            self.texcoords = np.resize(self.texcoords, (count, 2)).astype(np.float32)

        if colors is None:
            colors = self._default_colors_from_pos(self.vertices)
        self.colors = np.asarray(colors, dtype=np.float32)
        if self.colors.shape != (count, 3):
            self.colors = np.resize(self.colors, (count, 3)).astype(np.float32)

        self.primitive = primitive
        self.model = np.identity(4, dtype=np.float32)

        base = _btl_dir
        self.shader_color = Shader(str(base / "color_interp.vert"), str(base / "color_interp.frag"))
        self.shader_gouraud = Shader(str(base / "gouraud.vert"), str(base / "gouraud.frag"))
        self.shader_phong = Shader(str(base / "phong.vert"), str(base / "phong.frag"))
        self.shader_flat = Shader(self._flat_vertex_shader(), self._flat_fragment_shader())
        self.shader_texture = Shader(self._texture_vertex_shader(), self._texture_fragment_shader())
        self.shader_depth_prepass = Shader(self._depth_prepass_vertex_shader(), self._depth_prepass_fragment_shader())
        self.shader_depth_visual = Shader(self._depth_visual_vertex_shader(), self._depth_visual_fragment_shader())

        self.uma_flat = UManager(self.shader_flat)
        self.uma_color = UManager(self.shader_color)
        self.uma_gouraud = UManager(self.shader_gouraud)
        self.uma_phong = UManager(self.shader_phong)
        self.uma_texture = UManager(self.shader_texture)
        self.uma_depth_prepass = UManager(self.shader_depth_prepass)
        self.uma_depth_visual = UManager(self.shader_depth_visual)

        self.depth_fbo = None
        self.depth_texture = None
        self.depth_size = (0, 0)
        self.depth_colormap_mode = 0  # 0: grayscale, 1: heatmap

        self.lighting_gouraud = LightingManager(self.uma_gouraud)
        self.lighting_phong = LightingManager(self.uma_phong)
        self.lighting_texture = LightingManager(self.uma_texture)

        self.vao = VAO()
        self.vao.add_vbo(0, self.vertices, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(2, self.normals, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
        self.vao.add_vbo(3, self.texcoords, ncomponents=2, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)

        self.texture_path = None
        self.texture_ready = False
        self.flat_color = np.array([0.9, 0.6, 0.2], dtype=np.float32)
        self.material_override = None
        self.emissive_color = np.zeros(3, dtype=np.float32)
        self.emissive_strength = 0.0

    @staticmethod
    def _default_colors_from_pos(verts):
        mins = np.min(verts, axis=0)
        maxs = np.max(verts, axis=0)
        span = np.where((maxs - mins) < 1e-6, 1.0, (maxs - mins))
        colors = (verts - mins) / span
        return np.clip(colors, 0.0, 1.0).astype(np.float32)

    @staticmethod
    def _compose_modelview(view, model):
        mv = np.asarray(view, dtype=np.float32) @ np.asarray(model, dtype=np.float32)
        return mv.astype(np.float32)

    @staticmethod
    def _active_light(enabled, brightness):
        base_diff = np.array([0.9, 0.4, 0.6], dtype=np.float32)
        base_spec = np.array([0.8, 0.8, 0.8], dtype=np.float32)
        base_amb = np.array([0.35, 0.35, 0.35], dtype=np.float32)
        if not enabled:
            z = np.zeros(3, dtype=np.float32)
            return z, z, z
        return base_diff * brightness, base_spec * brightness, base_amb * brightness

    @staticmethod
    def _merge_lights(light1_enabled, light2_enabled, brightness):
        d1, s1, a1 = MeshDrawable._active_light(light1_enabled, brightness)
        d2, s2, a2 = MeshDrawable._active_light(light2_enabled, brightness * 0.8)
        diffuse = d1 + d2
        specular = s1 + s2
        ambient = a1 + a2
        # Keep values in shader-friendly range
        return np.clip(diffuse, 0.0, 2.0), np.clip(specular, 0.0, 2.0), np.clip(ambient, 0.0, 2.0)

    @staticmethod
    def _custom_light(enabled, position=None, color=None, intensity=1.0):
        if not enabled:
            z = np.zeros(3, dtype=np.float32)
            return False, z, z, z, z

        pos = np.asarray([0.0, 0.5, 0.9] if position is None else position, dtype=np.float32).reshape(3)
        col = np.asarray([1.0, 1.0, 1.0] if color is None else color, dtype=np.float32).reshape(3)
        gain = float(max(0.0, intensity))

        diffuse = np.clip(col * gain, 0.0, 4.0)
        specular = np.clip(col * gain, 0.0, 4.0)
        ambient = np.clip(col * (0.20 * gain), 0.0, 2.0)
        return True, pos, diffuse, specular, ambient

    @staticmethod
    def _surface_material(base_material, roughness=0.25, metallic=0.05):
        r = float(np.clip(roughness, 0.0, 1.0))
        m = float(np.clip(metallic, 0.0, 1.0))

        base_diff = np.asarray(base_material.diffuse, dtype=np.float32)
        base_spec = np.asarray(base_material.specular, dtype=np.float32)
        base_amb = np.asarray(base_material.ambient, dtype=np.float32)

        dielectric_f0 = np.array([0.04, 0.04, 0.04], dtype=np.float32)
        metal_f0 = np.clip(0.25 * base_spec + 0.75 * base_diff, 0.0, 1.0)

        specular = ((1.0 - m) * dielectric_f0 + m * metal_f0) * (1.0 - 0.75 * r)
        diffuse = base_diff * (1.0 - 0.65 * m) * (0.45 + 0.55 * (1.0 - r))
        ambient = base_amb * (0.7 + 0.3 * (1.0 - r)) * (1.0 - 0.35 * m)
        shininess = 8.0 + ((1.0 - r) ** 2) * 220.0

        return Material(
            diffuse=np.clip(diffuse, 0.0, 1.0),
            specular=np.clip(specular, 0.0, 1.0),
            ambient=np.clip(ambient, 0.0, 1.0),
            shininess=float(shininess),
        )

    def set_model(self, model):
        self.model = np.asarray(model, dtype=np.float32)

    def set_vertex_color(self, color_rgb):
        color = np.asarray(color_rgb, dtype=np.float32).reshape(3)
        self.colors = np.tile(color, (self.vertices.shape[0], 1)).astype(np.float32)
        self.vao.activate()
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vao.vbo[1])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self.colors, GL.GL_DYNAMIC_DRAW)
        self.vao.deactivate()

    def set_material(self, diffuse=None, specular=None, ambient=None, shininess=None):
        base = self.material_override if self.material_override is not None else LightingManager.DEFAULT_MATERIAL
        d = np.asarray(base.diffuse if diffuse is None else diffuse, dtype=np.float32)
        s = np.asarray(base.specular if specular is None else specular, dtype=np.float32)
        a = np.asarray(base.ambient if ambient is None else ambient, dtype=np.float32)
        sh = float(base.shininess if shininess is None else shininess)
        self.material_override = Material(diffuse=d, specular=s, ambient=a, shininess=sh)

    def set_emissive(self, color=None, strength=0.0):
        if color is None:
            self.emissive_color = np.zeros(3, dtype=np.float32)
            self.emissive_strength = 0.0
            return
        self.emissive_color = np.asarray(color, dtype=np.float32).reshape(3)
        self.emissive_strength = float(max(0.0, strength))

    def set_texture(self, texture_path):
        if not texture_path:
            self.texture_path = None
            self.texture_ready = False
            return
        p = Path(texture_path)
        if not p.is_absolute():
            p = _btl_dir / p
        if p.exists():
            self.texture_path = str(p)
            self.texture_ready = False

    def _ensure_texture(self):
        if self.texture_ready or not self.texture_path:
            return
        self.uma_texture.setup_texture("texture_diffuse", self.texture_path)
        self.texture_ready = True

    def _ensure_depth_fbo(self, width, height):
        w, h = int(max(1, width)), int(max(1, height))
        if self.depth_fbo is not None and self.depth_size == (w, h):
            return

        if self.depth_texture is not None:
            GL.glDeleteTextures([self.depth_texture])
            self.depth_texture = None
        if self.depth_fbo is not None:
            GL.glDeleteFramebuffers(1, [self.depth_fbo])
            self.depth_fbo = None

        self.depth_fbo = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.depth_fbo)

        self.depth_texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.depth_texture)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_DEPTH_COMPONENT24,
            w,
            h,
            0,
            GL.GL_DEPTH_COMPONENT,
            GL.GL_FLOAT,
            None,
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glFramebufferTexture2D(
            GL.GL_FRAMEBUFFER,
            GL.GL_DEPTH_ATTACHMENT,
            GL.GL_TEXTURE_2D,
            self.depth_texture,
            0,
        )

        GL.glDrawBuffer(GL.GL_NONE)
        GL.glReadBuffer(GL.GL_NONE)

        status = GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)
        if status != GL.GL_FRAMEBUFFER_COMPLETE:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            raise RuntimeError(f"Depth FBO incomplete: {status}")

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        self.depth_size = (w, h)

    def _upload_common(self, uma, projection, modelview):
        uma.upload_uniform_matrix4fv(np.asarray(projection, dtype=np.float32), 'projection', True)
        uma.upload_uniform_matrix4fv(np.asarray(modelview, dtype=np.float32), 'modelview', True)

    def draw(self, projection, view, model=None,
             shading_mode=MODE_LIGHTING,
             alpha_override=1.0,
             flat_color_override=None,
             lighting_algorithm='phong',
             light_1_enabled=True,
             light_2_enabled=False,
             brightness=1.0,
             hdri_environment_enabled=False,
             hdri_environment_intensity=0.55,
             hdri_environment_color=None,
             custom_light_enabled=False,
             custom_light_position=None,
             custom_light_color=None,
             custom_light_intensity=1.0,
             material_roughness=0.25,
             material_metallic=0.05,
             material_override=None,
             emissive_color=None,
             emissive_strength=None,
             show_depth_map=False,
             near_plane=0.1,
             far_plane=100.0,
             is_orthographic=False,
             depth_colormap_mode=None):
        use_model = self.model if model is None else np.asarray(model, dtype=np.float32)
        modelview = self._compose_modelview(view, use_model)
        alpha = float(np.clip(alpha_override, 0.0, 1.0))
        hdri_color = np.asarray([1.0, 1.0, 1.0] if hdri_environment_color is None else hdri_environment_color, dtype=np.float32).reshape(3)
        hdri_intensity = float(max(0.0, hdri_environment_intensity))

        self.vao.activate()
        if show_depth_map:
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            vx, vy, vw, vh = int(viewport[0]), int(viewport[1]), int(viewport[2]), int(viewport[3])
            self._ensure_depth_fbo(vw, vh)

            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.depth_fbo)
            GL.glViewport(0, 0, vw, vh)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

            GL.glUseProgram(self.shader_depth_prepass.render_idx)
            self._upload_common(self.uma_depth_prepass, projection, modelview)
            GL.glDrawArrays(self.primitive, 0, self.vertices.shape[0])

            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            GL.glViewport(vx, vy, vw, vh)

            GL.glUseProgram(self.shader_depth_visual.render_idx)
            self._upload_common(self.uma_depth_visual, projection, modelview)
            mode = int(self.depth_colormap_mode if depth_colormap_mode is None else depth_colormap_mode)
            self.uma_depth_visual.upload_uniform_scalar1f(float(max(1e-4, near_plane)), 'u_near')
            self.uma_depth_visual.upload_uniform_scalar1f(float(max(float(near_plane) + 1e-4, far_plane)), 'u_far')
            self.uma_depth_visual.upload_uniform_scalar1f(float(vw), 'u_view_w')
            self.uma_depth_visual.upload_uniform_scalar1f(float(vh), 'u_view_h')
            self.uma_depth_visual.upload_uniform_scalar1f(float(mode), 'u_color_mode')
            self.uma_depth_visual.upload_uniform_scalar1f(1.0 if is_orthographic else 0.0, 'u_is_ortho')
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.depth_texture)
            GL.glUniform1i(GL.glGetUniformLocation(self.shader_depth_visual.render_idx, 'u_depth_tex'), 0)

            GL.glDrawArrays(self.primitive, 0, self.vertices.shape[0])
            self.vao.deactivate()
            return

        if shading_mode == self.MODE_FLAT:
            GL.glUseProgram(self.shader_flat.render_idx)
            self._upload_common(self.uma_flat, projection, modelview)
            flat_color = self.flat_color if flat_color_override is None else np.asarray(flat_color_override, dtype=np.float32).reshape(3)
            self.uma_flat.upload_uniform_vector3fv(flat_color, 'u_color')
            self.uma_flat.upload_uniform_scalar1f(alpha, 'u_alpha')

        elif shading_mode == self.MODE_COLOR:
            GL.glUseProgram(self.shader_color.render_idx)
            self._upload_common(self.uma_color, projection, modelview)
            self.uma_color.upload_uniform_scalar1f(alpha, 'u_alpha')

        elif shading_mode == self.MODE_LIGHTING:
            use_gouraud = str(lighting_algorithm).lower().startswith('g')
            c_enabled, c_pos, c_diff, c_spec, c_amb = self._custom_light(
                custom_light_enabled,
                custom_light_position,
                custom_light_color,
                custom_light_intensity,
            )
            if use_gouraud:
                GL.glUseProgram(self.shader_gouraud.render_idx)
                self._upload_common(self.uma_gouraud, projection, modelview)
                d, s, a = self._merge_lights(light_1_enabled, light_2_enabled, brightness)
                light = LightingManager.DEFAULT_LIGHT
                mat = material_override if material_override is not None else self.material_override
                if mat is None:
                    mat = LightingManager.DEFAULT_MATERIAL
                mat = self._surface_material(mat, roughness=material_roughness, metallic=material_metallic)
                light.diffuse = d
                light.specular = s
                light.ambient = a
                self.lighting_gouraud.setup_gouraud(light=light, material=mat, shininess=float(mat.shininess))
                self.uma_gouraud.upload_uniform_scalar1i(1 if c_enabled else 0, 'custom_light_enabled')
                self.uma_gouraud.upload_uniform_vector3fv(c_pos, 'custom_light_pos')
                self.uma_gouraud.upload_uniform_vector3fv(c_diff, 'custom_light_diffuse')
                self.uma_gouraud.upload_uniform_vector3fv(c_spec, 'custom_light_specular')
                self.uma_gouraud.upload_uniform_vector3fv(c_amb, 'custom_light_ambient')
                self.uma_gouraud.upload_uniform_scalar1i(1 if hdri_environment_enabled else 0, 'hdri_environment_enabled')
                self.uma_gouraud.upload_uniform_vector3fv(hdri_color, 'hdri_environment_color')
                self.uma_gouraud.upload_uniform_scalar1f(hdri_intensity, 'hdri_environment_intensity')
                self.uma_gouraud.upload_uniform_scalar1f(alpha, 'u_alpha')
            else:
                GL.glUseProgram(self.shader_phong.render_idx)
                self._upload_common(self.uma_phong, projection, modelview)
                d, s, a = self._merge_lights(light_1_enabled, light_2_enabled, brightness)
                light = LightingManager.DEFAULT_LIGHT
                mat = material_override if material_override is not None else self.material_override
                if mat is None:
                    mat = LightingManager.DEFAULT_MATERIAL
                mat = self._surface_material(mat, roughness=material_roughness, metallic=material_metallic)
                light.diffuse = d
                light.specular = s
                light.ambient = a
                self.lighting_phong.setup_phong(light=light, material=mat, mode=1)
                self.uma_phong.upload_uniform_scalar1i(1 if c_enabled else 0, 'custom_light_enabled')
                self.uma_phong.upload_uniform_vector3fv(c_pos, 'custom_light_pos')
                self.uma_phong.upload_uniform_vector3fv(c_diff, 'custom_light_diffuse')
                self.uma_phong.upload_uniform_vector3fv(c_spec, 'custom_light_specular')
                self.uma_phong.upload_uniform_vector3fv(c_amb, 'custom_light_ambient')
                self.uma_phong.upload_uniform_scalar1i(1 if hdri_environment_enabled else 0, 'hdri_environment_enabled')
                self.uma_phong.upload_uniform_vector3fv(hdri_color, 'hdri_environment_color')
                self.uma_phong.upload_uniform_scalar1f(hdri_intensity, 'hdri_environment_intensity')
                active_emissive = self.emissive_color if emissive_color is None else np.asarray(emissive_color, dtype=np.float32).reshape(3)
                active_strength = self.emissive_strength if emissive_strength is None else float(emissive_strength)
                self.uma_phong.upload_uniform_vector3fv(active_emissive, 'emissive_color')
                self.uma_phong.upload_uniform_scalar1f(max(0.0, active_strength), 'emissive_strength')
                self.uma_phong.upload_uniform_scalar1f(alpha, 'u_alpha')

        elif shading_mode in (self.MODE_TEXTURE, self.MODE_COMBINED):
            self._ensure_texture()
            GL.glUseProgram(self.shader_texture.render_idx)
            self._upload_common(self.uma_texture, projection, modelview)
            d, s, a = self._merge_lights(light_1_enabled, light_2_enabled, brightness)
            c_enabled, c_pos, c_diff, c_spec, c_amb = self._custom_light(
                custom_light_enabled,
                custom_light_position,
                custom_light_color,
                custom_light_intensity,
            )
            light = LightingManager.DEFAULT_LIGHT
            mat = self._surface_material(LightingManager.DEFAULT_MATERIAL, roughness=material_roughness, metallic=material_metallic)
            light.diffuse = d
            light.specular = s
            light.ambient = a
            self.lighting_texture.setup_phong(light=light, material=mat, mode=1)
            self.uma_texture.upload_uniform_scalar1i(1 if c_enabled else 0, 'custom_light_enabled')
            self.uma_texture.upload_uniform_vector3fv(c_pos, 'custom_light_pos')
            self.uma_texture.upload_uniform_vector3fv(c_diff, 'custom_light_diffuse')
            self.uma_texture.upload_uniform_vector3fv(c_spec, 'custom_light_specular')
            self.uma_texture.upload_uniform_vector3fv(c_amb, 'custom_light_ambient')
            self.uma_texture.upload_uniform_scalar1i(1 if hdri_environment_enabled else 0, 'hdri_environment_enabled')
            self.uma_texture.upload_uniform_vector3fv(hdri_color, 'hdri_environment_color')
            self.uma_texture.upload_uniform_scalar1f(hdri_intensity, 'hdri_environment_intensity')
            self.uma_texture.upload_uniform_scalar1f(alpha, 'u_alpha')
            if shading_mode == self.MODE_TEXTURE:
                self.uma_texture.upload_uniform_scalar1f(0.0, 'color_factor')
                self.uma_texture.upload_uniform_scalar1f(0.0, 'phong_factor')
            else:
                self.uma_texture.upload_uniform_scalar1f(0.25, 'color_factor')
                self.uma_texture.upload_uniform_scalar1f(0.35, 'phong_factor')

        GL.glDrawArrays(self.primitive, 0, self.vertices.shape[0])
        self.vao.deactivate()

    @staticmethod
    def _flat_vertex_shader():
        return """
#version 330 core
layout(location = 0) in vec3 position;
uniform mat4 projection;
uniform mat4 modelview;
void main(){
    gl_Position = projection * modelview * vec4(position, 1.0);
}
"""

    @staticmethod
    def _flat_fragment_shader():
        return """
#version 330 core
uniform vec3 u_color;
uniform float u_alpha;
out vec4 out_color;
void main(){
    out_color = vec4(u_color, u_alpha);
}
"""

    @staticmethod
    def _depth_prepass_vertex_shader():
        return """
#version 330 core
layout(location = 0) in vec3 position;
uniform mat4 projection;
uniform mat4 modelview;
void main(){
    gl_Position = projection * modelview * vec4(position, 1.0);
}
"""

    @staticmethod
    def _depth_prepass_fragment_shader():
        return """
#version 330 core
void main(){ }
"""

    @staticmethod
    def _depth_visual_vertex_shader():
        return """
#version 330 core
layout(location = 0) in vec3 position;
uniform mat4 projection;
uniform mat4 modelview;
void main(){
    gl_Position = projection * modelview * vec4(position, 1.0);
}
"""

    @staticmethod
    def _depth_visual_fragment_shader():
        return """
#version 330 core
uniform sampler2D u_depth_tex;
uniform float u_near;
uniform float u_far;
uniform float u_view_w;
uniform float u_view_h;
uniform float u_color_mode; // 0 grayscale, 1 heatmap
uniform float u_is_ortho;   // 1 when orthographic projection

out vec4 out_color;

float linearize_depth(float d) {
    if (u_is_ortho > 0.5) {
        return clamp(d, 0.0, 1.0);
    }
    float z = d * 2.0 - 1.0;
    float linear = (2.0 * u_near * u_far) / (u_far + u_near - z * (u_far - u_near));
    return clamp((linear - u_near) / max(1e-6, (u_far - u_near)), 0.0, 1.0);
}

vec3 heatmap(float t) {
    t = clamp(t, 0.0, 1.0);
    vec3 c1 = vec3(0.10, 0.20, 0.85);
    vec3 c2 = vec3(0.20, 0.85, 0.95);
    vec3 c3 = vec3(0.95, 0.90, 0.20);
    vec3 c4 = vec3(0.90, 0.20, 0.10);
    if (t < 0.33) return mix(c1, c2, t / 0.33);
    if (t < 0.66) return mix(c2, c3, (t - 0.33) / 0.33);
    return mix(c3, c4, (t - 0.66) / 0.34);
}

void main(){
    vec2 uv = vec2(gl_FragCoord.x / max(1.0, u_view_w), gl_FragCoord.y / max(1.0, u_view_h));
    float d = texture(u_depth_tex, uv).r;
    float z01 = linearize_depth(d);
    vec3 color = (u_color_mode > 0.5) ? heatmap(z01) : vec3(z01);
    out_color = vec4(color, 1.0);
}
"""

    @staticmethod
    def _texture_vertex_shader():
        return """
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;
layout(location = 2) in vec3 normal;
layout(location = 3) in vec2 texcoord;

uniform mat4 projection;
uniform mat4 modelview;

out vec3 v_color;
out vec3 v_normal;
out vec3 v_pos;
out vec2 v_uv;

void main(){
    vec4 world = modelview * vec4(position, 1.0);
    v_pos = vec3(world) / world.w;
    mat4 normal_matrix = transpose(inverse(modelview));
    v_normal = normalize(vec3(normal_matrix * vec4(normal, 0.0)));
    v_color = color;
    v_uv = texcoord;
    gl_Position = projection * world;
}
"""

    @staticmethod
    def _texture_fragment_shader():
        return """
#version 330 core
in vec3 v_color;
in vec3 v_normal;
in vec3 v_pos;
in vec2 v_uv;

uniform mat3 K_materials;
uniform mat3 I_light;
uniform vec3 light_pos;
uniform int custom_light_enabled;
uniform vec3 custom_light_pos;
uniform vec3 custom_light_diffuse;
uniform vec3 custom_light_specular;
uniform vec3 custom_light_ambient;
uniform int hdri_environment_enabled;
uniform vec3 hdri_environment_color;
uniform float hdri_environment_intensity;
uniform float shininess;
uniform float color_factor;
uniform float phong_factor;
uniform float u_alpha;
uniform sampler2D texture_diffuse;

out vec4 fragColor;

void main(){
    vec3 N = normalize(v_normal);
    vec3 L = normalize(light_pos - v_pos);
    vec3 V = normalize(-v_pos);
    vec3 R = reflect(-L, N);
    float spec = pow(max(dot(R, V), 0.0), shininess);
    vec3 g = vec3(max(dot(L, N), 0.0), spec, 1.0);
    vec3 phong = matrixCompMult(K_materials, I_light) * g;
    if (custom_light_enabled != 0) {
        vec3 L2 = normalize(custom_light_pos - v_pos);
        vec3 R2 = reflect(-L2, N);
        float spec2 = pow(max(dot(R2, V), 0.0), shininess);
        vec3 g2 = vec3(max(dot(L2, N), 0.0), spec2, 1.0);
        mat3 I_custom = mat3(custom_light_diffuse, custom_light_specular, custom_light_ambient);
        phong += matrixCompMult(K_materials, I_custom) * g2;
    }
    if (hdri_environment_enabled != 0) {
        vec3 env = K_materials[2] * hdri_environment_color * hdri_environment_intensity;
        phong += env;
    }
    vec3 tex = texture(texture_diffuse, v_uv).rgb;
    float texture_factor = max(0.0, 1.0 - color_factor - phong_factor);
    vec3 rgb = color_factor * v_color + phong_factor * phong + texture_factor * tex;
    fragColor = vec4(rgb, u_alpha);
}
"""


def create_geo2d_drawable(shape_type, radius=1.0, width=1.0, height=1.0, segments=64):
    v, n, t = Geo2D.generate(shape_type, radius=radius, width=width, height=height, segments=segments)
    colors = MeshDrawable._default_colors_from_pos(v)
    return MeshDrawable(v, n, t, colors, primitive=GL.GL_TRIANGLE_FAN)


def create_geo3d_drawable(shape_type, radius=1.0, height=2.0, sectors=36, stacks=18, inner_radius=0.3):
    v, n, t = Geo3D.generate(shape_type, radius=radius, height=height, sectors=sectors, stacks=stacks, inner_radius=inner_radius)
    colors = MeshDrawable._default_colors_from_pos(v)
    return MeshDrawable(v, n, t, colors, primitive=GL.GL_TRIANGLES)


def create_math_surface_drawable(func_expr, x_min=-2.0, x_max=2.0, y_min=-2.0, y_max=2.0, steps=60):
    func_expr = (func_expr or "").strip()
    if not func_expr:
        raise ValueError("Expression is empty")
    func_expr = func_expr.replace("^", "**")
    safe_names = {
        'np': np,
        'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
        'asin': np.arcsin, 'acos': np.arccos, 'atan': np.arctan,
        'sinh': np.sinh, 'cosh': np.cosh, 'tanh': np.tanh,
        'exp': np.exp, 'sqrt': np.sqrt, 'log': np.log, 'log10': np.log10,
        'abs': np.abs, 'pow': np.power,
        'pi': np.pi, 'e': np.e,
    }
    

    # Basic expression validation to keep eval usage constrained.
    tree = ast.parse(func_expr, mode='eval')
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Name, ast.Load,
        ast.Call, ast.Attribute, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
        ast.USub, ast.UAdd, ast.Mod, ast.Constant,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError("Unsupported expression syntax")

    steps = max(4, int(steps))
    xs = np.linspace(float(x_min), float(x_max), steps, dtype=np.float64)
    ys = np.linspace(float(y_min), float(y_max), steps, dtype=np.float64)
    xg, yg = np.meshgrid(xs, ys, indexing='ij')

    compiled = compile(tree, '<expr>', 'eval')
    z_eval = eval(compiled, {'__builtins__': {}}, {**safe_names, 'x': xg, 'y': yg})
    z = np.asarray(z_eval, dtype=np.float64)
    if z.shape == ():
        z = np.full_like(xg, float(z), dtype=np.float64)
    elif z.shape != xg.shape:
        raise ValueError(f"Expression output shape mismatch: got {z.shape}, expected {xg.shape}")

    z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)

    dz_dx, dz_dy = np.gradient(z, xs, ys, edge_order=2)
    nx = -dz_dx
    ny = -dz_dy
    nz = np.ones_like(z)
    nlen = np.sqrt(nx * nx + ny * ny + nz * nz)
    nlen = np.where(nlen < 1e-8, 1.0, nlen)
    nx /= nlen
    ny /= nlen
    nz /= nlen

    z_min = float(np.min(z))
    z_max = float(np.max(z))
    span = max(1e-12, z_max - z_min)
    t = np.clip((z - z_min) / span, 0.0, 1.0)
    colors_grid = np.stack((t, 0.25 + 0.7 * (1.0 - np.abs(2.0 * t - 1.0)), 1.0 - t), axis=-1)

    u = np.linspace(0.0, 1.0, steps, dtype=np.float64)
    v = np.linspace(0.0, 1.0, steps, dtype=np.float64)
    ug, vg = np.meshgrid(u, v, indexing='ij')

    verts_grid = np.stack((xg, yg, z), axis=-1).astype(np.float32)
    norms_grid = np.stack((nx, ny, nz), axis=-1).astype(np.float32)
    tex_grid = np.stack((ug, vg), axis=-1).astype(np.float32)
    cols_grid = colors_grid.astype(np.float32)

    i, j = np.meshgrid(np.arange(steps - 1, dtype=np.int32), np.arange(steps - 1, dtype=np.int32), indexing='ij')
    i00 = i * steps + j
    i10 = (i + 1) * steps + j
    i11 = (i + 1) * steps + (j + 1)
    i01 = i * steps + (j + 1)

    tri1 = np.stack((i00, i10, i11), axis=-1).reshape(-1, 3)
    tri2 = np.stack((i00, i11, i01), axis=-1).reshape(-1, 3)
    indices = np.concatenate((tri1, tri2), axis=0).astype(np.int32)

    flat_vertices = verts_grid.reshape(-1, 3)
    flat_normals = norms_grid.reshape(-1, 3)
    flat_texcoords = tex_grid.reshape(-1, 2)
    flat_colors = cols_grid.reshape(-1, 3)

    tri_vertices = flat_vertices[indices.reshape(-1)]
    tri_normals = flat_normals[indices.reshape(-1)]
    tri_texcoords = flat_texcoords[indices.reshape(-1)]
    tri_colors = flat_colors[indices.reshape(-1)]

    return MeshDrawable(
        tri_vertices.astype(np.float32),
        tri_normals.astype(np.float32),
        tri_texcoords.astype(np.float32),
        colors=tri_colors.astype(np.float32),
        primitive=GL.GL_TRIANGLES,
    )


def create_loss_surface_drawable(
    loss_type,
    x_min=-30.0,
    x_max=30.0,
    y_min=-30.0,
    y_max=30.0,
    resolution=100,
):
    """
    Create a MeshDrawable for a predefined loss function surface.

    The mesh generator returns indexed arrays (vertex/index buffers).
    Current renderer path uses glDrawArrays, so we expand indices to
    per-triangle arrays before constructing MeshDrawable.
    """
    if isinstance(loss_type, str):
        key = loss_type.strip().upper()
        if key in LossFunctionType.__members__:
            loss_type = LossFunctionType[key]
        else:
            normalized = loss_type.strip().lower()
            matches = [lt for lt in LossFunctionType if lt.value == normalized]
            if not matches:
                raise ValueError(f"Unknown loss type: {loss_type}")
            loss_type = matches[0]

    mesh = LossSurfaceMeshGenerator.generate(
        loss_type=loss_type,
        x_min=float(x_min),
        x_max=float(x_max),
        y_min=float(y_min),
        y_max=float(y_max),
        resolution=resolution,
    )
    tri_vertices, tri_normals, tri_colors, tri_texcoords = LossSurfaceMeshGenerator.expand_indexed_triangles(mesh)

    tri_vertices = np.nan_to_num(np.asarray(tri_vertices, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    tri_normals = np.nan_to_num(np.asarray(tri_normals, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    tri_texcoords = np.nan_to_num(np.asarray(tri_texcoords, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    tri_colors = np.nan_to_num(np.asarray(tri_colors, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)

    return MeshDrawable(
        tri_vertices,
        tri_normals,
        tri_texcoords,
        colors=tri_colors,
        primitive=GL.GL_TRIANGLES,
    )


def _triangulate_faces(face):
    if len(face) < 3:
        return []
    if len(face) == 3:
        return [face]
    tris = []
    for i in range(1, len(face) - 1):
        tris.append([face[0], face[i], face[i + 1]])
    return tris


def create_drawable_from_file(mesh_path):
    raw_path = Path(mesh_path).expanduser()
    candidates = []
    if raw_path.exists():
        if raw_path.suffix.lower() == '.obj':
            return _load_obj_drawable(raw_path)
        if raw_path.suffix.lower() == '.ply':
            return _load_ply_drawable(raw_path)     
    else:
        candidates.extend([
            Path.cwd() / raw_path,
            _btl_dir / raw_path,
            _project_root / raw_path,
        ])

    path = None
    for cand in candidates:
        resolved = cand.resolve()
        if resolved.exists() and resolved.is_file():
            path = resolved
            break

    if path is None:
        searched = " | ".join(str(c.resolve()) for c in candidates)
        raise FileNotFoundError(f"Mesh file not found: {mesh_path}. Searched: {searched}")
    print(path)
    if path.suffix.lower() == '.obj':
        return _load_obj_drawable(path)
    if path.suffix.lower() == '.ply':
        return _load_ply_drawable(path)
    raise ValueError("Only .obj and .ply are supported")


def _load_obj_drawable(path):
    base_positions = []
    base_normals = []
    base_texcoords = []
    faces = []

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if parts[0] == 'v' and len(parts) >= 4:
                base_positions.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == 'vn' and len(parts) >= 4:
                base_normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == 'vt' and len(parts) >= 3:
                base_texcoords.append([float(parts[1]), float(parts[2])])
            elif parts[0] == 'f' and len(parts) >= 4:
                face = []
                for item in parts[1:]:
                    vals = item.split('/')
                    vi = int(vals[0]) - 1 if vals[0] else -1
                    ti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else -1
                    ni = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else -1
                    face.append((vi, ti, ni))
                faces.extend(_triangulate_faces(face))

    vertices = []
    normals = []
    texcoords = []
    for tri in faces:
        tri_positions = []
        for vi, ti, ni in tri:
            p = np.array(base_positions[vi], dtype=np.float32)
            t = np.array(base_texcoords[ti], dtype=np.float32) if ti >= 0 and ti < len(base_texcoords) else np.array([0.0, 0.0], dtype=np.float32)
            if ni >= 0 and ni < len(base_normals):
                n = np.array(base_normals[ni], dtype=np.float32)
            else:
                n = None
            vertices.append(p.tolist())
            texcoords.append(t.tolist())
            normals.append(n.tolist() if n is not None else [0.0, 0.0, 0.0])
            tri_positions.append(p)
        if np.linalg.norm(normals[-1]) < 1e-8:
            fn = np.cross(tri_positions[1] - tri_positions[0], tri_positions[2] - tri_positions[0])
            fnn = np.linalg.norm(fn)
            fn = (fn / fnn) if fnn > 1e-8 else np.array([0.0, 0.0, 1.0], dtype=np.float32)
            normals[-3:] = [fn.tolist(), fn.tolist(), fn.tolist()]

    return MeshDrawable(np.array(vertices, dtype=np.float32),
                        np.array(normals, dtype=np.float32),
                        np.array(texcoords, dtype=np.float32),
                        primitive=GL.GL_TRIANGLES)


def _load_ply_drawable(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    if not lines or lines[0].strip() != 'ply':
        raise ValueError('Invalid PLY file')

    vertex_count = 0
    face_count = 0
    header_end = -1
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('element vertex'):
            vertex_count = int(s.split()[-1])
        elif s.startswith('element face'):
            face_count = int(s.split()[-1])
        elif s == 'end_header':
            header_end = i
            break

    if header_end < 0:
        raise ValueError('PLY header is missing end_header')

    vstart = header_end + 1
    vend = vstart + vertex_count
    positions = []
    for line in lines[vstart:vend]:
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        positions.append([float(parts[0]), float(parts[1]), float(parts[2])])

    faces = []
    fstart = vend
    fend = fstart + face_count
    for line in lines[fstart:fend]:
        parts = line.strip().split()
        if not parts:
            continue
        n = int(parts[0])
        idxs = [int(x) for x in parts[1:1 + n]]
        faces.extend(_triangulate_faces([(i, -1, -1) for i in idxs]))

    vertices = []
    normals = []
    texcoords = []
    for tri in faces:
        p0 = np.array(positions[tri[0][0]], dtype=np.float32)
        p1 = np.array(positions[tri[1][0]], dtype=np.float32)
        p2 = np.array(positions[tri[2][0]], dtype=np.float32)
        fn = np.cross(p1 - p0, p2 - p0)
        fnn = np.linalg.norm(fn)
        fn = (fn / fnn) if fnn > 1e-8 else np.array([0.0, 0.0, 1.0], dtype=np.float32)
        vertices.extend([p0.tolist(), p1.tolist(), p2.tolist()])
        normals.extend([fn.tolist(), fn.tolist(), fn.tolist()])
        texcoords.extend([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]])

    return MeshDrawable(np.array(vertices, dtype=np.float32),
                        np.array(normals, dtype=np.float32),
                        np.array(texcoords, dtype=np.float32),
                        primitive=GL.GL_TRIANGLES)