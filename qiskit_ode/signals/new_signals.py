# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
# pylint: disable=invalid-name

"""
Module for representation of model coefficients.
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Union, Optional

import numpy as np
from matplotlib import pyplot as plt

from qiskit import QiskitError
from qiskit_ode.dispatch import Array

class Signal:
    r"""General signal class representing a function of the form:

    .. math::
        Re[f(t)e^{i (2 \pi \nu t + \phi)}]
                = Re[f(t)]\cos(2 \pi \nu t + \phi) - Im[f(t)]\sin(2 \pi \nu t + \phi),

    where

    - :math:`f(t)` is the envelope function.
    - :math:`\nu` is the carrier frequency.
    - :math:`\phi` is the phase.

    The envelope function can be complex-valued, and the frequency and phase must be real.
    """

    def __init__(
        self,
        envelope: Union[Callable, complex, float, int],
        carrier_freq: float = 0.0,
        phase: float = 0.0,
        name: Optional[str] = None,
        vectorize_envelope: Optional[bool] = False,
    ):
        """
        Initializes a signal given by an envelope and a carrier.

        Args:
            envelope: Envelope function of the signal, must be vectorized.
            carrier_freq: Frequency of the carrier.
            phase: The phase of the carrier.
            name: Name of the signal.
            vectorize_envelope: Whether or not automatically vectorize the envelope function.
        """
        self.name = name

        if isinstance(envelope, (float, int)):
            envelope = Array(complex(envelope))

        if isinstance(envelope, Array):
            self._envelope = lambda t: envelope

        if isinstance(envelope, Callable):
            # to do: put jax version
            if vectorize_envelope:
                envelope = np.vectorize(envelope)

            self._envelope = envelope

        # initialize internally stored carrier/phase information
        self._carrier_freq = None
        self._phase = None
        self._carrier_arg = None
        self._phase_arg = None

        # set carrier and phase
        self.carrier_freq = carrier_freq
        self.phase = phase

    @property
    def carrier_freq(self) -> Array:
        return self._carrier_freq

    @carrier_freq.setter
    def carrier_freq(self, carrier_freq: float):
        self._carrier_freq = Array(carrier_freq)
        self._carrier_arg = 1j * 2 * np.pi * self._carrier_freq

    @property
    def phase(self) -> Array:
        return self._phase

    @phase.setter
    def phase(self, phase: float):
        self._phase = Array(phase)
        self._phase_arg = 1j * self._phase

    def envelope(self, t: Union[float, np.array, Array]) -> Union[complex, np.array, Array]:
        """Vectorized evaluation of the envelope at time t."""
        return self._envelope(t)

    def complex_value(self, t: Union[float, np.array, Array]) -> Union[complex, np.array, Array]:
        """Vectorized evaluation of the complex value at time t."""
        arg = self._carrier_arg * t + self._phase_arg
        return self.envelope(t) * np.exp(arg)

    def __call__(self, t: Union[float, np.array, Array]) -> Array:
        """Vectorized evaluation of the signal at time t."""
        arg = self._carrier_arg * t + self._phase_arg
        return np.real(self.envelope(t) * np.exp(arg))

    def __str__(self) -> str:
        """Return string representation."""
        if self.name is not None:
            return str(self.name)

        return 'Signal(carrier_freq={freq}, phase={phase})'.format(freq=str(self.carrier_freq), phase=str(self.phase))

    def conjugate(self):
        """Return a new signal obtained via complex conjugation of the envelope and phase."""
        def conj_env(t):
            return np.conjugate(self.envelope(t))

        return Signal(conj_env, self.carrier_freq, -self.phase)

    def plot(self, t0: float, tf: float, n: int, axis=None):
        """Plot the signal over an interval.

        Args:
            t0: Initial time.
            tf: Final time.
            n: Number of points to sample in interval.
            axis: The axis to use for plotting.
        """
        t_vals = np.linspace(t0, tf, n)
        sig_vals = self(t_vals)

        if axis:
            axis.plot(t_vals, sig_vals)
        else:
            plt.plot(t_vals, sig_vals)

    def plot_envelope(self, t0: float, tf: float, n: int, axis=None):
        """Plot the signal over an interval.

        Args:
            t0: Initial time.
            tf: Final time.
            n: Number of points to sample in interval.
            axis: The axis to use for plotting.
        """
        t_vals = np.linspace(t0, tf, n)
        env_vals = self.envelope(t_vals)

        if axis:
            axis.plot(t_vals, np.real(env_vals))
            axis.plot(t_vals, np.imag(env_vals))
        else:
            plt.plot(t_vals, np.real(env_vals))
            plt.plot(t_vals, np.imag(env_vals))

    def plot_complex_value(self, t0: float, tf: float, n: int, axis=None):
        """Plot the complex value over an interval.

        Args:
            t0: Initial time.
            tf: Final time.
            n: Number of points to sample in interval.
            axis: The axis to use for plotting.
        """
        t_vals = np.linspace(t0, tf, n)
        sig_vals = self.complex_value(t_vals)

        if axis:
            axis.plot(t_vals, np.real(sig_vals))
            axis.plot(t_vals, np.imag(sig_vals))
        else:
            plt.plot(t_vals, np.real(sig_vals))
            plt.plot(t_vals, np.imag(sig_vals))


class SignalSum(Signal):
    """Class representing a sum of ``Signal`` objects."""

    def __init__(self, *args, name: Optional[str] = None):
        """Initialize with a list of Signal objects through ``args``.

        Args:
            args: ``Signal`` subclass objects.
            name: Name of the sum.
        """
        self.name = name

        self.components = []
        for sig in args:
            if isinstance(sig, SignalSum):
                self.components += sig.components
            elif isinstance(sig, Signal):
                self.components.append(sig)
            else:
                raise QiskitError('Components of a SignalSum must be instances of a Signal subclass.')

        self._envelopes = [sig.envelope for sig in self.components]

        # initialize internally stored carrier/phase information
        self._carrier_freq = None
        self._phase = None
        self._carrier_arg = None
        self._phase_arg = None

        carrier_freqs = []
        for sig in self.components:
            carrier_freqs.append(sig.carrier_freq)

        phases = []
        for sig in self.components:
            phases.append(sig.phase)

        # set carrier and phase
        self.carrier_freq = carrier_freqs
        self.phase = phases

    def envelope(self, t: Union[float, np.array, Array]) -> Array:
        """Evaluate envelopes of each component. For vectorized operation,
        last axis indexes the envelope, and all proceeding axes are the
        same as the ``t`` arg.
        """
        # to do: jax version
        # not sure what the right way to do this is, here we actually need
        # to get it to use np/jnp
        return np.moveaxis(Array([env(t) for env in self._envelopes]), 0, -1)

    def complex_value(self, t: Union[float, np.array, Array]) -> Array:
        exp_phases = np.exp(np.expand_dims(Array(t), -1) * self._carrier_arg + self._phase_arg)
        return np.sum(self.envelope(t) * exp_phases, axis=-1)

    def __call__(self, t: Union[float, np.array, Array]) -> Array:
        return np.real(self.complex_value(t))

    def __len__(self):
        return len(self.components)

    def __getitem__(self, idx):
        return self.components[idx]

    def __str__(self):
        if self.name is not None:
            return str(self.name)

        if len(self) == 0:
            return 'SignalSum()'

        default_str = str(self[0])
        for sig in self.components[1:]:
            default_str += ' + {}'.format(str(sig))

        return default_str

    def simplify(self):
        """Merge terms with the same frequency.
        """
        new_sigs = []
        new_freqs = []
        new_phases = []

        for sig in self.components:
            freq = Array(sig.carrier_freq)
            # if the negative of the frequency is present, signals can be combined by
            # conjugating the envelope
            if Array(-freq) in new_freqs:
                idx = new_freqs.index(-freq)
                compatible_sig = new_sigs[idx]
                new_env = add_envelopes(compatible_sig, sig, conj2=True)
                new_sigs[idx] = Signal(new_env, carrier_freq=-freq)
                # phases absorbed into envelope
                new_phases[idx] = 0.
            # if frequency is already present, just add the envelopes
            elif freq in new_freqs:
                idx = new_freqs.index(freq)
                compatible_sig = new_sigs[idx]
                new_env = add_envelopes(compatible_sig, sig)
                new_sigs[idx] = Signal(new_env, carrier_freq=freq)
                # phases are absorbed in envelope
                new_phases[idx] = 0.
            else:
                new_sigs.append(sig)
                new_freqs.append(freq)
                new_phases.append(sig.phase)

        self.components = new_sigs
        self.carrier_freq = new_freqs
        self.phase = new_phases
        self._envelopes = [sig.envelope for sig in self.components]

    def merge(self) -> Signal:
        """Merge into a single ``Signal``. The output frequency is given by the
        average.
        """

        if len(self) == 0:
            return Constant(0.)
        elif len(self) == 1:
            return self.components[0]

        ave_freq = np.sum(self.carrier_freq) / len(self)
        shifted_arg = self._carrier_arg - (1j * 2 * np.pi * ave_freq)

        def merged_env(t):
            exp_phases = np.exp(np.expand_dims(Array(t), -1) * shifted_arg + self._phase_arg)
            return np.sum(self.envelope(t) * exp_phases, axis=-1)

        return Signal(envelope=merged_env, carrier_freq=ave_freq, name=str(self))


def add_envelopes(sig1: Signal, sig2: Signal, conj2: bool = False) -> Callable:
    """Utility function for adding the envelopes (including phases) of two :class:`Signal`s.

    Args:
        sig1: First :class:`Signal`.
        sig2: Second :class:`Signal`
        conj2: Whether or not to conjugate the second :class:`Signal`.

    Returns:
        Callable: Function attained by adding both envelopes (including phases).
    """

    if conj2:
        sig2 = sig2.conjugate()

    env1_shift = np.exp(1j * sig1.phase)
    env2_shift = np.exp(1j * sig2.phase)

    def new_env(t):
        return env1_shift * sig1.envelope(t) + env2_shift * sig2.envelope(t)

    return new_env
