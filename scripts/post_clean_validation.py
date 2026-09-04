import argparse
from pathlib import Path

import duckdb

from config.config import (
    PROJECT_ROOT,
    FINAL_DIR
)


def get_final_file(test_mode):

    if test_mode:
        return (
            PROJECT_ROOT
            / "data"
            / "test"
            / "final"
            / "deduplicated_en_ja.parquet"
        )

    return (
        FINAL_DIR
        / "deduplicated_en_ja.parquet"
    )


def get_report_dir(test_mode):

    if test_mode:
        report_dir = (
            PROJECT_ROOT
            / "reports"
            / "test_run"
        )

    else:
        report_dir = (
            PROJECT_ROOT
            / "reports"
            / "full_run"
        )

    report_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return report_dir


def validate_final_dataset(
    input_file,
    report_dir
):

    if not input_file.exists():

        raise FileNotFoundError(
            f"Final Parquet file not found: {input_file}"
        )


    print(
        "\n"
        + "=" * 80
    )

    print(
        "POST-CLEAN VALIDATION STARTED"
    )

    print(
        "=" * 80
    )

    print(
        "Input File :",
        input_file
    )


    con = duckdb.connect()


    try:

        parquet_path = (
            input_file.as_posix()
        )


        # =====================================================
        # TOTAL RECORDS
        # =====================================================

        total_records = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{parquet_path}'
            )
            """
        ).fetchone()[0]


        # =====================================================
        # EMPTY / NULL ENGLISH
        # =====================================================

        empty_english = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{parquet_path}'
            )
            WHERE
                english IS NULL
                OR TRIM(english) = ''
            """
        ).fetchone()[0]


        # =====================================================
        # EMPTY / NULL JAPANESE
        # =====================================================

        empty_japanese = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{parquet_path}'
            )
            WHERE
                japanese IS NULL
                OR TRIM(japanese) = ''
            """
        ).fetchone()[0]


        # =====================================================
        # JAPANESE SCRIPT CHECK
        #
        # Hiragana
        # Katakana
        # Kanji
        # =====================================================

        no_japanese_script = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{parquet_path}'
            )
            WHERE NOT regexp_matches(
                japanese,
                '[ぁ-ヿ㐀-鿿]'
            )
            """
        ).fetchone()[0]


        # =====================================================
        # FOREIGN SCRIPT CHECK
        #
        # Arabic
        # Cyrillic
        # Hebrew
        # Korean
        # =====================================================

        foreign_script = con.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{parquet_path}'
            )
            WHERE regexp_matches(
                japanese,
                '[؀-ࣿЀ-ӿ֐-׿가-힣]'
            )
            """
        ).fetchone()[0]


        # =====================================================
        # EXACT EN-JA DUPLICATE PAIRS
        # =====================================================

        unique_records = con.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    english,
                    japanese
                FROM read_parquet(
                    '{parquet_path}'
                )
            )
            """
        ).fetchone()[0]


        duplicate_pairs = (
            total_records
            -
            unique_records
        )


        # =====================================================
        # FINAL VALIDATION STATUS
        # =====================================================

        validation_passed = (
            empty_english == 0
            and
            empty_japanese == 0
            and
            no_japanese_script == 0
            and
            foreign_script == 0
            and
            duplicate_pairs == 0
        )


        # =====================================================
        # SAVE REPORT
        # =====================================================

        report_file = (
            report_dir
            / "post_clean_validation.txt"
        )


        with open(
            report_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "POST-CLEAN VALIDATION REPORT\n"
            )

            f.write(
                "=" * 60
                + "\n\n"
            )

            f.write(
                f"Total Records              : "
                f"{total_records:,}\n"
            )

            f.write(
                f"Empty English              : "
                f"{empty_english:,}\n"
            )

            f.write(
                f"Empty Japanese             : "
                f"{empty_japanese:,}\n"
            )

            f.write(
                f"No Japanese Script          : "
                f"{no_japanese_script:,}\n"
            )

            f.write(
                f"Foreign Script Remaining    : "
                f"{foreign_script:,}\n"
            )

            f.write(
                f"Duplicate EN-JA Pairs       : "
                f"{duplicate_pairs:,}\n"
            )

            f.write(
                "\n"
            )

            f.write(
                "Validation Status           : "
            )

            if validation_passed:
                f.write(
                    "PASS\n"
                )
            else:
                f.write(
                    "FAIL\n"
                )


        # =====================================================
        # PRINT RESULT
        # =====================================================

        print()

        print(
            "Total Records              :",
            f"{total_records:,}"
        )

        print(
            "Empty English              :",
            f"{empty_english:,}"
        )

        print(
            "Empty Japanese             :",
            f"{empty_japanese:,}"
        )

        print(
            "No Japanese Script         :",
            f"{no_japanese_script:,}"
        )

        print(
            "Foreign Script Remaining   :",
            f"{foreign_script:,}"
        )

        print(
            "Duplicate EN-JA Pairs      :",
            f"{duplicate_pairs:,}"
        )


        print(
            "\nValidation Status          :",
            "PASS"
            if validation_passed
            else "FAIL"
        )


        print(
            "\nReport saved:"
        )

        print(
            report_file
        )

        print(
            "=" * 80
        )


    finally:

        con.close()


def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "Validate final cleaned "
            "EN-JA corpus"
        )
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Validate test final dataset"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Validate full final dataset"
    )

    return parser.parse_args()


def main():

    args = parse_arguments()


    if args.test and args.full:

        raise ValueError(
            "Use either --test or --full, not both."
        )


    # Default TEST for safety
    test_mode = not args.full


    mode = (
        "TEST"
        if test_mode
        else "FULL"
    )


    input_file = get_final_file(
        test_mode
    )

    report_dir = get_report_dir(
        test_mode
    )


    print(
        "\nMODE:",
        mode
    )


    validate_final_dataset(
        input_file=input_file,
        report_dir=report_dir
    )


if __name__ == "__main__":
    main()