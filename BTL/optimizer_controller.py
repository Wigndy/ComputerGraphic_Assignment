import numpy as np
import OpenGL.GL as GL

from libs import transform as T
from geometry import MeshDrawable, create_geo3d_drawable, create_loss_surface_drawable
from overlay_drawables import PointSetDrawable, TrajectoryDrawable
from sample_function import LossFunctionManager, LossFunctionType, LossSurfaceMeshGenerator, OptimizerFactory, OptimizerType


class OptimizerController:
    """Owns optimizer simulation state and rendering helpers."""

    BALL_DECAY_OPTIMAL = 0.98
    BALL_SPEED_LIFT_OPTIMAL = 0.0
    BALL_MIN_CLEARANCE_OPTIMAL = 0.01

    FIXED_LOSS_X_MIN = -30.0
    FIXED_LOSS_X_MAX = 30.0
    FIXED_LOSS_Y_MIN = -30.0
    FIXED_LOSS_Y_MAX = 30.0

    LOSS_BOUNDS = {
        LossFunctionType.BEALE: (-4.5, 4.5, -4.5, 4.5),
        LossFunctionType.HIMMELBLAU: (-5.0, 5.0, -5.0, 5.0),
        LossFunctionType.ROSENBROCK: (-30.0, 30.0, -30.0, 30.0),
        LossFunctionType.BOOTH: (-30.0, 30.0, -30.0, 30.0),
        LossFunctionType.QUADRATIC_2D: (-30.0, 30.0, -30.0, 30.0),
    }

    RECOMMENDED_RESOLUTION = {
        LossFunctionType.BEALE: 200,
        LossFunctionType.HIMMELBLAU: 200,
        LossFunctionType.ROSENBROCK: 200,
        LossFunctionType.BOOTH: 200,
        LossFunctionType.QUADRATIC_2D: 200,
    }

    def __init__(self):
        self.loss_function_types = list(LossFunctionType)
        self.loss_function_labels = [lt.name.replace("_", " ").title() for lt in self.loss_function_types]
        self.loss_function_idx = self.loss_function_types.index(LossFunctionType.HIMMELBLAU)
        self.loss_x_min = self.FIXED_LOSS_X_MIN
        self.loss_x_max = self.FIXED_LOSS_X_MAX
        self.loss_y_min = self.FIXED_LOSS_Y_MIN
        self.loss_y_max = self.FIXED_LOSS_Y_MAX
        self.loss_resolution = 200

        self.opt_start_x = -4.0
        self.opt_start_y = 4.0
        self.opt_learning_rate = 0.003
        self.opt_learning_rate_log10 = float(np.log10(self.opt_learning_rate))
        self.opt_momentum_coefficient = 0.9
        self.opt_batch_size = 16
        self.opt_noise_variance = 0.01
        self.max_epochs = 600
        self.current_epoch = 0
        self.use_random_reset_start = False
        self.last_reset_start = np.array([self.opt_start_x, self.opt_start_y], dtype=np.float64)
        self.steps_per_frame = 1
        self.sim_updates_per_second = 4.0
        self.simulation_running = False

        self.optimizer_order = [
            OptimizerType.BATCH_GRADIENT_DESCENT,
            OptimizerType.GRADIENT_DESCENT,
            OptimizerType.MINI_BATCH_SGD,
            OptimizerType.MOMENTUM,
            OptimizerType.ADAM,
        ]
        self.optimizer_display_names = {
            OptimizerType.BATCH_GRADIENT_DESCENT: "Batch GD",
            OptimizerType.GRADIENT_DESCENT: "SGD",
            OptimizerType.MINI_BATCH_SGD: "Mini-batch SGD",
            OptimizerType.MOMENTUM: "Momentum",
            OptimizerType.ADAM: "Adam",
        }
        self.optimizer_colors = {
            OptimizerType.BATCH_GRADIENT_DESCENT: np.array([0.95, 0.25, 0.25], dtype=np.float32),
            OptimizerType.GRADIENT_DESCENT: np.array([0.98, 0.75, 0.22], dtype=np.float32),
            OptimizerType.MINI_BATCH_SGD: np.array([0.20, 0.60, 1.00], dtype=np.float32),
            OptimizerType.MOMENTUM: np.array([0.70, 0.45, 0.98], dtype=np.float32),
            OptimizerType.ADAM: np.array([0.20, 0.90, 0.35], dtype=np.float32),
        }
        self.marker_layer_offsets = {
            opt_type: float(i) * 0.06 for i, opt_type in enumerate(self.optimizer_order)
        }

        self.optimizers = {}
        self.optimizer_markers = {}
        self.spin_indicators = {}
        self.trajectory_drawables = {}
        self.contour_trajectory_drawables = {}
        self.contour_marker_drawable = PointSetDrawable()
        self.contour_drawable = None
        self.contour_heatmap_drawable = None
        self.contour_start_marker_drawable = None
        self.ball_state = {}
        self.playback_buffers = {}
        self.display_state = {}
        self.playback_time = 0.0
        self.optimization_active = False
        self.marker_radius = 0.13
        self.marker_z_offset = 0.07
        self.trajectory_z_offset = 0.03

        self.ball_materials = {}

        self.ball_decay = self.BALL_DECAY_OPTIMAL
        self.ball_speed_to_height = self.BALL_SPEED_LIFT_OPTIMAL
        self.ball_min_height = self.BALL_MIN_CLEARANCE_OPTIMAL

        self.show_contour_map = True
        self.contour_view_mode = 0
        self.contour_view_modes = ["Split 50/50", "Inset Bottom-Right"]
        self.contour_inset_fraction = 0.35
        self.contour_levels = 8
        self.contour_grid_divisions = 4
        self.contour_heatmap_opacity = 0.18
        self.contour_line_opacity = 0.55
        self.contour_grid_opacity = 0.30
        self.contour_marker_size = 10.0
        self.contour_start_marker_scale = 0.25
        self._optimizer_rng = np.random.default_rng()

    def _lock_loss_bounds(self):
        bounds = self.LOSS_BOUNDS.get(self.active_loss_type(), None)
        if bounds is None:
            self.loss_x_min = self.FIXED_LOSS_X_MIN
            self.loss_x_max = self.FIXED_LOSS_X_MAX
            self.loss_y_min = self.FIXED_LOSS_Y_MIN
            self.loss_y_max = self.FIXED_LOSS_Y_MAX
            return

        self.loss_x_min, self.loss_x_max, self.loss_y_min, self.loss_y_max = bounds

    def recommended_resolution(self):
        return int(self.RECOMMENDED_RESOLUTION.get(self.active_loss_type(), 180))

    def active_loss_type(self):
        return self.loss_function_types[self.loss_function_idx]

    @staticmethod
    def _display_loss(loss_val: float) -> float:
        return float(LossSurfaceMeshGenerator.display_z(float(loss_val)))

    def clear_state(self):
        self.optimizers = {}
        self.optimizer_markers = {}
        self.spin_indicators = {}
        self.trajectory_drawables = {}
        self.contour_trajectory_drawables = {}
        self.contour_drawable = None
        self.contour_heatmap_drawable = None
        self.ball_state = {}
        self.ball_materials = {}
        self.playback_buffers = {}
        self.display_state = {}
        self.playback_time = 0.0
        self.optimization_active = False
        self.simulation_running = False
        self.current_epoch = 0

    def create_surface_drawable(self):
        self._lock_loss_bounds()
        self.loss_resolution = int(max(int(self.loss_resolution), int(self.recommended_resolution())))
        loss_type = self.active_loss_type()
        drawable = create_loss_surface_drawable(
            loss_type=loss_type,
            x_min=self.loss_x_min,
            x_max=self.loss_x_max,
            y_min=self.loss_y_min,
            y_max=self.loss_y_max,
            resolution=int(self.loss_resolution),
        )
        self._build_contour_drawable()
        return f"Loss Surface: {loss_type.value}", drawable

    @staticmethod
    def _interpolate_edge(p0, p1, z0, z1, level):
        dz = (z1 - z0)
        if abs(dz) < 1e-12:
            return None
        t = (level - z0) / dz
        if t < 0.0 or t > 1.0:
            return None
        return p0 + t * (p1 - p0)

    def _build_contour_drawable(self):
        def _mute_color(rgb, mix_to_gray=0.60):
            c = np.asarray(rgb, dtype=np.float32)
            lum = float(0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2])
            gray = np.array([lum, lum, lum], dtype=np.float32)
            return np.clip((1.0 - mix_to_gray) * c + mix_to_gray * gray, 0.0, 1.0)

        mesh = LossSurfaceMeshGenerator.generate(
            loss_type=self.active_loss_type(),
            x_min=self.loss_x_min,
            x_max=self.loss_x_max,
            y_min=self.loss_y_min,
            y_max=self.loss_y_max,
            resolution=int(self.loss_resolution),
        )

        z_min = 0.0
        z_max = float(mesh.z_range[1])
        levels = np.linspace(z_min, z_max, int(self.contour_levels) + 2)[1:-1]

        heatmap_vertices = np.column_stack(
            (
                mesh.vertices[:, 0],
                mesh.vertices[:, 1],
                np.full(mesh.vertices.shape[0], -0.010, dtype=np.float32),
            )
        ).astype(np.float32)
        heatmap_colors = np.zeros((mesh.vertices.shape[0], 3), dtype=np.float32)
        for i in range(mesh.vertices.shape[0]):
            raw = LossSurfaceMeshGenerator.viridis_color(float(mesh.vertices[i, 2]), z_min, z_max).astype(np.float32)
            heatmap_colors[i] = _mute_color(raw, mix_to_gray=0.68)

        tri_vertices = heatmap_vertices[mesh.indices]
        tri_normals = np.zeros_like(tri_vertices, dtype=np.float32)
        tri_texcoords = np.zeros((tri_vertices.shape[0], 2), dtype=np.float32)
        tri_colors = heatmap_colors[mesh.indices]
        self.contour_heatmap_drawable = MeshDrawable(
            tri_vertices,
            tri_normals,
            tri_texcoords,
            colors=tri_colors,
            primitive=GL.GL_TRIANGLES,
        )

        vertices = []
        colors = []
        tris = mesh.indices.reshape(-1, 3)

        for level in levels:
            raw_line = LossSurfaceMeshGenerator.inferno_color(float(level), z_min, z_max).astype(np.float32)
            line_color = _mute_color(raw_line, mix_to_gray=0.50)
            for tri in tris:
                p = mesh.vertices[tri]
                z = p[:, 2]
                edges = ((0, 1), (1, 2), (2, 0))
                hits = []
                for a, b in edges:
                    hit = self._interpolate_edge(p[a, :2], p[b, :2], float(z[a]), float(z[b]), float(level))
                    if hit is not None:
                        hits.append(hit)

                if len(hits) < 2:
                    continue

                a = np.array([hits[0][0], hits[0][1], 0.003], dtype=np.float32)
                b = np.array([hits[1][0], hits[1][1], 0.003], dtype=np.float32)
                vertices.extend([a, b])
                colors.extend([line_color, line_color])

        # Bounding box frame for contour panel readability.
        x0, x1 = float(self.loss_x_min), float(self.loss_x_max)
        y0, y1 = float(self.loss_y_min), float(self.loss_y_max)
        frame_color = np.array([0.92, 0.92, 0.92], dtype=np.float32)
        grid_color = np.array([0.42, 0.42, 0.42], dtype=np.float32)

        grid_div = max(1, int(self.contour_grid_divisions))
        gx_vals = np.linspace(x0, x1, grid_div + 1)
        gy_vals = np.linspace(y0, y1, grid_div + 1)
        for gx in gx_vals:
            vertices.extend([
                np.array([gx, y0, 0.001], dtype=np.float32),
                np.array([gx, y1, 0.001], dtype=np.float32),
            ])
            colors.extend([grid_color, grid_color])

        for gy in gy_vals:
            vertices.extend([
                np.array([x0, gy, 0.001], dtype=np.float32),
                np.array([x1, gy, 0.001], dtype=np.float32),
            ])
            colors.extend([grid_color, grid_color])

        frame_lines = [
            ([x0, y0, 0.004], [x1, y0, 0.004]),
            ([x1, y0, 0.004], [x1, y1, 0.004]),
            ([x1, y1, 0.004], [x0, y1, 0.004]),
            ([x0, y1, 0.004], [x0, y0, 0.004]),
        ]
        for p0, p1 in frame_lines:
            vertices.extend([np.array(p0, dtype=np.float32), np.array(p1, dtype=np.float32)])
            colors.extend([frame_color, frame_color])

        if not vertices:
            self.contour_drawable = None
            return

        verts = np.asarray(vertices, dtype=np.float32)
        cols = np.asarray(colors, dtype=np.float32)
        norms = np.zeros((verts.shape[0], 3), dtype=np.float32)
        uvs = np.zeros((verts.shape[0], 2), dtype=np.float32)
        self.contour_drawable = MeshDrawable(verts, norms, uvs, colors=cols, primitive=GL.GL_LINES)
        self._build_contour_start_marker_drawable()

    def _build_contour_start_marker_drawable(self):
        marker_color = np.array([1.0, 0.96, 0.35], dtype=np.float32)
        verts = np.array([
            [-1.0, -1.0, 0.0],
            [1.0, 1.0, 0.0],
            [-1.0, 1.0, 0.0],
            [1.0, -1.0, 0.0],
        ], dtype=np.float32)
        cols = np.array([marker_color, marker_color, marker_color, marker_color], dtype=np.float32)
        norms = np.zeros((verts.shape[0], 3), dtype=np.float32)
        uvs = np.zeros((verts.shape[0], 2), dtype=np.float32)
        self.contour_start_marker_drawable = MeshDrawable(verts, norms, uvs, colors=cols, primitive=GL.GL_LINES)

    def build_optimizer_markers(self):
        def make_ball(radius, sectors, stacks, color, emissive_strength, diffuse_scale, ambient_scale, shininess):
            ball = create_geo3d_drawable("Sphere (Lat-Long)", radius=radius, sectors=sectors, stacks=stacks)
            ball.flat_color = color
            ball.set_vertex_color(color)
            ball.set_material(
                diffuse=np.clip(color * diffuse_scale, 0.0, 1.0),
                specular=np.array([0.95, 0.95, 0.95], dtype=np.float32),
                ambient=np.clip(color * ambient_scale, 0.0, 1.0),
                shininess=shininess,
            )
            ball.set_emissive(color=color, strength=emissive_strength)
            return ball

        self.optimizer_markers = {}
        self.spin_indicators = {}
        for opt_type in self.optimizer_order:
            base_color = self.optimizer_colors[opt_type]
            marker = make_ball(self.marker_radius, 20, 14, base_color, 0.18, 0.95, 0.30, 120.0)
            self.optimizer_markers[opt_type] = marker
            self.ball_materials[opt_type] = marker.material_override

            indicator_color = np.clip(base_color * 0.35 + np.array([0.75, 0.75, 0.75], dtype=np.float32), 0.0, 1.0)
            indicator = make_ball(self.marker_radius * 0.22, 12, 10, indicator_color, 0.10, 0.90, 0.25, 110.0)
            self.spin_indicators[opt_type] = indicator

    @staticmethod
    def _draw_contour_mesh(drawable, projection, view, model, alpha_override=1.0):
        drawable.draw(
            projection,
            view,
            model,
            shading_mode=MeshDrawable.MODE_COLOR,
            alpha_override=float(np.clip(alpha_override, 0.0, 1.0)),
            lighting_algorithm="phong",
            light_1_enabled=False,
            light_2_enabled=False,
            brightness=1.0,
            show_depth_map=False,
        )

    def _surface_normal(self, x, y):
        z_raw = LossFunctionManager.evaluate(self.active_loss_type(), float(x), float(y))
        gx, gy = LossFunctionManager.gradient(self.active_loss_type(), float(x), float(y))
        gx_disp, gy_disp = LossSurfaceMeshGenerator.display_slopes(float(z_raw), float(gx), float(gy))
        n = np.array([-gx_disp, -gy_disp, 1.0], dtype=np.float32)
        n_norm = np.linalg.norm(n)
        if n_norm < 1e-8:
            return np.array([0.0, 0.0, 1.0], dtype=np.float32)
        return n / n_norm

    def _update_ball_rotation(self, opt_type, x, y, loss_val):
        loss_display = self._display_loss(loss_val)
        state = self.ball_state.setdefault(
            opt_type,
            {
                "rotation": np.identity(4, dtype=np.float32),
                "surface_pos": np.array([float(x), float(y), loss_display], dtype=np.float32),
                "rolling_distance": 0.0,
            },
        )

        current_surface = np.array([float(x), float(y), loss_display], dtype=np.float32)
        prev_surface = np.asarray(state.get("surface_pos", current_surface), dtype=np.float32)
        delta = current_surface - prev_surface
        if float(np.linalg.norm(delta)) < 1e-7:
            state["surface_pos"] = current_surface
            return np.asarray(state["rotation"], dtype=np.float32)

        prev_normal = self._surface_normal(float(prev_surface[0]), float(prev_surface[1]))
        curr_normal = self._surface_normal(x, y)
        normal = prev_normal + curr_normal
        normal_len = float(np.linalg.norm(normal))
        if normal_len < 1e-7:
            normal = curr_normal
        else:
            normal = normal / normal_len

        tangent = delta - normal * float(np.dot(delta, normal))
        tangent_len = float(np.linalg.norm(tangent))
        if tangent_len < 1e-7:
            state["surface_pos"] = current_surface
            return np.asarray(state["rotation"], dtype=np.float32)

        tangent_dir = tangent / tangent_len
        roll_axis = np.cross(normal, tangent_dir)
        axis_len = float(np.linalg.norm(roll_axis))
        if axis_len < 1e-7:
            state["surface_pos"] = current_surface
            return np.asarray(state["rotation"], dtype=np.float32)

        roll_axis /= axis_len
        roll_angle = tangent_len / max(1e-4, float(self.marker_radius))
        incremental = T.rotate(axis=roll_axis, radians=roll_angle)
        state["rotation"] = (incremental @ np.asarray(state["rotation"], dtype=np.float32)).astype(np.float32)
        state["surface_pos"] = current_surface
        state["rolling_distance"] = float(state.get("rolling_distance", 0.0)) + tangent_len
        return np.asarray(state["rotation"], dtype=np.float32)

    def _create_optimizer_instance(self, opt_type, x0, y0):
        return OptimizerFactory.create(
            optimizer_type=opt_type,
            loss_type=self.active_loss_type(),
            initial_x=x0,
            initial_y=y0,
            learning_rate=self.opt_learning_rate,
            momentum_coefficient=self.opt_momentum_coefficient,
            batch_size=self.opt_batch_size,
            noise_variance=self.opt_noise_variance,
        )

    def _precompute_playback_buffers(self, x0, y0):
        loss_type = self.active_loss_type()
        n_samples = int(max(1, int(self.max_epochs))) + 1
        self.playback_buffers = {}

        for opt_type in self.optimizer_order:
            sim_opt = self._create_optimizer_instance(opt_type, x0, y0)

            xy = np.zeros((n_samples, 2), dtype=np.float32)
            loss = np.zeros(n_samples, dtype=np.float32)
            altitude = np.zeros(n_samples, dtype=np.float32)

            alt = float(self.ball_min_height)
            xy[0] = [float(sim_opt.x), float(sim_opt.y)]
            loss[0] = float(LossFunctionManager.evaluate(loss_type, float(sim_opt.x), float(sim_opt.y)))
            altitude[0] = alt
            loss_display = np.zeros(n_samples, dtype=np.float32)
            loss_display[0] = self._display_loss(loss[0])

            x_min = float(self.loss_x_min)
            x_max = float(self.loss_x_max)
            y_min = float(self.loss_y_min)
            y_max = float(self.loss_y_max)

            for i in range(1, n_samples):
                before = np.array([sim_opt.x, sim_opt.y], dtype=np.float64)
                sim_opt.step()
                after = np.array([sim_opt.x, sim_opt.y], dtype=np.float64)

                if not np.all(np.isfinite(after)):
                    after = before.copy()

                after[0] = float(np.clip(after[0], x_min, x_max))
                after[1] = float(np.clip(after[1], y_min, y_max))
                sim_opt.set_position(float(after[0]), float(after[1]), clear_trajectory=False)

                speed = float(np.linalg.norm(after - before))
                if not np.isfinite(speed):
                    speed = 0.0
                alt = max(self.ball_min_height, alt * self.ball_decay + speed * self.ball_speed_to_height)
                if not np.isfinite(alt):
                    alt = float(altitude[i - 1])

                x = float(sim_opt.x)
                y = float(sim_opt.y)
                loss_val = float(LossFunctionManager.evaluate(loss_type, x, y))

                if not (np.isfinite(x) and np.isfinite(y) and np.isfinite(loss_val) and np.isfinite(alt)):
                    x = float(xy[i - 1, 0])
                    y = float(xy[i - 1, 1])
                    loss_val = float(loss[i - 1])
                    alt = float(altitude[i - 1])
                    xy[i:] = [x, y]
                    loss[i:] = loss_val
                    loss_display[i:] = float(loss_display[i - 1])
                    altitude[i:] = alt
                    break

                xy[i] = [x, y]
                loss[i] = loss_val
                loss_display[i] = self._display_loss(loss_val)
                altitude[i] = float(alt)

            path3d = np.column_stack((xy[:, 0], xy[:, 1], loss_display + self.trajectory_z_offset)).astype(np.float32)
            path2d = np.column_stack((xy[:, 0], xy[:, 1], np.zeros(n_samples, dtype=np.float32))).astype(np.float32)

            self.playback_buffers[opt_type] = {
                "xy": xy,
                "loss": loss,
                "loss_display": loss_display,
                "altitude": altitude,
                "path3d": path3d,
                "path2d": path2d,
            }

    def _apply_playback_state(self):
        if not self.playback_buffers:
            return

        sample_counts = [int(buf["xy"].shape[0]) for buf in self.playback_buffers.values() if "xy" in buf]
        if not sample_counts:
            return
        # Clamp by both UI max_epochs and precomputed buffer size to avoid OOB access.
        max_idx = int(max(0, min(int(self.max_epochs), min(sample_counts) - 1)))
        t = float(np.clip(self.playback_time, 0.0, float(max_idx)))
        i0 = int(np.floor(t))
        i1 = min(i0 + 1, max_idx)
        alpha = float(t - float(i0))

        self.current_epoch = i0
        self.display_state = {}

        for opt_type in self.optimizer_order:
            buf = self.playback_buffers.get(opt_type)
            if buf is None:
                continue

            xy0 = buf["xy"][i0]
            xy1 = buf["xy"][i1]
            x = float(xy0[0] * (1.0 - alpha) + xy1[0] * alpha)
            y = float(xy0[1] * (1.0 - alpha) + xy1[1] * alpha)
            loss_val = float(buf["loss"][i0] * (1.0 - alpha) + buf["loss"][i1] * alpha)
            loss_display = float(buf["loss_display"][i0] * (1.0 - alpha) + buf["loss_display"][i1] * alpha)
            altitude = float(buf["altitude"][i0] * (1.0 - alpha) + buf["altitude"][i1] * alpha)

            self.display_state[opt_type] = {
                "x": x,
                "y": y,
                "loss": loss_val,
                "loss_display": loss_display,
                "altitude": altitude,
            }

            traj3d = self.trajectory_drawables.get(opt_type)
            if traj3d is not None:
                points3 = buf["path3d"][: i0 + 1]
                if alpha > 1e-6 and i1 > i0:
                    p3 = np.array([[x, y, loss_display + self.trajectory_z_offset]], dtype=np.float32)
                    points3 = np.vstack((points3, p3))
                traj3d.update_points(points3)

            traj2d = self.contour_trajectory_drawables.get(opt_type)
            if traj2d is not None:
                points2 = buf["path2d"][: i0 + 1]
                if alpha > 1e-6 and i1 > i0:
                    p2 = np.array([[x, y, 0.0]], dtype=np.float32)
                    points2 = np.vstack((points2, p2))
                traj2d.update_points(points2)

    def build_optimizers(self, randomize_start=False):
        self._lock_loss_bounds()
        self.optimizers = {}
        self.trajectory_drawables = {}
        self.contour_trajectory_drawables = {}
        self.ball_state = {}
        self.playback_buffers = {}
        self.display_state = {}
        self.playback_time = 0.0
        self.simulation_running = False
        self.current_epoch = 0

        if randomize_start:
            x0 = float(self._optimizer_rng.uniform(self.loss_x_min, self.loss_x_max))
            y0 = float(self._optimizer_rng.uniform(self.loss_y_min, self.loss_y_max))
        else:
            x0 = float(self.opt_start_x)
            y0 = float(self.opt_start_y)

        self.last_reset_start = np.array([x0, y0], dtype=np.float64)
        for opt_type in self.optimizer_order:
            opt = self._create_optimizer_instance(opt_type, x0, y0)
            self.optimizers[opt_type] = opt
            self.trajectory_drawables[opt_type] = TrajectoryDrawable(self.optimizer_colors[opt_type], line_width=2.6)
            self.contour_trajectory_drawables[opt_type] = TrajectoryDrawable(self.optimizer_colors[opt_type], line_width=3.0)
            self.ball_state[opt_type] = {
                "rotation": np.identity(4, dtype=np.float32),
                "surface_pos": np.array([
                    float(x0),
                    float(y0),
                    self._display_loss(
                        LossFunctionManager.evaluate(self.active_loss_type(), float(x0), float(y0))
                    ),
                ], dtype=np.float32),
                "rolling_distance": 0.0,
            }

        self._precompute_playback_buffers(x0, y0)
        self._apply_playback_state()

    def set_start_point(self, x, y, rebuild=True):
        self._lock_loss_bounds()
        self.opt_start_x = float(np.clip(float(x), self.loss_x_min, self.loss_x_max))
        self.opt_start_y = float(np.clip(float(y), self.loss_y_min, self.loss_y_max))
        self.last_reset_start = np.array([self.opt_start_x, self.opt_start_y], dtype=np.float64)

        if rebuild and self.optimization_active:
            self.build_optimizers(randomize_start=False)
            self.simulation_running = False

    def activate_scene(self):
        self.build_optimizer_markers()
        self.build_optimizers()
        self.optimization_active = True
        self.simulation_running = False

    def refresh_trajectory_drawables(self):
        self._apply_playback_state()

    def optimizer_metrics(self):
        rows = []
        loss_type = self.active_loss_type()
        for opt_type in self.optimizer_order:
            state = self.display_state.get(opt_type)
            if state is None:
                continue
            loss_value = LossFunctionManager.evaluate(loss_type, state["x"], state["y"])
            grad = LossFunctionManager.gradient(loss_type, state["x"], state["y"])
            grad_norm = float(np.linalg.norm(grad))
            rows.append((opt_type, int(self.current_epoch), float(loss_value), grad_norm))
        return rows

    def step_optimizers(self, steps):
        if not self.optimization_active or not self.playback_buffers:
            return

        sample_counts = [int(buf["xy"].shape[0]) for buf in self.playback_buffers.values() if "xy" in buf]
        if not sample_counts:
            return
        max_time = float(max(0, min(int(self.max_epochs), min(sample_counts) - 1)))
        self.playback_time = min(max_time, float(self.playback_time) + float(max(1, int(steps))))
        self._apply_playback_state()
        if self.playback_time >= max_time:
            self.simulation_running = False

    def advance_playback(self, delta_time):
        if not self.optimization_active or not self.playback_buffers:
            return

        sample_counts = [int(buf["xy"].shape[0]) for buf in self.playback_buffers.values() if "xy" in buf]
        if not sample_counts:
            return
        max_time = float(max(0, min(int(self.max_epochs), min(sample_counts) - 1)))
        epochs_per_second = max(0.05, float(self.sim_updates_per_second) * float(max(1, int(self.steps_per_frame))))
        self.playback_time = min(max_time, float(self.playback_time) + float(delta_time) * epochs_per_second)
        self._apply_playback_state()
        if self.playback_time >= max_time:
            self.simulation_running = False

    def draw_overlays(
        self,
        proj_mat,
        view_mat,
        light_1_enabled,
        light_2_enabled,
        brightness,
        hdri_environment_enabled=False,
        hdri_environment_intensity=0.55,
        hdri_environment_color=None,
        custom_light_enabled=False,
        custom_light_position=None,
        custom_light_color=None,
        custom_light_intensity=1.0,
        material_roughness=0.25,
        material_metallic=0.05,
    ):
        if not self.optimization_active:
            return

        for opt_type in self.optimizer_order:
            traj = self.trajectory_drawables.get(opt_type)
            if traj is not None:
                traj.draw(proj_mat, view_mat)

        for opt_type in self.optimizer_order:
            state = self.display_state.get(opt_type)
            marker = self.optimizer_markers.get(opt_type)
            if state is None or marker is None:
                continue

            altitude = float(state.get("altitude", 0.0))
            layer_offset = float(self.marker_layer_offsets.get(opt_type, 0.0))
            rotation = self._update_ball_rotation(opt_type, state["x"], state["y"], state["loss"])
            z = float(state.get("loss_display", state["loss"])) + self.marker_z_offset + altitude + layer_offset
            model = T.translate(float(state["x"]), float(state["y"]), float(z)) @ rotation
            marker.draw(
                proj_mat,
                view_mat,
                model,
                shading_mode=MeshDrawable.MODE_LIGHTING,
                lighting_algorithm="phong",
                light_1_enabled=light_1_enabled,
                light_2_enabled=light_2_enabled,
                brightness=brightness,
                hdri_environment_enabled=hdri_environment_enabled,
                hdri_environment_intensity=hdri_environment_intensity,
                hdri_environment_color=hdri_environment_color,
                custom_light_enabled=custom_light_enabled,
                custom_light_position=custom_light_position,
                custom_light_color=custom_light_color,
                custom_light_intensity=custom_light_intensity,
                material_roughness=material_roughness,
                material_metallic=material_metallic,
                material_override=self.ball_materials.get(opt_type, None),
                emissive_color=self.optimizer_colors[opt_type],
                emissive_strength=0.18,
                show_depth_map=False,
            )

            indicator = self.spin_indicators.get(opt_type)
            if indicator is not None:
                # This marker is rigidly attached to the sphere body to make spin clearly visible.
                local_offset = T.translate(self.marker_radius * 0.78, 0.0, 0.0)
                indicator_model = T.translate(float(state["x"]), float(state["y"]), float(z)) @ rotation @ local_offset
                indicator.draw(
                    proj_mat,
                    view_mat,
                    indicator_model,
                    shading_mode=MeshDrawable.MODE_LIGHTING,
                    lighting_algorithm="phong",
                    light_1_enabled=light_1_enabled,
                    light_2_enabled=light_2_enabled,
                    brightness=brightness,
                    hdri_environment_enabled=hdri_environment_enabled,
                    hdri_environment_intensity=hdri_environment_intensity,
                    hdri_environment_color=hdri_environment_color,
                    custom_light_enabled=custom_light_enabled,
                    custom_light_position=custom_light_position,
                    custom_light_color=custom_light_color,
                    custom_light_intensity=custom_light_intensity,
                    material_roughness=material_roughness,
                    material_metallic=material_metallic,
                    show_depth_map=False,
                )

    def should_render_contour_panel(self):
        return bool(
            self.optimization_active
            and self.show_contour_map
            and (self.contour_drawable is not None or self.contour_heatmap_drawable is not None)
        )

    def contour_projection_and_view(self):
        proj = T.ortho(self.loss_x_min, self.loss_x_max, self.loss_y_min, self.loss_y_max, -1.0, 1.0)
        view = np.identity(4, dtype=np.float32)
        return proj, view

    def draw_contour_panel(self):
        if self.contour_drawable is None and self.contour_heatmap_drawable is None:
            return

        proj, view = self.contour_projection_and_view()
        if self.contour_heatmap_drawable is not None:
            self._draw_contour_mesh(
                self.contour_heatmap_drawable,
                proj,
                view,
                np.identity(4, dtype=np.float32),
                alpha_override=self.contour_heatmap_opacity,
            )

        if self.contour_drawable is not None:
            self._draw_contour_mesh(
                self.contour_drawable,
                proj,
                view,
                np.identity(4, dtype=np.float32),
                alpha_override=self.contour_line_opacity,
            )

        if self.contour_start_marker_drawable is not None:
            x_span = float(self.loss_x_max - self.loss_x_min)
            y_span = float(self.loss_y_max - self.loss_y_min)
            marker_scale = self.contour_start_marker_scale * min(x_span, y_span) / 20.0
            model = T.translate(float(self.opt_start_x), float(self.opt_start_y), 0.0) @ T.scale(marker_scale, marker_scale, 1.0)
            self._draw_contour_mesh(self.contour_start_marker_drawable, proj, view, model)

        for opt_type in self.optimizer_order:
            traj = self.contour_trajectory_drawables.get(opt_type)
            if traj is not None:
                traj.draw(proj, view)

        marker_points = []
        marker_colors = []
        for opt_type in self.optimizer_order:
            state = self.display_state.get(opt_type)
            if state is None:
                continue
            marker_points.append([float(state["x"]), float(state["y"]), 0.0])
            marker_colors.append(self.optimizer_colors[opt_type].tolist())

        if marker_points:
            self.contour_marker_drawable.update_points(
                np.asarray(marker_points, dtype=np.float32),
                np.asarray(marker_colors, dtype=np.float32),
            )
            self.contour_marker_drawable.draw(proj, view, point_size=self.contour_marker_size)
