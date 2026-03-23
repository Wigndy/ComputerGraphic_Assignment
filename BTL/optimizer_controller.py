import numpy as np

from libs import transform as T
from geometry import MeshDrawable, create_geo3d_drawable, create_loss_surface_drawable
from overlay_drawables import TrajectoryDrawable
from sample_function import LossFunctionManager, LossFunctionType, OptimizerFactory, OptimizerType


class OptimizerController:
    """Owns optimizer simulation state and rendering helpers."""

    def __init__(self):
        self.loss_function_types = list(LossFunctionType)
        self.loss_function_labels = [lt.name.replace("_", " ").title() for lt in self.loss_function_types]
        self.loss_function_idx = 0
        self.loss_x_min = -6.0
        self.loss_x_max = 6.0
        self.loss_y_min = -6.0
        self.loss_y_max = 6.0
        self.loss_resolution = 120

        self.opt_start_x = -4.0
        self.opt_start_y = 4.0
        self.opt_learning_rate = 0.003
        self.opt_learning_rate_log10 = float(np.log10(self.opt_learning_rate))
        self.opt_momentum_coefficient = 0.9
        self.opt_noise_variance = 0.01
        self.max_epochs = 600
        self.current_epoch = 0
        self.use_random_reset_start = False
        self.last_reset_start = np.array([self.opt_start_x, self.opt_start_y], dtype=np.float64)
        self.steps_per_frame = 1
        self.simulation_running = False

        self.optimizer_order = [
            OptimizerType.GRADIENT_DESCENT,
            OptimizerType.MOMENTUM,
            OptimizerType.ADAM,
        ]
        self.optimizer_display_names = {
            OptimizerType.GRADIENT_DESCENT: "Gradient Descent",
            OptimizerType.MOMENTUM: "Momentum",
            OptimizerType.ADAM: "Adam",
        }
        self.optimizer_colors = {
            OptimizerType.GRADIENT_DESCENT: np.array([1.0, 0.25, 0.25], dtype=np.float32),
            OptimizerType.MOMENTUM: np.array([0.95, 0.65, 0.10], dtype=np.float32),
            OptimizerType.ADAM: np.array([0.20, 0.90, 0.35], dtype=np.float32),
        }

        self.optimizers = {}
        self.optimizer_markers = {}
        self.trajectory_drawables = {}
        self.optimization_active = False
        self.marker_radius = 0.13
        self.marker_z_offset = 0.07
        self.trajectory_z_offset = 0.03
        self._optimizer_rng = np.random.default_rng()

    def active_loss_type(self):
        return self.loss_function_types[self.loss_function_idx]

    def clear_state(self):
        self.optimizers = {}
        self.optimizer_markers = {}
        self.trajectory_drawables = {}
        self.optimization_active = False
        self.simulation_running = False
        self.current_epoch = 0

    def create_surface_drawable(self):
        loss_type = self.active_loss_type()
        drawable = create_loss_surface_drawable(
            loss_type=loss_type,
            x_min=self.loss_x_min,
            x_max=self.loss_x_max,
            y_min=self.loss_y_min,
            y_max=self.loss_y_max,
            resolution=int(self.loss_resolution),
        )
        return f"Loss Surface: {loss_type.value}", drawable

    def build_optimizer_markers(self):
        self.optimizer_markers = {}
        for opt_type in self.optimizer_order:
            marker = create_geo3d_drawable("Sphere (Lat-Long)", radius=self.marker_radius, sectors=20, stacks=14)
            marker.flat_color = self.optimizer_colors[opt_type]
            self.optimizer_markers[opt_type] = marker

    def build_optimizers(self, randomize_start=False):
        loss_type = self.active_loss_type()
        self.optimizers = {}
        self.trajectory_drawables = {}
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
            opt = OptimizerFactory.create(
                optimizer_type=opt_type,
                loss_type=loss_type,
                initial_x=x0,
                initial_y=y0,
                learning_rate=self.opt_learning_rate,
                momentum_coefficient=self.opt_momentum_coefficient,
                noise_variance=self.opt_noise_variance,
            )
            self.optimizers[opt_type] = opt
            self.trajectory_drawables[opt_type] = TrajectoryDrawable(self.optimizer_colors[opt_type])
        self.refresh_trajectory_drawables()

    def activate_scene(self):
        self.build_optimizer_markers()
        self.build_optimizers()
        self.optimization_active = True
        self.simulation_running = False

    def refresh_trajectory_drawables(self):
        loss_type = self.active_loss_type()
        for opt_type in self.optimizer_order:
            opt = self.optimizers.get(opt_type)
            traj = self.trajectory_drawables.get(opt_type)
            if opt is None or traj is None:
                continue

            points = []
            for p in opt.trajectory:
                x = float(p[0])
                y = float(p[1])
                z = LossFunctionManager.evaluate(loss_type, x, y) + self.trajectory_z_offset
                points.append([x, y, z])
            traj.update_points(np.array(points, dtype=np.float32))

    def optimizer_metrics(self):
        rows = []
        loss_type = self.active_loss_type()
        for opt_type in self.optimizer_order:
            opt = self.optimizers.get(opt_type)
            if opt is None:
                continue
            loss_value = LossFunctionManager.evaluate(loss_type, opt.x, opt.y)
            grad = LossFunctionManager.gradient(loss_type, opt.x, opt.y)
            grad_norm = float(np.linalg.norm(grad))
            rows.append((opt_type, int(opt.step_count), float(loss_value), grad_norm))
        return rows

    def step_optimizers(self, steps):
        if not self.optimization_active or not self.optimizers:
            return

        remaining = max(0, int(self.max_epochs) - int(self.current_epoch))
        if remaining <= 0:
            self.simulation_running = False
            return

        n = max(1, int(steps))
        n = min(n, remaining)
        for _ in range(n):
            for opt_type in self.optimizer_order:
                self.optimizers[opt_type].step()
            self.current_epoch += 1

        if self.current_epoch >= self.max_epochs:
            self.simulation_running = False
        self.refresh_trajectory_drawables()

    def draw_overlays(self, proj_mat, view_mat, light_1_enabled, light_2_enabled, brightness):
        if not self.optimization_active:
            return

        for opt_type in self.optimizer_order:
            traj = self.trajectory_drawables.get(opt_type)
            if traj is not None:
                traj.draw(proj_mat, view_mat)

        loss_type = self.active_loss_type()
        for opt_type in self.optimizer_order:
            opt = self.optimizers.get(opt_type)
            marker = self.optimizer_markers.get(opt_type)
            if opt is None or marker is None:
                continue

            z = LossFunctionManager.evaluate(loss_type, opt.x, opt.y) + self.marker_z_offset
            model = T.translate(float(opt.x), float(opt.y), float(z))
            marker.draw(
                proj_mat,
                view_mat,
                model,
                shading_mode=MeshDrawable.MODE_FLAT,
                lighting_algorithm="phong",
                light_1_enabled=light_1_enabled,
                light_2_enabled=light_2_enabled,
                brightness=brightness,
                show_depth_map=False,
            )
