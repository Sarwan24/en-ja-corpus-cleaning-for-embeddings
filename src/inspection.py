import pandas as pd
import re


class DataInspector:
    
    # Arabic script
    ARABIC_PATTERN = re.compile(
        r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"
    )

    # Emoji ranges
    EMOJI_PATTERN = re.compile(
        r"[\U0001F300-\U0001FAFF"
        r"\U00002600-\U000026FF"
        r"\U00002700-\U000027BF]"
    )

    # Common symbols
    SYMBOL_PATTERN = re.compile(
        r"[©®™★☆→←↑↓✓✔✕✖♥♡♪♫]"
    )

    def __init__(self, df):
        self.df = df.copy()


    def emoji_statistics(self):
        
        en = self.df["english"].fillna("").astype(str)
        ja = self.df["japanese"].fillna("").astype(str)

        en_emoji = en.apply(
            lambda x: bool(self.EMOJI_PATTERN.search(x))
        )

        ja_emoji = ja.apply(
            lambda x: bool(self.EMOJI_PATTERN.search(x))
        )

        both = en_emoji & ja_emoji
        en_only = en_emoji & ~ja_emoji
        ja_only = ja_emoji & ~en_emoji

        print("\n" + "=" * 90)
        print("EMOJI ANALYSIS")
        print("=" * 90)

        print("Emoji in English :", en_emoji.sum())
        print("Emoji in Japanese:", ja_emoji.sum())
        print("Emoji on both    :", both.sum())
        print("English only     :", en_only.sum())
        print("Japanese only    :", ja_only.sum())
    
    
    def arabic_script_statistics(self):
    
        ja = self.df["japanese"].fillna("").astype(str)

        arabic_mask = ja.apply(
            lambda x: bool(
                self.ARABIC_PATTERN.search(x)
            )
        )

        count = arabic_mask.sum()

        print("\n" + "=" * 90)
        print("ARABIC SCRIPT IN JAPANESE TARGET")
        print("=" * 90)

        print("Rows containing Arabic script:", count)

        if len(self.df) > 0:
            print(
                f"Percentage: "
                f"{count / len(self.df) * 100:.2f}%"
            )
            
    
    def symbol_statistics(self):
    
        ja = self.df["japanese"].fillna("").astype(str)

        symbol_mask = ja.apply(
            lambda x: bool(
                self.SYMBOL_PATTERN.search(x)
            )
        )

        count = symbol_mask.sum()

        print("\n" + "=" * 90)
        print("SPECIAL SYMBOL ANALYSIS")
        print("=" * 90)

        print(
            "Rows containing selected symbols:",
            count
        )
        
        

    # =========================================================
    # 1. BASIC INFORMATION
    # =========================================================

    def basic_info(self):

        print("\n" + "=" * 90)
        print("BASIC DATASET INFORMATION")
        print("=" * 90)

        print("Total Rows    :", len(self.df))
        print("Total Columns :", len(self.df.columns))

        print("\nColumns:")
        print(self.df.columns.tolist())

        print("\nData Types:")
        print(self.df.dtypes)


    # =========================================================
    # 2. MISSING VALUES
    # =========================================================

    def missing_values(self):

        print("\n" + "=" * 90)
        print("MISSING VALUES")
        print("=" * 90)

        print(
            self.df.isnull().sum()
        )


    # =========================================================
    # 3. EMPTY EN / JA
    # =========================================================

    def empty_records(self):

        empty_en = (
            self.df["english"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )

        empty_ja = (
            self.df["japanese"]
            .fillna("")
            .astype(str)
            .str.strip()
            .eq("")
            .sum()
        )

        print("\n" + "=" * 90)
        print("EMPTY RECORDS")
        print("=" * 90)

        print("Empty English  :", empty_en)
        print("Empty Japanese :", empty_ja)


    # =========================================================
    # 4. DUPLICATES
    # =========================================================

    def duplicate_records(self):

        exact_duplicates = (
            self.df
            .duplicated()
            .sum()
        )

        pair_duplicates = (
            self.df
            .duplicated(
                subset=[
                    "english",
                    "japanese"
                ]
            )
            .sum()
        )

        english_duplicates = (
            self.df["english"]
            .duplicated()
            .sum()
        )

        japanese_duplicates = (
            self.df["japanese"]
            .duplicated()
            .sum()
        )

        print("\n" + "=" * 90)
        print("DUPLICATE ANALYSIS")
        print("=" * 90)

        print("Exact Duplicate Rows  :", exact_duplicates)
        print("Duplicate EN-JA Pairs :", pair_duplicates)
        print("Duplicate English     :", english_duplicates)
        print("Duplicate Japanese    :", japanese_duplicates)


    # =========================================================
    # 5. TEXT LENGTH FEATURES
    # =========================================================

    def with_lengths(self):

        df = self.df.copy()

        df["en_length"] = (
            df["english"]
            .fillna("")
            .astype(str)
            .str.len()
        )

        df["ja_length"] = (
            df["japanese"]
            .fillna("")
            .astype(str)
            .str.len()
        )

        df["length_ratio"] = (
            df["ja_length"]
            /
            df["en_length"].replace(
                0,
                pd.NA
            )
        )

        return df


    # =========================================================
    # 6. TEXT LENGTH STATISTICS
    # =========================================================

    def length_statistics(self):

        df = self.with_lengths()

        print("\n" + "=" * 90)
        print("TEXT LENGTH STATISTICS")
        print("=" * 90)

        print("\nENGLISH CHARACTER LENGTH:")
        print(
            df["en_length"]
            .describe()
        )

        print("\nJAPANESE CHARACTER LENGTH:")
        print(
            df["ja_length"]
            .describe()
        )

        print("\nJA / EN LENGTH RATIO:")
        print(
            df["length_ratio"]
            .describe()
        )


    # =========================================================
    # 7. CONFIDENCE SCORE
    # =========================================================

    def confidence_statistics(self):

        print("\n" + "=" * 90)
        print("CONFIDENCE SCORE STATISTICS")
        print("=" * 90)

        print(
            self.df[
                "confidence_score"
            ].describe()
        )


    # =========================================================
    # 8. SAMPLE TYPE DISTRIBUTION
    # =========================================================

    def sample_type_summary(self):

        if "sample_type" not in self.df.columns:
            return

        print("\n" + "=" * 90)
        print("SAMPLE TYPE DISTRIBUTION")
        print("=" * 90)

        counts = (
            self.df["sample_type"]
            .value_counts()
        )

        total = len(self.df)

        for sample_type, count in counts.items():

            percentage = (
                count / total * 100
            )

            print(
                f"{sample_type:<15}: "
                f"{count:<7} "
                f"({percentage:.2f}%)"
            )


    # =========================================================
    # 9. TARGETED CATEGORY SUMMARY
    # =========================================================

    def targeted_category_summary(self):

        if "sample_category" not in self.df.columns:
            return

        targeted_df = self.df[
            self.df["sample_type"]
            ==
            "TARGETED"
        ]

        print("\n" + "=" * 90)
        print("TARGETED CATEGORY DISTRIBUTION")
        print("=" * 90)

        counts = (
            targeted_df[
                "sample_category"
            ]
            .value_counts()
        )

        total = len(targeted_df)

        for category, count in counts.items():

            percentage = (
                count / total * 100
            )

            print(
                f"{category:<28}: "
                f"{count:<6} "
                f"({percentage:.2f}%)"
            )


    # =========================================================
    # 10. LATIN / JAPANESE RATIO STATISTICS
    # =========================================================

    def language_ratio_statistics(self):

        required_columns = [
            "latin_ratio",
            "japanese_ratio"
        ]

        if not all(
            col in self.df.columns
            for col in required_columns
        ):
            return

        print("\n" + "=" * 90)
        print("SCRIPT RATIO STATISTICS")
        print("=" * 90)

        print("\nLATIN RATIO:")
        print(
            self.df[
                "latin_ratio"
            ].describe()
        )

        print("\nJAPANESE RATIO:")
        print(
            self.df[
                "japanese_ratio"
            ].describe()
        )


    # =========================================================
    # 11. LATIN PREFIX STATISTICS
    # =========================================================

    def latin_prefix_statistics(self):

        if (
            "latin_prefix_chars"
            not in self.df.columns
        ):
            return

        print("\n" + "=" * 90)
        print("LATIN PREFIX STATISTICS")
        print("=" * 90)

        print(
            self.df[
                "latin_prefix_chars"
            ].describe()
        )


    # =========================================================
    # 12. SOURCE PREFIX SIMILARITY
    # =========================================================

    def source_similarity_statistics(self):

        if (
            "source_prefix_similarity"
            not in self.df.columns
        ):
            return

        print("\n" + "=" * 90)
        print("SOURCE PREFIX SIMILARITY")
        print("=" * 90)

        print(
            self.df[
                "source_prefix_similarity"
            ].describe()
        )


    # =========================================================
    # 13. LATIN TOKEN OVERLAP
    # =========================================================

    def token_overlap_statistics(self):

        if (
            "latin_token_overlap"
            not in self.df.columns
        ):
            return

        print("\n" + "=" * 90)
        print("LATIN TOKEN OVERLAP")
        print("=" * 90)

        print(
            self.df[
                "latin_token_overlap"
            ].describe()
        )


    # =========================================================
    # 14. IMPORTANT THRESHOLD COUNTS
    # =========================================================

    def threshold_summary(self):

        print("\n" + "=" * 90)
        print("IMPORTANT PATTERN COUNTS")
        print("=" * 90)

        total = len(self.df)

        def show(label, count):

            percentage = (
                count / total * 100
                if total
                else 0
            )

            print(
                f"{label:<38}: "
                f"{count:<7} "
                f"({percentage:.2f}%)"
            )


        if "latin_ratio" in self.df.columns:

            show(
                "Latin ratio >= 30%",
                (
                    self.df["latin_ratio"]
                    >= 0.30
                ).sum()
            )

            show(
                "Latin ratio >= 50%",
                (
                    self.df["latin_ratio"]
                    >= 0.50
                ).sum()
            )

            show(
                "Latin ratio >= 70%",
                (
                    self.df["latin_ratio"]
                    >= 0.70
                ).sum()
            )


        if (
            "latin_prefix_chars"
            in self.df.columns
        ):

            show(
                "Latin prefix >= 20 chars",
                (
                    self.df[
                        "latin_prefix_chars"
                    ]
                    >= 20
                ).sum()
            )

            show(
                "Latin prefix >= 30 chars",
                (
                    self.df[
                        "latin_prefix_chars"
                    ]
                    >= 30
                ).sum()
            )

            show(
                "Latin prefix >= 100 chars",
                (
                    self.df[
                        "latin_prefix_chars"
                    ]
                    >= 100
                ).sum()
            )


        if (
            "source_prefix_similarity"
            in self.df.columns
        ):

            show(
                "Prefix similarity >= 0.75",
                (
                    self.df[
                        "source_prefix_similarity"
                    ]
                    >= 0.75
                ).sum()
            )


        if (
            "latin_token_overlap"
            in self.df.columns
        ):

            show(
                "Token overlap >= 0.60",
                (
                    self.df[
                        "latin_token_overlap"
                    ]
                    >= 0.60
                ).sum()
            )

            show(
                "Token overlap >= 0.75",
                (
                    self.df[
                        "latin_token_overlap"
                    ]
                    >= 0.75
                ).sum()
            )


    # =========================================================
    # 15. FULL INSPECTION
    # =========================================================

    def run_all(self):

        self.basic_info()
        self.missing_values()
        self.empty_records()
        self.duplicate_records()
        self.length_statistics()
        self.confidence_statistics()

        self.sample_type_summary()
        self.targeted_category_summary()

        self.language_ratio_statistics()
        self.latin_prefix_statistics()
        self.source_similarity_statistics()
        self.token_overlap_statistics()

        self.threshold_summary()