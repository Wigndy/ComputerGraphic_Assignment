import sys
import os
import ctypes
import glfw
import numpy as np
import OpenGL.GL as GL

# Các import từ thư viện của bạn
from libs.shader import *
from libs import transform as T
from libs.buffer import *
from libs.lighting import LightingManager

class Sphere(object):
    def __init__(self, vert_shader, frag_shader, radius=1.0, sectors=36, stacks=18):
        """
        Khởi tạo hình cầu.
        :param radius: Bán kính hình cầu
        :param sectors: Số lượng phân đoạn dọc (kinh tuyến)
        :param stacks: Số lượng phân đoạn ngang (vĩ tuyến)
        """
        self.vert_shader = vert_shader
        self.frag_shader = frag_shader
        
        vertices = []
        normals = []
        colors = []
        
        # 1. Sinh tọa độ đỉnh, pháp tuyến và màu sắc
        for i in range(stacks + 1):
            # Vĩ độ (latitude) từ pi/2 tới -pi/2
            phi = np.pi / 2 - i * np.pi / stacks
            xy = radius * np.cos(phi)
            z = radius * np.sin(phi)
            
            for j in range(sectors + 1):
                # Kinh độ (longitude) từ 0 tới 2*pi
                theta = j * 2 * np.pi / sectors
                
                x = xy * np.cos(theta)
                y = xy * np.sin(theta)
                
                vertices.append([x, y, z])
                
                # Đối với hình cầu tâm (0,0,0), pháp tuyến chính là tọa độ đỉnh chuẩn hóa
                nx, ny, nz = x / radius, y / radius, z / radius
                normals.append([nx, ny, nz])
                
                # Tạo màu sắc dựa trên pháp tuyến (ánh xạ từ dải [-1, 1] sang dải [0, 1] của RGB)
                r, g, b = (nx + 1.0) / 2.0, (ny + 1.0) / 2.0, (nz + 1.0) / 2.0
                colors.append([r, g, b])
                
        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.colors = np.array(colors, dtype=np.float32)
        
        # 2. Sinh indices (chỉ mục) để nối các điểm thành các hình tam giác
        indices = []
        for i in range(stacks):
            k1 = i * (sectors + 1)
            k2 = k1 + sectors + 1
            
            for j in range(sectors):
                if i != 0:
                    indices.extend([k1, k2, k1 + 1])
                if i != (stacks - 1):
                    indices.extend([k1 + 1, k2, k2 + 1])
                
                k1 += 1
                k2 += 1
                
        self.indices = np.array(indices, dtype=np.int32)

        # 3. Khởi tạo các thành phần OpenGL
        self.vao = VAO()
        self.shader = Shader(vert_shader, frag_shader)
        self.uma = UManager(self.shader)
        self.lighting = LightingManager(self.uma)
        
        self.selected_texture = 0

    def setup(self):
        # Thiết lập VAO cho hình cầu (tương tự Cube)
        self.vao.add_vbo(0, self.vertices, ncomponents=3, stride=0, offset=None)
        self.vao.add_vbo(1, self.colors, ncomponents=3, stride=0, offset=None)
        
        # Thêm normals nếu dùng Gouraud/Phong
        if 'gouraud' in self.vert_shader.lower() or 'phong' in self.vert_shader.lower():
            self.vao.add_vbo(2, self.normals, ncomponents=3, stride=0, offset=None)

        # Thiết lập EBO
        self.vao.add_ebo(self.indices)

        return self

    def draw(self, projection, view, model):
        GL.glUseProgram(self.shader.render_idx)
        
        # Lưu ý: Nếu muốn hình cầu áp dụng ma trận model (di chuyển, xoay, scale), 
        # bạn nên nhân np.dot(view, model). Ở đây tôi giữ nguyên logic modelview = view giống code Cube của bạn.
        # modelview = view 
        if model is not None:
            # Dùng toán tử @ để nhân ma trận trong numpy (View * Model)
            modelview = view @ model 
        else:
            modelview = view

        self.uma.upload_uniform_matrix4fv(projection, 'projection', True)
        self.uma.upload_uniform_matrix4fv(modelview, 'modelview', True)
        
        # Cài đặt ánh sáng
        if 'gouraud' in self.vert_shader.lower():
            self.lighting.setup_gouraud()
        elif 'phong' in self.vert_shader.lower():
            self.lighting.setup_phong(mode=1)

        self.vao.activate()
        
        # QUAN TRỌNG: Đổi từ GL_TRIANGLE_STRIP sang GL_TRIANGLES 
        # vì thuật toán sinh indices bên trên tạo ra các tam giác độc lập (phổ biến nhất cho hình cầu).
        GL.glDrawElements(GL.GL_TRIANGLES, self.indices.shape[0], GL.GL_UNSIGNED_INT, None)

    def key_handler(self, key):
        if key == glfw.KEY_1:
            self.selected_texture = 1
        if key == glfw.KEY_2:
            self.selected_texture = 2