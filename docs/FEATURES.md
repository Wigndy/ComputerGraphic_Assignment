# 📋 BTL Features - Complete Reference

## Overview

This document provides a comprehensive breakdown of all BTL features with detailed explanations and usage patterns.

---

## 🎯 Feature Categories

### I. Geometry System

#### 2D Shapes
Support for creating flat geometric primitives:

- **Circle** - Smooth circle with configurable segments
- **Rectangle** - Axis-aligned rectangle  
- **Polygon** - N-sided regular polygon
- **Line** - Simple line segment

**Parameters:**
```python
# Circle example
radius = 1.0
segments = 64  # Higher = smoother

# Rectangle example  
width = 2.0
height = 1.5

# Polygon example
sides = 8  # Octagon
segments = 64
```

#### 3D Primitives
Full-featured 3D shapes with customizable tessellation:

- **Sphere (Lat-Long)** - Latitude-longitude parametric mesh
- **Cylinder** - Configurable height and radius
- **Cone** - Apex at origin
- **Cube** - Unit cube with normals
- **Torus** - Major/minor radii control
- **Pyramid** - Square base pyramid

**Parameters:**
```python
# Sphere
radius = 1.0
sectors = 32    # Longitude divisions
stacks = 32     # Latitude divisions

# Cylinder
radius = 0.5
height = 2.0
sectors = 32

# Torus
major_radius = 1.0
minor_radius = 0.3
sectors = 32
stacks = 32
```

#### Parametric Surfaces
Render custom mathematical surfaces of the form z = f(x, y):

```python
# Example expressions
"sin(x) * cos(y)"
"x**2 + y**2"  # Paraboloid
"sin(sqrt(x**2 + y**2))"
"1 / (1 + x**2 + y**2)"
```

**Configuration:**
- X range: [-30, 30]
- Y range: [-30, 30]
- Grid resolution: 8-200 divisions

---

### II. Shading Models

#### 1. Flat Shading
**What it is:** Constant color per triangle face

**Characteristics:**
- Sharp edges between faces
- No interpolation
- Fast rendering
- Good for low-poly aesthetics

**Use cases:**
- Wireframe preview
- CAD visualization
- Artistic/low-poly style

**Shader:** `flat.vert` / `flat.frag`

#### 2. Gouraud Shading
**What it is:** Vertex colors interpolated across face

**Characteristics:**
- Smooth color transitions
- Per-vertex calculation
- Mach banding artifacts possible
- Medium performance

**Use cases:**
- Real-time visualization
- Smooth gradients
- Early graphics techniques

**Shader:** `gouraud.vert` / `gouraud.frag`

#### 3. Phong Shading
**What it is:** Per-fragment lighting with specular highlights

**Characteristics:**
- High-quality visuals
- Specular reflections
- Smooth appearance
- Higher computational cost

**Components:**
- Ambient component
- Diffuse component  
- Specular component
- Shininess factor

**Shader:** `phong.vert` / `phong.frag`

#### 4. Extended Phong (PhongEx)
**What it is:** Advanced Phong with additional features

**Additional Features:**
- Multiple material support
- Metallic/roughness parameters
- Emissive color channel
- HDRI environment mapping
- Normal map support (optional)

**Shader:** `phongex.vert` / `phongex.frag`

#### 5. Color Interpolation
**What it is:** Per-vertex color blend

**Characteristics:**
- Simple interpolation from vertex colors
- No lighting calculations
- Fast rendering
- Good for colored point clouds

**Shader:** `color_interp.vert` / `color_interp.frag`

---

### III. Lighting System

#### Multiple Light Sources

**Light 1 (Fixed)**
- Direction-based directional light
- Always enabled or disabled as unit
- Pre-configured position

**Light 2 (Fixed)**
- Secondary directional light
- Similar to Light 1
- For fill lighting

**Custom Light (Free)**
- Point light source
- Draggable in viewport (pick within 30px radius)
- Configurable position: X, Y, Z (-60 to 60 range)
- Configurable color: RGB picker
- Configurable intensity: 0.0 to 4.0

#### HDRI Environment

