import numpy as np
from libs import transform as T

class Camera:
    def __init__(
        self,
        position=[0.0, 0.0, 5.0],
        target=[0.0, 0.0, 0.0],
        up=[0.0, 1.0, 0.0],
        orbit_axis=None,
        allow_pitch=True,
    ):
        self.position = np.array(position, dtype=np.float32)
        self.target = np.array(target, dtype=np.float32)
        self.up = np.array(up, dtype=np.float32)
        self.orbit_axis = self._normalize(
            np.array([0.0, 1.0, 0.0] if orbit_axis is None else orbit_axis, dtype=np.float32)
        )
        self.allow_pitch = bool(allow_pitch)
        self.use_orthographic = False
        self.fov = 45.0
        self.ortho_size = 3.0
        self.aspect = 640 / 480
        self.near = 0.1
        self.far = 100.0

    @staticmethod
    def _normalize(v):
        n = np.linalg.norm(v)
        if n < 1e-8:
            return v
        return v / n

    def set_aspect(self, width, height):
        h = max(1.0, float(height))
        self.aspect = float(width) / h
        
    def get_view_matrix(self):
        # return T.lookat(self.position, self.target, self.up)
        forward = self._normalize(self.target - self.position)
        safe_up = self.up
        if abs(np.dot(forward, self.up)) > 0.999:
            safe_up = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        return T.lookat(self.position, self.target, safe_up)
    
    def get_projection_matrix(self):
        return T.perspective(self.fov, self.aspect, self.near, self.far)
    
    def zoom(self, amount):
        if self.use_orthographic:
            self.ortho_size = max(0.2, min(80.0, self.ortho_size - amount * 0.1))
            return
        self.fov = max(10.0, min(120.0, self.fov - amount))

    def orbit(self, delta_yaw, delta_pitch):
        """Orbit camera around target by yaw/pitch (radians)."""
        offset = self.position - self.target
        radius = float(np.linalg.norm(offset))
        if radius < 1e-6:
            offset = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            radius = 1.0

        # Yaw around configured orbit axis (e.g. Oz for angled camera)
        cos_y, sin_y = np.cos(delta_yaw), np.sin(delta_yaw)
        ax = self._normalize(self.orbit_axis)
        kx, ky, kz = ax
        yaw_rot = np.array([
            [cos_y + kx * kx * (1 - cos_y), kx * ky * (1 - cos_y) - kz * sin_y, kx * kz * (1 - cos_y) + ky * sin_y],
            [ky * kx * (1 - cos_y) + kz * sin_y, cos_y + ky * ky * (1 - cos_y), ky * kz * (1 - cos_y) - kx * sin_y],
            [kz * kx * (1 - cos_y) - ky * sin_y, kz * ky * (1 - cos_y) + kx * sin_y, cos_y + kz * kz * (1 - cos_y)],
        ], dtype=np.float32)
        offset = yaw_rot @ offset

        if not self.allow_pitch:
            offset = self._normalize(offset) * radius
            self.position = self.target + offset
            return

        # Pitch around camera-right axis
        forward = self._normalize(-offset)
        right = self._normalize(np.cross(forward, self.up))
        if np.linalg.norm(right) < 1e-6:
            right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        c, s = np.cos(delta_pitch), np.sin(delta_pitch)
        kx, ky, kz = right
        pitch_rot = np.array([
            [c + kx * kx * (1 - c), kx * ky * (1 - c) - kz * s, kx * kz * (1 - c) + ky * s],
            [ky * kx * (1 - c) + kz * s, c + ky * ky * (1 - c), ky * kz * (1 - c) - kx * s],
            [kz * kx * (1 - c) - ky * s, kz * ky * (1 - c) + kx * s, c + kz * kz * (1 - c)],
        ], dtype=np.float32)
        offset = pitch_rot @ offset

        new_forward = self._normalize(-offset)
        # Avoid gimbal lock by clamping near-pole directions
        if abs(np.dot(new_forward, self.up)) > 0.995:
            return

        # Keep exact camera-target distance constant while orbiting.
        offset = self._normalize(offset) * radius
        self.position = self.target + offset

    # Intentionally no pan transform in BTL free camera.

