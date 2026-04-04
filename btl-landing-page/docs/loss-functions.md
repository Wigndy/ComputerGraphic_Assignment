# 📊 Loss Functions & Optimization Landscapes

This document describes the 5 loss functions built into BTL with their mathematical definitions, characteristics, and why they're interesting for optimization visualization.

---

## Overview

| Function | Domain | Global Min | Type | Difficulty |
|----------|--------|------------|------|------------|
| **Beale** | [-4.5, 4.5]² | (3.0, 0.5) f=0 | Multimodal | Medium |
| **Himmelblau** | [-5, 5]² | 4 minima (f≈0) | Multimodal | Hard |
| **Rosenbrock** | [-30, 30]² | (1.0, 1.0) f=0 | Unimodal valley | Very Hard |
| **Booth** | [-30, 30]² | (1.0, 3.0) f=0 | Unimodal | Easy |
| **Quadratic 2D** | [-30, 30]² | (0.0, 0.0) f=0 | Unimodal | Very Easy |

---

## 1. Beale Function

### Definition

$$f(x, y) = (1.5 - x + xy)^2 + (2.25 - x + xy^2)^2 + (2.625 - x + xy^3)^2$$

### Mathematical Properties

- **Global minimum:** $(3.0, 0.5)$ with $f = 0$
- **Gradient at minimum:** $\nabla f = (0, 0)$
- **Condition number:** High (difficult to optimize)
- **Range:** $[0, \infty)$

### Partial Derivatives

$$\frac{\partial f}{\partial x} = 2(1.5 - x + xy)(y - 1) + 2(2.25 - x + xy^2)(y^2 - 1) + 2(2.625 - x + xy^3)(y^3 - 1)$$

$$\frac{\partial f}{\partial y} = 2(1.5 - x + xy) \cdot x + 2(2.25 - x + xy^2) \cdot 2xy + 2(2.625 - x + xy^3) \cdot 3xy^2$$

### Characteristics

**Why it's interesting:**
- Multiple local minima create valleys
- Steep walls make optimization challenging  
- Good for testing robustness
- Gradient can be misleading
- Requires careful learning rates

### Visualization Description

[TODO: 3D surface plot of Beale function showing valleys]

### Optimizer Difficulty

```
Easy optimizers:  Adam (finds minimum readily)
Medium optimizers: Momentum (can overshoot)
Hard optimizers:   SGD, BGD (zigzag, get stuck)
```

### Starting Points to Try

```python
Start 1: (-2.0, 4.0)  → Easy descent
Start 2: (0.0, 0.0)   → More challenging
Start 3: (3.5, 0.0)   → Near minimum
Start 4: (-4.0, -4.0) → Far start
```

---

## 2. Himmelblau Function

### Definition

$$f(x, y) = (x^2 + y - 11)^2 + (x + y^2 - 7)^2$$

### Mathematical Properties

- **Global minimum:** Four global minima (all with f ≈ 0)
  - $(3.0, 2.0)$ → f = 0
  - $(-2.805, 3.131)$ → f ≈ 0
  - $(-3.779, -3.283)$ → f ≈ 0
  - $(3.584, -1.848)$ → f ≈ 0
- **Symmetry:** Approximate 4-fold symmetry
- **Range:** $[0, \infty)$

### Partial Derivatives

$$\frac{\partial f}{\partial x} = 2(x^2 + y - 11) \cdot 2x + 2(x + y^2 - 7) \cdot 1$$

$$\frac{\partial f}{\partial y} = 2(x^2 + y - 11) \cdot 1 + 2(x + y^2 - 7) \cdot 2y$$

### Characteristics

**Why it's interesting:**
- **Multiple global minima** - Which one do optimizers reach?
- **Deep valleys** - Different basins of attraction
- **No obvious pattern** - Good for testing algorithm behavior
- **Practical relevance** - Models real non-convex problems
- **Symmetry** - Interesting to observe

