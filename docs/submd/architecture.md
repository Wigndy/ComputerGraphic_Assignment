# 🏛️ BTL Architecture Overview

## System Design

BTL is a modular graphics engine with clear separation of concerns. This document explains how components interact.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Viewer Application                       │
│  (viewer.py, viewer_ui.py)                                  │
└────────────┬──────────────────────────┬─────────────────────┘
             │                          │
      ┌──────▼───────┐         ┌────────▼────────┐
      │ Rendering     │         │ Simulation       │
      │ System        │         │ System           │
      │               │         │                  │
      │ • MeshDrawable│         │ • OptimizerCtrl  │
      │ • Materials   │         │ • LossFunction   │
      │ • Shaders     │         │ • Optimizers     │
      │ • Lights      │         └────────┬─────────┘
      └──────┬────────┘                  │
             │                          │
      ┌──────▼──────────────────────────▼──────┐
      │      Geometry System (geometry.py)     │
      │  • Primitives (sphere,cube,cylinder)   │
      │  • Materials & Textures               │
      │  • VAO/VBO/EBO Management             │
      └──────┬─────────────────────────────────┘
             │
      ┌──────▼────────────────────────┐
      │   Transform & Camera System    │
      │   (camera.py, transform.py)    │
      │                                │
      │ • View/Projection matrices     │
      │ • Camera orbiting              │
      │ • Matrix composition           │
      └────────────────────────────────┘
```

---

## Module Breakdown

### 1. **Viewer** (`viewer.py`)
**Responsibility:** Main application orchestration

**Key Components:**
- **GLFW Window Management** - OpenGL context creation, events
- **Scene Management** - Object collection and lifecycle
- **Main Render Loop** - Frame timing, input polling, drawing
- **State Management** - Global viewer state (cameras, lights, etc.)

**Lifecycle:**
1. Create window and OpenGL context
2. Initialize ImGui renderer
3. Load all assets
4. Main loop:
   - Poll input events
   - Update state (camera, objects, simulation)
   - Render scene
   - Render UI
   - Swap buffers
5. Cleanup resources

---

### 2. **UI System** (`viewer_ui.py`)
**Responsibility:** ImGui control panel interface

**Key Sections:**
- **Camera Controls** - Camera selection, FOV/ortho adjustment
- **Lighting Controls** - Light toggles, HDRI, custom light position
- **Rendering Options** - Shading model, polygon mode, depth map
- **Object Creation** - Geometry factory controls
- **Optimization Controls** - Loss function, optimizer parameters
- **Material Editor** - Roughness, metallic sliders

---

### 3. **Rendering System** (`geometry.py`)
**Responsibility:** GPU-side rendering abstraction

**Hierarchy:**

```python
Drawable (abstract)
├── MeshDrawable (main implementation)
│   ├── VAO/VBO/EBO management
│   ├── Shader binding
│   ├── Material override
│   └── draw() method
└── Other specialized drawables

Material
├── diffuse: RGB
├── specular: RGB
├── ambient: RGB
└── shininess: float
```

**Shaders Supported:**
```
flat.vert/.frag           → Constant color
color_interp.vert/.frag   → Vertex color interpolation
gouraud.vert/.frag        → Gouraud shading
phong.vert/.frag          → Per-fragment Phong
phongex.vert/.frag        → Extended Phong + materials
```

**Drawing Pipeline:**
1. Bind VAO (vertex data)
2. Bind shader program
3. Set uniforms (matrices, materials, lights)
4. Issue draw call (glDrawElements)
5. Unbind

**Performance Features:**
- Triangle strip optimization
- Material caching
- Shader pre-compilation

---

### 4. **Geometry System** (`geometry.py` + `geometry_components/`)
**Responsibility:** Mesh generation and management

**Geometry Registry:**

```python
Geo2D.SHAPES = ["Circle", "Rectangle", "Polygon"]
Geo3D.SHAPES = ["Sphere", "Cylinder", "Cone", "Cube", "Torus", "Pyramid"]
```

**Factory Pattern:**
```python
create_geo2d_drawable(shape_type, segments, radius, width, height)
create_geo3d_drawable(shape_type, radius, height, sectors, stacks)
create_math_surface_drawable(expression, x_min, x_max, y_min, y_max, steps)
```

**Mesh Generation:**
1. Vertex generation (position, normal, texcoord)
2. Index array creation (triangle strips)
3. VAO/VBO/EBO buffer creation
4. Optional material assignment

---

### 5. **Camera System** (`camera.py`)
**Responsibility:** View matrix management and camera control

**Camera Types:**
```python
class Camera:
    position: Vec3           # World position
    target: Vec3             # Look-at point
    up: Vec3                 # Up direction
    orbit_axis: Vec3         # Rotation axis
    
    Methods:
    - get_view_matrix()      # Returns 4x4 view matrix
    - get_projection_matrix() # Returns 4x4 projection matrix
    - orbit(yaw, pitch)      # Rotate around target
    - zoom(amount)           # Zoom in/out
