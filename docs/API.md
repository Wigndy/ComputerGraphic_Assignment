# 📚 BTL API Reference

## Quick Navigation

- [Core Classes](#core-classes)
- [Geometry System](#geometry-system)
- [Rendering & Materials](#rendering--materials)
- [Camera System](#camera-system)
- [Optimization System](#optimization-system)
- [UI & Controls](#ui--controls)

---

## Core Classes

### `Viewer`
Main application class that manages rendering, scene, and interaction.

**Location:** `BTL/viewer.py`

**Constructor:**
```python
viewer = Viewer(width=1280, height=800)
```

**Key Attributes:**
```python
scene_items: List[SceneItem]              # Objects in scene
cameras: List[Camera]                     # Available cameras
current_camera_idx: int                   # Active camera
optimizer: OptimizerController            # Optimizer system
shading_mode: int                         # Flat/Gouraud/Phong/etc
lighting_algo_idx: int                    # Lighting algorithm
light_1_enabled: bool
light_2_enabled: bool
hdri_environment_enabled: bool
custom_light_position: [float, float, float]
custom_light_color: [float, float, float]
custom_light_intensity: float
```

**Key Methods:**
```python
def add_scene_item(name: str, drawable, model_matrix: np.ndarray) -> None
    """Add geometry object to scene"""

def run() -> None
    """Start main render loop"""

def set_camera(camera_idx: int) -> None
    """Switch between cameras"""

@property
def camera() -> Camera
    """Get current active camera"""
```

---

## Geometry System

### `MeshDrawable`
GPU-optimized geometry rendering class.

**Location:** `BTL/geometry.py`

**Constructor:**
```python
vertices: np.ndarray    # Nx3 float32: vertex positions
normals: np.ndarray     # Nx3 float32: vertex normals
texcoords: np.ndarray   # Nx2 float32: texture coordinates
colors: np.ndarray      # Nx3 float32: vertex colors (optional)
primitive: int          # GL_TRIANGLES, GL_LINES, GL_POINTS

drawable = MeshDrawable(vertices, normals, texcoords, colors, primitive)
```

**Shading Modes:**
```python
MODE_FLAT = 0        # Constant color
MODE_COLOR = 1       # Vertex color interpolation
MODE_LIGHTING = 2    # Full lighting calculation
```

**Drawing:**
```python
def draw(
    projection: np.ndarray,      # 4x4 view matrix
    view: np.ndarray,            # 4x4 projection matrix
    model: np.ndarray,           # 4x4 model matrix
    shading_mode: int = MODE_LIGHTING,
    lighting_algorithm: str = "phong",  # "phong", "gouraud", "flat"
    light_1_enabled: bool = True,
    light_2_enabled: bool = False,
    brightness: float = 1.0,
    material_override: Material = None,
    alpha_override: float = 1.0,
    show_depth_map: bool = False,
) -> None:
    """Render the mesh"""
```

**Material Control:**
```python
def set_material(
    diffuse: np.ndarray,       # RGB color
    specular: np.ndarray,      # RGB specular color
    ambient: np.ndarray,       # RGB ambient
    shininess: float,          # 8-256
) -> None:
    """Set material properties"""

def set_emissive(
    color: np.ndarray,         # RGB color
    strength: float,           # 0-2
) -> None:
    """Set glowing color"""

def set_vertex_color(
    color: np.ndarray,         # RGB for flat color
) -> None:
    """Set uniform vertex color"""
```

---

### Geometry Factory Functions

**Location:** `BTL/geometry.py`

```python
# 2D Shapes
def create_geo2d_drawable(
    shape_type: str,          # "Circle", "Rectangle", "Polygon"
    segments: int,            # Tessellation detail
    radius: float = 1.0,
    width: float = 1.0,
    height: float = 1.0,
) -> MeshDrawable:
    """Create 2D geometric shape"""

# 3D Shapes  
def create_geo3d_drawable(
    shape_type: str,          # "Sphere (Lat-Long)", "Cylinder", "Cone", etc
    radius: float = 1.0,
    height: float = 1.0,
    sectors: int = 32,
    stacks: int = 32,
    inner_radius: float = 0.5,
) -> MeshDrawable:
    """Create 3D geometric primitive"""

# Mathematical Surfaces
def create_math_surface_drawable(
    expression: str,           # "sin(x)*cos(y)", "x**2+y**2"
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    x_steps: int, y_steps: int,
) -> MeshDrawable:
    """Create surface from z=f(x,y) expression"""

# Loss Surface
def create_loss_surface_drawable(
    loss_type: LossFunctionType,
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    resolution: int,
) -> MeshDrawable:
    """Create loss landscape mesh"""
```

---

### `PointSetDrawable`
Render collections of points.

**Location:** `BTL/overlay_drawables.py`

```python
drawable = PointSetDrawable()

def update_points(
    points: np.ndarray,        # Nx3 positions
    colors: np.ndarray = None, # Nx3 RGB colors
) -> None:
    """Update point data"""

def draw(
    projection: np.ndarray,
    view: np.ndarray,
    point_size: float = 1.0,
) -> None:
    """Render points"""
```

---

### `TrajectoryDrawable`
Render connected line paths.

**Location:** `BTL/overlay_drawables.py`

```python
drawable = TrajectoryDrawable(
    color: np.ndarray,         # RGB color
    line_width: float = 1.0,
)

def update_points(points: np.ndarray) -> None:
    """Update line vertices (Nx3)"""

def draw(projection: np.ndarray, view: np.ndarray) -> None:
    """Render trajectory"""
```

---

## Camera System

### `Camera`
3D camera with orbit and perspective/orthographic projection.

**Location:** `BTL/camera.py`

**Constructor:**
```python
camera = Camera(
    position: List[float] = [0, 0, 5],
    target: List[float] = [0, 0, 0],
    up: List[float] = [0, 1, 0],
    orbit_axis: List[float] = [0, 1, 0],
    allow_pitch: bool = True,
)
```

**Attributes:**
```python
position: np.ndarray           # Camera position in world space
target: np.ndarray             # Look-at point
up: np.ndarray                 # Up vector
orbit_axis: np.ndarray         # Axis for rotation
allow_pitch: bool              # Can camera tilt?
use_orthographic: bool         # Projection type
fov: float                     # Field of view (45-120°)
ortho_size: float              # Orthographic height
near: float                    # Near clipping plane
far: float                     # Far clipping plane
```

**Methods:**
```python
def get_view_matrix() -> np.ndarray:
    """Get 4x4 view matrix"""

def get_projection_matrix() -> np.ndarray:
    """Get 4x4 projection matrix"""

def zoom(amount: float) -> None:
    """Zoom in (positive) or out (negative)"""

def orbit(yaw: float, pitch: float) -> None:
    """Rotate around target"""

def pan(right: float, up: float) -> None:
    """Move camera laterally"""

def set_aspect(width: int, height: int) -> None:
    """Update aspect ratio"""
```

---

## Rendering & Materials

### `Material`
Material properties for lighting.

**Location:** `BTL/geometry.py`

```python
material = Material(
    diffuse: np.ndarray = [0.8, 0.8, 0.8],
    specular: np.ndarray = [1.0, 1.0, 1.0],
    ambient: np.ndarray = [0.2, 0.2, 0.2],
    shininess: float = 32.0,
)

# Properties
material.diffuse: np.ndarray      # RGB diffuse color
material.specular: np.ndarray     # RGB specular color
material.ambient: np.ndarray      # RGB ambient color
material.shininess: float         # Specular exponent (1-256)
```

### Shader Enums

**Location:** `BTL/geometry.py`

```python
# Available shaders
SHADER_FLAT = "flat"
SHADER_COLOR_INTERP = "color_interp"
SHADER_GOURAUD = "gouraud"
SHADER_PHONG = "phong"
SHADER_PHONGEX = "phongex"

# Lighting algorithms
LIGHTING_PHONG = "phong"
LIGHTING_GOURAUD = "gouraud"
LIGHTING_FLAT = "flat"
```

---

## Optimization System

### `OptimizerController`
Orchestrates all 5 optimizers and loss surface visualization.

**Location:** `BTL/optimizer_controller.py`

**Key Attributes:**
```python
# Loss Function Control
loss_function_types: List[LossFunctionType]
loss_function_idx: int                    # Selected index
loss_x_min, loss_x_max: float             # Domain bounds X
loss_y_min, loss_y_max: float             # Domain bounds Y
loss_resolution: int                      # Mesh tessellation

# Optimizer Settings
opt_start_x, opt_start_y: float           # Initial position
opt_learning_rate: float                  # Step size
opt_learning_rate_log10: float            # Log10 for slider
opt_momentum_coefficient: float           # Momentum alpha
opt_batch_size: int                       # Batch size for SGD
opt_noise_variance: float                 # Noise level
max_epochs: int                           # Training duration
current_epoch: int                        # Current step

# Playback
playback_time: float                      # Current epoch (0 to max)
simulation_running: bool
steps_per_frame: int

# Optimization State
optimizers: Dict[OptimizerType, Optimizer]
optimizer_markers: Dict[OptimizerType, MeshDrawable]
trajectory_drawables: Dict[OptimizerType, TrajectoryDrawable]
ball_state: Dict[OptimizerType, dict]
```

**Key Methods:**
```python
def create_surface_drawable() -> Tuple[str, MeshDrawable]:
    """Generate loss surface mesh"""

def build_optimizer_markers() -> None:
    """Create colored sphere markers"""

def build_optimizers(randomize_start: bool = False) -> None:
    """Initialize all 5 optimizers"""

def activate_scene() -> None:
    """Setup and prepare visualization"""

def set_start_point(x: float, y: float, rebuild: bool = True) -> None:
    """Change initial position"""

def step_optimizers(steps: int) -> None:
    """Advance discrete steps"""

def advance_playback(delta_time: float) -> None:
    """Advance by elapsed time"""

def optimizer_metrics() -> List[Tuple]:
    """Get current metrics for each optimizer"""
    # Returns: [(opt_type, epoch, loss, grad_norm), ...]

def draw_overlays(
    proj_mat, view_mat,
    light_1_enabled, light_2_enabled,
    brightness,
    ...
) -> None:
    """Render optimizer markers, trajectories"""

def draw_contour_panel() -> None:
    """Render 2D contour visualization"""
```

---

### `LossFunctionType` Enum

**Location:** `BTL/sample_function/loss_functions.py`

```python
class LossFunctionType(Enum):
    BEALE = "Beale Function"
    HIMMELBLAU = "Himmelblau Function"
    ROSENBROCK = "Rosenbrock Function"
    BOOTH = "Booth Function"
    QUADRATIC_2D = "Quadratic 2D"
```

### `OptimizerType` Enum

```python
class OptimizerType(Enum):
    BATCH_GRADIENT_DESCENT = 0
    GRADIENT_DESCENT = 1          # SGD
    MINI_BATCH_SGD = 2
    MOMENTUM = 3
    ADAM = 4
```

### `LossFunctionManager`

**Location:** `BTL/sample_function/loss_functions.py`

```python
@staticmethod
def evaluate(loss_type: LossFunctionType, x: float, y: float) -> float:
    """Compute f(x, y)"""

@staticmethod
def gradient(loss_type: LossFunctionType, x: float, y: float) -> Tuple[float, float]:
    """Get (∂f/∂x, ∂f/∂y)"""
```

### `OptimizerFactory`

**Location:** `BTL/sample_function/optimizers.py`

```python
@staticmethod
def create(
    optimizer_type: OptimizerType,
    loss_type: LossFunctionType,
    initial_x: float, initial_y: float,
    learning_rate: float,
    momentum_coefficient: float,
    batch_size: int,
    noise_variance: float,
) -> Optimizer:
    """Instantiate optimizer"""
```

---

## UI & Controls

### Input Handling

**Mouse Events:**
```python
# In viewer
glfw.set_mouse_button_callback(window, on_mouse_button)
glfw.set_cursor_pos_callback(window, on_mouse_move)
glfw.set_scroll_callback(window, on_scroll)
```

**Keyboard Events:**
```python
glfw.set_key_callback(window, on_key)
```

### ImGui Integration

**Location:** `BTL/viewer_ui.py`

```python
def draw_control_panel(viewer: Viewer) -> None:
    """Draw the control panel UI"""
    imgui.new_frame()
    imgui.begin("Control Panel", True)
    # ... UI elements
    imgui.end()
    imgui.render()
```

---

## Enums & Constants

### Primitive Types

```python
GL.GL_TRIANGLES = 4               # Triangle mesh
GL.GL_LINES = 1                   # Line segments
GL.GL_POINTS = 0                  # Point cloud
GL.GL_LINE_STRIP = 3              # Continuous line
GL.GL_TRIANGLE_STRIP = 5          # Strip optimization
```

### Shading Modes

```python
MeshDrawable.MODE_FLAT = 0        # Flat color
MeshDrawable.MODE_COLOR = 1       # Vertex colors
MeshDrawable.MODE_LIGHTING = 2    # Computed lighting
```

---

## Common Patterns

### Pattern 1: Create and Render a Sphere

```python
from BTL.geometry import create_geo3d_drawable
from BTL.libs import transform as T
import numpy as np

# Create sphere
sphere = create_geo3d_drawable(
    "Sphere (Lat-Long)",
    radius=1.0,
    sectors=32,
    stacks=32
)

# Set material
sphere.set_material(
    diffuse=np.array([0.8, 0.2, 0.2]),
    specular=np.array([1.0, 1.0, 1.0]),
    ambient=np.array([0.2, 0.2, 0.2]),
    shininess=32.0
)

# Render
model = T.translate(0, 0, 0)
sphere.draw(proj, view, model)
```

### Pattern 2: Animate Optimizer

```python
from BTL.optimizer_controller import OptimizerController

# Setup
optimizer = OptimizerController()
optimizer.opt_learning_rate = 0.01
optimizer.activate_scene()

# Simulate
for frame in range(1000):
    optimizer.advance_playback(delta_time=0.016)  # 60 FPS
    
    # Get metrics
    metrics = optimizer.optimizer_metrics()
    for opt_type, epoch, loss, grad_norm in metrics:
        print(f"{opt_type.name}: epoch={epoch}, loss={loss:.4f}")
```

### Pattern 3: Custom Loss Surface

```python
from BTL.geometry import create_loss_surface_drawable
from BTL.sample_function import LossFunctionType

# Create surface
drawable = create_loss_surface_drawable(
    loss_type=LossFunctionType.ROSENBROCK,
    x_min=-30, x_max=30,
    y_min=-30, y_max=30,
    resolution=200
)

# Add to viewer
viewer.add_scene_item("Rosenbrock", drawable, identity_matrix)
```

---

## Transform Utilities

**Location:** `BTL/libs/transform.py`

```python
import BTL.libs.transform as T

# Matrix operations
T.identity() -> np.ndarray         # 4x4 identity
T.translate(x, y, z) -> np.ndarray
T.rotate(axis, radians) -> np.ndarray
T.scale(sx, sy, sz) -> np.ndarray
T.ortho(l, r, b, t, n, f) -> np.ndarray  # Orthographic projection
T.perspective(fov, aspect, near, far) -> np.ndarray
T.lookat(eye, target, up) -> np.ndarray

# Composition
model = T.translate(1, 2, 3) @ T.rotate([0,1,0], 0.5)
```

---

## Advanced Topics

- **Custom Shaders** → See [docs/shading-models.md](./docs/shading-models.md)
- **Custom Loss Functions** → See [docs/loss-functions.md](./docs/loss-functions.md)
- **Architecture Details** → See [docs/architecture.md](./docs/architecture.md)

---

**Last Updated:** April 2026  
**API Version:** 1.0

