"""Geometry manager: centralized public API for geometry components."""

from .drawable import MeshDrawable
from .factories import (
    create_drawable_from_file,
    create_geo2d_drawable,
    create_geo3d_drawable,
    create_loss_surface_drawable,
    create_math_surface_drawable,
)
from .primitives import Geo2D, Geo3D

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
