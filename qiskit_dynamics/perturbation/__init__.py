# -*- coding: utf-8 -*-

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

r"""
=========================================================
Perturbation Theory (:mod:`qiskit_dynamics.perturbation`)
=========================================================

.. currentmodule:: qiskit_dynamics.perturbation

This module contains tools for numerically computing and utilizing perturbation
theory terms, with functions for computing multi-variable Dyson series and Magnus expansions.
As perturbative expansions are phrased in terms of multi-variable power-series, the starting
point for this module is establishing a notation for multi-variable power series, which is outlined
in the remainder of this introduction.

Mathematically, a formal array-valued power-series in :math:`r` variables
:math:`c_0, \dots, c_{r-1}` is an expression of the form:

.. math::

    f(c_0, \dots, c_{r-1}) = A_\emptyset + \sum_{k=1}^\infty
                \sum_{0 \leq i_1 \leq \dots \leq i_k \leq r-1}
                (c_{i_1} \times \dots \times c_{i_k}) A_{i_1, \dots, i_k},

where the :math:`A_\emptyset` and :math:`A_{i_1, \dots, i_k}`
are arrays of common shape.

Structurally, each term in the power series is labelled by the number of times each
variable :math:`c_0, \dots, c_{r-1}` appears in the product :math:`c_{i_1} \dots c_{i_k}`.
Equivalently, each term may be indexed by the number of times each variable label
:math:`0, \dots, r-1` appears. The data structure used to represent these labels in this
module is that of a *multiset*, i.e. a "set with repeated entries". Denoting multisets
with round brackets, e.g. :math:`I = (i_1, \dots, i_k)`, we define

.. math::

    c_I = c_{i_1} \times \dots \times c_{i_k}.

and similarly denote :math:`A_I = A_{i_1, \dots, i_k}`. This notation is chosen due to
the simple relationship between algebraic operations and multiset operations. E.g.,
for two multisets :math:`I, J`, it holds that:

.. math::

    c_{I + J} = c_I \times c_J,

where :math:`I+J` denotes the multiset whose object counts are the sum of both :math:`I` and
:math:`J`.

Some example usages of this notation are:

    - :math:`c_{(0, 1)} = c_0 c_1`,
    - :math:`c_{(1, 1)} = c_1^2`, and
    - :math:`c_{(1, 2, 2, 3)} = c_1 c_2^2 c_3`.

Finally, we denote the set of multisets of size $k$ with elements lying in :math:`{0, \dots, r-1}`
as :math:`\mathcal{I}_k(r)`. Combining everything, the power series above may be
rewritten as:

.. math::

    f(c_0, \dots, c_{r-1}) = A_\emptyset + \sum_{k=1}^\infty \sum_{I \in \mathcal{I}_k(r)} c_I A_I.


Multisets and truncated power-series representation
===================================================

Can reinsert a description of ``Multiset`` in the ``multiset`` package here.
Need to be explicit that the functionality here restricts multisets to consist
only of non-negative integers.

The class :class:`~qiskit_dynamics.perturbation.ArrayPolynomial` represents an array-valued
multivariable polynomial (i.e. a truncated power series), and provides functionality for
both evaluating and transforming array-valued polynomials.
An :class:`~qiskit_dynamics.perturbation.ArrayPolynomial` ``ap`` can be evaluated on a 1d array
of variables ``c`` via:

.. code-block:: python

    ap(c)

Algebraic operations may be performed on :class:`~qiskit_dynamics.perturbation.ArrayPolynomial`\s,
e.g. for two instances ``ap1`` and ``ap2``, the line ``ap3 = ap1 * ap2``
results in a third instance ``ap3`` satisfying

.. code-block:: python

    ap3(c) == ap1(c) * ap2(c)

for all variable arrays ``c``.

Some array methods, such as ``trace`` and ``transpose``, are also implemented, and
satisfy, e.g.

.. code-block:: python

    (ap.trace())(c) == ap(c).trace()

.. _td perturbation theory:

Time-dependent perturbation theory
==================================

Using algorithms in [:footcite:`puzzuoli_sensitivity_2022`], the function
:func:`~qiskit_dynamics.perturbation.solve_lmde_perturbation`
computes Dyson series [:footcite:`dyson_radiation_1949`] and
Magnus expansion [:footcite:`magnus_exponential_1954`, :footcite:`blanes_magnus_2009`] terms,
which are time-dependent perturbation theory expansions
used in matrix differential equations (LMDEs). Using the power series notation of the
previous section, the general setting supported by this function involves LMDE generators
with power series decompositions of the form:

.. math::

    G(t, c_0, \dots, c_{r-1}) = G_\emptyset(t)
        + \sum_{k=1}^\infty \sum_{I \in \mathcal{I}_k(r)} c_I G_I(t),

where

    - :math:`G_\emptyset(t)` is the unperturbed generator,
    - The :math:`G_I(t)` give the time-dependent operator form of the perturbations, and
    - The expansion parameters :math:`c_0, \dots, c_{r-1}` are the perturbation parameters.

.. note::

    The above is written as an infinite power series, but of course, in practice,
    the function assumes only a finite number of the :math:`G_I(t)` are specified as being
    non-zero.

:func:`~qiskit_dynamics.perturbation.solve_lmde_perturbation` computes expansion terms
*in the toggling frame of the unperturbed generator* :math:`G_\emptyset(t)`
[:footcite:`evans_timedependent_1967`, :footcite:`haeberlen_1968`].
Denoting :math:`V(t) = \mathcal{T}\exp(\int_{t_0}^t ds G_\emptyset(s))`,
the generator :math:`G` in the toggling frame of :math:`G_\emptyset(t)`
is given by:

.. math::

    \tilde{G}(t, c_0, \dots, c_{r-1}) =
            \sum_{k=1}^\infty \sum_{I \in \mathcal{I}_k(r)} c_I \tilde{G}_I(t),

with :math:`\tilde{G}_I(t) = V^{-1}(t) G_I(t)V(t)`.

Denoting

.. math::

    U(t, c_0, \dots, c_{r-1}) =
        \mathcal{T}\exp\left(\int_{t_0}^t ds \tilde{G}(s, c_0, \dots, c_{r-1})\right),

the Dyson series directly expands the solution as a power series in the :math:`c_0, \dots, c_{r-1}`:

.. math::

    U(t, c_0, \dots, c_{r-1}) =
            I + \sum_{k=1}^\infty \sum_{I \in \mathcal{I}_k(r)} c_I \mathcal{D}_I(t).

The :math:`\mathcal{D}_I(t)`, which we refer to as *multivariable Dyson terms*, or
simply *Dyson terms*, are defined *implicitly* above as the power-series expansion coefficients.

The Magnus expansion similarly gives a power series decomposition of the
time-averaged generator:

.. math::

    \Omega(t, c_0, \dots, c_{r-1}) =
            \sum_{k=1}^\infty \sum_{I \in \mathcal{I}_k(r)} c_I \mathcal{O}_I(t),

which satisfies
:math:`U(t, c_0, \dots, c_{r-1}) = \exp(\Omega(t, c_0, \dots, c_{r-1}))`
under certain conditions [:footcite:`magnus_exponential_1954`, :footcite:`blanes_magnus_2009`].
Again, the :math:`\mathcal{O}_I(t)` are defined as *implicitly* as the coefficients
in the above series.

.. note::

    The above is a non-standard presentation of the Dyson series and Magnus expansion.
    These expansions are typically described via explicit expressions, and are not phrased
    in terms of multi-variable power series. Within the above notation, the standard
    definitions of the Dyson series and Magnus expansions may be viewed as the single-variable
    case.

:func:`~qiskit_dynamics.perturbation.solve_lmde_perturbation` numerically computes a desired
list of the :math:`\mathcal{D}_I(t)` or :math:`\mathcal{O}_I(t)`
using algorithms in [:footcite:`puzzuoli_sensitivity_2022`]. It may also be used to compute
Dyson-like integrals using the algorithm in [:footcite:`haas_engineering_2019`]. Results are
returned in a :class:`PerturbationResults` objects which is a data container with some
functionality for indexing and accessing specific perturbation terms. See the function
documentation for further details.

Add link to perturbative solvers here?


Perturbation module API
=======================

.. autosummary::
    :toctree: ../stubs/

    ArrayPolynomial
    solve_lmde_perturbation
    PerturbationResults

.. footbibliography::
"""

from .array_polynomial import ArrayPolynomial
from .solve_lmde_perturbation import solve_lmde_perturbation
from .perturbation_results import PerturbationResults
