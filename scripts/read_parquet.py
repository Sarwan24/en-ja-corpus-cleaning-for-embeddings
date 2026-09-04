import pandas as pd


# ============================================================
# PARQUET FILE PATH
# ============================================================

FILE_PATH = "data/test/shards/shard_00000.parquet"


# ============================================================
# READ PARQUET
# ============================================================

df = pd.read_parquet(FILE_PATH)


# ============================================================
# BASIC INFORMATION
# ============================================================

print("\n" + "=" * 100)
print("PARQUET DATA INSPECTION")
print("=" * 100)

print("\nTotal Rows:")
print(len(df))

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())


# ============================================================
# FIRST RECORDS
# ============================================================

print("\n" + "=" * 100)
print("FIRST 20 RECORDS")
print("=" * 100)

print(
    df.head(20).to_string(
        index=False
    )
)


# ============================================================
# RANDOM RECORDS
# ============================================================

print("\n" + "=" * 100)
print("RANDOM 20 RECORDS")
print("=" * 100)

print(
    df.sample(
        min(20, len(df))
    ).to_string(
        index=False
    )
)


# ============================================================
# COLUMN INFORMATION
# ============================================================

print("\n" + "=" * 100)
print("DATA INFO")
print("=" * 100)

df.info()