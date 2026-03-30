from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import numpy as np

from .loss_functions import LossFunctionManager, LossFunctionType


class OptimizerType(Enum):
    """Supported optimization algorithms for trajectory simulation."""

    BATCH_GRADIENT_DESCENT = "batch_gradient_descent"
    GRADIENT_DESCENT = "gradient_descent"
    MINI_BATCH_SGD = "mini_batch_sgd"
    MOMENTUM = "momentum"
    ADAM = "adam"


class BaseOptimizer(ABC):
    """
    Base class for 2D optimizers operating on analytical gradients.

    State management:
    - position: current coordinates [x, y]
    - previous_position: previous coordinates [x_prev, y_prev]
    - trajectory: list of visited coordinates for rendering paths
    """

    def __init__(
        self,
        loss_type: LossFunctionType,
        initial_x: float,
        initial_y: float,
        learning_rate: float = 0.01,
        noise_variance: float = 0.0,
        rng_seed: int | None = None,
    ):
        self.loss_type = loss_type
        self.learning_rate = float(learning_rate)
        self.noise_variance = max(0.0, float(noise_variance))

        self.position = np.array([initial_x, initial_y], dtype=np.float64)
        self.previous_position = self.position.copy()
        self.trajectory: list[np.ndarray] = [self.position.copy()]

        self._rng = np.random.default_rng(rng_seed)
        self.step_count = 0
        self.max_abs_gradient = 1e6
        self.max_abs_delta = 1e3
        self.max_abs_position = 1e4

    @property
    def x(self) -> float:
        return float(self.position[0])

    @property
    def y(self) -> float:
        return float(self.position[1])

    def set_loss_type(self, loss_type: LossFunctionType):
        self.loss_type = loss_type

    def set_position(self, x: float, y: float, clear_trajectory: bool = True):
        self.position = np.array([x, y], dtype=np.float64)
        self.previous_position = self.position.copy()
        if clear_trajectory:
            self.trajectory = [self.position.copy()]

    def current_loss(self) -> float:
        return LossFunctionManager.evaluate(self.loss_type, self.x, self.y)

    def _raw_gradient(self) -> np.ndarray:
        grad = LossFunctionManager.gradient(self.loss_type, self.x, self.y)
        return np.asarray(grad, dtype=np.float64)

    def _stochastic_gradient(self) -> np.ndarray:
        grad = self._raw_gradient()
        if self.noise_variance <= 0.0:
            return grad
        noise_std = np.sqrt(self.noise_variance)
        noise = self._rng.normal(loc=0.0, scale=noise_std, size=2)
        return grad + noise

    @abstractmethod
    def _compute_delta(self, gradient: np.ndarray) -> np.ndarray:
        """Return coordinate delta to apply: new_position = old_position + delta."""

    def _sanitize_vector(self, vec: np.ndarray, limit: float) -> np.ndarray:
        arr = np.asarray(vec, dtype=np.float64)
        arr = np.nan_to_num(arr, nan=0.0, posinf=limit, neginf=-limit)
        return np.clip(arr, -limit, limit)

    def _safe_delta(self, gradient: np.ndarray) -> np.ndarray:
        grad = self._sanitize_vector(gradient, self.max_abs_gradient)
        delta = self._compute_delta(grad)
        return self._sanitize_vector(delta, self.max_abs_delta)

    def _apply_update(self, delta: np.ndarray) -> np.ndarray:
        self.previous_position = self.position.copy()
        candidate = self.position + self._sanitize_vector(delta, self.max_abs_delta)
        if not np.all(np.isfinite(candidate)):
            candidate = self.position.copy()
        self.position = np.clip(candidate, -self.max_abs_position, self.max_abs_position)
        self.step_count += 1
        self.trajectory.append(self.position.copy())
        return self.position.copy()

    def step(self) -> np.ndarray:
        gradient = self._stochastic_gradient()
        delta = self._safe_delta(gradient)
        return self._apply_update(delta)


class GradientDescentOptimizer(BaseOptimizer):
    """Stochastic Gradient Descent (SGD) with optional gradient noise."""

    def _compute_delta(self, gradient: np.ndarray) -> np.ndarray:
        return -self.learning_rate * gradient


class BatchGradientDescentOptimizer(BaseOptimizer):
    """Full-batch Gradient Descent using analytical gradient without stochastic noise."""

    def _compute_delta(self, gradient: np.ndarray) -> np.ndarray:
        return -self.learning_rate * gradient

    def step(self) -> np.ndarray:
        gradient = self._raw_gradient()
        delta = self._safe_delta(gradient)
        return self._apply_update(delta)


class MiniBatchSGDOptimizer(BaseOptimizer):
    """Mini-batch SGD with noise scale reduced by sqrt(batch_size)."""

    def __init__(
        self,
        loss_type: LossFunctionType,
        initial_x: float,
        initial_y: float,
        learning_rate: float = 0.01,
        batch_size: int = 16,
        noise_variance: float = 0.0,
        rng_seed: int | None = None,
    ):
        super().__init__(
            loss_type=loss_type,
            initial_x=initial_x,
            initial_y=initial_y,
            learning_rate=learning_rate,
            noise_variance=noise_variance,
            rng_seed=rng_seed,
        )
        self.batch_size = max(1, int(batch_size))

    def _compute_delta(self, gradient: np.ndarray) -> np.ndarray:
        return -self.learning_rate * gradient

    def _stochastic_gradient(self) -> np.ndarray:
        grad = self._raw_gradient()
        if self.noise_variance <= 0.0:
            return grad
        noise_std = np.sqrt(self.noise_variance / float(self.batch_size))
        noise = self._rng.normal(loc=0.0, scale=noise_std, size=2)
        return grad + noise


