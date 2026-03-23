"""Factory component: high-level drawable creation helpers and mesh loaders."""

from .legacy_impl import (
    create_drawable_from_file,
    create_geo2d_drawable,
    create_geo3d_drawable,
    create_loss_surface_drawable,
    create_math_surface_drawable,
)

__all__ = [
    "create_geo2d_drawable",
    "create_geo3d_drawable",
    "create_math_surface_drawable",
    "create_loss_surface_drawable",
    "create_drawable_from_file",
]
