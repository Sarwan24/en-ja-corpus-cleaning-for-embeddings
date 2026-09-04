from pathlib import Path
import os


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# INPUT FILES
# ============================================================

EN_FILE = (
    PROJECT_ROOT
    / "data"
    / "full"
    / "raw"
    / "NLLB.en-ja.en"
)

JA_FILE = (
    PROJECT_ROOT
    / "data"
    / "full"
    / "raw"
    / "NLLB.en-ja.ja"
)


# ============================================================
# TEST DATA
# ============================================================

TEST_EN_FILE = (
    PROJECT_ROOT
    / "data"
    / "test"
    / "raw"
    / "test.en"
)

TEST_JA_FILE = (
    PROJECT_ROOT
    / "data"
    / "test"
    / "raw"
    / "test.ja"
)

TEST_SHARD_DIR = (
    PROJECT_ROOT
    / "data"
    / "test"
    / "shards"
)



# ============================================================
# OUTPUT DIRECTORIES
# ============================================================

SHARD_DIR = (
    PROJECT_ROOT
    / "data"
    / "full"
    / "shards"
)

FINAL_DIR = (
    PROJECT_ROOT
    / "data"
    / "full"
    / "final"
)

TEMP_DIR = (
    PROJECT_ROOT
    / "data"
    / "temp"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "full_run"
)


# ============================================================
# PIPELINE SETTINGS
# ============================================================

# Number of cleaned records in one Parquet shard
SHARD_SIZE = 500_000

# Future multiprocessing/chunk processing
CHUNK_SIZE = 50_000

# Leave one CPU core free
NUM_WORKERS = max(
    1,
    (os.cpu_count() or 2) - 1
)
# python -m scripts.full_cleaning_pipeline --full --workers 4 --chunk-size 50000

# ============================================================
# PARQUET SETTINGS
# ============================================================

PARQUET_COMPRESSION = "zstd"


# ============================================================
# CLEANING THRESHOLDS
# ============================================================

MIN_JAPANESE_CHARS = 3

LATIN_MIN_CHARS = 120

DIGIT_MIN_COUNT = 20

DIGIT_RATIO_THRESHOLD = 0.20

NUMBER_TOKEN_LIMIT = 12

SYMBOL_MIN_COUNT = 12

SYMBOL_RATIO_THRESHOLD = 0.35