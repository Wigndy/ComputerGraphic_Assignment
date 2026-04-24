import os

mtl_path = "road_junction/uploads-files-4395245-Road+Junction.mtl" # Chú ý sửa đúng đường dẫn trên máy bạn

# Danh sách tất cả các từ khóa gọi ảnh trong MTL
texture_keys = ("map_Kd", "map_Ks", "map_Ka", "map_Ns", "map_d", "bump", "map_bump", "disp", "decal")

with open(mtl_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open(mtl_path, 'w', encoding='utf-8') as f:
    for line in lines:
        is_texture_line = False
        
        for key in texture_keys:
            # Nếu dòng bắt đầu bằng từ khóa gọi ảnh (vd: "map_Kd ")
            if line.strip().startswith(key + " "):
                # Cắt bỏ từ khóa để lấy toàn bộ phần đường dẫn phía sau (bao gồm cả dấu cách)
                old_path = line.strip()[len(key):].strip()
                
                # Lấy tên file cuối cùng (loại bỏ mọi thư mục như "New folder/8/")
                filename = os.path.basename(old_path.replace('\\', '/'))
                
                # Ghi đè dòng mới với định dạng chuẩn
                new_line = f"{key} textures/{filename}\n"
                f.write(new_line)
                
                is_texture_line = True
                break # Đã tìm thấy và sửa xong dòng này
                
        # Nếu không phải dòng chứa ảnh, ghi lại nguyên bản
        if not is_texture_line:
            f.write(line)

print("Đã sửa triệt để tất cả đường dẫn ảnh trong file MTL!")