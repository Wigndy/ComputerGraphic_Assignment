"""Compatibility facade for geometry API.

This module keeps existing imports stable while delegating implementation
to componentized modules under `geometry_components`.
"""

from geometry_components.manager import (
    Geo2D,
    Geo3D,
    MeshDrawable,
    create_drawable_from_file,
    create_geo2d_drawable,
    create_geo3d_drawable,
    create_loss_surface_drawable,
    create_math_surface_drawable,
)

__all__ = [
    "Geo2D",
    "Geo3D",
    "MeshDrawable",
    "create_geo2d_drawable",
    "create_geo3d_drawable",
    "create_math_surface_drawable",
    "create_loss_surface_drawable",
    "create_drawable_from_file",
]
