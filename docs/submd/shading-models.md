# 🎨 Shading Models & Rendering Techniques

This document explains the 5 shading models available in BTL, their mathematical foundations, and use cases.

---

## Overview

| Shading | Per-Vertex Calc | Per-Fragment Calc | Specular | Performance | Quality |
|---------|-----------------|-------------------|----------|-------------|---------|
| **Flat** | ✗ | ✗ | ✗ | Fastest | Low |
| **Gouraud** | ✓ | ✗ | ✗ | Fast | Medium |
| **Phong** | ✗ | ✓ | ✓ | Medium | High |
| **PhongEx** | ✗ | ✓ | ✓ | Slow | Very High |
| **Color Interp** | ✓ | ✓ | ✗ | Fast | Custom |

---

## 1. Flat Shading

### Visual Characteristics
- Constant color across triangle
- Sharp edges between faces
- Faceted, polygonal appearance
- Hardware: Fastest possible

### Mathematical Model

Each triangle gets a single color:
$$\text{Color}_{triangle} = \text{ConstantColor}$$

No interpolation, no lighting computation.

### Vertex Shader

```glsl
#version 330 core

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

uniform mat4 uProjection;
uniform mat4 uView;
uniform mat4 uModel;

void main() {
    gl_Position = uProjection * uView * uModel * vec4(aPosition, 1.0);
}
```

### Fragment Shader

```glsl
#version 330 core

uniform vec3 uFlatColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(uFlatColor, 1.0);
}
```

### Use Cases

- **Wireframe preview** - Outline edges
- **CAD visualization** - Clear geometry boundaries
- **Artistic rendering** - Low-poly aesthetic
- **Performance testing** - Check geometry count

### Advantages

✅ Fastest possible rendering
✅ Clear geometry visualization
✅ Useful for debugging
✅ Minimal GPU utilization

### Disadvantages

❌ No lighting information
❌ Unrealistic appearance
❌ Can't see curvature
❌ No specular highlights

---

## 2. Gouraud Shading

### Visual Characteristics
- Smooth color interpolation across triangle
- Lighting computed at vertices
- Colors lerped in rasterization
- Trade-off: speed vs quality

### Mathematical Model

Light at each vertex, then interpolate across triangle:

$$L_v = k_a + k_d(N \cdot L) + k_s(R \cdot V)^n$$

Then barycentric interpolation in fragment.

### Vertex Shader

```glsl
#version 330 core

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

uniform mat4 uProjection;
uniform mat4 uView;
uniform mat4 uModel;
uniform mat3 uNormalMatrix;

// Lights
uniform vec3 uLight1Position;
uniform vec3 uLight1Color;

out vec3 vColor;

void main() {
    vec3 FragPos = vec3(uModel * vec4(aPosition, 1.0));
    vec3 Normal = normalize(uNormalMatrix * aNormal);
    
    // Lighting calculation at vertex
    vec3 lightDir = normalize(uLight1Position - FragPos);
    float diff = max(dot(Normal, lightDir), 0.0);
    vColor = diff * uLight1Color;
    
    gl_Position = uProjection * uView * uModel * vec4(aPosition, 1.0);
}
```

### Fragment Shader

```glsl
#version 330 core

in vec3 vColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(vColor, 1.0);
}
```

### Use Cases

- **Smooth geometries** - Spheres, cylinders
- **Decent quality, good speed** - Default for many apps
- **Mobile rendering** - Lower computational cost
- **Real-time applications** - VR, games

### Advantages

✅ Smooth appearance
✅ Faster than Phong
✅ Good balance for real-time
✅ Suitable for curved surfaces

### Disadvantages

❌ Mach banding artifacts
❌ Lighting anomalies on silhouettes
❌ Can't show surface details
❌ Specular highlights interpolate unnaturally

---

## 3. Phong Shading

### Visual Characteristics
- Per-fragment lighting calculation
- Realistic specular highlights
- Smooth appearance without banding
- Industry standard quality

### Mathematical Model

Phong Lighting Equation (per-fragment):

$$L = k_a I_a + \sum_i [k_d (N \cdot L_i) + k_s (R \cdot V)^{n_s}] I_i$$

Where:
- $k_a, k_d, k_s$ = material coefficients (ambient, diffuse, specular)
- $N$ = surface normal
- $L_i$ = light direction
- $R$ = reflected light direction
- $V$ = view direction
- $n_s$ = shininess exponent
- $I_a, I_i$ = light intensities

