"""Tests for the Isolation Forest anomaly detector."""

import numpy as np
import pytest

from ai import IsolationForestDetector


def _make_blobs_with_outliers(
    n_normal: int = 200, n_outliers: int = 10, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic 2-D data: a tight normal cluster plus far-away outliers."""
    rng = np.random.default_rng(seed)
    normal = rng.normal(0.0, 0.5, size=(n_normal, 2))
    outliers = rng.normal(50.0, 0.5, size=(n_outliers, 2))
    X = np.vstack([normal, outliers])
    labels = np.zeros(len(X), dtype=bool)
    labels[n_normal:] = True
    return X, labels


def test_isolation_forest_flags_extreme_outliers() -> None:
    """Far outliers are labelled anomalous, and flagged as anomalies."""
    X, true_labels = _make_blobs_with_outliers()
    detector = IsolationForestDetector(contamination=0.1, random_state=0).fit(X)

    result = detector.predict(X)

    # Every constructed outlier must be detected.
    assert bool(result.is_anomaly[true_labels].all())
    # With contamination=0.1 the flagged set stays small.
    assert result.n_anomalies <= 30
    # Outliers receive higher (more anomalous) scores on average.
    assert result.scores[true_labels].mean() > result.scores[~true_labels].mean()


def test_isolation_forest_handles_1d_input() -> None:
    """Flat arrays are reshaped to column vectors."""
    normal = np.random.default_rng(1).normal(0.0, 1.0, size=50)
    X = np.concatenate([normal, [10.0, 12.0]])
    detector = IsolationForestDetector(contamination=0.1, random_state=1).fit(X)

    result = detector.predict(X)

    assert result.is_anomaly[-2:].sum() == 2
    assert result.n_anomalies <= 10


def test_isolation_forest_is_reproducible() -> None:
    """The same random state yields identical labels."""
    X, _ = _make_blobs_with_outliers()
    a = IsolationForestDetector(random_state=3).fit(X)
    b = IsolationForestDetector(random_state=3).fit(X)

    np.testing.assert_array_equal(a.predict(X).scores, b.predict(X).scores)


def test_isolation_forest_requires_fit() -> None:
    with pytest.raises(AttributeError):
        IsolationForestDetector().predict(np.array([[1.0, 2.0]]))


def test_isolation_forest_rejects_bad_contamination() -> None:
    with pytest.raises(ValueError, match="contamination"):
        IsolationForestDetector(contamination=0.0)
    with pytest.raises(ValueError, match="contamination"):
        IsolationForestDetector(contamination=0.6)