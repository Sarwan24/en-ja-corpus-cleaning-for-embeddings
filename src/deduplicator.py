from pathlib import Path

import duckdb



class GlobalDeduplicator:

    """
    Cleaned Parquet shards ke across
    global EN-JA pair deduplication karta hai.

    Input:
        data/full/shards/*.parquet

    Output:
        data/full/final/*.parquet
    """

    def __init__(
        self,
        shard_dir,
        final_dir,
        temp_dir
    ):
        self.shard_dir = Path(shard_dir)
        self.final_dir = Path(final_dir)
        self.temp_dir = Path(temp_dir)

        self.final_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.temp_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.connection = duckdb.connect(
            database=str(
                self.temp_dir / "dedup.duckdb"
            )
        )


        # Disk spilling ke liye temp directory
        self.connection.execute(
            f"""
            SET temp_directory =
            '{self.temp_dir.as_posix()}'
            """
        )


    # ========================================================
    # COUNT INPUT RECORDS
    # ========================================================

    def count_input_records(self):

        shard_pattern = (
            self.shard_dir
            /
            "*.parquet"
        )

        result = self.connection.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{shard_pattern.as_posix()}'
            )
            """
        ).fetchone()

        return result[0]


    # ========================================================
    # COUNT UNIQUE RECORDS
    # ========================================================

    def count_unique_records(self):

        shard_pattern = (
            self.shard_dir
            /
            "*.parquet"
        )

        result = self.connection.execute(
            f"""
            SELECT COUNT(*)
            FROM (
                SELECT DISTINCT
                    english,
                    japanese

                FROM read_parquet(
                    '{shard_pattern.as_posix()}'
                )
            )
            """
        ).fetchone()

        return result[0]


    # ========================================================
    # RUN GLOBAL DEDUPLICATION
    # ========================================================

    def deduplicate(self):

        shard_pattern = (
            self.shard_dir
            /
            "*.parquet"
        )

        output_file = (
            self.final_dir
            /
            "deduplicated_en_ja.parquet"
        )


        print(
            "\n"
            + "=" * 80
        )

        print(
            "GLOBAL DEDUPLICATION STARTED"
        )

        print(
            "=" * 80
        )


        # ----------------------------------------------------
        # INPUT COUNT
        # ----------------------------------------------------

        total_records = (
            self.count_input_records()
        )


        print(
            "Input Records:",
            f"{total_records:,}"
        )


        # ----------------------------------------------------
        # DEDUPLICATE AND SAVE
        # ----------------------------------------------------

        self.connection.execute(
            f"""
            COPY (

                SELECT DISTINCT
                    english,
                    japanese

                FROM read_parquet(
                    '{shard_pattern.as_posix()}'
                )

            )

            TO '{output_file.as_posix()}'

            (
                FORMAT PARQUET,
                COMPRESSION ZSTD
            )
            """
        )


        # ----------------------------------------------------
        # FINAL COUNT
        # ----------------------------------------------------

        result = self.connection.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet(
                '{output_file.as_posix()}'
            )
            """
        ).fetchone()


        unique_records = result[0]


        duplicates_removed = (
            total_records
            -
            unique_records
        )


        print(
            "Unique Records:",
            f"{unique_records:,}"
        )

        print(
            "Duplicates Removed:",
            f"{duplicates_removed:,}"
        )

        print(
            "Output File:",
            output_file
        )

        print(
            "=" * 80
        )


        return {
            "total_records":
                total_records,

            "unique_records":
                unique_records,

            "duplicates_removed":
                duplicates_removed,

            "output_file":
                str(output_file)
        }


    # ========================================================
    # CLOSE CONNECTION
    # ========================================================

    def close(self):

        self.connection.close()