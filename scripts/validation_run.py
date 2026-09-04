from pathlib import Path

from src.data_loader import Dataloader
from src.validator import PairValidator


FILE_PATH = (
    "data/samples/raw/en_ja_30k_sample.csv"
)

OUTPUT_PATH = (
    "reports/validation/"
    "validated_30k_sample.csv"
)


# ============================================================
# LOAD
# ============================================================

loader = Dataloader(
    FILE_PATH
)

df = loader.load_csv()


validator = PairValidator()


# ============================================================
# SPLIT RANDOM / TARGETED
# ============================================================

random_df = df[
    df["sample_type"]
    ==
    "RANDOM"
].copy()


targeted_df = df[
    df["sample_type"]
    ==
    "TARGETED"
].copy()


# ============================================================
# VALIDATE BOTH
# ============================================================

random_validated = (
    validator.validate_dataframe(
        random_df
    )
)


targeted_validated = (
    validator.validate_dataframe(
        targeted_df
    )
)


# ============================================================
# SUMMARY FUNCTION
# ============================================================

def show_summary(
    df,
    title
):

    print(
        "\n"
        + "=" * 100
    )

    print(title)

    print(
        "=" * 100
    )


    total = len(df)


    status_counts = (
        df[
            "validation_status"
        ]
        .value_counts()
    )


    for status in [
        "KEEP",
        "REVIEW",
        "REMOVE_CANDIDATE"
    ]:

        count = (
            status_counts.get(
                status,
                0
            )
        )

        percentage = (
            count
            /
            total
            *
            100
        )

        print(
            f"{status:<20}: "
            f"{count:<7} "
            f"({percentage:.2f}%)"
        )


    print(
        "\nTOP VALIDATION ISSUES"
    )

    issue_counts = (
        df[
            "validation_issues"
        ]
        .value_counts()
        .head(20)
    )

    print(
        issue_counts
    )


# ============================================================
# RANDOM SUMMARY
# ============================================================

show_summary(
    random_validated,
    "RANDOM SAMPLE VALIDATION"
)


# ============================================================
# TARGETED SUMMARY
# ============================================================

show_summary(
    targeted_validated,
    "TARGETED SAMPLE VALIDATION"
)


# ============================================================
# COMBINE
# ============================================================

import pandas as pd


validated_df = pd.concat(
    [
        random_validated,
        targeted_validated
    ],
    ignore_index=True
)


# ============================================================
# SAVE
# ============================================================

output_file = Path(
    OUTPUT_PATH
)

output_file.parent.mkdir(
    parents=True,
    exist_ok=True
)


validated_df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)


print(
    "\nValidation report saved:"
)

print(
    OUTPUT_PATH
)