**Features:**
```python
enablement: bool          # Enable/disable environment mapping
intensity: float (0-2)    # Environmental light strength  
color: RGB tuple          # Tint color for environment
```

**Effect:**
- Dynamic reflection mapping
- Ambient lighting
- High-quality background illumination

#### Material Properties

**Per-object properties:**
```python
diffuse: RGB              # Diffuse color
specular: RGB             # Specular highlight color
ambient: RGB              # Ambient contribution
shininess: float (1-256)  # Specular highlight size
```

**Global material controls:**
```python
roughness: float (0-1)    # Surface roughness (inverted: low = shiny)
metallic: float (0-1)     # Metallic property (affects reflection)
```

---

### IV. Camera System

#### Camera 1: Free Orbit Camera
**Type:** Perspective projection with orbit control

**Controls:**
- Middle Mouse + Drag = Rotate around target
- Scroll Wheel = Zoom in/out
- YAW axis fixed (prevents camera roll)

**Parameters:**
- FOV: 10° - 120°
- Near plane: 0.1
- Far plane: 100.0
- Aspect ratio: Auto (from window)

**Use cases:**
- Detailed object inspection
- 360° review
- Flexible exploration

#### Camera 2: Angled Fixed Camera  
**Type:** Perspective projection, fixed angle

**Characteristics:**
- Pre-set viewing angle (isometric-like)
- Can still zoom
- Doesn't allow pitch (fixed tilt)
- Good for consistent framing

**Use cases:**
- Preset viewpoint
- Consistent screenshot angles
- Standard visualization

#### Orthographic Mode
Toggle between perspective and orthographic:
```python
camera.use_orthographic = True
camera.ortho_size = 3.0  # Visible height in world units
```

---

### V. Optimizer Visualization

#### 5 Optimization Algorithms

**1. Batch Gradient Descent (BGD)**
```
Updates: full_gradient_on_entire_dataset
Learning: Smooth, stable
Speed: Slow convergence
Color: Red (#F24040)
```

**2. Stochastic Gradient Descent (SGD)**
```
Updates: gradient_on_single_sample
Learning: Noisy, zigzag paths
Speed: Fast but unstable
Color: Orange (#FB6B16)
```

**3. Mini-batch SGD**
```
Updates: gradient_on_batch(configurable_size)
Learning: Balanced
Speed: Fast and stable
Color: Blue (#1496FF)
```

**4. Momentum**
```
Updates: velocity_accumulation
Learning: Accelerated, overshooting
Speed: Fastest straight paths
Color: Purple (#B33DFF)
Color: (#34E156) Teal
```

**5. Adam (Adaptive Moment)**
```
Updates: adaptive_learning_rate  
Learning: Fast, smooth convergence
Speed: Consistent fast descent
Color: Green (#34E156)
```

#### Visualization Features

**Ball Physics:**
- Rolling on surface simulates momentum
- Ball decays when moving slowly
- Animated spin shows rotation direction
- Height based on instantaneous velocity

**Trajectory Recording:**
- Records full path history
- Playback from epoch 0 to max
- Shows path in both 3D and 2D contour view
- Interpolated smooth animation

**Real-time Metrics:**
```python
# For each optimizer:
- Current epoch (% of training complete)
- Current loss value
- Gradient norm magnitude  
- X, Y position
```

#### Configuration Parameters

```python
start_point: (x, y)              # Initial position
learning_rate: 0.0001 - 0.1      # Via log10 slider
momentum_coefficient: 0.0 - 1.0  # Momentum factor
batch_size: 1 to 256             # Mini-batch size
noise_variance: 0.0 - 0.1        # SGD noise level
max_epochs: 1 to 1000            # Training length
```

---

### VI. Loss Functions

#### Beale Function
```
f(x,y) = (1.5 - x + xy)² + (2.25 - x + xy²)² + (2.625 - x + xy³)²

Domain: [-4.5, 4.5] × [-4.5, 4.5]
Global Minimum: (3.0, 0.5)
Characteristic: Multiple local minima, steep valleys
```

#### Himmelblau Function
```
f(x,y) = (x² + y - 11)² + (x + y² - 7)²

Domain: [-5, 5] × [-5, 5]  
Global Minima: 4 global minima at equal value
Characteristic: Four distinct valleys, symmetric-ish
```

