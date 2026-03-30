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

    Z_LOG_SCALE = 1.0

    @staticmethod
    def _map_color(t: float, stops: np.ndarray) -> np.ndarray:
        t = float(np.clip(t, 0.0, 1.0))
        n = int(stops.shape[0])
        if n <= 1:
            return np.array(stops[0], dtype=np.float64)
        scaled = t * float(n - 1)
        idx = min(int(scaled), n - 2)
        local_t = scaled - float(idx)
        c0 = stops[idx]
        c1 = stops[idx + 1]
        return (1.0 - local_t) * c0 + local_t * c1

    @classmethod
    def inferno_color(cls, z: float, z_min: float, z_max: float) -> np.ndarray:
        span = max(z_max - z_min, 1e-12)
        t = (float(z) - float(z_min)) / span
        stops = np.array([
            [0.00, 0.00, 0.02],
            [0.17, 0.04, 0.34],
            [0.44, 0.11, 0.43],
            [0.71, 0.22, 0.35],
            [0.90, 0.38, 0.18],
            [0.98, 0.64, 0.22],
            [0.99, 0.88, 0.64],
        ], dtype=np.float64)
        return cls._map_color(t, stops)

    @classmethod
    def viridis_color(cls, z: float, z_min: float, z_max: float) -> np.ndarray:
        span = max(z_max - z_min, 1e-12)
        t = (float(z) - float(z_min)) / span
        stops = np.array([
            [0.27, 0.00, 0.33],
            [0.23, 0.32, 0.55],
            [0.13, 0.57, 0.55],
            [0.37, 0.78, 0.38],
            [0.99, 0.91, 0.14],
        ], dtype=np.float64)
        return cls._map_color(t, stops)

    @classmethod
    def display_z(cls, z_raw: float) -> float:
        """Render-only Z transform: z' = log(1 + f(x,y))."""
        z = max(0.0, float(z_raw))
        return float(cls.Z_LOG_SCALE * np.log1p(z))

    @classmethod
    def display_slopes(cls, z_raw: float, fx_raw: float, fy_raw: float) -> tuple[float, float]:
        """Derivatives for z' = s*log(1 + z), with z clamped at 0 for stability."""
        z = float(z_raw)
        if z <= 0.0:
            return 0.0, 0.0
        scale = float(cls.Z_LOG_SCALE) / max(1e-9, (1.0 + z))
        return float(scale * fx_raw), float(scale * fy_raw)

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

        x_values = np.zeros(count, dtype=np.float64)
        y_values = np.zeros(count, dtype=np.float64)
        u_values = np.zeros(count, dtype=np.float64)
        v_values = np.zeros(count, dtype=np.float64)
        z_values = np.zeros(count, dtype=np.float64)
        fx_values = np.zeros(count, dtype=np.float64)
        fy_values = np.zeros(count, dtype=np.float64)
        z_display_values = np.zeros(count, dtype=np.float64)

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
                fx_raw, fy_raw = float(grad[0]), float(grad[1])
                x_values[idx] = float(x)
                y_values[idx] = float(y)
                u_values[idx] = float(u)
                v_values[idx] = float(v)
                z_values[idx] = z
                fx_values[idx] = fx_raw
                fy_values[idx] = fy_raw
                idx += 1

        z_display_values = cls.Z_LOG_SCALE * np.log1p(np.maximum(z_values, 0.0))
        z_min = 0.0
        z_max = float(np.max(z_display_values)) if count > 0 else 0.0

        for k in range(count):
            z_disp = float(z_display_values[k])
            fx_disp, fy_disp = cls.display_slopes(
                float(z_values[k]),
                float(fx_values[k]),
                float(fy_values[k]),
            )
            vertices[k] = [x_values[k], y_values[k], z_disp]
            normals[k] = cls._normalize(np.array([-fx_disp, -fy_disp, 1.0], dtype=np.float64))
            texcoords[k] = [u_values[k], v_values[k]]

        for k in range(count):
            colors[k] = cls.inferno_color(float(z_display_values[k]), z_min, z_max)

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
