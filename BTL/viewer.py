import os
import sys

# If pyimgui is unavailable in the current interpreter (e.g. Python 3.13),
# re-launch with the known working conda interpreter.
try:
    import imgui
except ModuleNotFoundError:
    fallback_python = "/opt/homebrew/anaconda3/bin/python"
    if os.path.exists(fallback_python) and os.path.realpath(sys.executable) != os.path.realpath(fallback_python):
        os.execv(fallback_python, [fallback_python, os.path.abspath(__file__), *sys.argv[1:]])
    raise

import OpenGL.GL as GL
import glfw
import numpy as np

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

        free_cam = Camera([0.0, 0.0, 3.0], [0.0, 0.0, 0.0], up=[0.0, 1.0, 0.0], orbit_axis=[0.0, 1.0, 0.0], allow_pitch=True)
        free_cam.use_orthographic = True
        free_cam.ortho_size = 3.0
        free_cam.fov = 35.0
        angled_cam = Camera([28.0, -28.0, 18.0], [0.0, 0.0, 0.0], up=[0.0, 0.0, 1.0], orbit_axis=[0.0, 0.0, 1.0], allow_pitch=False)
        self.cameras = [free_cam, angled_cam]
        self.current_camera_idx = 0

        self.bg_color = [0.10, 0.10, 0.14]
        self.light_brightness = 1.0
        self.light_1_enabled = True
        self.light_2_enabled = False
        self.hdri_environment_enabled = False
        self.hdri_environment_intensity = 0.55
        self.hdri_environment_color = [1.0, 1.0, 1.0]
        self.custom_light_enabled = False
        self.custom_light_position = [4.0, 4.0, 4.0]
        self.custom_light_color = [1.0, 1.0, 1.0]
        self.custom_light_intensity = 1.0
        self.custom_light_dragging = False
        self.custom_light_pick_radius_px = 30.0

        self.shading_mode = MeshDrawable.MODE_LIGHTING
        self.shading_names = [
            "A: Flat Color",
            "B: Vertex Color Interp",
            "C: Lighting",
            "D: Texture Mapping",
            "E: Combined (B+C+D)",
        ]
        self.flat_color = [0.9, 0.6, 0.2]
        self.material_roughness = 0.25
        self.material_metallic = 0.05
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
        self.custom_light_marker = create_geo3d_drawable("Sphere (Lat-Long)", radius=0.22, sectors=14, stacks=10)
        self.custom_light_marker.flat_color = np.array([1.0, 0.95, 0.35], dtype=np.float32)
        self.custom_light_marker.set_vertex_color(np.array([1.0, 0.95, 0.35], dtype=np.float32))
        self.custom_light_marker.set_emissive(color=np.array([1.0, 0.95, 0.35], dtype=np.float32), strength=0.35)

        self.mesh_path = ""
        self.texture_path = ""
        self.auto_texture_from_assets = True
        self.texture_assets = self._discover_texture_assets()
        self.texture_asset_idx = 0

        self.mouse_pos = (0.0, 0.0)
        self.fb_width = max(1, width)
        self.fb_height = max(1, height)
        self._picking_contour_start = False
        self._last_sim_time = glfw.get_time()
        self._sim_time_accum = 0.0

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
        self.on_mouse_button(win, button, action, mods)

    @property
    def camera(self):
        return self.cameras[self.current_camera_idx]

    def _discover_texture_assets(self):
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        if not os.path.isdir(assets_dir):
            return []
        supported = {".png", ".jpg", ".jpeg", ".bmp", ".tga", ".webp"}
        textures = []
        for name in sorted(os.listdir(assets_dir)):
            path = os.path.join(assets_dir, name)
            if not os.path.isfile(path):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext in supported:
                textures.append(path)
        return textures

    def _selected_texture_asset(self):
        if not self.texture_assets:
            return ""
        idx = int(np.clip(self.texture_asset_idx, 0, len(self.texture_assets) - 1))
        return self.texture_assets[idx]

    def on_resize(self, _win, width, height):
        self.fb_width = max(1, int(width))
        self.fb_height = max(1, int(height))
        GL.glViewport(0, 0, self.fb_width, self.fb_height)
        for cam in self.cameras:
            cam.set_aspect(width, height)

    def _main_and_contour_viewports(self):
        w = max(1, int(self.fb_width))
        h = max(1, int(self.fb_height))
        opt = self.optimizer

        if not opt.should_render_contour_panel():
            return (0, 0, w, h), None

        if opt.contour_view_mode == 0:
            main_w = max(1, w // 2)
            contour_w = max(1, w - main_w)
            return (0, 0, main_w, h), (main_w, 0, contour_w, h)

        inset_frac = float(np.clip(opt.contour_inset_fraction, 0.2, 0.6))
        inset_w = max(1, int(w * inset_frac))
        inset_h = max(1, int(h * inset_frac))
        margin = max(8, int(0.02 * min(w, h)))
        inset_x = max(0, w - inset_w - margin)
        inset_y = margin
        return (0, 0, w, h), (inset_x, inset_y, inset_w, inset_h)

    def _main_projection_and_view(self):
        main_vp, _ = self._main_and_contour_viewports()
        cam = self.camera
        main_w = max(1, int(main_vp[2]))
        main_h = max(1, int(main_vp[3]))
        aspect = float(main_w) / float(main_h)
        if cam.use_orthographic:
            half_h = float(cam.ortho_size)
            half_w = half_h * aspect
            proj = T.ortho(-half_w, half_w, -half_h, half_h, -cam.far, cam.far)
        else:
            proj = T.perspective(cam.fov, aspect, cam.near, cam.far)
        return proj, cam.get_view_matrix(), main_vp

    @staticmethod
    def _project_world_to_fb(world_pos, proj_mat, view_mat, viewport):
        p = np.array([float(world_pos[0]), float(world_pos[1]), float(world_pos[2]), 1.0], dtype=np.float32)
        clip = np.asarray(proj_mat, dtype=np.float32) @ (np.asarray(view_mat, dtype=np.float32) @ p)
        if abs(float(clip[3])) < 1e-8:
            return None
        ndc = clip[:3] / clip[3]
        x = float(viewport[0]) + (float(ndc[0]) * 0.5 + 0.5) * float(viewport[2])
        y = float(viewport[1]) + (float(ndc[1]) * 0.5 + 0.5) * float(viewport[3])
        return x, y

    def _begin_custom_light_drag(self, win):
        if not self.custom_light_enabled:
            return False
        proj, view, main_vp = self._main_projection_and_view()
        xpos, ypos = glfw.get_cursor_pos(win)
        fb_x, fb_y = self._cursor_to_framebuffer(xpos, ypos)
        light_fb = self._project_world_to_fb(self.custom_light_position, proj, view, main_vp)
        if light_fb is None:
            return False
        dx = float(fb_x - light_fb[0])
        dy = float(fb_y - light_fb[1])
        if np.hypot(dx, dy) > float(self.custom_light_pick_radius_px):
            return False
        self.custom_light_dragging = True
        return True

    def _drag_custom_light(self, dx, dy):
        target = np.asarray(self.camera.target, dtype=np.float32)
        pos = np.asarray(self.custom_light_position, dtype=np.float32)
        rel = pos - target
        radius = float(np.linalg.norm(rel))
        if radius < 1e-5:
            rel = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            radius = 1.0

        up = np.asarray(self.camera.up, dtype=np.float32)
        up_norm = float(np.linalg.norm(up))
        if up_norm < 1e-6:
            up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        else:
            up = up / up_norm

        view_dir = rel / radius
        right = np.cross(up, view_dir)
        right_norm = float(np.linalg.norm(right))
        if right_norm < 1e-6:
            right = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        else:
            right = right / right_norm

        # Map drag direction to light motion in the same cursor direction.
        precision = 0.35 if (glfw.get_key(self.win, glfw.KEY_LEFT_SHIFT) == glfw.PRESS or glfw.get_key(self.win, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS) else 1.0
        yaw = float(dx) * 0.01 * precision
        pitch = float(dy) * 0.01 * precision
        r4 = np.array([rel[0], rel[1], rel[2], 1.0], dtype=np.float32)
        rot_yaw = T.rotate(axis=up, radians=yaw)
        rot_pitch = T.rotate(axis=right, radians=pitch)
        new_rel = (rot_pitch @ (rot_yaw @ r4))[:3]

        new_norm = float(np.linalg.norm(new_rel))
        if new_norm < 1e-6:
            return
        new_rel = (new_rel / new_norm) * radius
        new_pos = target + new_rel
        self.custom_light_position = [float(new_pos[0]), float(new_pos[1]), float(new_pos[2])]

    @staticmethod
    def _clear_viewport(vp, color):
        x, y, w, h = vp
        GL.glEnable(GL.GL_SCISSOR_TEST)
        GL.glScissor(int(x), int(y), int(w), int(h))
        GL.glClearColor(float(color[0]), float(color[1]), float(color[2]), 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glDisable(GL.GL_SCISSOR_TEST)

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

    def _cursor_to_framebuffer(self, xpos, ypos):
        win_w, win_h = glfw.get_window_size(self.win)
        win_w = max(1, int(win_w))
        win_h = max(1, int(win_h))

        sx = float(self.fb_width) / float(win_w)
        sy = float(self.fb_height) / float(win_h)
        fb_x = float(xpos) * sx
        fb_y = float(self.fb_height) - float(ypos) * sy
        return fb_x, fb_y

    def _contour_pick_to_domain(self, xpos, ypos):
        _, contour_vp = self._main_and_contour_viewports()
        if contour_vp is None:
            return None

        fb_x, fb_y = self._cursor_to_framebuffer(xpos, ypos)
        vx, vy, vw, vh = contour_vp

        if fb_x < vx or fb_x > (vx + vw) or fb_y < vy or fb_y > (vy + vh):
            return None

        u = (fb_x - float(vx)) / float(max(1, vw))
        v = (fb_y - float(vy)) / float(max(1, vh))
        opt = self.optimizer
        x = opt.loss_x_min + u * (opt.loss_x_max - opt.loss_x_min)
        y = opt.loss_y_min + v * (opt.loss_y_max - opt.loss_y_min)
        return float(x), float(y)

    def on_mouse_button(self, win, button, action, _mods):
        if action == glfw.RELEASE:
            self._picking_contour_start = False
            self.custom_light_dragging = False

        io = imgui.get_io()
        if io.want_capture_mouse:
            return

        if button != glfw.MOUSE_BUTTON_LEFT or action != glfw.PRESS:
            return

        if self._begin_custom_light_drag(win):
            return

        if self.category_idx != 4 or not self.optimizer.should_render_contour_panel():
            return

        xpos, ypos = glfw.get_cursor_pos(win)
        picked = self._contour_pick_to_domain(xpos, ypos)
        if picked is None:
            return

        self._picking_contour_start = True
        self.optimizer.set_start_point(picked[0], picked[1], rebuild=True)

    def on_mouse_move(self, win, xpos, ypos):
        io = imgui.get_io()
        if io.want_capture_mouse:
            return
        old_x, old_y = self.mouse_pos
        self.mouse_pos = (xpos, ypos)

        dx = xpos - old_x
        dy = ypos - old_y

        if self.custom_light_dragging:
            self._drag_custom_light(dx, dy)
            return

        # Robust capture: if left button is held and cursor is near light marker,
        # switch to light-drag mode immediately (prevents accidental camera orbit).
        if self.custom_light_enabled and glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            if self._begin_custom_light_drag(win):
                self._drag_custom_light(dx, dy)
                return

        if self._picking_contour_start:
            return

        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
            self.camera.orbit(-dx * 0.005, -dy * 0.005)

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
        self.cameras[0].position = np.array([0.0, 0.0, 3.0], dtype=np.float32)
        self.cameras[0].target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.cameras[0].up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.cameras[0].orbit_axis = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.cameras[0].allow_pitch = True
        self.cameras[0].use_orthographic = True
        self.cameras[0].ortho_size = 3.0
        self.cameras[0].fov = 35.0

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
        # Loss landscape view: wider perspective and deeper far plane for global observation.
        self.cameras[0].use_orthographic = False
        self.cameras[0].fov = 68.0
        self.cameras[0].near = 0.05
        self.cameras[0].far = 2000.0
        self.cameras[0].position = np.array([0.0, -18.0, 10.5], dtype=np.float32)
        self.cameras[0].target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.cameras[0].up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
        self.optimizer.activate_scene()
        self._last_sim_time = glfw.get_time()
        self._sim_time_accum = 0.0

    def _draw_optimizer_overlays(self, proj_mat, view_mat):
        self.optimizer.draw_overlays(
            proj_mat,
            view_mat,
            light_1_enabled=self.light_1_enabled,
            light_2_enabled=self.light_2_enabled,
            brightness=self.light_brightness,
            hdri_environment_enabled=self.hdri_environment_enabled,
            hdri_environment_intensity=self.hdri_environment_intensity,
            hdri_environment_color=self.hdri_environment_color,
            custom_light_enabled=self.custom_light_enabled,
            custom_light_position=self.custom_light_position,
            custom_light_color=self.custom_light_color,
            custom_light_intensity=self.custom_light_intensity,
            material_roughness=self.material_roughness,
            material_metallic=self.material_metallic,
        )

    def _draw_custom_light_marker(self, proj_mat, view_mat):
        if not self.custom_light_enabled or self.custom_light_marker is None:
            return
        marker_model = T.translate(
            float(self.custom_light_position[0]),
            float(self.custom_light_position[1]),
            float(self.custom_light_position[2]),
        )
        self.custom_light_marker.draw(
            proj_mat,
            view_mat,
            marker_model,
            shading_mode=MeshDrawable.MODE_LIGHTING,
            lighting_algorithm="phong",
            light_1_enabled=self.light_1_enabled,
            light_2_enabled=self.light_2_enabled,
            brightness=self.light_brightness,
            hdri_environment_enabled=self.hdri_environment_enabled,
            hdri_environment_intensity=self.hdri_environment_intensity,
            hdri_environment_color=self.hdri_environment_color,
            custom_light_enabled=False,
            emissive_color=np.array(self.custom_light_color, dtype=np.float32),
            emissive_strength=0.55,
            show_depth_map=False,
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
            elif self.auto_texture_from_assets:
                asset_texture = self._selected_texture_asset()
                if asset_texture:
                    drawable.set_texture(asset_texture)

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

            now = glfw.get_time()
            dt = max(0.0, float(now - self._last_sim_time))
            self._last_sim_time = now

            self._apply_polygon_mode()
            fbw, fbh = glfw.get_framebuffer_size(self.win)
            self.fb_width = max(1, int(fbw))
            self.fb_height = max(1, int(fbh))

            GL.glViewport(0, 0, self.fb_width, self.fb_height)
            GL.glClearColor(*self.bg_color, 1.0)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            main_vp, contour_vp = self._main_and_contour_viewports()

            main_x, main_y, main_w, main_h = main_vp
            GL.glViewport(int(main_x), int(main_y), int(main_w), int(main_h))

            cam = self.camera
            proj_mat, view_mat, _ = self._main_projection_and_view()

            if self.optimizer.optimization_active and self.optimizer.simulation_running:
                self.optimizer.advance_playback(dt)
            else:
                self._sim_time_accum = 0.0

            algo = self.lighting_algo_names[self.lighting_algo_idx].lower()
            depth_visual_enabled = bool(self.show_depth_map and self.category_idx in (2, 4))
            for idx, item in enumerate(self.scene_items):
                transparent_loss_fill = bool(self.category_idx == 4 and self.polygon_mode == 0 and idx == 0)
                if transparent_loss_fill:
                    GL.glEnable(GL.GL_BLEND)
                    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
                    GL.glDepthMask(GL.GL_FALSE)

                item.drawable.draw(
                    proj_mat,
                    view_mat,
                    item.model,
                    shading_mode=self.shading_mode,
                    alpha_override=0.28 if transparent_loss_fill else 1.0,
                    flat_color_override=self.flat_color,
                    lighting_algorithm=algo,
                    light_1_enabled=self.light_1_enabled,
                    light_2_enabled=self.light_2_enabled,
                    brightness=self.light_brightness,
                    hdri_environment_enabled=self.hdri_environment_enabled,
                    hdri_environment_intensity=self.hdri_environment_intensity,
                    hdri_environment_color=self.hdri_environment_color,
                    custom_light_enabled=self.custom_light_enabled,
                    custom_light_position=self.custom_light_position,
                    custom_light_color=self.custom_light_color,
                    custom_light_intensity=self.custom_light_intensity,
                    material_roughness=self.material_roughness,
                    material_metallic=self.material_metallic,
                    show_depth_map=depth_visual_enabled,
                    near_plane=cam.near,
                    far_plane=cam.far,
                    is_orthographic=cam.use_orthographic,
                    depth_colormap_mode=1,
                )
                if transparent_loss_fill:
                    GL.glDepthMask(GL.GL_TRUE)
                    GL.glDisable(GL.GL_BLEND)

            self._draw_coordinate_axes(proj_mat, view_mat)

            self._draw_optimizer_overlays(proj_mat, view_mat)
            self._draw_custom_light_marker(proj_mat, view_mat)

            if contour_vp is not None:
                contour_bg = [0.05, 0.06, 0.08]
                self._clear_viewport(contour_vp, contour_bg)
                GL.glViewport(int(contour_vp[0]), int(contour_vp[1]), int(contour_vp[2]), int(contour_vp[3]))
                self.optimizer.draw_contour_panel()

            GL.glViewport(0, 0, self.fb_width, self.fb_height)

            self.draw_gui()
            glfw.swap_buffers(self.win)

        self.impl.shutdown()


def main():
    viewer = Viewer()
    # Spawn a small default scene
    default_cube = create_geo3d_drawable("Cube", radius=0.8)
    if viewer.auto_texture_from_assets:
        default_asset = viewer._selected_texture_asset()
        if default_asset:
            default_cube.set_texture(default_asset)
    viewer.scene_items.append(SceneItem("Cube", default_cube, T.translate(0.0, 0.0, 0.0)))
    viewer.next_spawn_idx = 0
    viewer.run()


if __name__ == "__main__":
    if not glfw.init():
        raise RuntimeError("Failed to initialize GLFW")
    try:
        main()
    finally:
        glfw.terminate()
