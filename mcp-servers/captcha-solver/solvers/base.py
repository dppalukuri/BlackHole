"""Base solver interface."""

from abc import ABC, abstractmethod
from core.types import CaptchaChallenge, SolveResult, SolverConfig


class BaseSolver(ABC):
    """Abstract base class for all CAPTCHA solvers."""

    name: str = "base"
    cost_per_solve: float = 0.0  # Estimated USD cost per solve

    @abstractmethod
    async def can_solve(self, challenge: CaptchaChallenge) -> bool:
        """Check if this solver can handle the given challenge type."""
        ...

    @abstractmethod
    async def solve(self, challenge: CaptchaChallenge, config: SolverConfig) -> SolveResult:
        """Attempt to solve the challenge. Returns result with success/failure."""
        ...
