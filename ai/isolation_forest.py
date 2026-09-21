"""Machine-learning anomaly detection with scikit-learn Isolation Forest.

Isolation Forest isolates anomalies instead of profiling normal points, which
makes it effective for multivariate telemetry where no baseline distribution
is assumed.
"""

import numpy as np
from sklearn.ensemble import IsolationForest

from ai.base import BaseDetector, DetectionResult


class IsolationForestDetector(BaseDetector):
    """Anomaly detector backed by :class:`sklearn.ensemble.IsolationForest`.

    Args:
        contamination: Expected proportion of anomalies in the fitted data.
        random_state: Seed for reproducible results.
        kwargs: Extra parameters forwarded to :class:`IsolationForest`.
    """

    def __init__(
        self,
        contamination: float = 0.1,
        random_state: int = 42,
        **kwargs,
    ) -> None:
        if not 0.0 < contamination <= 0.5:
            raise ValueError("contamination must be in (0, 0.5]")
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            **kwargs,
        )

    def fit(self, X: np.ndarray) -> "IsolationForestDetector":
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        self.model.fit(X)
        return self

    def predict(self, X: np.ndarray) -> DetectionResult:
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        # sklearn: decision_function returns higher values for normal samples;
        # negate so "higher == more anomalous" consistent with the rest.
        scores = -self.model.decision_function(X)
        is_anomaly = self.model.predict(X) == -1

        return DetectionResult(
            is_anomaly=is_anomaly,
            scores=np.asarray(scores, dtype=float),
            n_anomalies=int(is_anomaly.sum()),
        )