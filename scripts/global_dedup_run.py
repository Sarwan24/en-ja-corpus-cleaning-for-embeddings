import argparse

from src.deduplicator import GlobalDeduplicator

from config.config import (
    TEST_SHARD_DIR,
    SHARD_DIR,
    FINAL_DIR,
    TEMP_DIR,
    PROJECT_ROOT
)


def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Global EN-JA pair deduplication"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run deduplication on test shards"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Run deduplication on full corpus shards"
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    if args.test and args.full:
        raise ValueError(
            "Use either --test or --full, not both."
        )


    # -----------------------------------------------------
    # SELECT MODE
    # -----------------------------------------------------

    if args.full:

        mode = "FULL"

        shard_dir = SHARD_DIR

        final_dir = FINAL_DIR

        temp_dir = (
            TEMP_DIR / "full_dedup"
        )

    else:

        # Default = TEST for safety
        mode = "TEST"

        shard_dir = TEST_SHARD_DIR

        final_dir = (
            PROJECT_ROOT
            / "data"
            / "test"
            / "final"
        )

        temp_dir = (
            PROJECT_ROOT
            / "data"
            / "test"
            / "temp"
        )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "GLOBAL DEDUPLICATION"
    )

    print(
        "=" * 80
    )

    print(
        "Mode       :",
        mode
    )

    print(
        "Input      :",
        shard_dir
    )

    print(
        "Output     :",
        final_dir
    )

    print(
        "Temp       :",
        temp_dir
    )

    print(
        "=" * 80
    )


    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    parquet_files = list(
        shard_dir.glob(
            "*.parquet"
        )
    )

    if not parquet_files:

        raise FileNotFoundError(
            f"No Parquet shards found in: {shard_dir}"
        )


    print(
        "Parquet shards found:",
        len(parquet_files)
    )


    # -----------------------------------------------------
    # DEDUPLICATION
    # -----------------------------------------------------

    deduplicator = GlobalDeduplicator(
        shard_dir=shard_dir,
        final_dir=final_dir,
        temp_dir=temp_dir
    )


    try:

        result = (
            deduplicator.deduplicate()
        )

        print(
            "\nDeduplication completed successfully."
        )

        print(
            "Input Records      :",
            f"{result['total_records']:,}"
        )

        print(
            "Unique Records     :",
            f"{result['unique_records']:,}"
        )

        print(
            "Duplicates Removed :",
            f"{result['duplicates_removed']:,}"
        )

        print(
            "Output File        :",
            result["output_file"]
        )

    finally:

        deduplicator.close()


if __name__ == "__main__":
    main()