class MomentumOptimizer(BaseOptimizer):
    """Gradient descent with momentum term v."""

    def __init__(
        self,
        loss_type: LossFunctionType,
        initial_x: float,
        initial_y: float,
        learning_rate: float = 0.01,
        momentum_coefficient: float = 0.9,
        noise_variance: float = 0.0,
        rng_seed: int | None = None,
    ):
        super().__init__(
            loss_type=loss_type,
            initial_x=initial_x,
            initial_y=initial_y,
            learning_rate=learning_rate,
            noise_variance=noise_variance,
            rng_seed=rng_seed,
        )
        self.momentum_coefficient = float(momentum_coefficient)
        self.velocity = np.zeros(2, dtype=np.float64)

    def _compute_delta(self, gradient: np.ndarray) -> np.ndarray:
        self.velocity = self.momentum_coefficient * self.velocity - self.learning_rate * gradient
        self.velocity = self._sanitize_vector(self.velocity, self.max_abs_delta)
        return self.velocity


class AdamOptimizer(BaseOptimizer):
    """
    Adam optimizer.

    Notes:
    - momentum_coefficient corresponds to beta1 (1st-moment decay).
    - beta2 controls 2nd-moment decay.
    """

    def __init__(
        self,
        loss_type: LossFunctionType,
        initial_x: float,
        initial_y: float,
        learning_rate: float = 0.01,
        momentum_coefficient: float = 0.9,
        beta2: float = 0.999,
        epsilon: float = 1e-8,
        noise_variance: float = 0.0,
        rng_seed: int | None = None,
    ):
        super().__init__(
            loss_type=loss_type,
            initial_x=initial_x,
            initial_y=initial_y,
            learning_rate=learning_rate,
            noise_variance=noise_variance,
            rng_seed=rng_seed,
        )
        self.momentum_coefficient = float(momentum_coefficient)  # beta1
        self.beta2 = float(beta2)
        self.epsilon = float(epsilon)

        self.m = np.zeros(2, dtype=np.float64)
        self.v = np.zeros(2, dtype=np.float64)

    def _compute_delta(self, gradient: np.ndarray) -> np.ndarray:
        beta1 = self.momentum_coefficient
        self.m = beta1 * self.m + (1.0 - beta1) * gradient
        self.v = self.beta2 * self.v + (1.0 - self.beta2) * (gradient * gradient)
        self.m = self._sanitize_vector(self.m, self.max_abs_gradient)
        self.v = self._sanitize_vector(self.v, self.max_abs_gradient)

        t = self.step_count + 1
        m_hat = self.m / (1.0 - beta1 ** t)
        v_hat = self.v / (1.0 - self.beta2 ** t)

        update = self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)
        return -self._sanitize_vector(update, self.max_abs_delta)


class OptimizerFactory:
    """Factory to switch optimizer algorithm at runtime."""

    @staticmethod
    def create(
        optimizer_type: OptimizerType,
        loss_type: LossFunctionType,
        initial_x: float,
        initial_y: float,
        learning_rate: float = 0.01,
        momentum_coefficient: float = 0.9,
        batch_size: int = 16,
        noise_variance: float = 0.0,
        rng_seed: int | None = None,
    ) -> BaseOptimizer:
        if optimizer_type == OptimizerType.BATCH_GRADIENT_DESCENT:
            return BatchGradientDescentOptimizer(
                loss_type=loss_type,
                initial_x=initial_x,
                initial_y=initial_y,
                learning_rate=learning_rate,
                noise_variance=noise_variance,
                rng_seed=rng_seed,
            )
        if optimizer_type == OptimizerType.GRADIENT_DESCENT:
            return GradientDescentOptimizer(
                loss_type=loss_type,
                initial_x=initial_x,
                initial_y=initial_y,
                learning_rate=learning_rate,
                noise_variance=noise_variance,
                rng_seed=rng_seed,
            )
        if optimizer_type == OptimizerType.MINI_BATCH_SGD:
            return MiniBatchSGDOptimizer(
                loss_type=loss_type,
                initial_x=initial_x,
                initial_y=initial_y,
                learning_rate=learning_rate,
                batch_size=batch_size,
                noise_variance=noise_variance,
                rng_seed=rng_seed,
            )
        if optimizer_type == OptimizerType.MOMENTUM:
            return MomentumOptimizer(
                loss_type=loss_type,
                initial_x=initial_x,
                initial_y=initial_y,
                learning_rate=learning_rate,
                momentum_coefficient=momentum_coefficient,
                noise_variance=noise_variance,
                rng_seed=rng_seed,
            )
        if optimizer_type == OptimizerType.ADAM:
            return AdamOptimizer(
                loss_type=loss_type,
                initial_x=initial_x,
                initial_y=initial_y,
                learning_rate=learning_rate,
                momentum_coefficient=momentum_coefficient,
                noise_variance=noise_variance,
                rng_seed=rng_seed,
            )

        raise ValueError(f"Unsupported optimizer type: {optimizer_type}")