#### Rosenbrock Function
```
f(x,y) = (1 - x)² + 100(y - x²)²

Domain: [-30, 30] × [-30, 30]
Global Minimum: (1, 1) with f=0
Characteristic: Long narrow valley, non-convex, hard to optimize
```

#### Booth Function
```
f(x,y) = (x + 2y - 7)² + (2x + y - 5)²

Domain: [-30, 30] × [-30, 30]
Global Minimum: (1, 3) with f=0
Characteristic: Two crossing planes, clean valley
```

#### Quadratic 2D (Baseline)
```
f(x,y) = x² + y²

Domain: [-30, 30] × [-30, 30]
Global Minimum: (0, 0) with f=0  
Characteristic: Simple paraboloid, easiest to optimize
```

#### Loss Surface Display
```python
display_z = log(1 + f(x,y))     # Applied for visualization
                                # Makes small values visible
```

---

### VII. Contour Map Visualization

#### View Modes

**Mode 1: Split 50/50**
- Left half: 3D surface
- Right half: 2D contour map
- Both show same region

**Mode 2: Inset Bottom-Right**
- Large 3D view
- Small inset contour in bottom-right
- Configurable inset size: 10-50%

#### Contour Features

**Contour Lines:**
- Opacity control: 0-100%
- Grid divisions: 1-8
- Shows loss levels
- Algorithm trajectories overlaid

**Grid:**
- Reference grid on contour
- Opacity: 0-100%
- Divides domain into cells

**Heatmap:**
- Color-mapped surface
- Viridis colormap (blue→green→yellow)
- Muted to show contours
- Opacity: 0-100%

**Start Marker:**
- Yellow crosshair at initial position
- Interactive: drag to set new start point
- Updates all optimizer starts simultaneously

**Trajectory Markers:**
- Colored dots for current algorithm positions
- Color matches algorithm color scheme
- Size adjustable: 1px - 50px

---

### VIII. Interactive Controls

#### UI Elements

**Sliders:**
- Real-time value adjustment
- Numerical input alternative
- Min/max bounds enforced

**Color Pickers:**
- RGB selection
- Hexadecimal input support
- Live preview

**Dropdowns:**
- Quick selection from options
- Automatic UI update

**Checkboxes:**
- Toggle features on/off
- Immediate effect

**Text Input:**
- Mathematical expression input (for z=f(x,y))
- Error reporting

---

## 📊 Feature Interaction Matrix

| Feature A | Feature B | Interaction |
|-----------|-----------|-------------|
| Loss Function | Optimizer | Optimizers solve selected loss |
| Camera 1 | Camera 2 | Independent views |
| Light 1 | Custom Light | Both affect scene lighting |
| Phong Shading | Material Props | Material properties affect appearance |
| Contour Map | Trajectories | Trajectories render on contour |
| HDRI Env | Material Props | HDRI reflects in metallic surfaces |

---

## 🎮 Control Summary

| Action | Method |
|--------|--------|
| Rotate View | Middle Mouse Drag |
| Zoom | Scroll Wheel |
| Set Start Point | Click on contour + drag |
| Adjust Cameras | Camera dropdown |
| Change Shading | Lighting Algo dropdown |
| Control Lights | Lighting section sliders |
| Modify Surface | Loss Function dropdown |
| Run Optimization | Simulation controls |
| Pause/Resume | Play/Pause button |
| Replay | Reset epoch slider |

---

## 🚀 Advanced Features

### Trajectory Playback
- Pre-computed optimizer trajectories
- Realtime playback with interpolation
- Pause/resume/scrub support
- Smooth animation between epochs

### Custom Loss Functions
See [docs/loss-functions.md](../docs/loss-functions.md) for extending with custom functions.

### Shader Extension
See [docs/shading-models.md](../docs/shading-models.md) for creating custom shaders.

---

## 📈 Performance Notes

- Increasing mesh resolution (> 200) may impact FPS
- HDRI environment adds ~5-10% overhead
- Custom lights add ~2-3% overhead  
- 5 simultaneous optimizers have minimal impact
- VBO updates occur once per frame

---

**Last Updated:** April 2026
