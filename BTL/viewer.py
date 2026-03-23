import OpenGL.GL as GL
import glfw
import imgui
import numpy as np
import os
import sys

# Add parent/current directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs import transform as T
from camera import Camera
from geometry import (
    Geo2D,
    Geo3D,
    MeshDrawable,
    create_drawable_from_file,
    create_geo2d_drawable,
    create_geo3d_drawable,
    create_math_surface_drawable,
)
from overlay_drawables import CoordinateAxesOverlay
from optimizer_controller import OptimizerController
from viewer_ui import draw_control_panel


def _create_imgui_renderer(window):
    # Support different pyimgui module paths used in older/newer versions.
    candidates = [
        ("imgui.integrations.glfw", "GlfwRenderer"),
        ("imgui.interaction.glfw", "GlfwRenderer"),
    ]
    for module_name, class_name in candidates:
        try:
            module = __import__(module_name, fromlist=[class_name])
            renderer_cls = getattr(module, class_name)
            return renderer_cls(window)
        except Exception:
            continue
    raise ImportError("Cannot create imgui GLFW renderer. Install pyimgui with GLFW integration.")


class SceneItem:
    def __init__(self, name, drawable, model):
        self.name = name
        self.drawable = drawable
        self.model = np.asarray(model, dtype=np.float32)


