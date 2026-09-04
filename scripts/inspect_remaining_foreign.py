import duckdb

from config.config import FINAL_DIR, PROJECT_ROOT


INPUT_FILE = (
    FINAL_DIR
    / "deduplicated_en_ja.parquet"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "full_run"
    / "remaining_foreign_script.csv"
)


def main():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    con = duckdb.connect()

    try:

        parquet_path = INPUT_FILE.as_posix()
        output_path = OUTPUT_FILE.as_posix()

        con.execute(
            f"""
            COPY (
                SELECT
                    english,
                    japanese
                FROM read_parquet(
                    '{parquet_path}'
                )
                WHERE regexp_matches(
                    japanese,
                    '[؀-ࣿЀ-ӿ֐-׿가-힣]'
                )
            )
            TO '{output_path}'
            (
                HEADER,
                DELIMITER ','
            )
            """
        )

        count = con.execute(
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

        print(
            "\nForeign-script records:",
            count
        )

        print(
            "Saved to:",
            OUTPUT_FILE
        )

    finally:

        con.close()


if __name__ == "__main__":
    main()