from pathlib import Path

from src.data_loader import Dataloader
from src.cleaner import DataCleaner


# ============================================================
# FILE PATHS
# ============================================================

FILE_PATH = (
    "data/samples/raw/en_ja_30k_sample.csv"
)

FULL_REPORT_PATH = (
    "reports/cleaning/"
    "cleaning_report_30k.csv"
)

FINAL_OUTPUT_PATH = (
    "data/samples/processed/cleaned_en_ja_30k.csv"
)

# ============================================================
# HELPER: SHOW RECORDS BY STATUS
# ============================================================

def show_status_records(
    df,
    status_name,
    limit=10
):

    rows = df[
        df["cleaning_status"]
        ==
        status_name
    ]

    print("\n" + "=" * 100)
    print(f"{status_name} RECORDS")
    print("=" * 100)

    print(
        "Total Records:",
        len(rows)
    )

    if len(rows) == 0:

        print(
            "No records found."
        )

        return


    print(
        f"Showing first "
        f"{min(limit, len(rows))} records"
    )


    for _, row in (
        rows
        .head(limit)
        .iterrows()
    ):

        print("\n" + "-" * 100)

        print(
            "ID:",
            row["id"]
        )

        print(
            "\nSAMPLE TYPE:"
        )
        print(
            row["sample_type"]
        )

        print(
            "\nSAMPLE CATEGORY:"
        )
        print(
            row["sample_category"]
        )

        print(
            "\nORIGINAL ENGLISH:"
        )
        print(
            row["english"]
        )

        print(
            "\nORIGINAL JAPANESE:"
        )
        print(
            row["japanese"]
        )

        print(
            "\nCLEAN ENGLISH:"
        )
        print(
            row["clean_english"]
        )

        print(
            "\nCLEAN JAPANESE:"
        )
        print(
            row["clean_japanese"]
        )

        print(
            "\nCONFIDENCE SCORE:"
        )
        print(
            row["confidence_score"]
        )

        print(
            "\nCLEANING STATUS:"
        )
        print(
            row["cleaning_status"]
        )

        print(
            "\nCLEANING REASON:"
        )
        print(
            row["cleaning_reason"]
        )


# ============================================================
# HELPER: STATUS SUMMARY
# ============================================================

def show_status_summary(
    df,
    title
):

    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

    total = len(df)

    status_counts = (
        df[
            "cleaning_status"
        ]
        .value_counts()
    )

    for status in [
        "KEEP",
        "CLEAN",
        "REVIEW",
        "REMOVE"
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
            if total
            else 0
        )

        print(
            f"{status:<10}: "
            f"{count:<7} "
            f"({percentage:.2f}%)"
        )


# ============================================================
# HELPER: CLEANING REASON SUMMARY
# ============================================================

def show_reason_summary(df):

    print("\n" + "=" * 100)
    print("CLEANING REASON SUMMARY")
    print("=" * 100)

    reason_counts = (
        df[
            df[
                "cleaning_reason"
            ]
            !=
            ""
        ][
            "cleaning_reason"
        ]
        .value_counts()
    )

    if len(reason_counts) == 0:

        print(
            "No cleaning actions detected."
        )

        return


    total = len(df)

    for reason, count in (
        reason_counts.items()
    ):

        percentage = (
            count
            /
            total
            *
            100
        )

        print(
            f"{reason:<65}"
            f"{count:<7}"
            f"({percentage:.2f}%)"
        )


# ============================================================
# 1. LOAD DATASET
# ============================================================

print(
    "\n" + "#" * 100
)

print(
    "ENGLISH - JAPANESE CORPUS CLEANING"
)

print(
    "#" * 100
)


loader = Dataloader(
    FILE_PATH
)

df = loader.load_csv()


print(
    "\nTotal Input Records:",
    len(df)
)


# ============================================================
# 2. CREATE CLEANER
# ============================================================

cleaner = DataCleaner()


# ============================================================
# 3. RUN CLEANING
# ============================================================

print(
    "\nRunning cleaning..."
)

cleaned_df = (
    cleaner.clean_dataframe(
        df
    )
)

print(
    "Cleaning completed."
)


# ============================================================
# 4. POST-CLEAN QUALITY CHECK
# ============================================================

