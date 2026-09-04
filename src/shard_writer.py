from pathlib import Path

import pandas as pd

from config.config import (
    SHARD_DIR,
    SHARD_SIZE,
    PARQUET_COMPRESSION
)


class ShardWriter:

    """
    Cleaned English-Japanese records ko fixed-size
    compressed Parquet shards me save karta hai.

    Final shard columns:
        english
        japanese
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        output_dir=SHARD_DIR,
        shard_size=SHARD_SIZE,
        compression=PARQUET_COMPRESSION
    ):

        self.output_dir = Path(output_dir)

        self.shard_size = shard_size

        self.compression = compression

        # Temporary records yahan store honge
        self.buffer = []

        # Shard numbering
        self.shard_number = 0

        # Total saved records
        self.total_written = 0


        # Output directory automatically create karega
        self.output_dir.mkdir(
            parents=True, 
            exist_ok=True
        )


    # ========================================================
    # ADD ONE CLEAN RECORD
    # ========================================================

    def add_record(
        self,
        english,
        japanese
    ):

        record = {
            "english": english,
            "japanese": japanese
        }

        self.buffer.append(
            record
        )


        # Shard size reach hote hi disk par write
        if len(self.buffer) >= self.shard_size:

            self.write_shard()


    # ========================================================
    # WRITE CURRENT BUFFER
    # ========================================================

    def write_shard(self):

        # Empty buffer ko write nahi karna
        if not self.buffer:

            return


        # Buffer -> DataFrame
        df = pd.DataFrame(
            self.buffer,
            columns=[
                "english",
                "japanese"
            ]
        )


        # ----------------------------------------------------
        # SHARD FILE NAME
        # ----------------------------------------------------

        shard_name = (
            f"shard_"
            f"{self.shard_number:05d}"
            f".parquet"
        )


        shard_path = (
            self.output_dir
            /
            shard_name
        )


        # ----------------------------------------------------
        # SAVE PARQUET
        # ----------------------------------------------------

        df.to_parquet(
            shard_path,
            index=False,
            compression=self.compression,
            engine="pyarrow"
        )


        records_written = len(
            df
        )


        self.total_written += (
            records_written
        )


        # ----------------------------------------------------
        # CONSOLE INFORMATION
        # ----------------------------------------------------

        print(
            f"Saved: {shard_name}"
        )

        print(
            f"Records in shard: "
            f"{records_written:,}"
        )

        print(
            f"Total records written: "
            f"{self.total_written:,}"
        )

        print(
            "-" * 70
        )


        # ----------------------------------------------------
        # NEXT SHARD NUMBER
        # ----------------------------------------------------

        self.shard_number += 1


        # ----------------------------------------------------
        # FREE BUFFER MEMORY
        # ----------------------------------------------------

        self.buffer.clear()


    # ========================================================
    # FINALIZE
    # ========================================================

    def finalize(self):

        """
        Pipeline ke end me remaining records ko bhi save karega.

        Example:
            SHARD_SIZE = 500,000

            Last buffer = 127,430

        Ye 127,430 records bhi final shard me save honge.
        """

        if self.buffer:

            self.write_shard()


        print(
            "\n"
            + "=" * 80
        )

        print(
            "SHARD WRITING COMPLETED"
        )

        print(
            "=" * 80
        )

        print(
            "Total Shards  :",
            self.shard_number
        )

        print(
            "Total Records :",
            f"{self.total_written:,}"
        )

        print(
            "Output Folder :",
            self.output_dir
        )

        print(
            "Format        : Parquet"
        )

        print(
            "Compression   :",
            self.compression
        )

        print(
            "Columns       : english, japanese"
        )

        print(
            "=" * 80
        )