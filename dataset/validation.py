"""Dataset quality and leakage validation (STEP 8).

Leakage rules (documented, multi-service aware):

- No exact-duplicate rows may appear in more than one split.
- No ``scenario_id`` may appear in more than one split: a controlled
  experiment window must be wholly contained in a single split, otherwise
  the test set would preview training scenarios.
- Identical *timestamps* across splits are legitimate when different
  services (or different metrics) produce simultaneous observations — only
  identical full rows are rejected.
- Future leakage is covered by the two rules above plus chronological
  construction (splits are contiguous oldest→latest ranges).
"""

import pandas as pd


def find_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return all rows that occur more than once (kept, not dropped)."""
    mask = df.duplicated(keep=False)
    return df[mask]


def check_no_cross_split_duplicates(
    train: pd.DataFrame, validation: pd.DataFrame, test: pd.DataFrame
) -> list[str]:
    """Fail if any exact-duplicate row spans two splits."""
    issues: list[str] = []
    combined = pd.concat(
        [
            train.assign(_split="train"),
            validation.assign(_split="validation"),
            test.assign(_split="test"),
        ],
        ignore_index=True,
    )
    data_columns = [c for c in combined.columns if c != "_split"]
    for _, group in combined.groupby(
        [combined[c].astype(str) for c in data_columns], dropna=False
    ):
        splits = set(group["_split"])
        if len(splits) > 1:
            issues.append(
                f"duplicate row across splits {sorted(splits)}: "
                f"{group.iloc[0][data_columns].to_dict()}"
            )
    return issues


def check_scenario_containment(
    splits: dict[str, pd.DataFrame],
) -> list[str]:
    """Fail if one scenario_id lands in more than one split."""
    locations: dict[str, set[str]] = {}
    for name, frame in splits.items():
        if "scenario_id" not in frame.columns:
            continue
        for scenario_id in frame["scenario_id"].dropna().unique():
            locations.setdefault(str(scenario_id), set()).add(name)
    return [
        f"scenario '{scenario_id}' spans splits {sorted(names)}"
        for scenario_id, names in locations.items()
        if len(names) > 1
    ]


def check_row_accounting(
    total: int, train: pd.DataFrame, validation: pd.DataFrame, test: pd.DataFrame
) -> list[str]:
    """Fail unless train + validation + test equals the total."""
    if len(train) + len(validation) + len(test) != total:
        return [
            f"row accounting mismatch: {len(train)} + {len(validation)} + "
            f"{len(test)} != {total}"
        ]
    return []


def missing_value_report(df: pd.DataFrame) -> dict[str, int]:
    """Count missing values per column (reported, never zero-filled here)."""
    return {column: int(df[column].isna().sum()) for column in df.columns}
