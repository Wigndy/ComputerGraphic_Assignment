# 🎬 Assets Placeholder Guide

This file documents all visual assets needed to complete the BTL landing page.

---

## 📸 Screenshots Needed

### 1. Main Viewer Interface (`demo-main.png`)

**Description:** Full screenshot of BTL viewer showing complete interface

**Specifications:**
- Resolution: 1280x800 (or higher for clarity)
- Format: PNG
- Content:
  - Main 3D viewport with a sphere or default geometry
  - Control panel visible on right side
  - Multiple lights enabled
  - Phong shading applied
  - Coordinate axes visible (optional)

**How to capture:**
```bash
# Run viewer and take screenshot
python BTL/viewer.py

# In viewer:
1. Load default geometry (Sphere)
2. Enable: Light 1, Light 2, Coordinate axes
3. Set Shading to "Phong"
4. Adjust camera for nice angle
5. Take screenshot (Screenshot key or macOS: Cmd+Shift+4)
```

**Used in:** README.md, main landing page hero section

---

### 2. Shading Model Comparison (`shading-comparison.png`)

**Description:** Side-by-side comparison of all 5 shading models on same object

**Specifications:**
- Resolution: 1600x400 (or 5x 320x400 tiles)
- Format: PNG
- Content:
  - Same sphere rendered 5 times
  - Labels: "Flat", "Gouraud", "Phong", "PhongEx", "Color Interp"
  - Identical lighting/camera for all
  - Clear visual differences evident

**How to capture:**
```bash
# Render same object 5 times with different shaders:
1. Scene: Single sphere, medium-high poly
2. Lighting: Light 1 + Light 2 enabled
3. Camera: Fixed, good angle
4. Render 5 times:
   - Iteration 1: Set Shading = Flat, screenshot
   - Iteration 2: Set Shading = Gouraud, screenshot
   - Iteration 3: Set Shading = Phong, screenshot
   - Iteration 4: Set Shading = PhongEx, screenshot
   - Iteration 5: Set Shading = Color Interp, screenshot
5. Combine into grid (use GIMP, Photoshop, or Python PIL)
```

**Used in:** FEATURES.md (II. Shading Models section)

---

### 3. Optimization Animation (`optimization-demo.gif`)

**Description:** Animated GIF showing 5 optimizers racing down loss surface

**Specifications:**
- Resolution: 1024x768 (landscape)
- Format: GIF (animated, ~2-3 seconds)
- Frame rate: 15-30 FPS
- Duration: 2-3 seconds
- Content:
  - 3D loss surface (Himmelblau or Rosenbrock)
  - 5 colored balls + trajectories
  - Labels for each optimizer
  - Smooth animation to convergence

**How to capture:**
```bash
# Option 1: Use Python screen recording
import cv2
import numpy as np
from PIL import Image

# Run optimization simulation and capture frames
frames = []
controller = OptimizerController()
controller.activate_scene()

for epoch in range(0, 300, 10):
    controller.playback_time = float(epoch)
    controller._apply_playback_state()
    # Render to file/buffer
    frames.append(screenshot_frame)

# Save as GIF
frames[0].save('optimization-demo.gif', 
               save_all=True, 
               append_images=frames[1:],
               duration=100,  # 100ms per frame
               loop=0)

# Option 2: Record screen and convert
# ffmpeg -i screen_recording.mp4 -vf fps=15 optimization-demo.gif
```

**Used in:** README.md (Demo section), main showcase

---

### 4. Contour Map Visualization (`contour-map.png`)

**Description:** Loss surface with 2D contour overlay in split view

**Specifications:**
- Resolution: 1024x512 (landscape)
- Format: PNG
- Content:
  - Left half: 3D loss surface (elevated view)
  - Right half: 2D contour map (top-down)
  - Colored trajectories overlaid
  - Same domain visible in both views
  - Marker showing starting position

**How to capture:**
```bash
# In BTL viewer:
1. Category: Loss Optimization
2. Loss Function: Himmelblau or Rosenbrock
3. Enable: Show Contour Map
4. View Mode: Split 50/50
5. Run optimization to generate trajectories
6. Adjust camera for good 3D view
7. Screenshot
```

**Used in:** FEATURES.md (VII. Contour Map Visualization), README.md

---

## 🎨 Diagrams Needed

### 5. Architecture Diagram (`architecture.svg`)

**Description:** System architecture showing component relationships

**Format:** SVG (vector, scalable)

