# 🎨 BTL - Advanced 3D Geometry & Optimization Visualizer

## Overview

**BTL** is a comprehensive **3D Graphics Engine** built with Modern OpenGL (3.3+) and Python, designed for visualizing complex geometries, loss surfaces, and optimization algorithms in real-time. It combines interactive visualization with scientific computing to provide a powerful tool for understanding machine learning optimization landscapes.

---

## ✨ Key Features

### 🎯 Core Capabilities

- **Interactive 3D Viewer** - Real-time visualization of 2D/3D geometries using Modern OpenGL
- **Multiple Shading Models** - Flat, Gouraud, Phong, and Extended Phong shading algorithms
- **Optimization Visualization** - Animate 5 major optimization algorithms (SGD, Adam, Momentum, etc.)
- **Loss Surface Rendering** - Visualize 5 loss functions: Beale, Himmelblau, Rosenbrock, Booth, Quadratic
- **Advanced Lighting System** - Multiple lights, HDRI environment mapping, custom light sources
- **Real-time Material Control** - Dynamically adjust roughness, metallic properties, and emissive colors
- **Dual Camera System** - Free orbit camera + fixed angled view with independent controls
- **Contour Maps** - Split-view or inset 2D loss surface contours with trajectory overlays

### 🔧 Technical Features

- **GPU-Accelerated Rendering** - Vertex and Fragment shaders with 5 shading configurations
- **Efficient Geometry Management** - VAO/VBO/EBO-based buffering system
- **Interactive UI** - ImGui control panel for real-time parameter adjustment
- **Modular Architecture** - Separated concerns: geometry, rendering, physics simulation, visualization
- **Trajectory Recording** - Playback and visualization of optimizer paths
- **Ball Physics Simulation** - Rolling ball animation for optimizer visualization with decay and lift

---

## 📊 What Can You Do With BTL?

### 1️⃣ **Visualize Optimization Landscapes**
Understand how different optimizers navigate loss surfaces:
- Watch SGD, Adam, Momentum, Mini-batch SGD, and Batch GD compete
- Observe convergence patterns in real-time
- Compare algorithm behaviors side-by-side

### 2️⃣ **Explore Loss Functions**
Investigate mathematical landscapes:
- **Beale Function** - Multiple local minima
- **Himmelblau Function** - 4 global minima
- **Rosenbrock Function** - Valley-shaped surface
- **Booth Function** - Complex mountain terrain
- **Quadratic 2D** - Simple convex baseline

### 3️⃣ **Render Custom Geometries**
Create and visualize:
- 2D shapes (circles, rectangles, polygons)
- 3D primitives (spheres, cylinders, cubes, tori)
- Parametric surfaces (z = f(x, y) mathematical surfaces)
- Textured meshes

### 4️⃣ **Experiment With Rendering Techniques**
- Compare shading algorithms side-by-side
- Adjust material properties
- Experiment with different light configurations
- Visualize depth maps and normal maps

---

## 🚀 Quick Start

### Installation

**System Requirements:**
- Python 3.8+
- macOS / Linux (Windows with WSL2 tested)
- OpenGL 3.3+ capable GPU

**Install Dependencies:**

```bash
# Navigate to sample directory
cd /path/to/Sample

# Install required packages
conda create -n graphics python=3.9
conda activate graphics
pip install PyOpenGL numpy pyimgui glfw Pillow

# Alternatively with conda:
conda install -c conda-forge pyopengl numpy pyimgui glfw pillow
```

### Run BTL Viewer

```bash
# From Sample directory
python BTL/viewer.py
```

**Controls:**
- **Mouse Wheel** - Zoom in/out
- **Middle Mouse + Drag** - Rotate camera
- **Right Panel** - Control panel (camera, lighting, objects, optimization)

---

## 📚 Documentation

For detailed information, see:

| Document | Purpose |
|----------|---------|
| [**FEATURES.md**](./FEATURES.md) | Deep dive into all features with examples |
| [**INSTALLATION.md**](./INSTALLATION.md) | Detailed setup and troubleshooting |
| [**API.md**](./API.md) | API reference for main classes |
| [**EXAMPLES.md**](./EXAMPLES.md) | Code examples and usage patterns |
| [**Architecture**](./docs/architecture.md) | System design and component overview |
| [**Algorithms**](./docs/algorithms.md) | Optimization algorithms explained |
| [**Shading Models**](./docs/shading-models.md) | Rendering techniques deep dive |
| [**Loss Functions**](./docs/loss-functions.md) | Mathematical definitions and properties |

---

## 🎬 Demo & Screenshots

### Main Viewer Interface
[TODO: Screenshot of BTL main viewer with multiple objects and control panel]

### Shading Comparison
[TODO: Side-by-side comparison of Flat vs Gouraud vs Phong shading]

### Optimization Animation
[TODO: Animated GIF showing 5 optimizers racing down a loss surface]

### Contour Map View
[TODO: Screenshot of split-view with 3D surface and 2D contour overlay]

### Light Interaction
[TODO: Before/after showing HDRI vs custom lighting]

---

