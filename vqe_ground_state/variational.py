"""Dependency-free educational variational eigensolver for a one-qubit Hamiltonian.

H = offset * I + z * Z + x * X, with real coefficients in any consistent
energy unit (hartree when the inputs are in hartree). No molecular integrals
or electronic structure Hamiltonian are generated here.
"""
from dataclasses import asdict, dataclass
import math


@dataclass(frozen=True)
class VQEResult:
    energy: float
    exact_energy: float
    absolute_error: float
    theta_radians: float
    evaluations: int
    converged: bool

    def to_dict(self):
        return asdict(self)


def expectation(theta: float, offset: float, z: float, x: float) -> float:
    """Expectation of H in Ry(theta)|0>."""
    return offset + z * math.cos(theta) + x * math.sin(theta)


def solve_single_qubit(offset: float = -1.0, z: float = 0.5, x: float = 0.25) -> VQEResult:
    """Find the global minimum via coarse scan and golden-section refinement.

    Exact diagonalization is calculated separately as a validation reference.
    """
    coefficients = (offset, z, x)
    if any(not isinstance(v, (int, float)) or isinstance(v, bool)
           or not math.isfinite(v) or abs(v) > 1e6 for v in coefficients):
        raise ValueError("Hamiltonian coefficients must be finite real numbers within +/-1e6")
    if z == 0 and x == 0:
        return VQEResult(float(offset), float(offset), 0.0, 0.0, 1, True)

    n = 72
    spacing = 2 * math.pi / n
    samples = [expectation(k * spacing, offset, z, x) for k in range(n)]
    center = min(range(n), key=samples.__getitem__) * spacing
    left, right = center - spacing, center + spacing
    ratio = (math.sqrt(5) - 1) / 2
    p, q = right - ratio * (right - left), left + ratio * (right - left)
    fp, fq = expectation(p, offset, z, x), expectation(q, offset, z, x)
    evaluations = n + 2

    for _ in range(80):
        if right - left < 1e-11:
            break
        if fp < fq:
            right, q, fq = q, p, fp
            p = right - ratio * (right - left)
            fp = expectation(p, offset, z, x)
        else:
            left, p, fp = p, q, fq
            q = left + ratio * (right - left)
            fq = expectation(q, offset, z, x)
        evaluations += 1

    theta = (left + right) / 2 % (2 * math.pi)
    energy = expectation(theta, offset, z, x)
    exact = offset - math.hypot(z, x)
    difference = abs(energy - exact)
    return VQEResult(energy, exact, difference, theta, evaluations, difference < 1e-8)
