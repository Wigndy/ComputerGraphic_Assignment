import OpenGL.GL as GL              # standard Python OpenGL wrapper
import OpenGL.GL.shaders as shaders
import glfw                         # lean windows system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args
from itertools import cycle   # cyclic iterator to easily toggle polygon rendering modes
import sys
import os

# Add parent directory to path to import libs
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from libs.transform import Trackball, rotate
import sphere
from sphere import Sphere
from rotateObj import TransformNode
class Axes:
    """ Vẽ hệ trục tọa độ 3D (X: Đỏ, Y: Xanh lá, Z: Xanh dương) """
    def __init__(self, length=3.0):
        vertices = np.array([
            0.0, 0.0, 0.0,   1.0, 0.0, 0.0,  # X axis start
            length, 0.0, 0.0,   1.0, 0.0, 0.0,  # X axis end
            0.0, 0.0, 0.0,   0.0, 1.0, 0.0,  # Y axis start
            0.0, length, 0.0,   0.0, 1.0, 0.0,  # Y axis end
            0.0, 0.0, 0.0,   0.0, 0.0, 1.0,  # Z axis start
            0.0, 0.0, length,   0.0, 0.0, 1.0   # Z axis end
        ], dtype=np.float32)

        VERTEX_SHADER = """
        #version 330 core
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec3 color;
        uniform mat4 projection;
        uniform mat4 view;
        out vec3 fragColor;
        void main() {
            gl_Position = projection * view * vec4(position, 1.0);
            fragColor = color;
        }
        """
        FRAGMENT_SHADER = """
        #version 330 core
        in vec3 fragColor;
        out vec4 outColor;
        void main() {
            outColor = vec4(fragColor, 1.0);
        }
        """
        
        # --- FIX LỖI Ở ĐÂY ---
        # 1. Tạo và Bind VAO ĐẦU TIÊN để PyOpenGL không phàn nàn khi validate shader
        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)

        # 2. Lúc này compile program sẽ an toàn vì đã có VAO
        self.shader = shaders.compileProgram(
            shaders.compileShader(VERTEX_SHADER, GL.GL_VERTEX_SHADER),
            shaders.compileShader(FRAGMENT_SHADER, GL.GL_FRAGMENT_SHADER)
        )

        # 3. Tiếp tục setup VBO và đẩy dữ liệu
        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW)

        # Attribute 0: Position
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, GL.ctypes.c_void_p(0))
        # Attribute 1: Color
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 24, GL.ctypes.c_void_p(12))
        
        # Unbind VAO ở cuối để dọn dẹp
        GL.glBindVertexArray(0)

    def draw(self, projection, view, model=None):
        GL.glUseProgram(self.shader)
        proj_loc = GL.glGetUniformLocation(self.shader, "projection")
        view_loc = GL.glGetUniformLocation(self.shader, "view")
        
        # Gửi ma trận View và Projection xuống GPU
        GL.glUniformMatrix4fv(proj_loc, 1, GL.GL_TRUE, projection)
        GL.glUniformMatrix4fv(view_loc, 1, GL.GL_TRUE, view)

        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_LINES, 0, 6)
        GL.glBindVertexArray(0)

# ------------  Viewer class & windows management ------------------------------
class Viewer:
    """ GLFW viewer windows, with classic initialization & graphics loop """
    def __init__(self, width=800, height=800):
        self.fill_modes = cycle([GL.GL_LINE, GL.GL_POINT, GL.GL_FILL])
        
        # version hints: create GL windows with >= OpenGL 3.3 and core profile
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.RESIZABLE, False)
        glfw.window_hint(glfw.DEPTH_BITS, 16)
        glfw.window_hint(glfw.DOUBLEBUFFER, True)
        self.win = glfw.create_window(width, height, 'Viewer', None, None)

        # make win's OpenGL context current; no OpenGL calls can happen before
        glfw.make_context_current(self.win)

        # initialize trackball
        self.trackball = Trackball()
        self.mouse = (0, 0)

        # register event handlers
        glfw.set_key_callback(self.win, self.on_key)
        glfw.set_cursor_pos_callback(self.win, self.on_mouse_move)
        glfw.set_scroll_callback(self.win, self.on_scroll)

        # useful message to check OpenGL renderer characteristics
        print('OpenGL', GL.glGetString(GL.GL_VERSION).decode() + ', GLSL',
              GL.glGetString(GL.GL_SHADING_LANGUAGE_VERSION).decode() +
              ', Renderer', GL.glGetString(GL.GL_RENDERER).decode())

        # initialize GL by setting viewport and default render characteristics
        GL.glClearColor(0.5, 0.5, 0.5, 0.1)
        #GL.glEnable(GL.GL_CULL_FACE)   # enable backface culling (Exercise 1)
        #GL.glFrontFace(GL.GL_CCW) # GL_CCW: default

        GL.glEnable(GL.GL_DEPTH_TEST)  # enable depth test (Exercise 1)
        GL.glDepthFunc(GL.GL_LESS)   # GL_LESS: default


        # initially empty list of object to draw
        self.drawables = []

    def run(self):
        """ Main render loop for this OpenGL windows """
        while not glfw.window_should_close(self.win):
            # clear draw buffer
            GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

            win_size = glfw.get_window_size(self.win)
            view = self.trackball.view_matrix()
            projection = self.trackball.projection_matrix(win_size)

            # draw our scene objects
            for drawable in self.drawables:
                drawable.draw(projection, view, None)

            # flush render commands, and swap draw buffers
            glfw.swap_buffers(self.win)

            # Poll for and process events
            glfw.poll_events()

    def add(self, *drawables):
        """ add objects to draw in this windows """
        self.drawables.extend(drawables)

    def on_key(self, _win, key, _scancode, action, _mods):
        """ 'Q' or 'Escape' quits """
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_ESCAPE or key == glfw.KEY_Q:
                glfw.set_window_should_close(self.win, True)

            if key == glfw.KEY_W:
                GL.glPolygonMode(GL.GL_FRONT_AND_BACK, next(self.fill_modes))

            for drawable in self.drawables:
                if hasattr(drawable, 'key_handler'):
                    drawable.key_handler(key)

    def on_mouse_move(self, win, xpos, ypos):
        """ Rotate on left-click & drag, pan on right-click & drag """
        old = self.mouse
        self.mouse = (xpos, glfw.get_window_size(win)[1] - ypos)
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_LEFT):
            self.trackball.drag(old, self.mouse, glfw.get_window_size(win))
        if glfw.get_mouse_button(win, glfw.MOUSE_BUTTON_RIGHT):
            self.trackball.pan(old, self.mouse)

    def on_scroll(self, win, _deltax, deltay):
        """ Scroll controls the camera distance to trackball center """
        self.trackball.zoom(deltay, glfw.get_window_size(win)[1])



# -------------- main program and scene setup --------------------------------
def main():

    """ create windows, add shaders & scene objects, then run rendering loop """
    viewer = Viewer()

    # 1. Thêm hệ trục tọa độ (Axes) vào Scene
    axes = Axes(length=4.0)
    viewer.add(axes)

    # 2. Setup Sphere
    sphere_model = Sphere("./phong.vert", "./phong.frag").setup()
    
    # 3. Bọc Sphere bằng TransformNode để điều khiển biến đổi
    orbit_sphere = TransformNode(sphere_model)
    viewer.add(orbit_sphere)

    # start rendering loop
    viewer.run()


if __name__ == '__main__':
    glfw.init()                # initialize windows system glfw
    main()                     # main function keeps variables locally scoped
    glfw.terminate()           # destroy all glfw windows and GL contexts
