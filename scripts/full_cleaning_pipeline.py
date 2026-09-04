import argparse
import csv
import os
import time

from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import zip_longest
from pathlib import Path

from src.cleaner import DataCleaner
from src.shard_writer import ShardWriter
from src.stats import PipelineStats

from config.config import (
    EN_FILE,
    JA_FILE,
    SHARD_DIR,
    TEST_EN_FILE,
    TEST_JA_FILE,
    TEST_SHARD_DIR
)


# ============================================================
# SETTINGS
# ============================================================

PROGRESS_EVERY = 100_000

MAX_REMOVED_EXAMPLES_PER_REASON = 50

DEFAULT_CHUNK_SIZE = 50_000

DEFAULT_NUM_WORKERS = max(
    1,
    (os.cpu_count() or 2) - 1
) 


# ============================================================
# GLOBAL WORKER CLEANER
# ============================================================

_WORKER_CLEANER = None


# ============================================================
# INITIALIZE WORKER
# ============================================================

def initialize_worker():
    """
    Create one DataCleaner object per worker process.

    This avoids creating a new DataCleaner object
    for every individual record.
    """

    global _WORKER_CLEANER

    _WORKER_CLEANER = DataCleaner()


# ============================================================
# CLEAN ONE RECORD IN WORKER PROCESS
# ============================================================

def clean_worker(record):
    """
    Clean one aligned English-Japanese record.

    Input:
        (
            record_no,
            english,
            japanese
        )

    Output:
        (
            record_no,
            english,
            japanese,
            cleaning_result
        )
    """

    global _WORKER_CLEANER

    record_no, english, japanese = record

    result = _WORKER_CLEANER.clean_pair(
        english,
        japanese
    )

    return (
        record_no,
        english,
        japanese,
        result
    )


# ============================================================
# INPUT FILE CHECK
# ============================================================

def check_input_files(
    en_file,
    ja_file
):

    print("\n" + "=" * 80)

    print(
        "CHECKING INPUT FILES"
    )

    print("=" * 80)

    files = {
        "English": Path(en_file),
        "Japanese": Path(ja_file)
    }

    for name, path in files.items():

        if not path.exists():

            raise FileNotFoundError(
                f"{name} file not found:\n{path}"
            )

        print(
            f"{name:<10}: {path}"
        )

    print(
        "\nInput files found successfully."
    )


# ============================================================
# EXISTING SHARD CHECK
# ============================================================

def check_existing_shards(
    shard_dir
):

    shard_dir = Path(
        shard_dir
    )

    shard_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    existing_shards = list(
        shard_dir.glob(
            "shard_*.parquet"
        )
    )

    if existing_shards:

        print(
            "\n" + "!" * 80
        )

        print(
            f"{len(existing_shards)} existing shard files found:"
        )

        print(
            shard_dir
        )

        print(
            "\nOld shards should not be mixed with a new run."
        )

        print(
            "Delete/move them first."
        )

        print(
            "!" * 80
        )

        raise RuntimeError(
            "Existing shard files detected."
        )


# ============================================================
# REPORT DIRECTORY
# ============================================================

def get_report_directory(
    mode
):

    if mode == "test":

        report_dir = (
            Path("reports")
            / "test_run"
        )

    else:

        report_dir = (
            Path("reports")
            / "full_run"
        )

    report_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return report_dir


# ============================================================
# SAVE REMOVED EXAMPLES
# ============================================================

def save_removed_examples(
    removed_examples,
    report_dir
):

    output_file = (
        report_dir
        / "removed_examples.csv"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "record_no",
                "english",
                "japanese",
                "cleaning_reason"
            ]
        )

        writer.writeheader()

        for reason, examples in (
            removed_examples.items()
        ):

            for example in examples:

                writer.writerow(
                    example
                )

    print(
        "\n" + "=" * 80
    )

    print(
        "REMOVED EXAMPLES REPORT SAVED"
    )

    print("=" * 80)

    print(
        output_file
    )


# ============================================================
# PROCESS CLEANED RESULT
# ============================================================

