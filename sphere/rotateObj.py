from OpenGL.GL import shaders
from libs.transform import Trackball
from libs.transform import rotate  # Import hàm rotate bạn vừa đề cập
import numpy as np
import glfw
# import sphere
# from sphere import Sphere
class TransformNode:
    """ Node quản lý phép biến đổi và event bàn phím cho 1 drawable """
    def __init__(self, drawable):
        self.drawable = drawable
        self.is_rotation_mode = False
        self.is_animating = False
        self.angle = 0.0
        self.anim_speed = 2.0
        
        # Khởi tạo ma trận dịch chuyển ban đầu (đưa Sphere sang phần âm trục Ox)
        self.translate_matrix = np.array([
            [1., 0., 0., -5.0],
            [0., 1., 0., 0.0],
            [0., 0., 1., 0.0],
            [0., 0., 0., 1.0]
        ], dtype=np.float32)
        
        # Ma trận model hiện tại
        self.model_matrix = self.translate_matrix

    def update_model_matrix(self):
        """ Hàm bổ trợ để tính toán lại ma trận model dựa trên góc hiện tại """
        rot_matrix = rotate(axis=(0., 0., 1.), angle=self.angle)
        self.model_matrix = rot_matrix @ self.translate_matrix

    def draw(self, projection, view, model=None):
        # Gọi hàm draw của Sphere và truyền model_matrix đã được biến đổi vào
        if self.is_animating:
            self.angle += self.anim_speed
            self.angle %= 360
            self.update_model_matrix()
        self.drawable.draw(projection, view, self.model_matrix)

    def key_handler(self, key):
        # Bật/tắt chế độ xoay khi nhấn R
        if key == glfw.KEY_R:
            self.is_rotation_mode = not self.is_rotation_mode
            status = "BẬT" if self.is_rotation_mode else "TẮT"
            print(f"Chế độ xoay: {status}")

        # Thực hiện xoay khi nhấn O (chỉ khi chế độ xoay đang bật)
        elif key == glfw.KEY_O and self.is_rotation_mode:
            self.angle += 5.0  # Mỗi lần nhấn O xoay 5 độ
            self.angle %= 360
            # Tính ma trận xoay quanh trục Oz (0, 0, 1)
            self.update_model_matrix()
            print(f"Góc hiện tại (Manual): {self.angle:.1f}")
            print(f"Góc hiện tại: {self.angle} độ")
        elif key == glfw.KEY_A:
            self.is_animating = not self.is_animating
            print(f"Animation tự động (A): {'BẬT' if self.is_animating else 'TẮT'}")