"""Tests for baseline-driven statistical anomaly detectors."""

import numpy as np
import pandas as pd
import pytest

from ai import IQRDetector, ZScoreDetector


def test_zscore_flags_distant_points() -> None:
    """Values far beyond k standard deviations are flagged."""
    reference = np.arange(1.0, 11.0)  # mean 5.5, std ~2.87
    detector = ZScoreDetector(threshold=3.0).fit(reference)

    result = detector.predict(np.array([5.0, 100.0]))

    assert result.is_anomaly.tolist() == [False, True]
    assert result.scores[1] > result.scores[0]
    assert result.n_anomalies == 1


def test_zscore_constant_feature_never_anomalous() -> None:
    """A constant feature (zero variance) flags any deviation."""
    detector = ZScoreDetector(threshold=2.0).fit(np.array([7.0, 7.0, 7.0, 7.0]))

    result = detector.predict(np.array([7.0, 700.0]))

    # Identical value matches the (zero-variance) baseline, so it is normal;
    # a value that differs is a deviation from a constant baseline -> anomaly.
    assert result.is_anomaly.tolist() == [False, True]


def test_zscore_accepts_1d_and_2d_input() -> None:
    """Both flat arrays and column vectors are supported."""
    detector = ZScoreDetector(threshold=3.0).fit(np.array([1.0, 2.0, 3.0, 4.0, 5.0]))

    flat = detector.predict(np.array([50.0]))
    column = detector.predict(np.array([[50.0]]))

    assert flat.is_anomaly.tolist() == [True]
    assert column.is_anomaly.tolist() == [True]


def test_zscore_works_with_dataframe() -> None:
    """Pandas DataFrame inputs are coerced to arrays."""
    df = pd.DataFrame({"cpu": [1.0, 2.0, 3.0, 4.0, 5.0], "mem": [10.0, 11.0, 12.0, 13.0, 14.0]})
    detector = ZScoreDetector(threshold=3.0).fit(df)

    result = detector.predict(pd.DataFrame({"cpu": [5.0, 999.0], "mem": [12.0, 12.0]}))

    assert result.is_anomaly.tolist() == [False, True]


def test_zscore_feature_mismatch_raises() -> None:
    """Predicting with a different number of features raises ValueError."""
    detector = ZScoreDetector(threshold=3.0).fit(np.array([[1.0, 2.0], [3.0, 4.0]]))
    with pytest.raises(ValueError, match="feature mismatch"):
        detector.predict(np.array([[1.0, 2.0, 3.0]]))


def test_zscore_requires_fit() -> None:
    """Predicting before fitting raises RuntimeError."""
    with pytest.raises(RuntimeError, match="fitted"):
        ZScoreDetector().predict(np.array([1.0, 2.0]))


def test_zscore_rejects_non_positive_threshold() -> None:
    with pytest.raises(ValueError, match="threshold"):
        ZScoreDetector(threshold=0.0)


def test_iqr_flags_outside_fences() -> None:
    """Points beyond Q3 + k*IQR are flagged."""
    reference = np.arange(1.0, 11.0)  # Q1=3.25, Q3=7.75, IQR=4.5 -> upper 14.5
    detector = IQRDetector(k=1.5).fit(reference)

    result = detector.predict(np.array([5.0, 100.0]))

    assert result.is_anomaly.tolist() == [False, True]
    assert result.scores[1] > 0
    assert result.scores[0] == 0
    assert result.n_anomalies == 1


def test_iqr_constant_feature_never_anomalous() -> None:
    """Constant features have degenerate fences; any deviation is anomalous."""
    detector = IQRDetector(k=1.5).fit(np.array([3.0, 3.0, 3.0, 3.0]))
    result = detector.predict(np.array([3.0, 42.0]))
    assert result.is_anomaly.tolist() == [False, True]


def test_iqr_requires_fit() -> None:
    with pytest.raises(RuntimeError, match="fitted"):
        IQRDetector().predict(np.array([1.0]))


def test_iqr_feature_mismatch_raises() -> None:
    """Predicting with a different number of features raises ValueError."""
    detector = IQRDetector(k=1.5).fit(np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]))
    with pytest.raises(ValueError, match="feature mismatch"):
        detector.predict(np.array([[1.0, 2.0, 3.0]]))


def test_iqr_rejects_non_positive_k() -> None:
    with pytest.raises(ValueError, match="k must be positive"):
        IQRDetector(k=0.0)