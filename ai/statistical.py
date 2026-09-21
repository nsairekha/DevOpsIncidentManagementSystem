"""Baseline-driven statistical anomaly detectors.

These detectors fit compact statistics ("baselines") on a reference window and
flag samples that deviate beyond fixed thresholds. They complement the
:mod:`dataset.baseline` module: baselines describe normal behaviour, while the
detectors here turn that description into anomaly labels.
"""

import numpy as np

from ai.base import BaseDetector, DetectionResult


class ZScoreDetector(BaseDetector):
    """Flag samples whose z-score exceeds a threshold on any feature.

    A sample is anomalous when :math:`|x - \\mu| / \\sigma > threshold` for at
    least one feature. Features with zero variance are treated as constant and
    never trigger an anomaly (their z-score is 0).
    """

    def __init__(self, threshold: float = 3.0) -> None:
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.threshold = threshold
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "ZScoreDetector":
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        return self

    def predict(self, X: np.ndarray) -> DetectionResult:
        if self.mean_ is None or self.std_ is None:
            raise RuntimeError("detector must be fitted before predict()")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if X.shape[1] != self.mean_.shape[0]:
            raise ValueError(
                f"feature mismatch: fitted on {self.mean_.shape[0]} features, "
                f"got {X.shape[1]}"
            )

        std_safe = np.where(self.std_ == 0.0, 1.0, self.std_)
        z = np.abs((X - self.mean_) / std_safe)

        scores = z.max(axis=1)
        is_anomaly = scores > self.threshold
        return DetectionResult(
            is_anomaly=is_anomaly,
            scores=np.asarray(scores, dtype=float),
            n_anomalies=int(is_anomaly.sum()),
        )


class IQRDetector(BaseDetector):
    """Flag samples outside [Q1 - k*IQR, Q3 + k*IQR] on any feature."""

    def __init__(self, k: float = 1.5) -> None:
        if k <= 0:
            raise ValueError("k must be positive")
        self.k = k
        self.lower_: np.ndarray | None = None
        self.upper_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "IQRDetector":
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        q1 = np.percentile(X, 25, axis=0)
        q3 = np.percentile(X, 75, axis=0)
        iqr = q3 - q1
        # Constant features have zero IQR; keep their bounds equal so no value
        # is flagged purely because the feature never varies.
        self.lower_ = q1 - self.k * iqr
        self.upper_ = q3 + self.k * iqr
        return self

    def predict(self, X: np.ndarray) -> DetectionResult:
        if self.lower_ is None or self.upper_ is None:
            raise RuntimeError("detector must be fitted before predict()")
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        if X.shape[1] != self.lower_.shape[0]:
            raise ValueError(
                f"feature mismatch: fitted on {self.lower_.shape[0]} features, "
                f"got {X.shape[1]}"
            )

        outside_low = X < self.lower_
        outside_high = X > self.upper_
        is_anomaly = (outside_low | outside_high).any(axis=1)

        # Score: largest relative excursion outside the IQR fence (0 if inside).
        deviation = np.maximum(self.lower_ - X, 0.0) + np.maximum(X - self.upper_, 0.0)
        span = np.maximum(self.upper_ - self.lower_, 1e-9)
        scores = deviation / span
        scores = scores.max(axis=1) if scores.ndim > 1 else scores

        return DetectionResult(
            is_anomaly=is_anomaly,
            scores=np.asarray(scores, dtype=float),
            n_anomalies=int(is_anomaly.sum()),
        )