def handle_result(
    record_no,
    english,
    japanese,
    result,
    stats,
    writer,
    removed_examples
):

    status = result[
        "cleaning_status"
    ]

    reason = result[
        "cleaning_reason"
    ]


    # --------------------------------------------------------
    # UPDATE STATS
    # --------------------------------------------------------

    stats.update(
        status,
        reason
    )


    # --------------------------------------------------------
    # WRITE USABLE DATA
    # --------------------------------------------------------

    if status != "REMOVE":

        writer.add_record(
            result["clean_english"],
            result["clean_japanese"]
        )


    # --------------------------------------------------------
    # STORE LIMITED REMOVED EXAMPLES
    # --------------------------------------------------------

    else:

        current_examples = (
            removed_examples[
                reason
            ]
        )

        if (
            len(current_examples)
            <
            MAX_REMOVED_EXAMPLES_PER_REASON
        ):

            current_examples.append(
                {
                    "record_no": record_no,
                    "english": english,
                    "japanese": japanese,
                    "cleaning_reason": reason
                }
            )


    # --------------------------------------------------------
    # PROGRESS REPORT
    # --------------------------------------------------------

    if (
        record_no
        %
        PROGRESS_EVERY
        ==
        0
    ):

        print(
            "\n" + "-" * 80
        )

        print(
            "Processed :",
            f"{record_no:,}"
        )

        print(
            "KEEP      :",
            f"{stats.keep_records:,}"
        )

        print(
            "CLEAN     :",
            f"{stats.clean_records:,}"
        )

        print(
            "REMOVE    :",
            f"{stats.remove_records:,}"
        )

        print(
            "Buffered  :",
            f"{len(writer.buffer):,}"
        )

        print(
            "Written   :",
            f"{writer.total_written:,}"
        )

        print(
            "-" * 80
        )


# ============================================================
# PROCESS ONE CHUNK
# ============================================================

def process_chunk(
    chunk,
    executor,
    stats,
    writer,
    removed_examples
):

    """
    Send one chunk to multiprocessing workers.

    executor.map preserves input order.
    Therefore EN-JA ordering remains preserved.
    """

    results = executor.map(
        clean_worker,
        chunk,
        chunksize=500
    )

    for (
        record_no,
        english,
        japanese,
        result
    ) in results:

        handle_result(
            record_no=record_no,
            english=english,
            japanese=japanese,
            result=result,
            stats=stats,
            writer=writer,
            removed_examples=removed_examples
        )


# ============================================================
# PIPELINE
# ============================================================

