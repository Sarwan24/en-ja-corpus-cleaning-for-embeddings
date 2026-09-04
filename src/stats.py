import json
from pathlib import Path
from collections import Counter



class PipelineStats:

    """
    Full corpus cleaning ke statistics maintain karta hai.

    Track karega:
        total records
        keep records
        clean records
        remove records
        cleaning reasons
        duplicate removed
        final written records
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        report_dir
    ):


        self.report_dir = Path(
            report_dir
        )

        self.report_dir.mkdir(
            parents=True,
            exist_ok=True
        )


        self.total_records = 0

        self.keep_records = 0

        self.clean_records = 0

        self.remove_records = 0

        self.duplicate_removed = 0

        self.final_written_records = 0


        # Cleaning reasons count
        self.reason_counts = Counter()


    # ========================================================
    # UPDATE STATS FOR ONE RECORD
    # ========================================================

    def update(
        self,
        status,
        reason=""
    ):

        self.total_records += 1


        if status == "KEEP":

            self.keep_records += 1


        elif status == "CLEAN":

            self.clean_records += 1


        elif status == "REMOVE":

            self.remove_records += 1


        # Cleaning reason count
        if reason:

            reasons = [
                r.strip()
                for r in reason.split(",")
                if r.strip()
            ]

            for r in reasons:

                self.reason_counts[r] += 1


    # ========================================================
    # UPDATE DUPLICATE COUNT
    # ========================================================

    def add_duplicates(
        self,
        count
    ):

        self.duplicate_removed += count


    # ========================================================
    # UPDATE FINAL WRITTEN COUNT
    # ========================================================

    def set_final_written(
        self,
        count
    ):

        self.final_written_records = count


    # ========================================================
    # BUILD STATS DICTIONARY
    # ========================================================

    def get_stats(self):

        if self.total_records > 0:

            preserved_records = (
                self.keep_records
                +
                self.clean_records
            )

            preserved_percentage = (
                preserved_records
                /
                self.total_records
                *
                100
            )

            removed_percentage = (
                self.remove_records
                /
                self.total_records
                *
                100
            )

        else:

            preserved_percentage = 0

            removed_percentage = 0


        return {

            "total_records":
                self.total_records,

            "keep_records":
                self.keep_records,

            "clean_records":
                self.clean_records,

            "remove_records":
                self.remove_records,

            "duplicate_removed":
                self.duplicate_removed,

            "final_written_records":
                self.final_written_records,

            "preserved_percentage":
                round(
                    preserved_percentage,
                    2
                ),

            "removed_percentage":
                round(
                    removed_percentage,
                    2
                ),

            "cleaning_reasons":
                dict(
                    self.reason_counts
                )
        }


    # ========================================================
    # SAVE JSON REPORT
    # ========================================================

    def save_json_report(self):

        stats = self.get_stats()


        output_path = (
            self.report_dir
            /
            "cleaning_stats.json"
        )


        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                stats,
                f,
                ensure_ascii=False,
                indent=4
            )


        print(
            "\nJSON report saved:"
        )

        print(
            output_path
        )


    # ========================================================
    # SAVE TEXT SUMMARY
    # ========================================================

    def save_text_summary(self):

        stats = self.get_stats()


        output_path = (
            self.report_dir
            /
            "run_summary.txt"
        )


        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                "ENGLISH-JAPANESE CORPUS CLEANING SUMMARY\n"
            )

            f.write(
                "=" * 60
                + "\n\n"
            )


            f.write(
                f"Total Records           : "
                f"{stats['total_records']:,}\n"
            )

            f.write(
                f"KEEP Records            : "
                f"{stats['keep_records']:,}\n"
            )

            f.write(
                f"CLEAN Records           : "
                f"{stats['clean_records']:,}\n"
            )

            f.write(
                f"REMOVE Records          : "
                f"{stats['remove_records']:,}\n"
            )

            f.write(
                f"Duplicate Removed       : "
                f"{stats['duplicate_removed']:,}\n"
            )

            f.write(
                f"Final Written Records   : "
                f"{stats['final_written_records']:,}\n"
            )

            f.write(
                f"Preserved Percentage    : "
                f"{stats['preserved_percentage']}%\n"
            )

            f.write(
                f"Removed Percentage      : "
                f"{stats['removed_percentage']}%\n"
            )


            f.write(
                "\n"
                + "=" * 60
                + "\n"
            )

            f.write(
                "CLEANING REASONS\n"
            )

            f.write(
                "=" * 60
                + "\n"
            )


            for reason, count in (
                self.reason_counts
                .most_common()
            ):

                f.write(
                    f"{reason:<50}"
                    f"{count:,}\n"
                )


        print(
            "\nText summary saved:"
        )

        print(
            output_path
        )


    # ========================================================
    # PRINT CONSOLE SUMMARY
    # ========================================================

    def print_summary(self):

        stats = self.get_stats()


        print(
            "\n"
            + "=" * 80
        )

        print(
            "FULL CORPUS CLEANING SUMMARY"
        )

        print(
            "=" * 80
        )


        print(
            "Total Records         :",
            f"{stats['total_records']:,}"
        )

        print(
            "KEEP Records          :",
            f"{stats['keep_records']:,}"
        )

        print(
            "CLEAN Records         :",
            f"{stats['clean_records']:,}"
        )

        print(
            "REMOVE Records        :",
            f"{stats['remove_records']:,}"
        )

        print(
            "Duplicate Removed     :",
            f"{stats['duplicate_removed']:,}"
        )

        print(
            "Final Written Records :",
            f"{stats['final_written_records']:,}"
        )

        print(
            "Preserved             :",
            f"{stats['preserved_percentage']}%"
        )

        print(
            "Removed               :",
            f"{stats['removed_percentage']}%"
        )


        print(
            "\nTop Cleaning Reasons:"
        )


        for reason, count in (
            self.reason_counts
            .most_common(15)
        ):

            print(
                f"{reason:<50}"
                f"{count:,}"
            )


        print(
            "=" * 80
        )


    # ========================================================
    # SAVE ALL REPORTS
    # ========================================================

    def save_all(self):

        self.save_json_report()

        self.save_text_summary()

        self.print_summary()