**Content (ASCII version below):**
```
┌─────────────────────────────────────────────────────────────┐
│                     BTL Application                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │  Viewer (Main)  │  │ Control Panel UI │  │  Scene Mgmt │ │
│  └────────┬────────┘  └────────┬─────────┘  └──────┬──────┘ │
│           │                    │                    │         │
│  ┌────────▼────────────────────▼────────────────────▼──────┐ │
│  │         Rendering System                                  │ │
│  │  • MeshDrawable  • Materials  • Shaders  • VAO/VBO      │ │
│  └────────┬────────────────────────────────────────────────┘ │
│           │                                                   │
│  ┌────────▼────────────────────────────────────────────────┐ │
│  │         Geometry System                                  │ │
│  │  • Primitives  • Factories  • Mesh Generation           │ │
│  └────────┬────────────────────────────────────────────────┘ │
│           │                                                   │
│  ┌────────▼────────────────────────────────────────────────┐ │
│  │         Transform & Camera                              │ │
│  │  • View/Projection Matrices  • Camera Control           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Optimization System                             │ │
│  │  • Loss Functions  • Optimizers  • Trajectories        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
       ▲
       │ OpenGL Calls
       ▼
    GPU
```

**Tools to create:**
- Lucidchart (online, free tier)
- Draw.io (free, browser-based)
- Inkscape (free, desktop)
- Adobe XD (commercial)
- OmniGraffle (Apple)

**Used in:** docs/architecture.md

---

### 6. Optimizer Flow Diagram (`optimizer-flow.svg`)

**Description:** Pipeline showing optimizer simulation workflow

**Content (ASCII version below):**
```
┌─────────────────────────────────────────────────────────────┐
│                  Optimization Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Select Loss Function                                     │
│     │                                                        │
│     ▼                                                        │
│  2. Generate Mesh Surface                                    │
│     (resolution: 64-320)                                     │
│     │                                                        │
│     ▼                                                        │
│  3. Instantiate 5 Optimizers                               │
│     • BGD, SGD, Mini-batch, Momentum, Adam                 │
│     │                                                        │
│     ▼                                                        │
│  4. Pre-compute Trajectories (Epochs 0→max)                │
│     ├─ For each optimizer:                                 │
│     │  ├─ Initialize at (x₀, y₀)                           │
│     │  ├─ Loop: epoch 0 to max_epochs                      │
│     │  │  ├─ optimizer.step()                              │
│     │  │  ├─ Evaluate f(x, y)                              │
│     │  │  ├─ Record position + loss                        │
│     │  │  └─ Store in buffer                               │
│     │  └─ Interpolate for smooth playback                  │
│     │                                                        │
│     ▼                                                        │
│  5. Playback & Visualization                               │
│     ├─ Render 3D surface                                    │
│     ├─ Render optimizer markers (colored balls)             │
│     ├─ Render trajectories (lines)                          │
│     ├─ Update ball rotation (rolling effect)                │
│     └─ Render contour map (optional)                        │
│     │                                                        │
│     ▼                                                        │
│  6. Display Metrics                                          │
│     • Current epoch, loss, gradient norm                    │
│     • Optimizer position (x, y)                             │
│     • Convergence status                                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Used in:** docs/architecture.md, FEATURES.md

---

### 7. Camera System Diagram (`camera-system.svg`)

**Description:** Camera controls and coordinate system

**Content (ASCII version below):**
```
┌──────────────────────────────────────────────────────┐
│           Camera Control System                       │
├──────────────────────────────────────────────────────┤
│                                                        │
│  Input Controls:                                      │
│  ├─ Middle Mouse Drag  → Orbit (around target)       │
│  ├─ Scroll Wheel       → Zoom in/out                 │
│  └─ Keyboard (optional)→ Pan/Tilt                    │
│                                                        │
│  Camera 1: Free Orbit                                │
│  ├─ Position: Orbits around target                   │
│  ├─ FOV: 10-120° (adjustable)                        │
│  ├─ Pitch: Allowed (can tilt)                        │
│  └─ Use: Detailed inspection                         │
│                                                        │
│  Camera 2: Fixed Angle                               │
│  ├─ Position: Fixed isometric-like view             │
│  ├─ FOV: Fixed                                       │
│  ├─ Pitch: Not allowed (no tilt)                     │
│  └─ Use: Consistent framing                          │
│                                                        │
│  Projection:                                          │
│  ├─ Perspective: 3D with vanishing points           │
│  ├─ Orthographic: Technical drawing, no vanishing   │
│  └─ Toggle: Use Ortho Size slider                    │
│                                                        │
│  Matrices Generated:                                  │
│  ├─ View Matrix: Eye position, look direction, up   │
│  ├─ Projection Matrix: FOV, aspect, near/far planes │
│  └─ Model Matrix: Object transform (position, rot)  │
│                                                        │
│  Coordinate System:                                   │
│        +Y (Up)                                        │
│        │                                              │
│        ▲                                              │
│        │                                              │
│    ┌───┼───┐ +X (Right)                             │
│    │   │   │                                         │
│    ◄───●───►                                         │
│    ├───┼───┤                                         │
│    │   │   │                                         │
│    └───┼───┘                                         │
│        │ -Z or +Z (Into/Out screen)                 │
│        │                                              │
│                                                        │
└──────────────────────────────────────────────────────┘
```

**Used in:** docs/architecture.md, FEATURES.md

---

## 📊 Loss Function Plots Needed (Optional)

### 8-12. Loss Function Surface Plots

For each loss function, a 3D surface plot would be helpful:

**For each:**
- Quadratic 2D: Perfect paraboloid
- Booth: Two intersecting plane-like surface
- Beale: Multiple valleys
- Himmelblau: Four peaks
- Rosenbrock: Long curved valley

**How to generate:**
```python
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# Example for Rosenbrock
x = np.linspace(-2, 2, 100)
y = np.linspace(-1, 3, 100)
X, Y = np.meshgrid(x, y)
Z = (1 - X)**2 + 100 * (Y - X**2)**2

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(X, Y, Z, cmap='viridis')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('f(X,Y)')
ax.set_title('Rosenbrock Function')
plt.savefig('rosenbrock-surface.png', dpi=150, bbox_inches='tight')
```

**Used in:** docs/loss-functions.md (optional enhancement)

---

## 📋 Asset Tracking Checklist

### Screenshots
- [ ] demo-main.png (1280x800)
- [ ] shading-comparison.png (1600x400)
- [ ] contour-map.png (1024x512)

### Animations  
- [ ] optimization-demo.gif (2-3 seconds)

### Diagrams
- [ ] architecture.svg
- [ ] optimizer-flow.svg
- [ ] camera-system.svg

### Optional Enhancements
- [ ] Rosenbrock surface plot
- [ ] Himmelblau surface plot
- [ ] Booth surface plot
- [ ] Beale surface plot
- [ ] Quadratic 2D surface plot

---

## 🎬 Tools & Resources

### Screenshot Tools
- **macOS:** Cmd+Shift+4 (built-in)
- **Windows:** Snip & Sketch or ShareX
- **Linux:** GIMP, Flameshot, or built-in tools

### GIF Creation
- **Python:** Pillow + imageio
- **FFmpeg:** `ffmpeg -i video.mp4 output.gif`
- **Online:** gifmaker.me, ezgif.com
- **Mac:** ScreenFloat, Gifox

### Diagram Tools
- **Draw.io** - Free, browser-based (https://draw.io)
- **Lucidchart** - Free tier available
- **Inkscape** - Free, open-source SVG editor
- **OmniGraffle** - Mac, professional
- **Miro** - Online whiteboarding

### Image Editing
- **GIMP** - Free, open-source
- **Photoshop** - Commercial
- **Pixlr** - Free, web-based
- **Canva** - Free, templates available

---

## 💾 File Organization

```
assets/
├── screenshots/
│   ├── demo-main.png             ← Main viewer
│   ├── shading-comparison.png     ← 5 shading models
│   ├── optimization-demo.gif      ← Animated optimizers
│   ├── contour-map.png           ← Contour visualization
│   └── losses/                   ← Optional loss surface plots
│       ├── quadratic-2d.png
│       ├── booth.png
│       ├── beale.png
│       ├── himmelblau.png
│       └── rosenbrock.png
│
└── diagrams/
    ├── architecture.svg           ← System components
    ├── optimizer-flow.svg         ← Optimization pipeline
    └── camera-system.svg          ← Camera controls
