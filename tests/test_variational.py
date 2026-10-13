"""Numerical regression tests for the explicit, educational 1-qubit solver."""
import math
import pytest
from vqe_ground_state.variational import expectation, solve_single_qubit


@pytest.mark.parametrize("offset,z,x", [
    (-1.0, 0.5, 0.25),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, -2.0),
    (5.0, -0.7, 1.2),
    (-12.0, 0.00001, 0.00002),
])
def test_vqe_matches_exact_diagonalization(offset, z, x):
    result = solve_single_qubit(offset, z, x)
    assert result.converged
    assert math.isclose(result.exact_energy, offset - math.hypot(z, x), abs_tol=1e-12)
    assert result.absolute_error < 1e-8
    assert result.energy >= result.exact_energy - 1e-12
    assert math.isclose(result.energy, expectation(result.theta_radians, offset, z, x), abs_tol=1e-12)


def test_identity_hamiltonian():
    result = solve_single_qubit(-0.7, 0.0, 0.0)
    assert result.energy == -0.7
    assert result.absolute_error == 0


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, 1e7, True])
def test_invalid_coefficient_rejected(bad):
    with pytest.raises(ValueError):
        solve_single_qubit(z=bad)
