"""Tests for reproducible train/validation/test splitting."""

import numpy as np
import pandas as pd
import pytest

from dataset import train_val_test_split


def test_pandas_split_sizes_and_disjointness() -> None:
    """DataFrame inputs split into the requested proportions with no overlap."""
    df = pd.DataFrame({"a": np.arange(100), "b": np.arange(100) * 2})
    split = train_val_test_split(df)

    assert len(split.X_train) == 70
    assert len(split.X_val) == 15
    assert len(split.X_test) == 15

    train_idx = set(split.X_train.index)
    val_idx = set(split.X_val.index)
    test_idx = set(split.X_test.index)

    assert not (train_idx & val_idx)
    assert not (train_idx & test_idx)
    assert not (val_idx & test_idx)
    assert train_idx | val_idx | test_idx == set(df.index)

    # Target members exist and are aligned (same row counts).
    assert split.y_train is None
    assert split.y_val is None
    assert split.y_test is None


def test_ndarray_split_with_targets() -> None:
    """ndarray inputs with y split correctly and preserve shapes."""
    X = np.arange(200).reshape(100, 2)
    y = np.arange(100)
    split = train_val_test_split(X, y)

    assert split.X_train.shape == (70, 2)
    assert split.X_val.shape == (15, 2)
    assert split.X_test.shape == (15, 2)
    assert split.y_train is not None and len(split.y_train) == 70
    assert split.y_val is not None and len(split.y_val) == 15
    assert split.y_test is not None and len(split.y_test) == 15


def test_split_is_reproducible() -> None:
    """The same random_state yields the identical split."""
    X = np.arange(100).reshape(50, 2)
    first = train_val_test_split(X, random_state=7)
    second = train_val_test_split(X, random_state=7)

    np.testing.assert_array_equal(first.X_train, second.X_train)
    np.testing.assert_array_equal(first.X_val, second.X_val)
    np.testing.assert_array_equal(first.X_test, second.X_test)


def test_stratified_split_preserves_class_proportions() -> None:
    """Stratified splitting keeps imbalanced class shares in every subset."""
    y = np.array([0] * 20 + [1] * 80)
    split = train_val_test_split(y, y=y, stratify=y, train_size=0.7)

    train_counts = np.bincount(split.y_train)
    val_counts = np.bincount(split.y_val)
    test_counts = np.bincount(split.y_test)

    assert train_counts.tolist() == [14, 56]  # 70% of each class
    assert val_counts.tolist() == [3, 12]     # 15% of each class
    assert test_counts.tolist() == [3, 12]    # 15% of each class


def test_invalid_fraction_combinations_raise() -> None:
    """Sizes that do not sum to one are rejected."""
    with pytest.raises(ValueError, match="must sum to 1.0"):
        train_val_test_split(np.arange(10), train_size=0.5, val_size=0.2, test_size=0.2)


def test_non_positive_sizes_raise() -> None:
    """Non-positive sizes are rejected."""
    with pytest.raises(ValueError, match="all be positive"):
        train_val_test_split(np.arange(10), train_size=0.0, val_size=0.5, test_size=0.5)