### Visualization Description

[TODO: 3D surface plot of Himmelblau function with 4 peaks]

### The 4 Minima

```
Minimum 1: (3.0, 2.0)
  Location: Northeast quadrant
  Basin: Easy to reach
  
Minimum 2: (-2.805, 3.131)  
  Location: Northwest quadrant
  Basin: Moderate difficulty
  
Minimum 3: (-3.779, -3.283)
  Location: Southwest quadrant
  Basin: Hard to reach from center
  
Minimum 4: (3.584, -1.848)
  Location: Southeast quadrant
  Basin: Very close to global min 1
```

### Optimizer Behavior

```
SGD: Explores, may jump between basins
Adam: Usually finds one minimum and settles
Momentum: Oscillates, can cross basins
BGD: Gets stuck in local minima
Mini-batch: Hybrid behavior
```

### Starting Points to Try

```python
Start 1: (-4.0, 4.0)    → Northwest basin
Start 2: (4.0, 4.0)     → Northeast (min 1)
Start 3: (-4.0, -4.0)   → Southwest (min 3)
Start 4: (4.0, -4.0)    → Southeast area
```

---

## 3. Rosenbrock Function

### Definition

$$f(x, y) = (1 - x)^2 + 100(y - x^2)^2$$

### Mathematical Properties

- **Global minimum:** $(1.0, 1.0)$ with $f = 0$
- **Gradient at minimum:** $\nabla f = (0, 0)$
- **Characteristic:** Very narrow, curved valley
- **Condition number:** Extremely high (~1000)
- **Range:** $[0, \infty)$

### Partial Derivatives

$$\frac{\partial f}{\partial x} = -2(1-x) - 400x(y - x^2)$$

$$\frac{\partial f}{\partial y} = 200(y - x^2)$$

### Characteristics

**Why it's interesting:**
- **Classic benchmark** - Used in optimization literature since 1960s
- **Notoriously difficult** - Even "easy" methods can struggle
- **Non-convex valley** - Curved path to optimum
- **Misleading gradients** - Gradient points wrong direction often
- **Tests acceleration** - Which algorithms find shortcut?

### The Rosenbrock Valley

```
Starting point: (-1.5, 2.5)
   ↓
First phase: Descend into valley     (hard, steep walls)
   ↓
Second phase: Follow curved valley   (slow, winding path)
   ↓
Final point: (1.0, 1.0)              (stop at bottom)
```

Typical distance: ~2000 curvature units to traverse!

### Visualization Description

[TODO: 3D surface plot of Rosenbrock function showing characteristic valley]

### Optimizer Comparison

| Algorithm | Typical Performance |
|-----------|-------------------|
| BGD | Very slow, gets stuck |
| SGD | Struggles, noisy |
| Mini-batch | Better, but still slow |
| **Momentum** | **Fast, smooth path** |
| **Adam** | **Fastest, steepest** |

### Why This Function?

The Rosenbrock function was created by Howard H. Rosenbrock in 1960 as a test function that:
1. Has a single global minimum (no ambiguity)
2. Is extremely difficult for optimization
3. Reveals algorithmic shortcomings
4. Requires sophisticated solution methods

It remains the **gold standard** for testing optimizers.

### Starting Points to Try

```python
Start 1: (-1.5, 2.5)   → Classic (far)
Start 2: (0.0, 0.0)    → On valley
Start 3: (0.5, 0.25)   → Closer to min
Start 4: (1.5, 2.25)   → Far, other side
```

---

## 4. Booth Function

### Definition

$$f(x, y) = (x + 2y - 7)^2 + (2x + y - 5)^2$$

### Mathematical Properties

- **Global minimum:** $(1.0, 3.0)$ with $f = 0$
- **Form:** Sum of two linear functions, squared
- **Condition number:** Low-moderate
- **Range:** $[0, \infty)$

### Partial Derivatives