```

**Projection Modes:**
- **Perspective:** Realistic 3D, vanishing points
- **Orthographic:** Technical drawing, equal scaling

**Constraints:**
- Pitch: Optional (prevent roll)
- Orbit axis: Fixed (prevent unwanted rotations)
- Near/far planes: Prevent clipping

---

### 6. **Transform Utilities** (`libs/transform.py`)
**Responsibility:** Matrix operations

**Functions:**

```python
# Base transformations
T.translate(x, y, z) -> Mat4
T.rotate(axis: Vec3, radians: float) -> Mat4
T.scale(sx, sy, sz) -> Mat4

# Compositions (right-to-left multiplication)
model = T.translate(x, y, z) @ T.rotate(...) @ T.scale(...)

# View/Projection
T.lookat(eye, target, up) -> Mat4
T.perspective(fov, aspect, near, far) -> Mat4
T.ortho(left, right, bottom, top, near, far) -> Mat4
```

---

### 7. **Optimization System** (`sample_function/`)
**Responsibility:** Loss function evaluation and optimizer simulation

**Components:**

```
sample_function/
├── loss_functions.py           # Beale, Himmelblau, Rosenbrock, Booth, Quadratic
├── loss_surface_generator.py   # Mesh generation from loss landscapes
├── optimizers/
│   ├── base.py               # Optimizer interface
│   ├── sgd.py                # SGD implementations
│   ├── momentum.py           # Momentum optimizer
│   └── adam.py               # Adam optimizer
└── __init__.py               # Factory pattern implementations
```

**Loss Function Interface:**
```python
class LossFunctionType(Enum):
    BEALE, HIMMELBLAU, ROSENBROCK, BOOTH, QUADRATIC_2D

class LossFunctionManager:
    @staticmethod
    def evaluate(loss_type, x: float, y: float) -> float
    
    @staticmethod
    def gradient(loss_type, x: float, y: float) -> Tuple[float, float]
```

**Optimizer Interface:**
```python
class Optimizer(ABC):
    x: float
    y: float
    
    def step() -> None          # One optimization step
    def set_position(x, y) -> None
    def get_trajectory() -> List[Vec2]
```

---

### 8. **Optimizer Controller** (`optimizer_controller.py`)
**Responsibility:** Orchestrates all 5 optimizers and visualization

**Key Features:**

1. **Optimizer Management:**
   - Creates 5 optimizer instances
   - Manages lifecycle (build, step, reset)
   - Records trajectory data

2. **Playback System:**
   - Pre-computes all trajectories (epochs 0 to max)
   - Supports pause/resume/scrub
   - Interpolates between epochs

3. **Ball Physics:**
   - Tracks rotation for rolling effect
   - Decay simulation
   - Height based on velocity

4. **Contour Map:**
   - 2D heatmap with color mapping
   - Contour line generation
   - Grid overlay

5. **Visualization:**
   - Renders colored sphere markers
   - Trajectory line drawing
   - Spin indicators

---

### 9. **Overlay System** (`overlay_drawables.py`)
**Responsibility:** Specialized drawable types forUI elements

**Classes:**

```python
class PointSetDrawable:
    """Render point clouds"""
    update_points(points: Nx3, colors: Nx3)
    draw(proj, view, point_size)

class TrajectoryDrawable:
    """Render connected line paths"""
    update_points(points: Nx3)
    draw(proj, view)

class CoordinateAxesOverlay:
    """Render XYZ axes"""
    draw(proj, view, model)
```

---

## Data Flow Diagrams

### Rendering Data Flow

```
Scene Item
    │
    ├─ Drawable (geometry)
    │   ├─ Vertices (Nx3)
    │   ├─ Normals (Nx3)
    │   ├─ TexCoords (Nx2)
    │   ├─ Colors (Nx3, optional)
    │   └─ Primitive type (GL_TRIANGLES, etc.)
    │
    └─ Model Matrix (4x4)
         │
         ▼
    [GPU Transform]
         │
         ▼
    Fragment Shader
         │
         ├─ Material properties
         ├─ Lighting calculations
         └─ Output: Fragment color
         │
         ▼
    Framebuffer
