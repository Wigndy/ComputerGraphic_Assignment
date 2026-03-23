from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict

import numpy as np


class LossFunctionType(Enum):
    HIMMELBLAU = "himmelblau"
    ROSENBROCK = "rosenbrock"
    BOOTH = "booth"
    QUADRATIC_2D = "quadratic_2d"


@dataclass(frozen=True)
class LossFunction:
    loss_type: LossFunctionType
    label: str
    evaluate: Callable[[float, float], float]
    gradient: Callable[[float, float], np.ndarray]


class LossFunctionManager:
    @staticmethod
    def _himmelblau(x: float, y: float) -> float:
        term1 = x * x + y - 11.0
        term2 = x + y * y - 7.0
        return float(term1 * term1 + term2 * term2)

    @staticmethod
    def _himmelblau_grad(x: float, y: float) -> np.ndarray:
        term1 = x * x + y - 11.0
        term2 = x + y * y - 7.0
        dfdx = 4.0 * x * term1 + 2.0 * term2
        dfdy = 2.0 * term1 + 4.0 * y * term2
        return np.array([dfdx, dfdy], dtype=np.float64)

    @staticmethod
    def _rosenbrock(x: float, y: float) -> float:
        term1 = 1.0 - x
        term2 = y - x * x
        return float(term1 * term1 + 100.0 * term2 * term2)

    @staticmethod
    def _rosenbrock_grad(x: float, y: float) -> np.ndarray:
        term2 = y - x * x
        dfdx = 2.0 * (x - 1.0) - 400.0 * x * term2
        dfdy = 200.0 * term2
        return np.array([dfdx, dfdy], dtype=np.float64)

    @staticmethod
    def _booth(x: float, y: float) -> float:
        term1 = x + 2.0 * y - 7.0
        term2 = 2.0 * x + y - 5.0
        return float(term1 * term1 + term2 * term2)

    @staticmethod
    def _booth_grad(x: float, y: float) -> np.ndarray:
        # Expanded derivatives for lower overhead and clarity.
        dfdx = 10.0 * x + 8.0 * y - 34.0
        dfdy = 8.0 * x + 10.0 * y - 38.0
        return np.array([dfdx, dfdy], dtype=np.float64)

    @staticmethod
    def _quadratic_2d(x: float, y: float) -> float:
        return float(x * x + y * y)

    @staticmethod
    def _quadratic_2d_grad(x: float, y: float) -> np.ndarray:
        return np.array([2.0 * x, 2.0 * y], dtype=np.float64)

    _REGISTRY: Dict[LossFunctionType, LossFunction] = {
        LossFunctionType.HIMMELBLAU: LossFunction(
            loss_type=LossFunctionType.HIMMELBLAU,
            label="Himmelblau",
            evaluate=_himmelblau.__func__,
            gradient=_himmelblau_grad.__func__,
        ),
        LossFunctionType.ROSENBROCK: LossFunction(
            loss_type=LossFunctionType.ROSENBROCK,
            label="Rosenbrock (a=1, b=100)",
            evaluate=_rosenbrock.__func__,
            gradient=_rosenbrock_grad.__func__,
        ),
        LossFunctionType.BOOTH: LossFunction(
            loss_type=LossFunctionType.BOOTH,
            label="Booth",
            evaluate=_booth.__func__,
            gradient=_booth_grad.__func__,
        ),
        LossFunctionType.QUADRATIC_2D: LossFunction(
            loss_type=LossFunctionType.QUADRATIC_2D,
            label="Quadratic 2D",
            evaluate=_quadratic_2d.__func__,
            gradient=_quadratic_2d_grad.__func__,
        ),
    }

    @classmethod
    def list_available(cls) -> list[LossFunctionType]:
        return list(cls._REGISTRY.keys())

    @classmethod
    def get(cls, loss_type: LossFunctionType) -> LossFunction:
        return cls._REGISTRY[loss_type]

    @classmethod
    def evaluate(cls, loss_type: LossFunctionType, x: float, y: float) -> float:
        return cls.get(loss_type).evaluate(x, y)

    @classmethod
    def gradient(cls, loss_type: LossFunctionType, x: float, y: float) -> np.ndarray:
        return cls.get(loss_type).gradient(x, y)