cleaner.post_clean_summary(
    cleaned_df
)


# ============================================================
# 5. COMPLETE SAMPLE SUMMARY
# ============================================================

show_status_summary(
    cleaned_df,
    "COMPLETE SAMPLE CLEANING SUMMARY"
)


# ============================================================
# 6. RANDOM SAMPLE SUMMARY
# ============================================================

random_cleaned = (
    cleaned_df[
        cleaned_df[
            "sample_type"
        ]
        ==
        "RANDOM"
    ]
    .copy()
)


show_status_summary(
    random_cleaned,
    "RANDOM SAMPLE CLEANING SUMMARY"
)


# ============================================================
# 7. TARGETED SAMPLE SUMMARY
# ============================================================

targeted_cleaned = (
    cleaned_df[
        cleaned_df[
            "sample_type"
        ]
        ==
        "TARGETED"
    ]
    .copy()
)


show_status_summary(
    targeted_cleaned,
    "TARGETED SAMPLE CLEANING SUMMARY"
)


# ============================================================
# 8. CLEANING REASON SUMMARY
# ============================================================

show_reason_summary(
    cleaned_df
)


# ============================================================
# 9. SHOW REMOVE RECORDS
# ============================================================

show_status_records(
    cleaned_df,
    "REMOVE",
    limit=20
)


# ============================================================
# 10. SHOW CLEAN RECORDS
# ============================================================

show_status_records(
    cleaned_df,
    "CLEAN",
    limit=20
)


# ============================================================
# 11. SHOW REVIEW RECORDS
# ============================================================

show_status_records(
    cleaned_df,
    "REVIEW",
    limit=10
)


# ============================================================
# 12. CREATE REPORT DIRECTORY
# ============================================================

report_path = Path(
    FULL_REPORT_PATH
)

report_path.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 13. SAVE FULL AUDIT REPORT
# ============================================================

cleaned_df.to_csv(
    FULL_REPORT_PATH,
    index=False,
    encoding="utf-8-sig"
)


print("\n" + "=" * 100)
print("FULL CLEANING REPORT SAVED")
print("=" * 100)

print(
    FULL_REPORT_PATH
)


# ============================================================
# 14. KEEP ONLY USABLE ROWS
# ============================================================

usable_df = (
    cleaned_df[
        cleaned_df[
            "cleaning_status"
        ]
        !=
        "REMOVE"
    ]
    .copy()
)


removed_rows = (
    len(cleaned_df)
    -
    len(usable_df)
)


# ============================================================
# 15. REMOVE DUPLICATE EN-JA PAIRS
# ============================================================

usable_df, duplicate_removed = (
    cleaner.remove_duplicate_pairs(
        usable_df
    )
)


# ============================================================
# 16. CREATE OUTPUT DIRECTORY
# ============================================================

output_path = Path(
    FINAL_OUTPUT_PATH
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 17. FINAL TRAINING DATASET
# ============================================================

final_df = (
    usable_df[
        [
            "clean_english",
            "clean_japanese",
            "confidence_score"
        ]
    ]
    .rename(
        columns={
            "clean_english":
                "english",

            "clean_japanese":
                "japanese"
        }
    )
)


# ============================================================
# 18. SAVE FINAL CLEANED DATASET
# ============================================================

final_df.to_csv(
    FINAL_OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# 19. FINAL SUMMARY
# ============================================================

print(
    "\n" + "#" * 100
)

print(
    "FINAL CLEANING SUMMARY"
)

print(
    "#" * 100
)


print(
    "Original Records        :",
    len(cleaned_df)
)

print(
    "Rows Removed            :",
    removed_rows
)

print(
    "Duplicate Pairs Removed :",
    duplicate_removed
)

print(
    "Final Records           :",
    len(final_df)
)


preserved_percentage = (
    len(final_df)
    /
    len(cleaned_df)
    *
    100
)


print(
    f"Data Preserved          : "
    f"{preserved_percentage:.2f}%"
)


print(
    "\nFinal Training Dataset:"
)

print(
    FINAL_OUTPUT_PATH
)


print(
    "\nFull Audit Report:"
)

print(
    FULL_REPORT_PATH
)


print(
    "\n" + "#" * 100
)

print(
    "CLEANING COMPLETED"
)

print(
    "#" * 100
)