import os

import imgui

from geometry import Geo2D, Geo3D


def draw_control_panel(viewer):
    imgui.new_frame()
    imgui.begin("Control Panel", True)

    imgui.text("Camera")
    changed, viewer.current_camera_idx = imgui.combo(
        "Select Camera",
        viewer.current_camera_idx,
        ["Cam 1 - Free", "Cam 2 - Angled"],
    )
    cam = viewer.camera
    if cam.use_orthographic:
        changed, cam.ortho_size = imgui.slider_float("Ortho Size", cam.ortho_size, 0.2, 30.0)
    else:
        changed, cam.fov = imgui.slider_float("FOV", cam.fov, 10.0, 120.0)

    imgui.separator()
    imgui.text("Lighting")
    changed, viewer.light_1_enabled = imgui.checkbox("Light 1", viewer.light_1_enabled)
    changed, viewer.light_2_enabled = imgui.checkbox("Light 2", viewer.light_2_enabled)
    changed, viewer.light_brightness = imgui.slider_float("Brightness", viewer.light_brightness, 0.0, 2.0)
    changed, viewer.hdri_environment_enabled = imgui.checkbox("HDRI Environment", viewer.hdri_environment_enabled)
    if viewer.hdri_environment_enabled:
        changed, viewer.hdri_environment_intensity = imgui.slider_float("HDRI Intensity", float(viewer.hdri_environment_intensity), 0.0, 2.0)
        changed, viewer.hdri_environment_color = imgui.color_edit3("HDRI Color", *viewer.hdri_environment_color)
    changed, viewer.custom_light_enabled = imgui.checkbox("Custom Light", viewer.custom_light_enabled)
    if viewer.custom_light_enabled:
        changed, viewer.custom_light_position[0] = imgui.slider_float("Custom X", float(viewer.custom_light_position[0]), -60.0, 60.0)
        changed, viewer.custom_light_position[1] = imgui.slider_float("Custom Y", float(viewer.custom_light_position[1]), -60.0, 60.0)
        changed, viewer.custom_light_position[2] = imgui.slider_float("Custom Z", float(viewer.custom_light_position[2]), -60.0, 60.0)
        changed, viewer.custom_light_color = imgui.color_edit3("Custom Color", *viewer.custom_light_color)
        changed, viewer.custom_light_intensity = imgui.slider_float("Custom Intensity", float(viewer.custom_light_intensity), 0.0, 4.0)

    imgui.separator()
    imgui.text("Render")
    changed, viewer.shading_mode = imgui.combo("Shading", viewer.shading_mode, viewer.shading_names)
    changed, viewer.flat_color = imgui.color_edit3("Flat Color", *viewer.flat_color)
    changed, viewer.lighting_algo_idx = imgui.combo("Lighting Algo", viewer.lighting_algo_idx, viewer.lighting_algo_names)
    changed, viewer.polygon_mode = imgui.combo("Polygon", viewer.polygon_mode, viewer.polygon_mode_names)
    changed, viewer.show_depth_map = imgui.checkbox("Show Depth Map", viewer.show_depth_map)
    changed, viewer.show_coordinate_axes = imgui.checkbox("Show Coordinate Axes", viewer.show_coordinate_axes)

    imgui.separator()
    imgui.text("Surface Material")
    changed, viewer.material_roughness = imgui.slider_float("Roughness", float(viewer.material_roughness), 0.0, 1.0)
    changed, viewer.material_metallic = imgui.slider_float("Metallic", float(viewer.material_metallic), 0.0, 1.0)

    imgui.separator()
    imgui.text("Spawn Objects")
    changed, viewer.category_idx = imgui.combo("Category", viewer.category_idx, viewer.categories)

    if viewer.category_idx == 0:
        changed, viewer.selected_2d = imgui.combo("2D Shape", viewer.selected_2d, Geo2D.SHAPES)
        changed, viewer.radius = imgui.slider_float("Radius", viewer.radius, 0.1, 3.0)
        changed, viewer.width = imgui.slider_float("Width", viewer.width, 0.1, 5.0)
        changed, viewer.height = imgui.slider_float("Height", viewer.height, 0.1, 5.0)
        changed, viewer.segments = imgui.slider_int("Segments", int(viewer.segments), 3, 128)

    elif viewer.category_idx == 1:
        changed, viewer.selected_3d = imgui.combo("3D Shape", viewer.selected_3d, Geo3D.SHAPES)
        changed, viewer.radius = imgui.slider_float("Radius", viewer.radius, 0.1, 3.0)
        changed, viewer.height = imgui.slider_float("Height", viewer.height, 0.1, 6.0)
        changed, viewer.sectors = imgui.slider_int("Sectors", int(viewer.sectors), 3, 128)
        changed, viewer.stacks = imgui.slider_int("Stacks", int(viewer.stacks), 3, 128)
        changed, viewer.inner_radius = imgui.slider_float("Inner Radius", viewer.inner_radius, 0.05, 2.0)

    elif viewer.category_idx == 2:
        changed, viewer.math_expr = imgui.input_text("z = f(x, y)", viewer.math_expr, 256)
        if viewer.math_error:
            imgui.text_colored(f"Error: {viewer.math_error}", 1.0, 0.3, 0.3)
        changed, viewer.math_x_min = imgui.slider_float("x min", viewer.math_x_min, -30.0, 0.0)
        changed, viewer.math_x_max = imgui.slider_float("x max", viewer.math_x_max, 0.0, 30.0)
        changed, viewer.math_y_min = imgui.slider_float("y min", viewer.math_y_min, -30.0, 0.0)
        changed, viewer.math_y_max = imgui.slider_float("y max", viewer.math_y_max, 0.0, 30.0)
        changed, viewer.math_steps = imgui.slider_int("Grid steps", int(viewer.math_steps), 8, 200)

    elif viewer.category_idx == 4:
        opt = viewer.optimizer
        changed, opt.loss_function_idx = imgui.combo(
            "Loss Function",
            opt.loss_function_idx,
            opt.loss_function_labels,
        )
        if changed:
            opt.loss_resolution = max(int(opt.loss_resolution), int(opt.recommended_resolution()))
            viewer._spawn_loss_optimization_scene()

        changed, opt.loss_resolution = imgui.slider_int("Grid resolution", int(opt.loss_resolution), 64, 320)
        imgui.text(f"Domain lock: x,y in [{opt.loss_x_min:.1f}, {opt.loss_x_max:.1f}]")
        imgui.text("Rendered height: z = log(1 + f(x,y))")
        imgui.text("Recommended mesh density: 200 x 200")

        imgui.separator()
        imgui.text("Optimization")
        imgui.text("Start point: click directly on the 2D contour panel")

        changed, opt.opt_learning_rate_log10 = imgui.slider_float("log10(Learning Rate)", opt.opt_learning_rate_log10, -5.0, -0.5)
        opt.opt_learning_rate = float(10.0 ** opt.opt_learning_rate_log10)
        imgui.text(f"Learning Rate: {opt.opt_learning_rate:.6f}")

        changed, opt.opt_batch_size = imgui.slider_int("Mini-batch size", int(opt.opt_batch_size), 1, 512)
        changed, opt.opt_momentum_coefficient = imgui.slider_float("Momentum coeff", opt.opt_momentum_coefficient, 0.0, 0.999)
        changed, opt.opt_noise_variance = imgui.slider_float("Noise variance", opt.opt_noise_variance, 0.0, 0.2)
        changed, opt.max_epochs = imgui.slider_int("Max Epochs", int(opt.max_epochs), 10, 10000)
        changed, opt.sim_updates_per_second = imgui.slider_float("Simulation speed (updates/s)", opt.sim_updates_per_second, 0.2, 20.0)
        changed, opt.steps_per_frame = imgui.slider_int("Steps / frame", int(opt.steps_per_frame), 1, 50)
        imgui.text(f"Effective speed: {opt.sim_updates_per_second * max(1, int(opt.steps_per_frame)):.2f} epochs/s")
        changed, opt.use_random_reset_start = imgui.checkbox("Reset with random start", opt.use_random_reset_start)

        imgui.separator()
        imgui.text("Rolling Ball + Contour")
        changed, opt.show_contour_map = imgui.checkbox("Show 2D contour panel", opt.show_contour_map)
        changed, opt.contour_view_mode = imgui.combo("Contour panel mode", opt.contour_view_mode, opt.contour_view_modes)
        if opt.contour_view_mode == 1:
            changed, opt.contour_inset_fraction = imgui.slider_float("Inset size", opt.contour_inset_fraction, 0.20, 0.60)
        contour_style_changed = False
        changed, opt.contour_levels = imgui.slider_int("Contour levels", int(opt.contour_levels), 4, 24)
        contour_style_changed = contour_style_changed or changed
        changed, opt.contour_grid_divisions = imgui.slider_int("Grid divisions", int(opt.contour_grid_divisions), 1, 10)
        contour_style_changed = contour_style_changed or changed
        changed, opt.contour_heatmap_opacity = imgui.slider_float("Heatmap opacity", float(opt.contour_heatmap_opacity), 0.0, 0.50)
        contour_style_changed = contour_style_changed or changed
        changed, opt.contour_line_opacity = imgui.slider_float("Contour line opacity", float(opt.contour_line_opacity), 0.20, 1.0)
        contour_style_changed = contour_style_changed or changed
        if contour_style_changed and opt.optimization_active:
            opt._build_contour_drawable()
        imgui.text("Ball Decay (fixed): 0.98")
        imgui.text("Speed Lift (fixed): 0.00")
        imgui.text("Min Clearance (fixed): 0.01")
        imgui.text("Start height: f(x_start, y_start) + 0.01")

        if imgui.button("Rebuild surface + contour"):
            viewer._spawn_loss_optimization_scene()

        if imgui.button("Play"):
            if opt.optimization_active:
                if opt.current_epoch >= opt.max_epochs:
                    opt.build_optimizers(randomize_start=opt.use_random_reset_start)
                opt.simulation_running = True

        imgui.same_line()
        if imgui.button("Pause"):
            opt.simulation_running = False

        imgui.same_line()
        if imgui.button("Resume"):
            if opt.optimization_active and opt.current_epoch < opt.max_epochs:
                opt.simulation_running = True

        imgui.same_line()
        if imgui.button("Reset"):
            if opt.optimization_active:
                opt.build_optimizers(randomize_start=opt.use_random_reset_start)

        imgui.same_line()
        if imgui.button("Step Once"):
            opt.step_optimizers(1)

        if opt.optimization_active:
            imgui.text("Trajectory Colors: Batch GD=Red, SGD=Yellow, Mini-batch=Blue, Momentum=Purple, Adam=Green")
            imgui.text(f"Simulation: {'Running' if opt.simulation_running else 'Paused'}")
            imgui.text(f"Epoch: {opt.current_epoch}/{opt.max_epochs}")
            imgui.text(f"Reset start: ({opt.last_reset_start[0]:.3f}, {opt.last_reset_start[1]:.3f})")

            imgui.separator()
            imgui.text("Metrics (Realtime)")
            imgui.text("Algorithm | Epoch | Loss(z) | |Grad|")
            for opt_type, epoch, loss_val, grad_norm in opt.optimizer_metrics():
                c = opt.optimizer_colors[opt_type]
                name = opt.optimizer_display_names[opt_type]
                imgui.text_colored(
                    f"{name:16s} | {epoch:5d} | {loss_val:10.6f} | {grad_norm:10.6f}",
                    float(c[0]), float(c[1]), float(c[2])
                )

    else:
        changed, viewer.mesh_path = imgui.input_text("Mesh path (.obj/.ply)", viewer.mesh_path, 512)

    changed, viewer.texture_path = imgui.input_text("Texture path (optional)", viewer.texture_path, 512)
    if viewer.texture_assets:
        texture_labels = [os.path.basename(p) for p in viewer.texture_assets]
        changed, viewer.texture_asset_idx = imgui.combo("Texture Asset", int(viewer.texture_asset_idx), texture_labels)
        changed, viewer.auto_texture_from_assets = imgui.checkbox("Auto apply selected asset", viewer.auto_texture_from_assets)
    else:
        imgui.text("No textures found in BTL/assets")

    if imgui.button("Spawn Shape"):
        viewer.spawn_shape()

    imgui.same_line()
    if imgui.button("Clear Scene"):
        viewer.scene_items = []
        viewer.optimizer.clear_state()
        viewer._reset_view_home()

    imgui.separator()
    imgui.text(f"Objects in scene: {len(viewer.scene_items)}")
    imgui.text("Mouse: Left=Rotate (or drag light marker), Wheel=Zoom")
    if viewer.custom_light_enabled:
        imgui.text("Tip: click near bright light marker, then drag to move around object")
        imgui.text("When marker is grabbed, camera rotation is locked")
        imgui.text("Hold Shift while dragging for precision light movement")
    imgui.text("Keys: C=Switch camera, 1/2=Toggle lights, F=Wireframe cycle, Z=Depth")

    imgui.end()
