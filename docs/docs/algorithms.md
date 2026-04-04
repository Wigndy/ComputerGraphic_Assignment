# 🚀 Optimization Algorithms Deep Dive

This document provides mathematical foundations and implementation details for the 5 optimization algorithms implemented in BTL.

---

## Overview

| Algorithm | Type | Update Rule | Complexity | Best For |
|-----------|------|-------------|-----------|----------|
| **Batch GD** | First-order deterministic | Full gradient | Linear in dataset | Smooth, convex functions |
| **SGD** | First-order stochastic | Single sample gradient | Constant | Large-scale learning |
| **Mini-batch SGD** | First-order stochastic | Batch gradient | Batch size | Balance: stability vs speed |
| **Momentum** | Accelerated | Velocity accumulation | Linear in history | Escaping plateaus |
| **Adam** | Adaptive | Adaptive per-dimension | Linear in parameters | General purpose (recommended) |

---

## 1. Batch Gradient Descent (BGD)

### Mathematical Definition

$$\theta_{t+1} = \theta_t - \alpha \nabla f(\theta_t)$$

Where:
- $\alpha$ = learning rate
- $\nabla f(\theta_t)$ = gradient on entire dataset

### Characteristics

**Pros:**
- Guaranteed convergence (convex functions)
- Smooth, deterministic path
- No noise in updates

**Cons:**
- Slow convergence
- Cannot escape local minima
- High memory requirement (full dataset)
- Gets stuck on plateaus

### Visual Behavior

```
Loss Surface View:
  Smooth, straight paths
  Direct descent to minimum
  No oscillation
  
Trajectory Shape:
  Monotonically decreasing
  Potential: get stuck at saddle points
```

### Implementation Details

```python
# BGD step
gradient = compute_gradient(parameters, full_dataset)
parameters -= learning_rate * gradient
```

### Convergence Rate

