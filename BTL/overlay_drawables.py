import OpenGL.GL as GL
import numpy as np

from libs.buffer import VAO
from libs.shader import Shader
from geometry import MeshDrawable


class TrajectoryDrawable:
    """Lightweight GL line-strip drawable for optimizer trajectories."""

    def __init__(self, color):
        self.color = np.asarray(color, dtype=np.float32)
        self.shader = Shader(self._vertex_shader(), self._fragment_shader())
        self.vao = VAO()
        self.vertex_count = 0
        self.initialized = False

    def update_points(self, points_xyz):
        points = np.asarray(points_xyz, dtype=np.float32)
        if points.ndim != 2 or points.shape[1] != 3:
            raise ValueError("points_xyz must have shape (N, 3)")

        self.vertex_count = int(points.shape[0])
        if self.vertex_count <= 0:
            return

        colors = np.tile(self.color, (self.vertex_count, 1)).astype(np.float32)

        if not self.initialized:
            self.vao.add_vbo(0, points, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
            self.vao.add_vbo(1, colors, ncomponents=3, dtype=GL.GL_FLOAT, normalized=False, stride=0, offset=None)
            self.initialized = True
            return

        self.vao.activate()
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vao.vbo[0])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, points, GL.GL_DYNAMIC_DRAW)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vao.vbo[1])
        GL.glBufferData(GL.GL_ARRAY_BUFFER, colors, GL.GL_DYNAMIC_DRAW)
        self.vao.deactivate()

    def draw(self, projection, view):
        if not self.initialized or self.vertex_count < 2:
            return

        GL.glUseProgram(self.shader.render_idx)
        proj_loc = GL.glGetUniformLocation(self.shader.render_idx, "projection")
        mv_loc = GL.glGetUniformLocation(self.shader.render_idx, "modelview")
        GL.glUniformMatrix4fv(proj_loc, 1, True, np.asarray(projection, dtype=np.float32))
        GL.glUniformMatrix4fv(mv_loc, 1, True, np.asarray(view, dtype=np.float32))

        self.vao.activate()
        GL.glDrawArrays(GL.GL_LINE_STRIP, 0, self.vertex_count)
        self.vao.deactivate()

    @staticmethod
    def _vertex_shader():
        return """
#version 330 core
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;

uniform mat4 projection;
uniform mat4 modelview;

out vec3 v_color;

void main(){
    v_color = color;
    gl_Position = projection * modelview * vec4(position, 1.0);
}
"""

    @staticmethod
    def _fragment_shader():
        return """
#version 330 core
in vec3 v_color;
out vec4 fragColor;

void main(){
    fragColor = vec4(v_color, 1.0);
}
"""


def _create_lines_drawable(vertices, colors):
    verts = np.asarray(vertices, dtype=np.float32)
    cols = np.asarray(colors, dtype=np.float32)
    count = int(verts.shape[0])
    normals = np.zeros((count, 3), dtype=np.float32)
    texcoords = np.zeros((count, 2), dtype=np.float32)
    return MeshDrawable(verts, normals, texcoords, colors=cols, primitive=GL.GL_LINES)


def _glyph_segments(letter):
    if letter == "O":
        return [
            ((0.0, 0.0), (1.0, 0.0)),
            ((1.0, 0.0), (1.0, 1.0)),
            ((1.0, 1.0), (0.0, 1.0)),
            ((0.0, 1.0), (0.0, 0.0)),
        ]
    if letter == "x":
        return [
            ((0.0, 0.0), (1.0, 1.0)),
            ((0.0, 1.0), (1.0, 0.0)),
        ]
    if letter == "y":
        return [
            ((0.0, 1.0), (0.5, 0.5)),
            ((1.0, 1.0), (0.5, 0.5)),
            ((0.5, 0.5), (0.5, 0.0)),
        ]
    if letter == "z":
        return [
            ((0.0, 1.0), (1.0, 1.0)),
            ((1.0, 1.0), (0.0, 0.0)),
            ((0.0, 0.0), (1.0, 0.0)),
        ]
    return []


class CoordinateAxesOverlay:
    """Coordinate axes + Ox/Oy/Oz labels rendered as line drawables."""

    def __init__(self, axes_length=30.0, enabled_categories=(2, 4)):
        self.axes_length = float(axes_length)
        self.enabled_categories = set(enabled_categories)
        self.axes_drawable = None
        self.axis_label_drawables = []
        self._build()

    def _make_axis_label_drawable(self, text, origin, u_dir, v_dir, scale=1.2, gap=0.35, color=(1.0, 1.0, 1.0)):
        u = np.asarray(u_dir, dtype=np.float32)
        v = np.asarray(v_dir, dtype=np.float32)
        o = np.asarray(origin, dtype=np.float32)
        col = np.asarray(color, dtype=np.float32)

        vertices = []
        colors = []
        x_offset = 0.0
        for ch in text:
            segs = _glyph_segments(ch)
            for (x0, y0), (x1, y1) in segs:
                p0 = o + (x_offset + x0 * scale) * u + (y0 * scale) * v
                p1 = o + (x_offset + x1 * scale) * u + (y1 * scale) * v
                vertices.extend([p0.tolist(), p1.tolist()])
                colors.extend([col.tolist(), col.tolist()])
            x_offset += scale + gap

        return _create_lines_drawable(vertices, colors)

    def _build(self):
        L = self.axes_length
        vertices = [
            [-L, 0.0, 0.0], [L, 0.0, 0.0],
            [0.0, -L, 0.0], [0.0, L, 0.0],
            [0.0, 0.0, -L], [0.0, 0.0, L],
        ]
        colors = [
            [1.0, 0.0, 0.0], [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0], [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0], [0.0, 0.0, 1.0],
        ]
        self.axes_drawable = _create_lines_drawable(vertices, colors)

        offset = 1.5
        self.axis_label_drawables = [
            self._make_axis_label_drawable(
                "Ox",
                origin=(L + offset, 0.8, 0.0),
                u_dir=(1.0, 0.0, 0.0),
                v_dir=(0.0, 1.0, 0.0),
                scale=1.2,
            ),
            self._make_axis_label_drawable(
                "Oy",
                origin=(0.8, L + offset, 0.0),
                u_dir=(1.0, 0.0, 0.0),
                v_dir=(0.0, 1.0, 0.0),
                scale=1.2,
            ),
            self._make_axis_label_drawable(
                "Oz",
                origin=(0.8, 0.0, L + offset),
                u_dir=(1.0, 0.0, 0.0),
                v_dir=(0.0, 0.0, 1.0),
                scale=1.2,
            ),
        ]

    def draw(self, category_idx, projection, view, show=True, light_1_enabled=True, light_2_enabled=False, brightness=1.0):
        if not show:
            return
        if category_idx not in self.enabled_categories:
            return
        if self.axes_drawable is None:
            return

        identity = np.identity(4, dtype=np.float32)
        self.axes_drawable.draw(
            projection,
            view,
            identity,
            shading_mode=MeshDrawable.MODE_COLOR,
            lighting_algorithm="phong",
            light_1_enabled=light_1_enabled,
            light_2_enabled=light_2_enabled,
            brightness=brightness,
            show_depth_map=False,
        )
        for label in self.axis_label_drawables:
            label.draw(
                projection,
                view,
                identity,
                shading_mode=MeshDrawable.MODE_COLOR,
                lighting_algorithm="phong",
                light_1_enabled=light_1_enabled,
                light_2_enabled=light_2_enabled,
                brightness=brightness,
                show_depth_map=False,
            )
