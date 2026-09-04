from src.data_loader import Dataloader
from src.inspection import DataInspector


FILE_PATH = "data/samples/raw/en_ja_30k_sample.csv"


loader = Dataloader(FILE_PATH)

df = loader.load_csv()



import pandas as pd

from src.inspection import DataInspector





# ============================================================
# 1. LOAD DATASET
# ============================================================

print("\n" + "#" * 100)
print("ENGLISH - JAPANESE CORPUS INSPECTION")
print("#" * 100)

df = pd.read_csv(
    FILE_PATH
)

print("\nDataset loaded successfully.")
print("Total Records:", len(df))


# ============================================================
# 2. SPLIT RANDOM / TARGETED
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


print(
    "Random Records   :",
    len(random_df)
)

print(
    "Targeted Records :",
    len(targeted_df)
)


# ============================================================
# 3. WHOLE DATASET INSPECTION
# ============================================================

print("\n\n" + "#" * 100)
print("PART A - COMPLETE SAMPLE INSPECTION")
print("#" * 100)

full_inspector = DataInspector(
    df
)

full_inspector.basic_info()
full_inspector.missing_values()
full_inspector.empty_records()
full_inspector.duplicate_records()
full_inspector.sample_type_summary()
full_inspector.targeted_category_summary()


# ============================================================
# 4. RANDOM SAMPLE INSPECTION
# ============================================================

print("\n\n" + "#" * 100)
print("PART B - RANDOM SAMPLE INSPECTION")
print("#" * 100)

print(
    "\nIMPORTANT:"
    "\nRandom sample is used to estimate"
    " the natural distribution of the full corpus."
)

random_inspector = DataInspector(
    random_df
)

random_inspector.missing_values()
random_inspector.empty_records()
random_inspector.duplicate_records()
random_inspector.length_statistics()
random_inspector.confidence_statistics()
random_inspector.language_ratio_statistics()
random_inspector.latin_prefix_statistics()
random_inspector.source_similarity_statistics()
random_inspector.token_overlap_statistics()
random_inspector.threshold_summary()


# ============================================================
# 5. TARGETED SAMPLE INSPECTION
# ============================================================

print("\n\n" + "#" * 100)
print("PART C - TARGETED SAMPLE INSPECTION")
print("#" * 100)

print(
    "\nIMPORTANT:"
    "\nTargeted records are intentionally suspicious."
    "\nTheir percentages do NOT represent the full 40M corpus."
)

targeted_inspector = DataInspector(
    targeted_df
)

targeted_inspector.missing_values()
targeted_inspector.empty_records()
targeted_inspector.duplicate_records()
targeted_inspector.emoji_statistics()
targeted_inspector.arabic_script_statistics()
targeted_inspector.symbol_statistics()
targeted_inspector.targeted_category_summary()
targeted_inspector.length_statistics()
targeted_inspector.confidence_statistics()
targeted_inspector.language_ratio_statistics()
targeted_inspector.latin_prefix_statistics()
targeted_inspector.source_similarity_statistics()
targeted_inspector.token_overlap_statistics()
targeted_inspector.threshold_summary()



# ============================================================
# 6. RANDOM VS TARGETED COMPARISON
# ============================================================

print("\n\n" + "#" * 100)
print("PART D - RANDOM VS TARGETED COMPARISON")
print("#" * 100)


comparison_columns = [
    "confidence_score",
    "latin_ratio",
    "japanese_ratio",
    "latin_prefix_chars",
    "source_prefix_similarity",
    "latin_token_overlap"
]


print(
    f"\n{'FEATURE':<32}"
    f"{'RANDOM MEAN':<18}"
    f"{'TARGETED MEAN'}"
)

print("-" * 75)


for column in comparison_columns:

    random_mean = (
        random_df[column]
        .mean()
    )

    targeted_mean = (
        targeted_df[column]
        .mean()
    )

    print(
        f"{column:<32}"
        f"{random_mean:<18.4f}"
        f"{targeted_mean:.4f}"
    )


# ============================================================
# 7. FINAL MESSAGE
# ============================================================

print("\n\n" + "#" * 100)
print("INSPECTION COMPLETED")
print("#" * 100)

print(
    "\nNext Step:"
    "\nRun validation separately on RANDOM and TARGETED data."
)