- **For quadratic functions:** Exponential convergence
- **For general convex:** O(1/t) convergence rate
- **Color in BTL:** Red (#F24040)

---

## 2. Stochastic Gradient Descent (SGD)

### Mathematical Definition

$$\theta_{t+1} = \theta_t - \alpha \nabla f_i(\theta_t)$$

Where:
- $i$ = random sample index
- $\nabla f_i$ = gradient on single sample

### Characteristics

**Pros:**
- Fast iterations (single sample)
- Automatic noise helps escape local minima
- Low memory footprint
- Scales to massive datasets

**Cons:**
- Noisy updates cause oscillation
- Slower convergence per epoch
- Requires careful learning rate tuning
- Zigzag path to convergence

### Visual Behavior

```
Loss Surface View:
  Noisy, zigzag paths
  Random direction fluctuations
  Can "jump" over obstacles
  
Trajectory Shape:
  High variance
  Generally downward trend
  Many local deviations
```

### Implementation Details

```python
# SGD step (one sample)
gradient = compute_gradient(parameters, single_sample)
parameters -= learning_rate * gradient

# Typical training loop
for epoch in range(max_epochs):
    for sample in dataset:
        gradient = compute_gradient(parameters, sample)
        parameters -= learning_rate * gradient
```

### Noise Benefits

The stochastic noise in SGD provides:
1. **Escape from local minima** - Random perturbations
2. **Implicit regularization** - Acts like noise injection
3. **Better generalization** - Finds flatter minima
4. **Parallelizability** - Independent sample gradients
- **Color in BTL:** Orange (#FB6B16)

---

## 3. Mini-batch SGD

### Mathematical Definition

$$\theta_{t+1} = \theta_t - \alpha \frac{1}{|B|}\sum_{i \in B} \nabla f_i(\theta_t)$$

Where:
- $B$ = batch of samples (typically 16-128)
- $|B|$ = batch size

### Characteristics

**Pros:**
- Balances stability and speed
- Hardware-efficient (vectorized operations)
- Reduces variance vs SGD
- Faster than full-batch GD

**Cons:**
- Hyperparameter: batch size
- Larger mini-batches → more like BGD
- Smaller mini-batches → more like SGD

### Visual Behavior

```
Loss Surface View:
  Medium frequency oscillation
  Less noisy than SGD
  Smoother than BGD
  
Trajectory Shape:
  Intermediate variance
  Faster convergence than SGD
  Fewer deviations than SGD
```

### Batch Size Effects

```
Batch Size 1:     → SGD (noisy)
Batch Size 16:    → Mini-batch (balanced)
Batch Size 256:   → BGD (smooth)
Batch Size Full:  → Full Batch GD
```

### Implementation Details

```python
# Mini-batch SGD step
batch = sample_batch(dataset, batch_size=32)
gradient = compute_gradient(parameters, batch)
parameters -= learning_rate * gradient
```

### Typical Configuration

In BTL:
```python
opt_batch_size = 16              # Default mini-batch size
opt_noise_variance = 0.01        # Added noise level
```

- **Color in BTL:** Blue (#1496FF)

---

## 4. Momentum

### Mathematical Definition

$$v_{t+1} = \gamma v_t + \nabla f(\theta_t)$$
$$\theta_{t+1} = \theta_t - \alpha v_{t+1}$$

Where:
- $\gamma$ = momentum coefficient (typically 0.9)
- $v_t$ = velocity accumulator

### Characteristics

**Pros:**
- Accelerated convergence
- Escapes plateaus faster
- Smooths out oscillations
- Builds velocity down slopes

**Cons:**
- Can overshoot minima
- Requires tuning momentum coefficient
- May oscillate around minimum
- Not inherently adaptive

### Visual Behavior

```
Loss Surface View:
  Rolling ball metaphor
  Accelerates in consistent directions
  Overshoots valleys
  
Trajectory Shape:
  Faster straight lines
  Potential oscillation at end
  Momentum carries through
```

### Physics Interpretation

Think of parameter update as a **rolling ball**:
- Gradient = force pushing the ball
- Momentum coefficient = friction (0.9 = low friction)
- Velocity = accumulated momentum

### Update Variants

**Vanilla Momentum:**
```python
v = momentum * v + gradient
parameters -= learning_rate * v
```

**Nesterov Momentum (look-ahead):**
```python
v = momentum * v + gradient
parameters -= learning_rate * (momentum * v + gradient)
```

### Convergence Acceleration

- **Quadratic functions:** Factor of $1/\sqrt{1-\gamma}$ faster
- **Typical speedup:** 2-3x with $\gamma = 0.9$
- **Color in BTL:** Purple (#B33DFF)

---

## 5. Adam (Adaptive Moment Estimation)

### Mathematical Definition

$$m_t = \beta_1 m_{t-1} + (1 - \beta_1) \nabla f(\theta_t)$$
$$v_t = \beta_2 v_{t-1} + (1 - \beta_2) (\nabla f(\theta_t))^2$$
$$\hat{m}_t = m_t / (1 - \beta_1^t)$$
$$\hat{v}_t = v_t / (1 - \beta_2^t)$$
$$\theta_{t+1} = \theta_t - \alpha \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$

Where:
- $m_t$ = first moment estimate (mean)
- $v_t$ = second moment estimate (variance)
- $\beta_1$ = exponential decay for first moment (default 0.9)
- $\beta_2$ = exponential decay for second moment (default 0.999)
- $\epsilon$ = numerical stability (default 1e-8)
- $t$ = step count (for bias correction)

### Characteristics

**Pros:**
- Adaptive learning rate per parameter
- Combines benefits of Momentum + RMSprop
- Fast convergence
- Robust to hyperparameters
- **Default recommended optimizer**

**Cons:**
- More parameters to tune
- Slightly higher memory (maintains 2 accumulators)
- May not generalize as well as SGD in some cases

### Visual Behavior

```
Loss Surface View:
  Smooth, confident descent
  Adapts to local geometry
  Smaller steps near minima
  
Trajectory Shape:
  Fast initial descent
  Graceful slowdown near minimum
  Smooth convergence curves
```

### Intuition

Adam is like a **smart gradient descent** where:
1. **First moment ($m_t$)** = momentum/velocity accumulator
2. **Second moment ($v_t$)** = adaptive step size per dimension
3. **Bias correction** = accounts for cold-start at t=0

### Convergence Properties

- **Adaptive:** Step size adjusts per dimension
- **Robust:** Works well across many problems
- **Fast:** Converges 5-10x faster than SGD typically
- **Reliable:** Less sensitive to learning rate choice

### Typical Configuration

```python
learning_rate = 0.001          # Standard Adam LR
beta_1 = 0.9                   # First moment decay
beta_2 = 0.999                 # Second moment decay
epsilon = 1e-8                 # Numerical stability
```

- **Color in BTL:** Green (#34E156)

---

## Comparative Analysis

### Convergence on Quadratic Functions

$$f(x) = \frac{1}{2}x^T Q x$$

| Algorithm | Steps to Converge | Trajectory |
|-----------|------------------|------------|
| BGD | $O(\kappa)$ | Straight line |
| SGD | $O(\kappa + \frac{1}{\epsilon})$ | Noisy |
| Mini-batch | $O(\kappa + \frac{B}{\epsilon})$ | Medium noise |
| Momentum | $O(\sqrt{\kappa})$ | Smooth spiral |
| Adam | $O(\sqrt{\kappa})$ | Adaptive spiral |

Where $\kappa$ = condition number (ratio of max/min eigenvalues)

### Loss Function Difficulty

```python
# Easy: Quadratic
f(x,y) = x² + y²
All algorithms converge quickly

# Medium: Rosenbrock  
f(x,y) = (1-x)² + 100(y-x²)²
SGD struggles, Adam excels

# Hard: Himmelblau
f(x,y) = (x²+y-11)² + (x+y²-7)²
Multiple minima, SGD can jump, Adam stable
```

---

## Visualization Interpretation in BTL

### Ball Rolling Metaphor

The BTL visualizer animates all 5 optimizers as **colored rolling balls** on the loss surface:

```
Height map Z = log(1 + f(x,y))
Gravity = negative gradient

Ball Properties:
- Radius = 0.13 units
- Color = algorithm identity
- Spin = indicates momentum
- Altitude = instantaneous velocity
- Rolling = accumulated motion
```

### What to Observe

**BGD (Red):**
- Smoothest path
- Might stop before reaching optimum
- Good for simple landscapes

**SGD (Orange):**
- Jittery, bouncy movement
- Can jump over obstacles
- Finds different minima

**Mini-batch SGD (Blue):**
- Less jitter than SGD
- Faster than BGD
- Sweet spot for most problems

**Momentum (Purple):**
- Accelerates on slopes
- Overshoots at valleys
- Watch for oscillations

**Adam (Green):**
- Confident, swift descent
- Adapts to terrain
- Most reliable overall

---

## Hyperparameter Tuning Guidelines

### Learning Rate

```python
Too high (0.1):     Divergence, overshooting
Optimal (0.001-0.01): Smooth convergence
Too low (1e-6):     Extremely slow
```

### Momentum Coefficient (for Momentum only)

```python
Low (0.5):    Less acceleration, more responsive
Medium (0.9): Sweet spot, 2-3x speedup
High (0.99):  Strong acceleration, oscillation risk
```

### Batch Size (for Mini-batch SGD)

```python
1:         Full stochasticity, noisy
16:        Balanced (default in BTL)
256:       Smooth but slower per update
Full:      BGD behavior
```

---

## Common Pitfalls

### Pitfall 1: Same Learning Rate for All
- Different algorithms need different step sizes
- Adam typically needs smaller LR than SGD
- Solution: Use BTL UI to adjust per-algorithm

### Pitfall 2: Not Enough Epochs
- May stop before convergence
- Solution: Increase `max_epochs` in controller

### Pitfall 3: Ignoring Local Minima
- Stochastic methods can escape, adaptive methods find plateaus
- Solution: Try from different starting points

### Pitfall 4: Misinterpreting Ball Height
- Height = velocity magnitude, not loss value
- High ball = fast movement, not near optimum
- Watch actual loss curve, not ball position

---

## Research References

**Classic Papers:**

1. Rumelhart, Hinton, Williams (1986) - **Backprop with Momentum**
2. Nesterov (1983) - **Accelerated Gradient Methods**
3. Kingma, Ba (2014) - **Adam Optimizer** [arXiv:1412.6980](https://arxiv.org/abs/1412.6980)
4. Robbins, Monro (1951) - **Stochastic Approximation**

**Modern perspectives:**
- Wilson et al. (2017) - SGD Generalization vs Adam
- Choi et al. (2019) - Intrinsic Noise in SGD

---

## Mathematical Notation

| Symbol | Meaning |
|--------|---------|
| $\theta$ | Parameters (x, y in 2D case) |
| $\alpha$ | Learning rate |
| $\nabla f$ | Gradient (partial derivatives) |
| $\gamma$ | Momentum coefficient |
| $\beta$ | Exponential decay rate |
| $t$ | Step/epoch number |
| $\epsilon$ | Small constant (numerical stability) |

---

**Last Updated:** April 2026