```

### Optimization Data Flow

```
OptimizerController
    │
    ├─ Loss Function Selection
    │   ▼
    ├─ Mesh Generation (LossSurfaceGenerator)
    │   ├─ Vertices with z = f(x,y)
    │   ├─ Normal calculation
    │   └─ Color mapping (viridis)
    │   ▼
    ├─ Optimizer Instantiation (OptimizerFactory)
    │   ├─ Create 5 instances (SGD, Adam, etc.)
    │   ├─ Set initial position
    │   └─ Set hyperparameters
    │   ▼
    ├─ Trajectory Pre-computation
    │   ├─ Loop: epoch 0 to max
    │   ├─ Call optimizer.step()
    │   ├─ Record position + loss
    │   └─ Store in playback buffers
    │   ▼
    ├─ Playback
    │   ├─ Interpolate between epochs
    │   ├─ Update ball rotation
    │   └─ Update trajectory drawable
    │   ▼
    └─ Visualization
        ├─ Render 3D surface
        ├─ Render optimizer markers
        ├─ Render trajectories
        └─ Render contour map
```

---

## Performance Characteristics

### GPU Bound Operations
- Mesh rendering (millions of vertices)
- Shader computation (especially Phong)
- HDRI environment mapping

### CPU Bound Operations
- Optimizer stepping
- Trajectory pre-computation
- UI rendering (ImGui)

### Typical FPS
- Simple geometry (< 50k tris): 60 FPS
- Complex loss surface (200x200): 45-55 FPS
- With HDRI + custom lights: 40-50 FPS
- All 5 optimizers + contours: 50-60 FPS

---

## Extension Points

### Adding a New Geometry Type

1. **Define generation in `geometry.py`:**
```python
def create_ico_sphere_drawable(radius, detail_level):
    # Generate icosahedral sphere
    vertices, indices = ...
    return MeshDrawable(vertices, normals, texcoords)
```

2. **Register in `Geo3D.SHAPES`**

3. **Add to UI dropdown in `viewer_ui.py`**

### Adding a New Optimizer

1. **Implement in `sample_function/optimizers/`:**
```python
class RMSprop(Optimizer):
    def __init__(self, loss_type, x0, y0, lr):
        ...
    
    def step(self):
        # RMSprop update rule
        ...
```

2. **Register in `OptimizerFactory`**

3. **Add to `OptimizerType` enum and display names**

### Adding a New Shader

1. **Create `.vert` and `.frag` files in `BTL/`**

2. **Register in shader manager**

3. **Add shading mode enum**

4. **Update geometry.py binding logic**

---

## Thread Safety

**Current Implementation:** Single-threaded (no thread safety guarantees)

**Optimizer stepping:** Happens on main thread

**Potential bottleneck:** Pre-computing 200x200 surface + 5 optimizers takes several seconds

**Future:** Could parallelize optimizer simulation across CPU cores.

---

## Testing Strategy

**Unit Test Targets:**
- `LossFunctionManager.evaluate()` accuracy
- `Optimizer.step()` convergence
- `Camera.get_view_matrix()` correctness
- `MeshDrawable` rendering

**Integration Test Targets:**
- Full optimization pipeline
- Trajectory pre-computation
- Playback interpolation

**Manual Testing:**
- Visual comparison of shading models
- FPS monitoring at various resolutions
- Memory usage over time

---

## Known Limitations

1. **No multi-threading** - All operations single-threaded
2. **Fixed 5 optimizers** - Cannot easily add/remove at runtime
3. **Pre-computed trajectories** - Cannot adjust hyperparameters during playback
4. **Limited custom shaders** - No hot-reload support
5. **No asset loading** - Cannot dynamically load .obj/.fbx files

---

## Future Enhancements

1. **Compute shaders** - GPU-based optimizer stepping
2. **Collaborative editing** - Real-time parameter sharing
3. **Custom loss functions** - User-defined function input
4. **3D model loading** - OBJ/FBX format support
5. **Ray tracing** - Advanced rendering modes
6. **Batched processing** - Parallel optimizer instances

---

**Last Updated:** April 2026
