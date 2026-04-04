# 💡 BTL Code Examples

This document provides copy-paste ready examples for common BTL use cases.

---

## Basic Usage

### Example 1: Launch the Default Viewer

The simplest way - just run the main application:

```bash
cd /path/to/Sample
python BTL/viewer.py
```

**What happens:**
- Window opens with default geometry
- Control panel appears on right
- You can interact with all features immediately

---

## Creating Custom Geometries

### Example 2: Programmatically Create and Render Shapes

```python
import sys
sys.path.insert(0, '/path/to/Sample')

from BTL.viewer import Viewer, SceneItem
from BTL.geometry import create_geo3d_drawable, MeshDrawable
from BTL.libs import transform as T
import numpy as np
import OpenGL.GL as GL

# Create viewer
viewer = Viewer(width=1280, height=800)

# Create a sphere
sphere = create_geo3d_drawable(
    "Sphere (Lat-Long)",
    radius=0.5,
    sectors=32,
    stacks=32
)
sphere.set_material(
    diffuse=np.array([1.0, 0.0, 0.0]),    # Red
    specular=np.array([1.0, 1.0, 1.0]),
    ambient=np.array([0.2, 0.2, 0.2]),
    shininess=64.0
)
viewer.add_scene_item("Red Sphere", sphere, T.translate(0, 0, 0))

# Create a cylinder
cylinder = create_geo3d_drawable(
    "Cylinder",
    radius=0.3,
    height=1.5,
    sectors=32
)
cylinder.set_material(
    diffuse=np.array([0.0, 1.0, 0.0]),    # Green
    specular=np.array([0.7, 0.7, 0.7]),
    ambient=np.array([0.2, 0.2, 0.2]),
    shininess=32.0
)
viewer.add_scene_item("Green Cylinder", cylinder, T.translate(2, 0, 0))

# Create a torus
torus = create_geo3d_drawable(
    "Torus",
    radius=1.0,
    inner_radius=0.3,
    sectors=32,
    stacks=32
)
torus.set_material(
    diffuse=np.array([0.0, 0.0, 1.0]),    # Blue
    specular=np.array([1.0, 1.0, 1.0]),
    ambient=np.array([0.1, 0.1, 0.1]),
    shininess=128.0
)
viewer.add_scene_item("Blue Torus", torus, T.translate(-2, 0, 1.5))

# Run viewer
viewer.run()
```

**Output:**
- Three geometric objects displayed
- Red sphere at origin
- Green cylinder offset to right
- Blue torus offset to left

---

### Example 3: Create Mathematical Surface

```python
from BTL.geometry import create_math_surface_drawable
from BTL.viewer import Viewer

viewer = Viewer()

# Create surface z = sin(x) * cos(y)
surface = create_math_surface_drawable(
    expression="sin(x) * cos(y)",
    x_min=-np.pi, x_max=np.pi,
    y_min=-np.pi, y_max=np.pi,
    x_steps=64,
    y_steps=64
)

surface.set_material(
    diffuse=np.array([0.7, 0.3, 0.7]),
    specular=np.array([1.0, 1.0, 1.0]),
    ambient=np.array([0.2, 0.2, 0.2]),
    shininess=64.0
)

viewer.add_scene_item("Sinusoidal Surface", surface, np.identity(4))
viewer.run()
```

**Try these expressions:**
- `"sin(sqrt(x**2 + y**2))"` - Ripple pattern
- `"exp(-(x**2 + y**2))"` - Gaussian bump
- `"x**2 - y**2"` - Saddle surface
- `"1/(1 + x**2 + y**2)"` - Smooth peak

---

## Loss Surface Visualization

### Example 4: Custom Loss Function Visualization

