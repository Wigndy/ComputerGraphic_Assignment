# 🔧 BTL Installation & Setup Guide

## System Requirements

### Minimum Requirements
- **OS**: macOS 10.13+, Ubuntu 18.04+, or Windows 10+ (WSL2)
- **Python**: 3.8 or higher
- **GPU**: Supports OpenGL 3.3+
- **RAM**: 4GB RAM
- **Disk**: 500MB free space

### Recommended Specifications
- **OS**: macOS 11+, Ubuntu 20.04+, or Windows 11
- **Python**: 3.10 or 3.11
- **GPU**: Dedicated GPU with 2GB VRAM (NVIDIA/AMD/Intel Arc)
- **RAM**: 8GB+ RAM
- **Disk**: 1GB free space

### GPU Compatibility

**macOS:**
- Apple Silicon (M1/M2/M3): Native support via Metal-OpenGL bridge
- Intel Macs: Full NVIDIA/AMD support

**Linux:**
- NVIDIA: CUDA Compute Capability 3.0+
- AMD: RDNA or newer recommended
- Intel: Iris Xe or newer

**Windows (WSL2):**
- NVIDIA: Full support
- AMD: Experimental support
- Intel: Iris Pro Graphics 580+

---

## Installation Steps

### Option 1: Conda (Recommended)

```bash
# Create new environment
conda create -n btl-graphics python=3.10
conda activate btl-graphics

# Install packages from conda-forge (more reliable for graphics)
conda install -c conda-forge \
    pyopengl \
    numpy \
    pillow \
    glfw \
    imgui

# Navigate to Sample directory and test
cd /path/to/Sample
python BTL/viewer.py
```

### Option 2: Pip + Virtual Environment

```bash
# Create virtual environment
python3.10 -m venv btl-env
source btl-env/bin/activate  # On Windows: btl-env\Scripts\activate

# Install via pip
pip install --upgrade pip
pip install PyOpenGL numpy Pillow glfw imgui

# Navigate and test
cd /path/to/Sample
python BTL/viewer.py
```

### Option 3: Manual Installation (Advanced)

For detailed per-package installation, see [Manual Installation](./docs/installation-advanced.md).

---

## Verification

Confirm installation succeeded:

```bash
# Test imports
python3 -c "
import OpenGL.GL as GL
import glfw
import numpy as np
import imgui
from PIL import Image
print('✓ All dependencies installed successfully')
"

# Run viewer
cd /path/to/Sample
python BTL/viewer.py
```

**Expected Output:**
- Window titled "BTL - Geometry Viewer" opens
- Right panel shows "Control Panel"
- Scene displays with default geometry

---

## Common Issues & Solutions

### Issue 1: ModuleNotFoundError for imgui

**Symptom:**
```
ModuleNotFoundError: No module named 'imgui'
```

**Solution:**
```bash
# Use conda-forge (has better pre-built binaries)
conda install -c conda-forge imgui

# OR manually build
pip install --upgrade pip setuptools wheel
pip install imgui[glfw]
```

### Issue 2: PyOpenGL Error - "No module named OpenGL"

**Symptom:**
```
ImportError: No module named OpenGL
```

**Solution:**
```bash
# Clear and reinstall
pip uninstall PyOpenGL
pip install --force-reinstall PyOpenGL
```

### Issue 3: GLFW Window Fails to Create

**Symptom:**
```
RuntimeError: Failed to create GLFW window
```

**Causes & Solutions:**

**macOS:**
```bash
# May need homebrew
brew install glfw
pip install glfw
```

**Linux (Ubuntu):**
```bash
# Install system dependencies
sudo apt-get install libglfw3-dev libglew-dev

# Reinstall pip packages
pip install --force-reinstall PyOpenGL glfw
```

**Windows (WSL2):**
```bash
# Ensure X server running (e.g., VcXsrv)
# Set DISPLAY variable
export DISPLAY=:0

# Try with software renderer if no GPU available
export LIBGL_ALWAYS_INDIRECT=1
```

### Issue 4: OpenGL Version Error

**Symptom:**
```
ValueError: OpenGL 3.3+ required
```

**Causes:**
- GPU doesn't support OpenGL 3.3+
- Old GPU drivers
- Running on integrated graphics

