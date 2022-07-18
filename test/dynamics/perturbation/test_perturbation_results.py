# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests for perturbation_results.py"""

from qiskit import QiskitError

from multiset import Multiset

from qiskit_dynamics.array import Array
from qiskit_dynamics.perturbation.perturbation_results import PerturbationResults

from ..common import QiskitDynamicsTestCase


class TestPerturbationResults(QiskitDynamicsTestCase):
    """Test PerturbationResults."""

    def test_get_term(self):
        """Test that get_term works."""

        results = PerturbationResults(
            expansion_method="dyson_like",
            expansion_labels=[[0], [1], [0, 1]],
            expansion_terms=Array([5, 6, 7]),
        )

        self.assertTrue(results.get_term([1]) == Array(6))

    def test_sorted_get_term(self):
        """Test that sorting in get_item works."""

        results = PerturbationResults(
            expansion_method="dyson",
            expansion_labels=[
                Multiset([0]),
                Multiset([1]),
                Multiset([0, 1]),
            ],
            expansion_terms=Array([5, 6, 7]),
        )

        self.assertTrue(results.get_term([1, 0]) == Array(7))

    def test_get_item_error(self):
        """Test an error gets raised when a requested term doesn't exist."""

        results = PerturbationResults(
            expansion_method="dyson_like",
            expansion_labels=[[0], [1], [0, 1]],
            expansion_terms=Array([5, 6, 7]),
        )

        with self.assertRaises(QiskitError):
            # pylint: disable=pointless-statement
            results.get_term([2])
