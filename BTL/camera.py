import numpy as np
from libs import transform as T

class Camera:
    PROJ_PERSPECTIVE = "perspective"
    PROJ_ORTHOGRAPHIC = "orthographic"
    PROJ_FRUSTUM = "frustum"

    def __init__(self, position=[0.0, 0.0, 5.0], target=[0.0, 0.0, 0.0], up=[0.0,1.0,0.0]):
        self.position = np.array(position, dtype=np.float32)
        self.target = np.array(target, dtype=np.float32)
        self.up = np.array(up, dtype=np.float32)
        self.ortho_size = 4.0
        self.fov = 45.0
        self.aspect = 640 / 480
        self.near = 0.1
        self.far = 100.0
        self.frustum_half_height = 1.0
        self.projection_mode = Camera.PROJ_PERSPECTIVE

    @property
    def is_perspective(self):
        # Backward compatibility with existing code.
        return self.projection_mode == Camera.PROJ_PERSPECTIVE

    @is_perspective.setter
    def is_perspective(self, value):
        self.projection_mode = Camera.PROJ_PERSPECTIVE if bool(value) else Camera.PROJ_ORTHOGRAPHIC

    def cycle_projection_mode(self):
        modes = [Camera.PROJ_PERSPECTIVE, Camera.PROJ_ORTHOGRAPHIC, Camera.PROJ_FRUSTUM]
        idx = modes.index(self.projection_mode) if self.projection_mode in modes else 0
        self.projection_mode = modes[(idx + 1) % len(modes)]

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
        if self.projection_mode == Camera.PROJ_PERSPECTIVE:
            return T.perspective(self.fov, self.aspect, self.near, self.far)
        if self.projection_mode == Camera.PROJ_ORTHOGRAPHIC:
            size = max(0.1, float(self.ortho_size))
            return T.ortho(-size * self.aspect, size * self.aspect, -size, size, self.near, self.far)
        half_h = max(0.01, float(self.frustum_half_height))
        half_w = half_h * self.aspect
        return T.frustum(-half_w, half_w, -half_h, half_h, self.near, self.far)
    
    def zoom(self, amount):
        if self.projection_mode == Camera.PROJ_PERSPECTIVE:
            self.fov = max(10.0, min(120.0, self.fov - amount))
        elif self.projection_mode == Camera.PROJ_ORTHOGRAPHIC:
            self.ortho_size = max(0.2, min(50.0, self.ortho_size + amount * 0.05))
        else:
            self.frustum_half_height = max(0.1, min(50.0, self.frustum_half_height + amount * 0.05))

    def orbit(self, delta_yaw, delta_pitch):
        """Orbit camera around target by yaw/pitch (radians)."""
        offset = self.position - self.target
        radius = np.linalg.norm(offset)
        if radius < 1e-6:
            offset = np.array([0.0, 0.0, 1.0], dtype=np.float32)
            radius = 1.0

        # Yaw around world up axis
        cos_y, sin_y = np.cos(delta_yaw), np.sin(delta_yaw)
        yaw_rot = np.array([
            [cos_y, 0.0, sin_y],
            [0.0, 1.0, 0.0],
            [-sin_y, 0.0, cos_y],
        ], dtype=np.float32)
        offset = yaw_rot @ offset

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

        self.position = self.target + offset

    def pan(self, delta_x, delta_y, scale=0.003):
        """Pan camera and target in view plane."""
        forward = self._normalize(self.target - self.position)
        right = self._normalize(np.cross(forward, self.up))
        up_vec = self._normalize(np.cross(right, forward))
        motion = (-right * delta_x + up_vec * delta_y) * float(scale)
        self.position = self.position + motion
        self.target = self.target + motion
        
        