class Viewer:
    def __init__(self, width=1280, height=800):
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.DEPTH_BITS, 24)

        self.win = glfw.create_window(width, height, "BTL - Geometry Viewer", None, None)
        if not self.win:
            raise RuntimeError("Failed to create GLFW window")
        glfw.make_context_current(self.win)

        imgui.create_context()
        
        self.scene_items = []
        self.next_spawn_idx = 0

        self.cameras = [
            Camera([0.0, 0.0, 10.0], [0.0, 0.0, 0.0]),
            Camera([12.0, 10.0, 12.0], [0.0, 0.0, 0.0]),
            Camera([0.0, 10.0, 0.001], [0.0, 0.0, 0.0]),
        ]
        self.current_camera_idx = 0

        self.bg_color = [0.10, 0.10, 0.14]
        self.light_brightness = 1.0
        self.light_1_enabled = True
        self.light_2_enabled = False

        self.shading_mode = MeshDrawable.MODE_LIGHTING
        self.shading_names = [
            "A: Flat Color",
            "B: Vertex Color Interp",
            "C: Lighting",
            "D: Texture Mapping",
            "E: Combined (B+C+D)",
        ]
        self.lighting_algo_idx = 1
        self.lighting_algo_names = ["Gouraud", "Phong"]

        self.polygon_mode = 0
        self.polygon_mode_names = ["Fill", "Wireframe", "Point"]
        self.show_depth_map = False

        self.category_idx = 1
        self.categories = ["2D", "3D", "Math Surface", "Import .obj/.ply", "Loss Optimizer Surface"]

        self.selected_2d = 0
        self.selected_3d = 0

        self.radius = 1.0
        self.width = 2.0
        self.height = 2.0
        self.segments = 36
        self.sectors = 36
        self.stacks = 18
        self.inner_radius = 0.3

        self.math_expr = ""
        self.math_x_min = -2.0
        self.math_x_max = 2.0
        self.math_y_min = -2.0
        self.math_y_max = 2.0
        self.math_steps = 60
        self.math_error = ""

        self.optimizer = OptimizerController()

        self.axes_length = 30.0
        self.show_coordinate_axes = True
        self.coordinate_axes = CoordinateAxesOverlay(axes_length=self.axes_length, enabled_categories=(2, 4))

        self.mesh_path = ""
        self.texture_path = ""

        self.mouse_pos = (0.0, 0.0)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthFunc(GL.GL_LESS)

        # self.impl = _create_imgui_renderer(self.win)
        # glfw.set_key_callback(self.win, self.on_key)
        # glfw.set_cursor_pos_callback(self.win, self.on_mouse_move)
        # glfw.set_scroll_callback(self.win, self.on_scroll)
        # glfw.set_framebuffer_size_callback(self.win, self.on_resize)
        # fbw, fbh = glfw.get_framebuffer_size(self.win)
        # self.on_resize(self.win, fbw, fbh)
        self.impl = _create_imgui_renderer(self.win)

        glfw.set_key_callback(self.win, self._dispatch_key)
        glfw.set_char_callback(self.win, self._dispatch_char)
        glfw.set_scroll_callback(self.win, self._dispatch_scroll)
        glfw.set_cursor_pos_callback(self.win, self._dispatch_cursor_pos)
        glfw.set_mouse_button_callback(self.win, self._dispatch_mouse_button)
        glfw.set_framebuffer_size_callback(self.win, self.on_resize)
        
    def _dispatch_key(self, win, key, scancode, action, mods):
        if hasattr(self.impl, "keyboard_callback"):
            self.impl.keyboard_callback(win, key, scancode, action, mods)
        self.on_key(win, key, scancode, action, mods)

    def _dispatch_char(self, win, char):
        if hasattr(self.impl, "char_callback"):
            self.impl.char_callback(win, char)

    def _dispatch_scroll(self, win, dx, dy):
        if hasattr(self.impl, "scroll_callback"):
            self.impl.scroll_callback(win, dx, dy)
        self.on_scroll(win, dx, dy)

    def _dispatch_cursor_pos(self, win, x, y):
        if hasattr(self.impl, "cursor_pos_callback"):
            self.impl.cursor_pos_callback(win, x, y)
        self.on_mouse_move(win, x, y)

    def _dispatch_mouse_button(self, win, button, action, mods):
        if hasattr(self.impl, "mouse_button_callback"):
            self.impl.mouse_button_callback(win, button, action, mods)
    @property
    def camera(self):
        return self.cameras[self.current_camera_idx]

    def on_resize(self, _win, width, height):
        GL.glViewport(0, 0, max(1, width), max(1, height))
        for cam in self.cameras:
            cam.set_aspect(width, height)

    def on_key(self, _win, key, _scancode, action, _mods):
        io = imgui.get_io()
        if io.want_capture_keyboard:
            return
        if action not in (glfw.PRESS, glfw.REPEAT):
            return

        if key in (glfw.KEY_ESCAPE, glfw.KEY_Q):
            glfw.set_window_should_close(self.win, True)
            return

        # Camera switching
        if key == glfw.KEY_C:
            self.current_camera_idx = (self.current_camera_idx + 1) % len(self.cameras)
        if key == glfw.KEY_O:
            self.camera.cycle_projection_mode()
        # Light toggles
        if key == glfw.KEY_1:
            self.light_1_enabled = not self.light_1_enabled
        if key == glfw.KEY_2:
            self.light_2_enabled = not self.light_2_enabled

        # Display modes
        if key == glfw.KEY_Z:
            self.show_depth_map = not self.show_depth_map

        if key == glfw.KEY_F:
            self.polygon_mode = (self.polygon_mode + 1) % len(self.polygon_mode_names)

        # Zoom keyboard shortcut
        if key in (glfw.KEY_EQUAL, glfw.KEY_KP_ADD):
            self.camera.zoom(2.0)
        if key in (glfw.KEY_MINUS, glfw.KEY_KP_SUBTRACT):
            self.camera.zoom(-2.0)

    def on_mouse_move(self, win, xpos, ypos):
        io = imgui.get_io()
        if io.want_capture_mouse:
            return
        old_x, old_y = self.mouse_pos
        self.mouse_pos = (xpos, ypos)

        dx = xpos - old_x
        dy = ypos - old_y

        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            self.camera.orbit(-dx * 0.005, -dy * 0.005)

        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS:
            self.camera.pan(dx, -dy, scale=0.005)

    def on_scroll(self, _win, _deltax, deltay):
        self.camera.zoom(deltay * 1.5)

    # def _spawn_transform(self):
    #     # Spread spawned objects on a grid for easier comparison.
    #     idx = self.next_spawn_idx
    #     self.next_spawn_idx += 1
    #     col = idx % 4
    #     row = idx // 4
    #     tx = (col - 1.5) * 3.0
    #     ty = (1.0 - row) * 2.5
    #     tz = 0.0
    #     return T.translate(tx, ty, tz)

    def _model_center_to_origin(self, drawable):
        if hasattr(drawable, "vertices") and drawable.vertices is not None and len(drawable.vertices) > 0:
            c = np.mean(drawable.vertices, axis = 0)
            return T.translate(-float(c[0]), -float(c[1]), -float(c[2]))
        return np.identity(4, dtype=np.float32)
    
    def _reset_view_home(self):
        self.current_camera_idx = 0
        self.cameras[0].position = np.array([0.0, 0.0, 6.0], dtype=np.float32)
        self.cameras[0].target = np.array([0.0, 0.0, 0.0], dtype=np.float32)

    def _draw_coordinate_axes(self, proj_mat, view_mat):
        self.coordinate_axes.draw(
            category_idx=self.category_idx,
            projection=proj_mat,
            view=view_mat,
            show=self.show_coordinate_axes,
            light_1_enabled=self.light_1_enabled,
            light_2_enabled=self.light_2_enabled,
            brightness=self.light_brightness,
        )

    def _spawn_loss_optimization_scene(self):
        name, drawable = self.optimizer.create_surface_drawable()
        self.scene_items = [SceneItem(name, drawable, np.identity(4, dtype=np.float32))]
        self._reset_view_home()
        self.optimizer.activate_scene()

    def _draw_optimizer_overlays(self, proj_mat, view_mat):
        self.optimizer.draw_overlays(
            proj_mat,
            view_mat,
            light_1_enabled=self.light_1_enabled,
            light_2_enabled=self.light_2_enabled,
            brightness=self.light_brightness,
        )
    
    def spawn_shape(self):
        try:
            if self.category_idx == 4:
                self._spawn_loss_optimization_scene()
                self.math_error = ""
                return

            if self.category_idx == 0:
                name = Geo2D.SHAPES[self.selected_2d]
                drawable = create_geo2d_drawable(
                    name, radius=self.radius, width=self.width,
                    height=self.height, segments=self.segments
                )

            elif self.category_idx == 1:
                name = Geo3D.SHAPES[self.selected_3d]
                drawable = create_geo3d_drawable(
                    name, radius=self.radius, height=self.height,
                    sectors=self.sectors, stacks=self.stacks,
                    inner_radius=self.inner_radius
                )

            elif self.category_idx == 2:
                name = "Math Surface"
                drawable = create_math_surface_drawable(
                    self.math_expr,
                    x_min=self.math_x_min, x_max=self.math_x_max,
                    y_min=self.math_y_min, y_max=self.math_y_max,
                    steps=self.math_steps
                )
                self.math_error = ""

            else:
                name = os.path.basename(self.mesh_path.strip())
                drawable = create_drawable_from_file(self.mesh_path.strip())

            if self.texture_path.strip():
                drawable.set_texture(self.texture_path.strip())

            model = self._model_center_to_origin(drawable)
            self.scene_items = [SceneItem(name, drawable, model)]
            self.optimizer.clear_state()
            self._reset_view_home()

        except Exception as exc:
            self.math_error = str(exc)
            print("Spawn error:", exc)

    def draw_gui(self):
        draw_control_panel(self)
        imgui.render()
        self.impl.render(imgui.get_draw_data())

    def _apply_polygon_mode(self):
        if self.polygon_mode == 0:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        elif self.polygon_mode == 1:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        else:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_POINT)

    def run(self):
        while not glfw.window_should_close(self.win):
            glfw.poll_events()
            self.impl.process_inputs()

            self._apply_polygon_mode()
            GL.glClearColor(*self.bg_color, 1.0)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            cam = self.camera
            proj_mat = cam.get_projection_matrix()
            view_mat = cam.get_view_matrix()

            if self.optimizer.optimization_active and self.optimizer.simulation_running:
                self.optimizer.step_optimizers(int(self.optimizer.steps_per_frame))

            algo = self.lighting_algo_names[self.lighting_algo_idx].lower()
            for item in self.scene_items:
                item.drawable.draw(
                    proj_mat,
                    view_mat,
                    item.model,
                    shading_mode=self.shading_mode,
                    lighting_algorithm=algo,
                    light_1_enabled=self.light_1_enabled,
                    light_2_enabled=self.light_2_enabled,
                    brightness=self.light_brightness,
                    show_depth_map=self.show_depth_map,
                )

            self._draw_coordinate_axes(proj_mat, view_mat)

            self._draw_optimizer_overlays(proj_mat, view_mat)

            self.draw_gui()
            glfw.swap_buffers(self.win)

        self.impl.shutdown()


def main():
    viewer = Viewer()
    # Spawn a small default scene
    viewer.scene_items.append(SceneItem("Cube", create_geo3d_drawable("Cube", radius=0.8), T.translate(0.0, 0.0, 0.0)))
    viewer.next_spawn_idx = 0
    viewer.run()


if __name__ == "__main__":
    if not glfw.init():
        raise RuntimeError("Failed to initialize GLFW")
    try:
        main()
    finally:
        glfw.terminate()