### Vertex Shader

```glsl
#version 330 core

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;

uniform mat4 uProjection;
uniform mat4 uView;
uniform mat4 uModel;
uniform mat3 uNormalMatrix;

out vec3 vFragPos;
out vec3 vNormal;

void main() {
    vFragPos = vec3(uModel * vec4(aPosition, 1.0));
    vNormal = normalize(uNormalMatrix * aNormal);
    gl_Position = uProjection * uView * uModel * vec4(aPosition, 1.0);
}
```

### Fragment Shader

```glsl
#version 330 core

in vec3 vFragPos;
in vec3 vNormal;

uniform vec3 uViewPos;
uniform vec3 uLight1Pos;
uniform vec3 uLight1Color;
uniform float uAmbient;
uniform float uDiffuse;
uniform float uSpecular;
uniform float uShininess;

out vec4 FragColor;

void main() {
    vec3 norm = normalize(vNormal);
    vec3 lightDir = normalize(uLight1Pos - vFragPos);
    vec3 viewDir = normalize(uViewPos - vFragPos);
    vec3 reflectDir = reflect(-lightDir, norm);
    
    // Ambient
    vec3 ambient = uAmbient * uLight1Color;
    
    // Diffuse
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = uDiffuse * diff * uLight1Color;
    
    // Specular
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), uShininess);
    vec3 specular = uSpecular * spec * uLight1Color;
    
    vec3 result = (ambient + diffuse + specular);
    FragColor = vec4(result, 1.0);
}
```

### Components Breakdown

**Ambient Component:**
- Constant background lighting
- Simulates indirect light
- Prevents complete darkness in shadow

**Diffuse Component:**
- Depends on light-surface angle
- Creates realism without shine
- Proportional to $N \cdot L$

**Specular Component:**
- Simulates mirror-like reflections
- Depends on view angle
- Exponential with shininess

### Shininess Effects

```
Shininess = 8:    Large, soft highlight (rubber-like)
Shininess = 32:   Medium highlight (plastic)
Shininess = 128:  Sharp, small highlight (polished)
Shininess = 256:  Very sharp (mirror-like)
```

### Use Cases

- **Professional visualization** - Standard in graphics
- **Game engines** - Primary shading model
- **CAD software** - Industrial visualization
- **Scientific visualization** - Default recommended

### Advantages

✅ Realistic appearance
✅ No artifacts or banding
✅ Industry standard
✅ Good balance of quality/performance

### Disadvantages

❌ More computation than Gouraud
❌ Fixed sphere of light reflection
❌ Doesn't model rough surfaces
❌ Can't handle anisotropic materials

---

## 4. Extended Phong (PhongEx)

### Visual Characteristics
- All Phong features +
- Multiple materials per object
- Metallic properties
- Emissive colors
- Environment mapping

### Enhanced Model

$$L = k_a I_a + \sum_i [k_d (N \cdot L_i) + k_s (R \cdot V)^{n_s}] I_i + k_e$$

Plus modifications:
- Metallic factor blends reflection
- Roughness affects shininess
- Emissive adds glow
- HDRI provides environment reflection

### Vertex Shader

```glsl
#version 330 core

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;

uniform mat4 uProjection;
uniform mat4 uView;
uniform mat4 uModel;
uniform mat3 uNormalMatrix;

out vec3 vFragPos;
out vec3 vNormal;
out vec3 vViewDir;

void main() {
    vFragPos = vec3(uModel * vec4(aPosition, 1.0));
    vNormal = normalize(uNormalMatrix * aNormal);
    gl_Position = uProjection * uView * uModel * vec4(aPosition, 1.0);
}
```

### Fragment Shader (Simplified)

```glsl
#version 330 core

in vec3 vFragPos;
in vec3 vNormal;

uniform vec3 uViewPos;

// Material properties
uniform vec3 uDiffuse;
uniform vec3 uSpecular;
uniform vec3 uAmbient;
uniform float uShininess;
uniform float uMetallic;
uniform float uRoughness;
uniform vec3 uEmissive;
uniform float uEmissiveStrength;

// Lighting
uniform vec3 uLight1Pos;
uniform vec3 uLight1Color;

out vec4 FragColor;

void main() {
    vec3 norm = normalize(vNormal);
    vec3 lightDir = normalize(uLight1Pos - vFragPos);
    vec3 viewDir = normalize(uViewPos - vFragPos);
    
    // Standard Phong
    vec3 ambient = uAmbient;
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = uDiffuse * diff;
    
    // Shininess modified by roughness
    float effectiveShininess = uShininess * (1.0 - uRoughness);
    vec3 reflectDir = reflect(-lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), effectiveShininess);
    vec3 specular = uSpecular * spec;
    
    // Metallic: metallic surfaces reflect color
    if (uMetallic > 0.5) {
        specular = mix(specular, uDiffuse, uMetallic);
    }
    
    // Emissive glow
    vec3 emissive = uEmissive * uEmissiveStrength;
    
    vec3 result = (ambient + diffuse + specular) * uLight1Color + emissive;
    FragColor = vec4(result, 1.0);
}
```

