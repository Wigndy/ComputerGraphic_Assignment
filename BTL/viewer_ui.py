import imgui

from geometry import Geo2D, Geo3D


def draw_control_panel(viewer):
    imgui.new_frame()
    imgui.begin("Control Panel", True)

    imgui.text("Camera")
    changed, viewer.current_camera_idx = imgui.combo(
        "Select Camera",
        viewer.current_camera_idx,
        ["Cam 1 - Front", "Cam 2 - Angled", "Cam 3 - Top"],
    )
    cam = viewer.camera
    modes = [cam.PROJ_PERSPECTIVE, cam.PROJ_ORTHOGRAPHIC, cam.PROJ_FRUSTUM]
    labels = ["Perspective", "Orthographic", "Frustum"]
    mode_idx = modes.index(cam.projection_mode) if cam.projection_mode in modes else 0
    changed, mode_idx = imgui.combo("Projection", mode_idx, labels)
    if changed:
        cam.projection_mode = modes[mode_idx]

    if cam.projection_mode == cam.PROJ_PERSPECTIVE:
        changed, cam.fov = imgui.slider_float("FOV", cam.fov, 10.0, 120.0)
    elif cam.projection_mode == cam.PROJ_ORTHOGRAPHIC:
        changed, cam.ortho_size = imgui.slider_float("Ortho Size", cam.ortho_size, 0.2, 50.0)
    else:
        changed, cam.frustum_half_height = imgui.slider_float("Frustum Half Height", cam.frustum_half_height, 0.1, 50.0)

    imgui.separator()
    imgui.text("Lighting")
    changed, viewer.light_1_enabled = imgui.checkbox("Light 1", viewer.light_1_enabled)
    changed, viewer.light_2_enabled = imgui.checkbox("Light 2", viewer.light_2_enabled)
    changed, viewer.light_brightness = imgui.slider_float("Brightness", viewer.light_brightness, 0.0, 2.0)

    imgui.separator()
    imgui.text("Render")
    changed, viewer.shading_mode = imgui.combo("Shading", viewer.shading_mode, viewer.shading_names)
    changed, viewer.lighting_algo_idx = imgui.combo("Lighting Algo", viewer.lighting_algo_idx, viewer.lighting_algo_names)
    changed, viewer.polygon_mode = imgui.combo("Polygon", viewer.polygon_mode, viewer.polygon_mode_names)
    changed, viewer.show_depth_map = imgui.checkbox("Show Depth Map", viewer.show_depth_map)
    changed, viewer.show_coordinate_axes = imgui.checkbox("Show Coordinate Axes", viewer.show_coordinate_axes)

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
        changed, viewer.math_x_min = imgui.slider_float("x min", viewer.math_x_min, -10.0, 0.0)
        changed, viewer.math_x_max = imgui.slider_float("x max", viewer.math_x_max, 0.0, 10.0)
        changed, viewer.math_y_min = imgui.slider_float("y min", viewer.math_y_min, -10.0, 0.0)
        changed, viewer.math_y_max = imgui.slider_float("y max", viewer.math_y_max, 0.0, 10.0)
        changed, viewer.math_steps = imgui.slider_int("Grid steps", int(viewer.math_steps), 8, 200)

    elif viewer.category_idx == 4:
        opt = viewer.optimizer
        changed, opt.loss_function_idx = imgui.combo(
            "Loss Function",
            opt.loss_function_idx,
            opt.loss_function_labels,
        )
        if changed:
            viewer._spawn_loss_optimization_scene()

        changed, opt.loss_x_min = imgui.slider_float("x min", opt.loss_x_min, -20.0, 0.0)
        changed, opt.loss_x_max = imgui.slider_float("x max", opt.loss_x_max, 0.0, 20.0)
        changed, opt.loss_y_min = imgui.slider_float("y min", opt.loss_y_min, -20.0, 0.0)
        changed, opt.loss_y_max = imgui.slider_float("y max", opt.loss_y_max, 0.0, 20.0)
        changed, opt.loss_resolution = imgui.slider_int("Grid resolution", int(opt.loss_resolution), 16, 240)

        imgui.separator()
        imgui.text("Optimization")
        changed, opt.opt_start_x = imgui.slider_float("Start x", opt.opt_start_x, -20.0, 20.0)
        changed, opt.opt_start_y = imgui.slider_float("Start y", opt.opt_start_y, -20.0, 20.0)

        changed, opt.opt_learning_rate_log10 = imgui.slider_float("log10(Learning Rate)", opt.opt_learning_rate_log10, -5.0, -0.5)
        opt.opt_learning_rate = float(10.0 ** opt.opt_learning_rate_log10)
        imgui.text(f"Learning Rate: {opt.opt_learning_rate:.6f}")

        changed, opt.opt_momentum_coefficient = imgui.slider_float("Momentum coeff", opt.opt_momentum_coefficient, 0.0, 0.999)
        changed, opt.opt_noise_variance = imgui.slider_float("Noise variance", opt.opt_noise_variance, 0.0, 0.2)
        changed, opt.max_epochs = imgui.slider_int("Max Epochs", int(opt.max_epochs), 10, 10000)
        changed, opt.steps_per_frame = imgui.slider_int("Steps / frame", int(opt.steps_per_frame), 1, 50)
        changed, opt.use_random_reset_start = imgui.checkbox("Reset with random start", opt.use_random_reset_start)

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
            imgui.text("Trajectory Colors: GD=Red, Momentum=Orange, Adam=Green")
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

    if imgui.button("Spawn Shape"):
        viewer.spawn_shape()

    imgui.same_line()
    if imgui.button("Clear Scene"):
        viewer.scene_items = []
        viewer.optimizer.clear_state()
        viewer._reset_view_home()

    imgui.separator()
    imgui.text(f"Objects in scene: {len(viewer.scene_items)}")
    imgui.text("Mouse: Left=Rotate camera, Right=Pan, Wheel=Zoom")
    imgui.text("Keys: C=Switch camera, 1/2=Toggle lights, F=Wireframe cycle, Z=Depth")

    imgui.end()