## 🏗️ Project Structure

```
BTL/
├── viewer.py                     # Main application entry point
├── viewer_ui.py                  # ImGui control panel UI
├── optimizer_controller.py        # Optimization visualization orchestrator
├── camera.py                     # Camera system (free + angled views)
├── geometry.py                   # Geometry generation & rendering
├── overlay_drawables.py          # Trajectory, axes, and UI overlays
│
├── geometry_components/          # Modular geometry system
│   ├── drawable.py              # Base drawable abstraction
│   ├── factories.py              # Geometry creation factories
│   ├── primitives.py             # 2D/3D shape definitions
│   ├── manager.py                # Geometry resource management
│   └── legacy_impl.py            # Legacy geometry implementations
│
├── sample_function/              # Loss functions & optimizers
│   ├── loss_functions.py         # 5 loss function implementations
│   ├── loss_surface_generator.py # Mesh generation from loss surfaces
│   └── optimizers/               # Optimizer implementations
│
├── *.vert / *.frag               # GLSL Shader files
│   ├── flat.* & phong.*          # Standard shading
│   ├── gouraud.* & phongex.*     # Advanced shading
│   └── color_interp.*            # Vertex color models
│
├── assets/                       # Textures and 3D models
│   └── ...
│
└── imgui.ini                     # ImGui layout cache
```

---

## 🔌 Using BTL in Your Projects

### Example 1: Basic Viewer Usage

```python
from BTL.viewer import Viewer
from BTL.geometry import create_geo3d_drawable

# Create viewer
viewer = Viewer(width=1280, height=800)

# Add a sphere
sphere = create_geo3d_drawable("Sphere (Lat-Long)", radius=1.0, sectors=32, stacks=32)
viewer.add_scene_item("Sphere", sphere, model_matrix)

# Run
viewer.run()
```

### Example 2: Visualize Custom Optimization

```python
from BTL.optimizer_controller import OptimizerController
from BTL.sample_function import OptimizerType, LossFunctionType

controller = OptimizerController()
controller.loss_function_idx = controller.loss_function_types.index(LossFunctionType.ROSENBROCK)
controller.opt_learning_rate = 0.01
controller.max_epochs = 500

# Build and visualize
controller.activate_scene()
controller.build_optimizers(randomize_start=False)
```

### Example 3: Create Custom Loss Function

See [EXAMPLES.md](./EXAMPLES.md) for complete examples.

---

## 📊 Supported Optimizers

Visualize and compare real optimization algorithms:

| Optimizer | Type | Use Case |
|-----------|------|----------|
| **Batch Gradient Descent** | First-order | Smooth learning, full dataset |
| **Stochastic GD (SGD)** | First-order | Single sample per step |
| **Mini-batch SGD** | First-order | Configurable batch size |
| **Momentum** | Accelerated | Faster convergence, overshooting risk |
| **Adam** | Adaptive | Fast convergence, default recommended |

---

## 🎨 Rendering Capabilities

### Shading Models

- **Flat Shading** - Constant color per face, sharp edges
- **Gouraud Shading** - Vertex color interpolation
- **Phong Shading** - Per-fragment lighting with specular highlights
- **Extended Phong** - Multiple materials, emissive colors, metallic/roughness

### Lighting System

- **Direct Lights** - 2 configurable directional lights
- **HDRI Environment** - Dynamic environment mapping with intensity control
- **Custom Light** - Free-positioned point light with drag manipulation
- **Material Properties** - Roughness, metallic, ambient, specular, shininess

---

## 🛠️ Development

### Adding a New Geometry

See [docs/architecture.md](./docs/architecture.md) for the geometry system design.

### Adding a New Optimizer

Implement `Optimizer` interface in `sample_function/optimizers/` and register in `OptimizerFactory`.

### Adding Custom Shaders

Create `.vert` and `.frag` files in BTL directory, register in shader manager.

---

## 📈 Performance

- **Typical FPS**: 60+ FPS on modern GPUs at 1280x800 resolution
- **Mesh Resolution**: Up to 320x320 loss surface grids
- **Trajectory Playback**: Real-time playback for 600+ epoch simulations
- **Multi-object Rendering**: 100+ geometric objects simultaneously

---

## 🐛 Troubleshooting

For common issues and solutions, see [INSTALLATION.md](./INSTALLATION.md#troubleshooting).

---

## 📖 Algorithm Details

For mathematical foundations and implementation details, see:
- [Algorithms Deep Dive](./docs/algorithms.md)
- [Loss Functions](./docs/loss-functions.md)

---

## 📝 License

This project is part of the Computer Graphics course materials. See LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Please follow the architecture guide in [docs/architecture.md](./docs/architecture.md).

---

## 📞 Questions?

- Check [INSTALLATION.md](./INSTALLATION.md) for setup help
- See [EXAMPLES.md](./EXAMPLES.md) for usage patterns
- Review [docs/](./docs/) for deep technical dives

---

**Last Updated**: April 2026  
**Version**: 1.0  
**Language**: Python 3.8+  
**Graphics API**: OpenGL 3.3+