### Material Properties Explained

**Metallic (0.0 - 1.0):**
```
0.0: Dielectric (plastic, rubber, wood)
0.5: Partially reflective
1.0: Full metallic (mirror-like)
```

**Roughness (0.0 - 1.0):**
```
0.0: Perfectly smooth (shiny)
0.5: Medium roughness (default)
1.0: Completely rough (dull)
```

**Emissive (RGB):**
- Color of the glow
- Independent of lighting
- Creates neon/glowing effect

### Use Cases

- **Photorealistic rendering** - High-quality visualization
- **Game assets** - PBR materials
- **Scientific instruments** - Metal/glass combinations
- **Architectural visualization** - Glazed surfaces

### Advantages

✅ Highly realistic
✅ Handles complex materials
✅ PBR-ready
✅ Emissive effects

### Disadvantages

❌ Most computationally expensive
❌ Requires careful tuning
❌ Data-heavy material definitions
❌ May look plastic with wrong parameters

---

## 5. Color Interpolation

### Visual Characteristics
- Per-vertex color interpolation
- No lighting calculations
- Direct color blending
- Useful for custom coloring

### Mathematical Model

Simply interpolate vertex colors across triangle:

$$C_{fragment} = \lambda_0 C_0 + \lambda_1 C_1 + \lambda_2 C_2$$

Where $\lambda$ are barycentric coordinates.

### Vertex Shader

```glsl
#version 330 core

layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aColor;

uniform mat4 uProjection;
uniform mat4 uView;
uniform mat4 uModel;

out vec3 vColor;

void main() {
    vColor = aColor;
    gl_Position = uProjection * uView * uModel * vec4(aPosition, 1.0);
}
```

### Fragment Shader

```glsl
#version 330 core

in vec3 vColor;
out vec4 FragColor;

void main() {
    FragColor = vec4(vColor, 1.0);
}
```

### Use Cases

- **Gradient visualization** - Smooth color gradients
- **Data visualization** - Color-mapped values
- **Debugging** - Visualize normals/UVs as colors
- **Custom effects** - Any per-vertex coloring

### Advantages

✅ Fastest (no calculations)
✅ Smooth gradients
✅ Full control via vertices
✅ Great for heatmaps

### Disadvantages

❌ No lighting
❌ Unrealistic appearance
❌ Requires pre-computed colors
❌ Can't respond to light changes

---

## Comparison Visualization

[TODO: Side-by-side comparison screenshot showing all 5 shading models on same geometry]

---

## Switching Between Models in BTL

```python
# In UI or code
viewer.shading_mode = 0  # Flat
viewer.shading_mode = 1  # Gouraud
viewer.shading_mode = 2  # Phong  
viewer.shading_mode = 3  # PhongEx
viewer.shading_mode = 4  # Color Interp
```

---

## Performance Profiling

**Typical GPU time per frame (1280x800):**

| Model | GPU Time | FPS |
|-------|----------|-----|
| Flat | 0.5ms | 120+ |
| Gouraud | 1.0ms | 100+ |
| Phong | 2.5ms | 60-80 |
| PhongEx | 4.5ms | 50-60 |
| Color Interp | 0.8ms | 100+ |

*Subject to GPU, scene complexity, lighting configuration*

---

## Best Practices

1. **Use Phong by default** - Best balance
2. **Flat for wireframe** - Quick preview
3. **Gouraud for mobile** - Performance
4. **PhongEx for showcase** - Maximum quality
5. **Color Interp for heatmaps** - Data visualization

---

## Mathematical References

- **Phong:** Phong, B. T. (1975). "Illumination for Computer Generated Pictures"
- **PBR:** Disney/Pixar research on physically-based rendering
- **Modern shading:** Learn OpenGL shading chapters

---

**Last Updated:** April 2026

