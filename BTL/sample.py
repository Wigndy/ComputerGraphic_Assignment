import numpy as np

def create_axes_drawable(length=3.0):
    # Định nghĩa các đỉnh cho 3 đường thẳng (từ gốc tọa độ ra 2 phía hoặc 1 phía)
    # Cấu trúc: [Đỉnh bắt đầu], [Đỉnh kết thúc] cho mỗi trục
    vertices = np.array([
        [-length, 0.0, 0.0], [length, 0.0, 0.0],  # Trục X
        [0.0, -length, 0.0], [0.0, length, 0.0],  # Trục Y
        [0.0, 0.0, -length], [0.0, 0.0, length]   # Trục Z
    ], dtype=np.float32)

    # Nếu engine đồ họa của bạn hỗ trợ truyền màu qua vertex attributes:
    colors = np.array([
        [1.0, 0.0, 0.0], [1.0, 0.0, 0.0],  # Màu đỏ cho X
        [0.0, 1.0, 0.0], [0.0, 1.0, 0.0],  # Màu xanh lá cho Y
        [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]   # Màu xanh dương cho Z
    ], dtype=np.float32)

    # Pháp tuyến (normals) và texcoords không thực sự cần thiết cho đường thẳng (GL_LINES)
    normals = np.zeros_like(vertices)
    texcoords = np.zeros((6, 2), dtype=np.float32)

    # Giả định bạn có lớp LineDrawable hoặc có thể dùng MeshDrawable với primitive GL_LINES
    from OpenGL import GL
    return MeshDrawable(vertices, normals, texcoords, colors=colors, primitive=GL.GL_LINES)