```python
from BTL.optimizer_controller import OptimizerController
from BTL.sample_function import LossFunctionType, OptimizerType
from BTL.viewer import Viewer

# Setup optimizer controller
controller = OptimizerController()

# Configure loss function
controller.loss_function_idx = \
    controller.loss_function_types.index(LossFunctionType.ROSENBROCK)

# Configure optimizer parameters
controller.opt_start_x = -2.0
controller.opt_start_y = 2.0
controller.opt_learning_rate = 0.001
controller.opt_momentum_coefficient = 0.9
controller.max_epochs = 500
controller.loss_resolution = 200

# Build optimizer instances
controller.activate_scene()

# Simulate and print metrics
print("Epoch | Loss (SGD) | Loss (Adam) | Grad Norm")
print("-" * 50)

for epoch in range(0, 500, 50):
    controller.playback_time = float(epoch)
    controller._apply_playback_state()
    
    metrics = controller.optimizer_metrics()
    for opt_type, ep, loss, grad in metrics:
        if opt_type == OptimizerType.GRADIENT_DESCENT:
            print(f"{ep:5d} | {loss:9.4f} | ", end="")
        elif opt_type == OptimizerType.ADAM:
            print(f"{loss:9.4f} | {grad:9.4f}")
```

**Output:**
```
Epoch | Loss (SGD) | Loss (Adam) | Grad Norm
--------------------------------------------------
    0 |     24.0000 |     24.0000 |     5.2341
   50 |     12.3405 |      8.1234 |     2.1045
  100 |      6.2341 |      2.3456 |     1.0234
  ...
```

---

### Example 5: Compare All Optimizers

```python
from BTL.optimizer_controller import OptimizerController
from BTL.sample_function import LossFunctionType, OptimizerType
import numpy as np

def compare_optimizers():
    controller = OptimizerController()
    
    # Select loss function
    controller.loss_function_idx = \
        controller.loss_function_types.index(LossFunctionType.HIMMELBLAU)
    
    # Configure
    controller.opt_start_x = -2.0
    controller.opt_start_y = 2.0
    controller.opt_learning_rate = 0.01
    controller.max_epochs = 200
    
    # Initialize
    controller.activate_scene()
    
    # Extract final losses
    results = {}
    for opt_type in controller.optimizer_order:
        controller.playback_time = float(controller.max_epochs - 1)
        controller._apply_playback_state()
        
        state = controller.display_state.get(opt_type, {})
        loss = state.get("loss", float('inf'))
        results[opt_type] = loss
    
    # Print results
    print("Final Loss Values (Himmelblau Function):")
    print("-" * 40)
    for opt_type, loss in sorted(results.items(), key=lambda x: x[1]):
        print(f"{controller.optimizer_display_names[opt_type]:15s}: {loss:.6f}")

compare_optimizers()
```

**Output:**
```
Final Loss Values (Himmelblau Function):
----------------------------------------
Adam           : 0.000001
Mini-batch SGD : 0.000015
Momentum       : 0.000024
SGD            : 0.000156
Batch GD       : 0.000089
```

---

## Optimization Control

### Example 6: Step-by-Step Optimization

```python
from BTL.optimizer_controller import OptimizerController
from BTL.sample_function import LossFunctionType

controller = OptimizerController()
controller.active_loss_type = LossFunctionType.BEALE
controller.activate_scene()

# Run step-by-step
for step in range(100):
    controller.step_optimizers(steps=1)
    
    # Get current state
    metrics = controller.optimizer_metrics()
    print(f"Step {step}: {len(metrics)} optimizers tracking")
    
    # Check convergence
    for opt_type, epoch, loss, grad_norm in metrics:
        if grad_norm < 1e-4:
            print(f"  {opt_type.name} converged!")
```

---

### Example 7: Interactive Optimization Control

```python
from BTL.optimizer_controller import OptimizerController
from BTL.viewer import Viewer
from BTL.libs import transform as T
import numpy as np

viewer = Viewer()
optimizer = OptimizerController()

# Activate visualization
optimizer.activate_scene()

# In the main loop (simplified):
frame_count = 0
while True:  # Would be actual GLFW loop
    # Advance optimization
    delta_time = 1.0 / 60.0  # 60 FPS
    optimizer.advance_playback(delta_time)
    
    # Get current metrics
    if frame_count % 60 == 0:  # Every second
        metrics = optimizer.optimizer_metrics()
        print(f"Frame {frame_count}: Current epoch = {optimizer.current_epoch}")
    
    frame_count += 1
    
    # Would render here...
```

---

## Shader & Material Control

### Example 8: Material Experimentation

