"""Common interfaces for anomaly detectors.

All detectors follow a two-phase lifecycle:

1. ``fit(X)`` — learn "normal" behaviour from a reference window of samples.
2. ``predict(X)`` — score new samples and label them normal / anomalous.

Scores are always "the higher, the more anomalous".
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DetectionResult:
    """Outcome of anomaly detection over a batch of samples.

    Attributes:
        is_anomaly: Boolean array aligned with the input rows.
        scores: Per-row anomaly score (higher == more anomalous).
        n_anomalies: Number of flagged samples.
    """

    is_anomaly: np.ndarray
    scores: np.ndarray
    n_anomalies: int


class BaseDetector(ABC):
    """Interface shared by every anomaly detector."""

    @abstractmethod
    def fit(self, X: np.ndarray) -> "BaseDetector":
        """Learn normal behaviour from reference samples."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def predict(self, X: np.ndarray) -> DetectionResult:
        """Label each sample in ``X`` as normal or anomalous."""
        raise NotImplementedError  # pragma: no cover