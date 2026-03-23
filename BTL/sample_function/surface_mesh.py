from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .loss_functions import LossFunctionManager, LossFunctionType


@dataclass(frozen=True)
class SurfaceMeshData:
    """Indexed grid mesh data for rendering a loss surface."""

    vertices: np.ndarray   # (N, 3)
    normals: np.ndarray    # (N, 3)
    colors: np.ndarray     # (N, 3)
    texcoords: np.ndarray  # (N, 2)
    indices: np.ndarray    # (M,) flat uint32 triangle index buffer
    grid_shape: Tuple[int, int]  # (nx, ny)
    z_range: Tuple[float, float]  # (z_min, z_max)


class LossSurfaceMeshGenerator:
    """Generate a 2D regular grid surface z=f(x, y) with colors and normals."""

    @staticmethod
    def heatmap_color(z: float, z_min: float, z_max: float) -> np.ndarray:
        """
        Map z to RGB in [0,1] using a simple heatmap:
        blue -> cyan -> green -> yellow -> red.
        """
        span = max(z_max - z_min, 1e-12)
        t = float(np.clip((z - z_min) / span, 0.0, 1.0))

        # Piecewise linear interpolation with 4 segments.
        stops = np.array([
            [0.0, 0.0, 1.0],  # blue
            [0.0, 1.0, 1.0],  # cyan
            [0.0, 1.0, 0.0],  # green
            [1.0, 1.0, 0.0],  # yellow
            [1.0, 0.0, 0.0],  # red
        ], dtype=np.float64)

        scaled = t * 4.0
        idx = min(int(scaled), 3)
        local_t = scaled - idx
        c0 = stops[idx]
        c1 = stops[idx + 1]
        return (1.0 - local_t) * c0 + local_t * c1

    @staticmethod
    def _normalize(v: np.ndarray) -> np.ndarray:
        n = float(np.linalg.norm(v))
        if n < 1e-12:
            return np.array([0.0, 0.0, 1.0], dtype=np.float64)
        return v / n

    @classmethod
    def generate(
        cls,
        loss_type: LossFunctionType,
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        resolution: int | tuple[int, int] = 80,
    ) -> SurfaceMeshData:
        """
        Build indexed mesh arrays for the selected loss function.

        Args:
            loss_type: Target loss function enum.
            x_min, x_max: X range.
            y_min, y_max: Y range.
            resolution: int for uniform grid or (nx, ny).
        """
        if isinstance(resolution, int):
            nx = ny = max(2, int(resolution))
        else:
            nx = max(2, int(resolution[0]))
            ny = max(2, int(resolution[1]))

        if x_max <= x_min or y_max <= y_min:
            raise ValueError("Invalid coordinate range")

        xs = np.linspace(x_min, x_max, nx, dtype=np.float64)
        ys = np.linspace(y_min, y_max, ny, dtype=np.float64)

        count = nx * ny
        vertices = np.zeros((count, 3), dtype=np.float64)
        normals = np.zeros((count, 3), dtype=np.float64)
        colors = np.zeros((count, 3), dtype=np.float64)
        texcoords = np.zeros((count, 2), dtype=np.float64)

        z_values = np.zeros(count, dtype=np.float64)

        # 1) Evaluate surface and analytical-gradient normals at grid vertices.
        # Surface paramization: S(x, y) = (x, y, f(x,y))
        # Normal from tangents Tx=(1,0,fx), Ty=(0,1,fy): n = normalize([-fx, -fy, 1]).
        idx = 0
        for i, x in enumerate(xs):
            u = i / float(nx - 1)
            for j, y in enumerate(ys):
                v = j / float(ny - 1)
                z = LossFunctionManager.evaluate(loss_type, float(x), float(y))
                grad = LossFunctionManager.gradient(loss_type, float(x), float(y))
                fx, fy = float(grad[0]), float(grad[1])

                vertices[idx] = [x, y, z]
                normals[idx] = cls._normalize(np.array([-fx, -fy, 1.0], dtype=np.float64))
                texcoords[idx] = [u, v]
                z_values[idx] = z
                idx += 1

        z_min = float(np.min(z_values))
        z_max = float(np.max(z_values))

        for k in range(count):
            colors[k] = cls.heatmap_color(float(vertices[k, 2]), z_min, z_max)

        # 2) Build triangle index buffer (2 triangles per cell).
        tri_count = (nx - 1) * (ny - 1) * 2
        indices = np.zeros(tri_count * 3, dtype=np.uint32)
        t = 0
        for i in range(nx - 1):
            for j in range(ny - 1):
                i00 = i * ny + j
                i10 = (i + 1) * ny + j
                i11 = (i + 1) * ny + (j + 1)
                i01 = i * ny + (j + 1)

                # CCW when viewed from +Z on flat plane.
                indices[t:t + 3] = [i00, i10, i11]
                indices[t + 3:t + 6] = [i00, i11, i01]
                t += 6

        return SurfaceMeshData(
            vertices=vertices.astype(np.float32),
            normals=normals.astype(np.float32),
            colors=colors.astype(np.float32),
            texcoords=texcoords.astype(np.float32),
            indices=indices,
            grid_shape=(nx, ny),
            z_range=(z_min, z_max),
        )

    @staticmethod
    def expand_indexed_triangles(mesh: SurfaceMeshData) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Expand indexed mesh into triangle lists for renderers using glDrawArrays."""
        tri_vertices = mesh.vertices[mesh.indices]
        tri_normals = mesh.normals[mesh.indices]
        tri_colors = mesh.colors[mesh.indices]
        tri_texcoords = mesh.texcoords[mesh.indices]
        return tri_vertices, tri_normals, tri_colors, tri_texcoords