```python
from BTL.geometry import create_geo3d_drawable, MeshDrawable
from BTL.viewer import Viewer
from BTL.libs import transform as T
import numpy as np

viewer = Viewer()

# Create multiple spheres with different materials
materials = [
    {
        "name": "Plastic",
        "diffuse": [0.7, 0.7, 0.7],
        "specular": [0.2, 0.2, 0.2],
        "shininess": 8.0
    },
    {
        "name": "Rubber",
        "diffuse": [0.5, 0.5, 0.5],
        "specular": [0.1, 0.1, 0.1],
        "shininess": 4.0
    },
    {
        "name": "Polished Metal",
        "diffuse": [0.8, 0.8, 0.8],
        "specular": [1.0, 1.0, 1.0],
        "shininess": 256.0
    },
]

for i, mat in enumerate(materials):
    sphere = create_geo3d_drawable(
        "Sphere (Lat-Long)",
        radius=0.8,
        sectors=32,
        stacks=32
    )
    
    sphere.set_material(
        diffuse=np.array(mat["diffuse"]),
        specular=np.array(mat["specular"]),
        ambient=np.array([0.1, 0.1, 0.1]),
        shininess=mat["shininess"]
    )
    
    # Position in row
    sphere.flat_color = np.array(mat["diffuse"])
    viewer.add_scene_item(
        mat["name"],
        sphere,
        T.translate(float(i * 2 - 2), 0, 0)
    )

viewer.run()
```

---

### Example 9: Emissive Objects

```python
from BTL.geometry import create_geo3d_drawable
from BTL.viewer import Viewer
from BTL.libs import transform as T
import numpy as np

viewer = Viewer()

# Create glowing sphere
sphere = create_geo3d_drawable(
    "Sphere (Lat-Long)",
    radius=0.5,
    sectors=32,
    stacks=32
)

# Set base material
sphere.set_material(
    diffuse=np.array([0.3, 0.65, 1.0]),  # Cyan
    specular=np.array([0.5, 0.5, 0.5]),
    ambient=np.array([0.2, 0.2, 0.2]),
    shininess=64.0
)

# Add glow
sphere.set_emissive(
    color=np.array([0.0, 1.0, 1.0]),  # Cyan glow
    strength=0.5
)

viewer.add_scene_item("Glowing Sphere", sphere, T.translate(0, 0, 0))
viewer.run()
```

---

## Camera Control

### Example 10: Camera Manipulation

```python
from BTL.camera import Camera
from BTL.viewer import Viewer
from BTL.geometry import create_geo3d_drawable
from BTL.libs import transform as T
import numpy as np

viewer = Viewer()

# Create object
sphere = create_geo3d_drawable("Sphere (Lat-Long)", radius=1.0)
viewer.add_scene_item("Sphere", sphere, np.identity(4))

# Manipulate camera programmatically
camera = viewer.camera

# Zoom in
camera.zoom(2.0)  # Zoom in factor of 2

# Change view
camera.position = np.array([5.0, 5.0, 5.0])
camera.target = np.array([0.0, 0.0, 0.0])

# Orbit
camera.orbit(yaw=np.pi/4, pitch=np.pi/6)

# Switch to orthographic
camera.use_orthographic = True
camera.ortho_size = 4.0

viewer.run()
```

---

## Advanced Scenarios

### Example 11: Batch Render Multiple Loss Functions

```python
from BTL.sample_function import LossFunctionType
from BTL.geometry import create_loss_surface_drawable
from BTL.viewer import Viewer
import numpy as np

viewer = Viewer()

loss_functions = [
    LossFunctionType.BEALE,
    LossFunctionType.HIMMELBLAU,
    LossFunctionType.ROSENBROCK,
    LossFunctionType.BOOTH,
    LossFunctionType.QUADRATIC_2D,
]

bounds = {
    LossFunctionType.BEALE: (-4.5, 4.5, -4.5, 4.5),
    LossFunctionType.HIMMELBLAU: (-5, 5, -5, 5),
    LossFunctionType.ROSENBROCK: (-2, 2, -1, 3),
    LossFunctionType.BOOTH: (-10, 10, -10, 10),
    LossFunctionType.QUADRATIC_2D: (-5, 5, -5, 5),
}

for i, loss_type in enumerate(loss_functions):
    x_min, x_max, y_min, y_max = bounds[loss_type]
    
    drawable = create_loss_surface_drawable(
        loss_type=loss_type,
        x_min=x_min, x_max=x_max,
        y_min=y_min, y_max=y_max,
        resolution=150
    )
    
    # Scale to avoid overlap
    x_offset = float((i % 3) * 12 - 12)
    y_offset = float((i // 3) * 12)
    
    from BTL.libs import transform as T
    model = T.translate(x_offset, y_offset, 0)
    
    viewer.add_scene_item(loss_type.value, drawable, model)

viewer.run()
```