$$\frac{\partial f}{\partial x} = 2(x + 2y - 7) \cdot 1 + 2(2x + y - 5) \cdot 2 = 2(x + 2y - 7) + 4(2x + y - 5)$$

$$\frac{\partial f}{\partial y} = 2(x + 2y - 7) \cdot 2 + 2(2x + y - 5) \cdot 1 = 4(x + 2y - 7) + 2(2x + y - 5)$$

Simplified:
$$\frac{\partial f}{\partial x} = 10x + 8y - 34$$
$$\frac{\partial f}{\partial y} = 8x + 10y - 34$$

### Characteristics

**Why it's interesting:**
- **Simplest non-trivial function** - Easy to understand geometrically
- **Linear structure** - Two perpendicular planes
- **Clean solution** - Good for testing basics
- **Educational value** - Shows fundamental concepts clearly
- **Moderate difficulty** - All algorithms work reasonably

### Geometric Interpretation

The Booth function represents the intersection of two planes:
1. Plane 1: $x + 2y - 7 = 0$ (passes through (7,0), (1,3), (-5,6))
2. Plane 2: $2x + y - 5 = 0$ (passes through (2.5,0), (1,3), (0,5))

Their intersection is a valley with minimum at $(1, 3)$.

### Visualization Description

[TODO: 3D surface plot of Booth function showing two intersection planes]

### Optimizer Behavior

```
All optimizers converge smoothly
No tricks or surprises
Good performance from all algorithms
'''

### Starting Points to Try

```python
Start 1: (-2.0, 3.0)    → Medium distance
Start 2: (8.0, -3.0)    → Far corner
Start 3: (0.0, 0.0)     → Origin
Start 4: (-5.0, 5.0)    → Opposite
```

---

## 5. Quadratic 2D (Baseline)

### Definition

$$f(x, y) = x^2 + y^2$$

### Mathematical Properties

- **Global minimum:** $(0, 0)$ with $f = 0$
- **Spherical symmetry:** Same distance from origin = same value
- **Gradient:** Always points toward origin
- **Perfect paraboloid:** Ideal geometric shape
- **Condition number:** 1.0 (perfectly conditioned)

### Partial Derivatives

$$\frac{\partial f}{\partial x} = 2x$$

$$\frac{\partial f}{\partial y} = 2y$$

Gradient: $\nabla f = (2x, 2y)$ - always points away from origin

### Characteristics

**Why it's interesting:**
- **Trivial for optimization** - All algorithms succeed equally
- **Baseline comparison** - Benchmark reference
- **Theoretical analysis** - Clean mathematics
- **Educational tool** - Introduces quadratic functions
- **Visual clarity** - Perfect bowl shape

### Solution Path

Starting from point $(x_0, y_0)$:
- Distance to origin: $r = \sqrt{x_0^2 + y_0^2}$
- Optimal step size: $\alpha = 0.5$
- Steps to convergence: $\log_2(r/\epsilon)$ for convergence tolerance $\epsilon$

### Optimizer Performance

| Algorithm | Epochs to Converge |
|-----------|------------------|
| BGD (α=0.1) | ~50 |
| SGD (α=0.1) | ~50 (noisy) |
| Mini-batch (α=0.1) | ~50 |
| Momentum (γ=0.9) | ~20 |
| Adam | ~15 |

All converge very fast!

### Visualization Description

[TODO: 3D surface plot of Quadratic 2D - perfect paraboloid]

### Starting Points to Try

```python
Start 1: (10.0, 10.0)   → Standard distance
Start 2: (1.0, 0.0)     → Easy
Start 3: (-15.0, 15.0)  → Diagonal far
Start 4: (0.1, 0.1)     → Very close
```

---

## Comparative Analysis

### Optimization Difficulty Ranking

```
Easiest ─────────────────────────────── Hardest