**Solutions:**
```bash
# Check OpenGL version
python3 -c "
from OpenGL.GL import glGetString, GL_VERSION
import OpenGL.GL as GL
GL.glCreateContext()  
print(glGetString(GL_VERSION))
"

# Update GPU drivers:
# - NVIDIA: https://www.nvidia.com/Download/driverDetails.aspx
# - AMD: https://www.amd.com/en/support
# - Intel: https://www.intel.com/content/www/en/en/support/detect.html
```

### Issue 5: ImGui Freezes or Doesn't Render

**Symptom:**
- Window opens but no UI
- Window freezes immediately

**Solution:**
```bash
# Try alternative ImGui backend
pip uninstall imgui
pip install imgui[glfw] --force-reinstall

# If still issues, check GLFW version
pip show glfw  # Should be 2.0+
pip install --upgrade glfw
```

### Issue 6: Performance Issues (Low FPS)

**Symptom:**
- FPS below 30
- Jerky animation
- Slow interaction response

**Causes & Solutions:**

```bash
# 1. Check what's running
# Close other GPU-intensive apps
# (Chrome with many tabs, Discord, games, etc.)

# 2. Reduce mesh resolution in UI
# Lower "Grid resolution" slider from 200 to 100

# 3. Disable HDRI environment mapping
# Uncheck "HDRI Environment" in Lighting

# 4. Reduce optimizer count
# Comment out some in optimizer_order

# 5. Check if running on integrated GPU
python3 -c "
import OpenGL.GL as GL
print(GL.glGetString(GL.GL_RENDERER).decode())
"
# If says "Intel HD Graphics" or similar, performance will be limited
```

### Issue 7: Fallback Python Interpreter

**Context:**
BTL's `viewer.py` auto-falls back to Conda python if current environment doesn't have imgui.

**Symptom:**
```
os.execv() permission denied
```

**Solution:**
```bash
# Make sure conda python path is correct
condensearch -n root which python
# Update path in viewer.py line 8 if needed

# OR explicitly run with conda
conda activate graphics-env
python BTL/viewer.py
```

---

## Advanced Configuration

### Environment Variables

```bash
# Use software renderer (slower but always works)
export LIBGL_ALWAYS_INDIRECT=1
python BTL/viewer.py

# Verbose OpenGL debugging
export PYTHONPATH="$(python -c 'import OpenGL; print(OpenGL.__path__[0])')"
python -c "import OpenGL; OpenGL.ERROR_CHECKING = True" && python BTL/viewer.py

# WSL2 X11 Display
export DISPLAY=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}'):0
python BTL/viewer.py
```

### Custom Configuration Files

Modify `BTL/imgui.ini` to restore custom UI layouts:
```ini
[Window][Control Panel]
Pos=1100,20
Size=180,780
```

---

## Docker Setup (Optional)

If you prefer containerized environment:

```dockerfile
FROM nvidia/cuda:12.2-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 python3-pip \
    libglfw3-dev libglew-dev libxrandr-dev

WORKDIR /workspace
COPY requirements.txt .
RUN pip install -r requirements.txt

CMD ["python", "BTL/viewer.py"]
```

```bash
# Build and run
docker build -t btl-graphics .
docker run --gpus all --env DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v $(pwd):/workspace \
    btl-graphics
```

---

## Next Steps

After successful installation:

1. **Read [README.md](./README.md)** - Overview of features
2. **Read [FEATURES.md](./FEATURES.md)** - Detailed feature breakdown
3. **Try [EXAMPLES.md](./EXAMPLES.md)** - Code examples
4. **Explore [docs/](./docs/)** - Technical deep dives
5. **Modify the code** - Experiment with parameters

---

## Getting Help

- **Error in terminal?** Check troubleshooting above
- **Want to understand a feature?** Read [FEATURES.md](./FEATURES.md)
- **Want code examples?** See [EXAMPLES.md](./EXAMPLES.md)
- **Technical question?** See [docs/architecture.md](./docs/architecture.md)

---

## Version Information

| Component | Minimum | Tested | Recommended |
|-----------|---------|--------|-------------|
| Python | 3.8 | 3.9, 3.10, 3.11 | 3.10+ |
| PyOpenGL | 3.1.5 | 3.1.5+ | Latest |
| NumPy | 1.19 | 1.21+ | 1.24+ |
| glfw | 2.0 | 2.0+ | Latest |
| imgui | 1.4 | 1.4.1+ | Latest |

---

**Last Updated:** April 2026