```

---

## Quick Start: Capture Screenshots

### Fastest Way (10 minutes total)

```bash
# 1. Run viewer
cd /path/to/Sample
python BTL/viewer.py

# 2. For demo-main.png:
#    - Wait for viewer to load
#    - Screenshot immediately (best-effort composition)
#    - Save as demo-main.png

# 3. For shading-comparison.png:
#    - Load default sphere
#    - Change shading 5 times, screenshot each
#    - Combine into grid (use Quick Markup on Mac)

# 4. For contour-map.png:
#    - Select Category: Loss Optimization
#    - Enable Show Contour Map
#    - Set View Mode: Split 50/50
#    - Run optimization
#    - Screenshot

# 5. For optimization-demo.gif:
#    - Record 2-3 seconds of optimization
#    - Convert to GIF with ffmpeg or Python
```

---

## 📝 Template for Adding Images to Markdown

Once assets are ready, replace placeholders with:

```markdown
### Example: Main Viewer Interface

[TODO: Screenshot of BTL main viewer interface]

↓ (Replace with)

![BTL Main Viewer Interface](./assets/screenshots/demo-main.png)
*Figure 1: BTL main viewer with Phong shading, dual lights, and coordinate axes visible.*
```

---

## ⚠️ Important Notes

1. **High Quality:** Use high-resolution screenshots (at least 1280px wide)
2. **Consistency:** Ensure consistent lighting/camera across comparisons
3. **Clarity:** Maximize contrast for easy viewing on light/dark backgrounds
4. **Attribution:** If using third-party tools, include license information
5. **Accessibility:** Add alt text descriptions to all images

---

**Last Updated:** April 2026  
**Status:** Ready for asset capture