1. Quadratic 2D    ✓ All algorithms succeed
2. Booth           ✓✓ Most algorithms succeed  
3. Beale           ✓✓✓ Some struggle
4. Himmelblau      ✓✓✓✓ Multiple minima confuse
5. Rosenbrock      ✓✓✓✓✓ Extreme difficulty
```

### Characteristic Contour Patterns

[TODO: Contour plot comparison of all 5 functions]

---

## Mathematical Properties Comparison

| Property | Quadratic | Booth | Beale | Himmelblau | Rosenbrock |
|----------|-----------|-------|-------|-----------|-----------|
| Minima | 1 | 1 | 1 | 4 | 1 |
| Convex | Yes | Yes | No | No | No |
| Smooth | Yes | Yes | Yes | Yes | Yes |
| Condition # | 1 | ~5 | ~100 | ~1000 | ~1000 |
| Difficulty | Trivial | Easy | Medium | Hard | Very Hard |

---

## Using Loss Functions in Code

### Evaluate a Function

```python
from BTL.sample_function import LossFunctionManager, LossFunctionType

loss = LossFunctionManager.evaluate(
    LossFunctionType.ROSENBROCK, 
    x=0.5, 
    y=0.25
)
# Returns approximately 24.375
```

### Get Gradient

```python
gx, gy = LossFunctionManager.gradient(
    LossFunctionType.ROSENBROCK,
    x=0.5,
    y=0.25
)
# Returns gradient components for next step
```

### Visualize in BTL

```python
from BTL.optimizer_controller import OptimizerController
from BTL.sample_function import LossFunctionType

controller = OptimizerController()
controller.loss_function_idx = \
    controller.loss_function_types.index(LossFunctionType.ROSENBROCK)
controller.activate_scene()
```

---

## Extended Mathematical Notes

### Condition Number Explanation

The **condition number** $\kappa$ indicates how "hard" direct optimization is:

$$\kappa = \frac{\lambda_{max}}{\lambda_{min}}$$

Where $\lambda$ are eigenvalues of the Hessian matrix.

- $\kappa = 1$: Perfectly conditioned (Quadratic 2D)
- $\kappa = 10$: Well-conditioned (Booth)
- $\kappa = 100$: Ill-conditioned (Beale)
- $\kappa = 1000$: Very ill-conditioned (Rosenbrock)

Higher condition number = more difficult for gradient descent.

### Hessian Matrices

For each function, the Hessian (second derivative matrix) reveals curvature:

```python
H = [
    [∂²f/∂x², ∂²f/∂x∂y],
    [∂²f/∂y∂x, ∂²f/∂y²]
]
```

Eigenvalues of H determine:
- Local curvature
- Required step size
- Convergence rate

---

## References

1. **Beale, E.** (1962) - "On an Iterative Method for Finding Local Minima"
2. **Himmelblau, D.** (1972) - "Applied Nonlinear Programming"
3. **Rosenbrock, H.** (1960) - "An Automatic Method for Finding the Greatest or Least Value of a Function"
4. **Booth, A.** (1958) - "Numerical Methods"

---

## Visualization Tips in BTL

### For Each Function

**Quadratic 2D:**
- Lower mesh resolution (radius of convergence is obvious)
- Use Momentum to see acceleration
- Try all starting points - all converge equally

**Booth:**
- Medium resolution
- Good for teaching basics
- All algorithms perform similarly
- Observe smooth descent paths

**Beale:**
- Higher resolution to see valley details
- Multiple starting points show different behaviors
- Notice where SGD gets stuck
- See Adam's adaptivity advantage

**Himmelblau:**
- Full resolution for all 4 minima
- Start from different corners
- Observe which minima algorithms find
- Use contour view to see basins

**Rosenbrock:**
- Full resolution (200x200)
- Classic start: (-1.5, 2.5)
- Observe the winding valley
- Compare epoch counts of algorithms
- This is the ultimate test!

---

**Last Updated:** April 2026

