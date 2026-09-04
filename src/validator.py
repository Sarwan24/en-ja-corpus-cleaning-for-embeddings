import re
import unicodedata
from difflib import SequenceMatcher


class PairValidator:

    # =========================================================
    # REGEX PATTERNS
    # =========================================================

    JAPANESE_PATTERN = re.compile(
        r"[\u3040-\u30ff\u3400-\u9fff]"
    )

    ARABIC_PATTERN = re.compile(
        r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]"
    )

    LATIN_PATTERN = re.compile(
        r"[A-Za-z]"
    )

    WORD_PATTERN = re.compile(
        r"[A-Za-z][A-Za-z0-9'_-]*"
    )

    NUMBER_PATTERN = re.compile(
        r"\d+(?:\.\d+)?"
    )

    PERCENT_PATTERN = re.compile(
        r"\d+(?:\.\d+)?\s*[%％]"
    )

    EMOJI_PATTERN = re.compile(
        r"[\U0001F300-\U0001FAFF"
        r"\U00002600-\U000026FF"
        r"\U00002700-\U000027BF]"
    )

    SYMBOL_PATTERN = re.compile(
        r"[©®™★☆→←↑↓✓✔✕✖♥♡♪♫]"
    )


    # =========================================================
    # 1. NORMALIZATION
    # =========================================================

    def normalize_text(self, text):

        if text is None:
            return ""

        text = str(text)

        return unicodedata.normalize(
            "NFC",
            text
        ).strip()


    # =========================================================
    # 2. EMPTY / MALFORMED
    # =========================================================

    def malformed_validation(self, en, ja):

        en = self.normalize_text(en)
        ja = self.normalize_text(ja)

        return (
            not en
            or
            not ja
        )


    # =========================================================
    # 3. JAPANESE SCRIPT CHECK
    # =========================================================

    def contains_japanese(self, text):

        return bool(
            self.JAPANESE_PATTERN.search(
                str(text)
            )
        )


    # =========================================================
    # 4. ARABIC SCRIPT CHECK
    # =========================================================

    def contains_arabic(self, text):

        return bool(
            self.ARABIC_PATTERN.search(
                str(text)
            )
        )


    # =========================================================
    # 5. EMOJI CORRESPONDENCE
    # =========================================================

    def emoji_validation(self, en, ja):

        en_emoji = (
            self.EMOJI_PATTERN.findall(
                str(en)
            )
        )

        ja_emoji = (
            self.EMOJI_PATTERN.findall(
                str(ja)
            )
        )

        if (
            not en_emoji
            and
            not ja_emoji
        ):
            return False

        return (
            sorted(en_emoji)
            !=
            sorted(ja_emoji)
        )


    # =========================================================
    # 6. SYMBOL CORRESPONDENCE
    # =========================================================

    def symbol_validation(self, en, ja):

        en_symbols = (
            self.SYMBOL_PATTERN.findall(
                str(en)
            )
        )

        ja_symbols = (
            self.SYMBOL_PATTERN.findall(
                str(ja)
            )
        )

        if (
            not en_symbols
            and
            not ja_symbols
        ):
            return False

        return (
            sorted(en_symbols)
            !=
            sorted(ja_symbols)
        )


    # =========================================================
    # 7. NUMBER CORRESPONDENCE
    # =========================================================

    def number_validation(self, en, ja):

        en = unicodedata.normalize(
            "NFKC",
            str(en)
        )

        ja = unicodedata.normalize(
            "NFKC",
            str(ja)
        )

        en_numbers = sorted(
            self.NUMBER_PATTERN.findall(
                en
            )
        )

        ja_numbers = sorted(
            self.NUMBER_PATTERN.findall(
                ja
            )
        )

        if (
            not en_numbers
            and
            not ja_numbers
        ):
            return False

        return (
            en_numbers
            !=
            ja_numbers
        )


    # =========================================================
    # 8. PERCENT CORRESPONDENCE
    # =========================================================

    def percent_validation(self, en, ja):

        en = unicodedata.normalize(
            "NFKC",
            str(en)
        )

        ja = unicodedata.normalize(
            "NFKC",
            str(ja)
        )

        en_percent = [
            value.replace(
                " ",
                ""
            )
            for value in
            self.PERCENT_PATTERN.findall(en)
        ]

        ja_percent = [
            value.replace(
                " ",
                ""
            )
            for value in
            self.PERCENT_PATTERN.findall(ja)
        ]

        if (
            not en_percent
            and
            not ja_percent
        ):
            return False

        return (
            sorted(en_percent)
            !=
            sorted(ja_percent)
        )


    # =========================================================
    # 9. LATIN PREFIX
    # =========================================================

    def get_latin_prefix(self, ja):

        ja = self.normalize_text(ja)

        match = (
            self.JAPANESE_PATTERN.search(
                ja
            )
        )

        if not match:
            return ja

        return (
            ja[:match.start()]
            .strip()
        )


    # =========================================================
    # 10. JAPANESE SUFFIX
    # =========================================================

    def get_japanese_suffix(self, ja):

        ja = self.normalize_text(ja)

        match = (
            self.JAPANESE_PATTERN.search(
                ja
            )
        )

        if not match:
            return ""

        return (
            ja[match.start():]
            .strip()
        )


    # =========================================================
    # 11. TEXT SIMILARITY
    # =========================================================

    def text_similarity(self, text1, text2):

        text1 = (
            self.normalize_text(text1)
            .lower()
        )

        text2 = (
            self.normalize_text(text2)
            .lower()
        )

        if (
            not text1
            or
            not text2
        ):
            return 0.0

        return SequenceMatcher(
            None,
            text1,
            text2
        ).ratio()


    # =========================================================
    # 12. TOKEN OVERLAP
    # =========================================================

    def token_overlap(self, en, prefix):

        en_tokens = {
            token.lower()
            for token in
            self.WORD_PATTERN.findall(
                str(en)
            )
        }

        prefix_tokens = {
            token.lower()
            for token in
            self.WORD_PATTERN.findall(
                str(prefix)
            )
        }

        if (
            not en_tokens
            or
            not prefix_tokens
        ):
            return 0.0

        common = (
            en_tokens
            &
            prefix_tokens
        )

        return (
            len(common)
            /
            len(en_tokens)
        )


    # =========================================================
    # 13. LATIN INFORMATION
    # =========================================================

    def latin_info(self, en, ja):

        ja = self.normalize_text(ja)

        prefix = (
            self.get_latin_prefix(
                ja
            )
        )

        suffix = (
            self.get_japanese_suffix(
                ja
            )
        )

        latin_chars = len(
            self.LATIN_PATTERN.findall(
                ja
            )
        )

        japanese_chars = len(
            self.JAPANESE_PATTERN.findall(
                ja
            )
        )

        total_language_chars = (
            latin_chars
            +
            japanese_chars
        )

        if total_language_chars == 0:

            latin_ratio = 0.0

        else:

            latin_ratio = (
                latin_chars
                /
                total_language_chars
            )


        prefix_latin_chars = len(
            self.LATIN_PATTERN.findall(
                prefix
            )
        )


        similarity = (
            self.text_similarity(
                en,
                prefix
            )
        )


        overlap = (
            self.token_overlap(
                en,
                prefix
            )
        )


        return {
            "latin_ratio":
                latin_ratio,

            "latin_prefix_chars":
                prefix_latin_chars,

            "source_prefix_similarity":
                similarity,

            "latin_token_overlap":
                overlap,

            "japanese_suffix":
                suffix
        }


    # =========================================================
    # 14. COPIED SOURCE CANDIDATE
    # =========================================================

    def copied_source_validation(
        self,
        en,
        ja
    ):

        info = self.latin_info(
            en,
            ja
        )

        if (
            info["latin_prefix_chars"]
            < 30
        ):
            return False

        if not info[
            "japanese_suffix"
        ]:
            return False

        if (
            info[
                "source_prefix_similarity"
            ]
            >= 0.75
        ):
            return True

        if (
            info[
                "latin_token_overlap"
            ]
            >= 0.75
        ):
            return True

        return False


    # =========================================================
    # 15. UNRELATED LATIN CONTAMINATION
    # =========================================================

    def unrelated_latin_validation(
        self,
        en,
        ja
    ):

        info = self.latin_info(
            en,
            ja
        )

        if (
            info["latin_prefix_chars"]
            < 30
        ):
            return False

        if (
            info[
                "source_prefix_similarity"
            ]
            < 0.35
            and
            info[
                "latin_token_overlap"
            ]
            < 0.30
        ):

            return True

        return False


    # =========================================================
    # 16. VALIDATE SINGLE PAIR
    # =========================================================

    def validate_pair(self, en, ja):

        issues = []

        strong_issues = []


        # -----------------------------------------------------
        # HARD FAILURE
        # -----------------------------------------------------

        if self.malformed_validation(
            en,
            ja
        ):

            return {
                "validation_status":
                    "REMOVE_CANDIDATE",

                "validation_issues":
                    "empty_or_malformed_pair",

                "risk_score":
                    5
            }


        # -----------------------------------------------------
        # NO JAPANESE SCRIPT
        # -----------------------------------------------------

        if not self.contains_japanese(
            ja
        ):

            issues.append(
                "no_japanese_script"
            )


        # -----------------------------------------------------
        # ARABIC / UNEXPECTED SCRIPT
        # -----------------------------------------------------

        if self.contains_arabic(
            ja
        ):

            issues.append(
                "arabic_script_in_japanese"
            )


        # -----------------------------------------------------
        # EMOJI
        # -----------------------------------------------------

        if self.emoji_validation(
            en,
            ja
        ):

            issues.append(
                "emoji_mismatch"
            )


        # -----------------------------------------------------
        # SYMBOL
        # -----------------------------------------------------

        if self.symbol_validation(
            en,
            ja
        ):

            issues.append(
                "symbol_mismatch"
            )


        # -----------------------------------------------------
        # NUMBER
        # weak signal only
        # -----------------------------------------------------

        if self.number_validation(
            en,
            ja
        ):

            issues.append(
                "number_mismatch"
            )


        # -----------------------------------------------------
        # PERCENT
        # weak signal only
        # -----------------------------------------------------

        if self.percent_validation(
            en,
            ja
        ):

            issues.append(
                "percent_mismatch"
            )


        # -----------------------------------------------------
        # COPIED SOURCE
        # -----------------------------------------------------

        if self.copied_source_validation(
            en,
            ja
        ):

            issues.append(
                "copied_source_in_japanese"
            )


        # -----------------------------------------------------
        # UNRELATED LATIN
        # strong signal
        # -----------------------------------------------------

        if self.unrelated_latin_validation(
            en,
            ja
        ):

            strong_issues.append(
                "unrelated_latin_contamination"
            )


        # =====================================================
        # FINAL DECISION
        # =====================================================

        if strong_issues:

            all_issues = (
                issues
                +
                strong_issues
            )

            return {
                "validation_status":
                    "REMOVE_CANDIDATE",

                "validation_issues":
                    ", ".join(
                        all_issues
                    ),

                "risk_score":
                    3
            }


        if issues:

            return {
                "validation_status":
                    "REVIEW",

                "validation_issues":
                    ", ".join(
                        issues
                    ),

                "risk_score":
                    1
            }


        return {
            "validation_status":
                "KEEP",

            "validation_issues":
                "",

            "risk_score":
                0
        }


    # =========================================================
    # 17. VALIDATE DATAFRAME
    # =========================================================

    def validate_dataframe(self, df):

        validated_df = (
            df.copy()
        )

        results = []


        for _, row in (
            validated_df.iterrows()
        ):

            result = (
                self.validate_pair(
                    row["english"],
                    row["japanese"]
                )
            )

            results.append(
                result
            )


        validated_df[
            "validation_status"
        ] = [
            result[
                "validation_status"
            ]
            for result
            in results
        ]


        validated_df[
            "validation_issues"
        ] = [
            result[
                "validation_issues"
            ]
            for result
            in results
        ]


        validated_df[
            "validation_risk_score"
        ] = [
            result[
                "risk_score"
            ]
            for result
            in results
        ]


        return validated_df