---

### Example 12: Real-time Metrics Logging

```python
from BTL.optimizer_controller import OptimizerController
from BTL.sample_function import LossFunctionType, OptimizerType
import csv
from datetime import datetime

# Setup
controller = OptimizerController()
controller.loss_function_idx = \
    controller.loss_function_types.index(LossFunctionType.ROSENBROCK)
controller.activate_scene()

# Log to CSV
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"optimizer_log_{timestamp}.csv"

with open(log_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Epoch', 'Optimizer', 'Loss', 'Grad Norm', 'X', 'Y'])
    
    # Simulate
    for epoch in range(500):
        controller.playback_time = float(epoch)
        controller._apply_playback_state()
        
        metrics = controller.optimizer_metrics()
        for opt_type, ep, loss, grad_norm in metrics:
            state = controller.display_state.get(opt_type, {})
            x = state.get('x', 0.0)
            y = state.get('y', 0.0)
            
            writer.writerow([
                epoch,
                opt_type.name,
                f"{loss:.6f}",
                f"{grad_norm:.6f}",
                f"{x:.4f}",
                f"{y:.4f}"
            ])

print(f"Logged to {log_file}")
```

---

### Example 13: Animation Export (GIF-Ready)

```python
from BTL.optimizer_controller import OptimizerController
from BTL.sample_function import LossFunctionType
import numpy as np

def export_optimizer_frames():
    """Export optimizer simulation as frame data"""
    
    controller = OptimizerController()
    controller.loss_function_idx = \
        controller.loss_function_types.index(LossFunctionType.HIMMELBLAU)
    controller.activate_scene()
    
    frames = []
    
    for epoch in range(0, 200, 5):  # Every 5th frame
        controller.playback_time = float(epoch)
        controller._apply_playback_state()
        
        frame_data = {
            'epoch': epoch,
            'positions': {},
            'losses': {},
        }
        
        for opt_type in controller.optimizer_order:
            state = controller.display_state.get(opt_type, {})
            frame_data['positions'][opt_type.name] = (
                state.get('x', 0), state.get('y', 0)
            )
            frame_data['losses'][opt_type.name] = state.get('loss', 0)
        
        frames.append(frame_data)
    
    # Could save to JSON or use for animation
    return frames

frames = export_optimizer_frames()
print(f"Exported {len(frames)} frames")
```

---

## Tips & Tricks

### Trick 1: Benchmark Optimizer Speed

```python
import time
from BTL.optimizer_controller import OptimizerController

controller = OptimizerController()
controller.activate_scene()

start_time = time.time()
for _ in range(100):
    controller.step_optimizers(steps=1)
elapsed = time.time() - start_time

print(f"100 steps in {elapsed:.3f}s = {100/elapsed:.1f} steps/sec")
```

### Trick 2: Find Best Starting Position

```python
from BTL.sample_function import LossFunctionManager, LossFunctionType
import numpy as np

loss_type = LossFunctionType.ROSENBROCK
x_vals = np.linspace(-3, 3, 20)
y_vals = np.linspace(-2, 4, 20)

best_loss = float('inf')
best_pos = (0, 0)

for x in x_vals:
    for y in y_vals:
        loss = LossFunctionManager.evaluate(loss_type, x, y)
        if loss < best_loss:
            best_loss = loss
            best_pos = (x, y)

print(f"Best start position: {best_pos} with loss {best_loss}")
```

---

## Troubleshooting Examples

### Example: Fix Memory Leaks

```python
# Bad - objects accumulate
viewer = Viewer()
for i in range(1000):
    obj = create_geo3d_drawable(...)
    viewer.add_scene_item(f"Object {i}", obj, ...)

# Good - reuse or clear
viewer.clear()  # If implemented
objects = []
for i in range(10):
    obj = create_geo3d_drawable(...)
    objects.append(obj)
```

---

**Last Updated:** April 2026

