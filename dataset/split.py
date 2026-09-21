"""Reproducible train / validation / test dataset splitting.

Works with pandas DataFrames, NumPy arrays, and any input supported by
:func:`sklearn.model_selection.train_test_split`.
"""

from dataclasses import dataclass
from typing import TypeVar

from sklearn.model_selection import train_test_split

T = TypeVar("T")


@dataclass(frozen=True)
class DatasetSplit:
    """The result of a train/validation/test split.

    ``y_*`` attributes are ``None`` when the input data had no targets.
    """

    X_train: T
    X_val: T
    X_test: T
    y_train: T | None = None
    y_val: T | None = None
    y_test: T | None = None


def _validate_sizes(train_size: float, val_size: float, test_size: float) -> None:
    """Ensure the split sizes are valid fractions that sum to one."""
    sizes = (train_size, val_size, test_size)
    if any(s <= 0 for s in sizes):
        raise ValueError("train_size, val_size, and test_size must all be positive")
    if not abs(train_size + val_size + test_size - 1.0) < 1e-9:
        raise ValueError(
            f"Split sizes must sum to 1.0, got "
            f"train={train_size}, val={val_size}, test={test_size}"
        )


def train_val_test_split(
    X: T,
    y: T | None = None,
    *,
    train_size: float = 0.7,
    val_size: float = 0.15,
    test_size: float = 0.15,
    random_state: int = 42,
    shuffle: bool = True,
    stratify=None,
) -> DatasetSplit:
    """Split data into train, validation, and test sets.

    Parameters mirror :func:`sklearn.model_selection.train_test_split`. The
    split is performed in two stages (train vs. remainder, then validation vs.
    test) so all three sets are disjoint and, when ``stratify`` is provided,
    preserve the class distribution.

    Args:
        X: Feature data (DataFrame, ndarray, or list).
        y: Optional target data aligned with ``X``.
        train_size: Fraction (or count) of the sample for training.
        val_size: Fraction (or count) of the sample for validation.
        test_size: Fraction (or count) of the sample for testing.
        random_state: Seed for reproducible shuffling.
        shuffle: Whether to shuffle before splitting.
        stratify: Labels used for stratified splitting (typically ``y``).

    Returns:
        A :class:`DatasetSplit` with aligned ``X_*`` and ``y_*`` members.
    """
    _validate_sizes(train_size, val_size, test_size)

    split_kwargs = {"random_state": random_state, "shuffle": shuffle}

    # First split: train vs. (validation + test).
    # Only train_size is passed so sklearn infers the remainder internally,
    # avoiding floating-point drift in the complement (e.g. 1.0 - 0.7).
    # `None` targets are handled explicitly: newer sklearn versions do
    # not accept None in train_test_split and would try to index it.
    if y is None:
        X_train, X_remainder = train_test_split(
            X, train_size=train_size, stratify=stratify, **split_kwargs
        )
        y_train = y_remainder = None
    else:
        X_train, X_remainder, y_train, y_remainder = train_test_split(
            X, y, train_size=train_size, stratify=stratify, **split_kwargs
        )

    # Second split: validation vs. test over the remainder.
    # Recompute the fraction so the remainder divides exactly as requested.
    remainder_share = val_size / (val_size + test_size)

    if y is None:
        X_val, X_test = train_test_split(
            X_remainder,
            train_size=remainder_share,
            random_state=random_state + 1,
            shuffle=shuffle,
        )
        y_val = y_test = None
    else:
        second_stratify = y_remainder if stratify is not None else None
        X_val, X_test, y_val, y_test = train_test_split(
            X_remainder,
            y_remainder,
            train_size=remainder_share,
            random_state=random_state + 1,
            shuffle=shuffle,
            stratify=second_stratify,
        )

    return DatasetSplit(
        X_train=X_train,
        X_val=X_val,
        X_test=X_test,
        y_train=y_train,
        y_val=y_val,
        y_test=y_test,
    )