def run_pipeline(
    en_file,
    ja_file,
    shard_dir,
    mode,
    chunk_size,
    num_workers
):

    # ========================================================
    # START EXECUTION TIMER
    # ========================================================

    start_time = time.perf_counter()


    print(
        "\n" + "#" * 90
    )

    print(
        "ENGLISH-JAPANESE CORPUS CLEANING PIPELINE"
    )

    print(
        "#" * 90
    )

    print(
        "Mode        :",
        mode.upper()
    )

    print(
        "Chunk Size  :",
        f"{chunk_size:,}"
    )

    print(
        "CPU Workers :",
        num_workers
    )


    # --------------------------------------------------------
    # CHECK INPUT FILES
    # --------------------------------------------------------

    check_input_files(
        en_file,
        ja_file
    )


    # --------------------------------------------------------
    # CHECK EXISTING OUTPUT SHARDS
    # --------------------------------------------------------

    check_existing_shards(
        shard_dir
    )


    # --------------------------------------------------------
    # REPORT DIRECTORY
    # --------------------------------------------------------

    report_dir = (
        get_report_directory(
            mode
        )
    )


    # --------------------------------------------------------
    # INITIALIZE MAIN PROCESS COMPONENTS
    # --------------------------------------------------------

    writer = ShardWriter(
        output_dir=shard_dir
    )

    stats = PipelineStats(
        report_dir=report_dir
    )

    removed_examples = (
        defaultdict(list)
    )


    print(
        "\n" + "=" * 80
    )

    print(
        "CLEANING STARTED"
    )

    print(
        "=" * 80
    )


    # ========================================================
    # START MULTIPROCESSING
    # ========================================================

    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=initialize_worker
    ) as executor:


        # ====================================================
        # OPEN ALIGNED FILES
        # ====================================================

        with open(
            en_file,
            "r",
            encoding="utf-8"
        ) as en_stream, open(
            ja_file,
            "r",
            encoding="utf-8"
        ) as ja_stream:


            # ------------------------------------------------
            # TEMPORARY PROCESSING CHUNK
            # ------------------------------------------------

            chunk = []


            # =================================================
            # STREAM ALIGNED ENGLISH + JAPANESE
            # =================================================

            for record_no, (
                english,
                japanese
            ) in enumerate(

                zip_longest(
                    en_stream,
                    ja_stream,
                    fillvalue=None
                ),

                start=1
            ):


                # =============================================
                # ALIGNMENT CHECK
                # =============================================

                if (
                    english is None
                    or
                    japanese is None
                ):

                    raise ValueError(
                        f"EN-JA line count mismatch "
                        f"at record {record_no:,}"
                    )


                # =============================================
                # REMOVE ONLY LINE ENDINGS
                # =============================================

                english = english.rstrip(
                    "\r\n"
                )

                japanese = japanese.rstrip(
                    "\r\n"
                )


                # =============================================
                # ADD RECORD TO CURRENT CHUNK
                # =============================================

                chunk.append(
                    (
                        record_no,
                        english,
                        japanese
                    )
                )


                # =============================================
                # PROCESS FULL CHUNK
                # =============================================

                if (
                    len(chunk)
                    >=
                    chunk_size
                ):

                    process_chunk(
                        chunk=chunk,
                        executor=executor,
                        stats=stats,
                        writer=writer,
                        removed_examples=removed_examples
                    )

                    chunk.clear()


            # =================================================
            # PROCESS FINAL PARTIAL CHUNK
            # =================================================

            if chunk:

                process_chunk(
                    chunk=chunk,
                    executor=executor,
                    stats=stats,
                    writer=writer,
                    removed_examples=removed_examples
                )

                chunk.clear()


    # ========================================================
    # WRITE FINAL PARTIAL SHARD
    # ========================================================

    writer.finalize()


    # ========================================================
    # SAVE REMOVED EXAMPLES
    # ========================================================

    save_removed_examples(
        removed_examples,
        report_dir
    )


    # ========================================================
    # FINAL STATS
    # ========================================================

    stats.set_final_written(
        writer.total_written
    )

    stats.save_all()


    # ========================================================
    # STOP EXECUTION TIMER
    # ========================================================

    end_time = time.perf_counter()

    elapsed_time = (
        end_time
        -
        start_time
    )

    minutes = int(
        elapsed_time // 60
    )

    seconds = (
        elapsed_time % 60
    )


    # ========================================================
    # CALCULATE PROCESSING SPEED
    # ========================================================

    total_processed = (
        stats.keep_records
        +
        stats.clean_records
        +
        stats.remove_records
    )

    if elapsed_time > 0:

        records_per_second = (
            total_processed
            /
            elapsed_time
        )

    else:

        records_per_second = 0


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print(
        "\n" + "#" * 90
    )

    print(
        "CLEANING COMPLETED SUCCESSFULLY"
    )

    print(
        "#" * 90
    )

    print(
        "Mode          :",
        mode.upper()
    )

    print(
        "Chunk Size    :",
        f"{chunk_size:,}"
    )

    print(
        "CPU Workers   :",
        num_workers
    )

    print(
        "Output Folder :",
        Path(shard_dir)
    )

    print(
        "Report Folder :",
        report_dir
    )

    print(
        "Records Saved :",
        f"{writer.total_written:,}"
    )

    print(
        "Elapsed Time  :",
        f"{minutes} min {seconds:.2f} sec"
    )

    print(
        "Throughput    :",
        f"{records_per_second:,.2f} records/sec"
    )

    print(
        "#" * 90
    )


# ============================================================
# COMMAND LINE ARGUMENTS
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "English-Japanese corpus cleaning pipeline"
        )
    )


    parser.add_argument(
        "--test",
        action="store_true",
        help=(
            "Run pipeline on test dataset."
        )
    )


    parser.add_argument(
        "--full",
        action="store_true",
        help=(
            "Run pipeline on full dataset."
        )
    )


    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=(
            "Number of aligned records loaded "
            "into one processing chunk."
        )
    )


    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_NUM_WORKERS,
        help=(
            "Number of multiprocessing worker processes."
        )
    )


    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    args = (
        parse_arguments()
    )


    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if (
        args.test
        and
        args.full
    ):

        raise ValueError(
            "Use only one mode: --test OR --full"
        )


    if args.chunk_size <= 0:

        raise ValueError(
            "--chunk-size must be greater than 0."
        )


    if args.workers <= 0:

        raise ValueError(
            "--workers must be greater than 0."
        )


    # --------------------------------------------------------
    # FULL MODE
    # --------------------------------------------------------

    if args.full:

        run_pipeline(
            en_file=EN_FILE,
            ja_file=JA_FILE,
            shard_dir=SHARD_DIR,
            mode="full",
            chunk_size=args.chunk_size,
            num_workers=args.workers
        )


    # --------------------------------------------------------
    # TEST MODE
    # --------------------------------------------------------

    else:

        run_pipeline(
            en_file=TEST_EN_FILE,
            ja_file=TEST_JA_FILE,
            shard_dir=TEST_SHARD_DIR,
            mode="test",
            chunk_size=args.chunk_size,
            num_workers=args.workers
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()