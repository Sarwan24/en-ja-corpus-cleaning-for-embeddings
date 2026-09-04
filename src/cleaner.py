import re
import unicodedata
from collections import Counter

import pandas as pd


class DataCleaner:

    # =========================================================
    # REGEX PATTERNS
    # =========================================================

    JAPANESE_PATTERN = re.compile(
        r"[\u3040-\u30ff\u3400-\u9fff]"
    )

    LATIN_PATTERN = re.compile(
        r"[A-Za-z]"
    )

    FOREIGN_SCRIPT_PATTERN = re.compile(
        r"["
        r"\u0600-\u06FF"   # Arabic
        r"\u0750-\u077F"
        r"\u08A0-\u08FF"
        r"\u0400-\u04FF"   # Cyrillic
        r"\u0590-\u05FF"   # Hebrew
        r"\uAC00-\uD7AF"   # Korean
        r"]"
    )

    EMOJI_PATTERN = re.compile(
        r"[\U0001F300-\U0001FAFF"
        r"\u2600-\u26FF"
        r"\u2700-\u27BF]"
    )

    SYMBOL_PATTERN = re.compile(
        r"[©®™★☆→←↑↓✓✔✕✖♥♡♪♫"
        r"●◆◇■□▲△▼▽※]"
    )


    # =========================================================
    # 1. SAFE NORMALIZATION
    # =========================================================

    def normalize_text(self, text):

        if text is None or pd.isna(text):
            return ""

        text = str(text)

        # Safe Unicode normalization
        text = unicodedata.normalize(
            "NFC",
            text
        )

        # Zero-width junk
        text = re.sub(
            r"[\u200b\u200c\u200d\ufeff]",
            "",
            text
        )

        # Tabs/new lines
        text = re.sub(
            r"[\t\r\n]+",
            " ",
            text
        )

        # Multiple spaces
        text = re.sub( # " hello  "^{]}:;;;' .,
            r" {2,}",
            " ",
            text
        )

        return text.strip()


    # =========================================================
    # 2. BASIC SCRIPT CHECK
    # =========================================================

    def contains_japanese(self, text):

        return bool(
            self.JAPANESE_PATTERN.search(
                str(text)
            )
        )


    # =========================================================
    # 3. TEXT STATISTICS
    # =========================================================

    def text_stats(self, text):

        text = str(text)

        japanese_chars = len(
            self.JAPANESE_PATTERN.findall(
                text
            )
        )

        latin_chars = len(
            self.LATIN_PATTERN.findall(
                text
            )
        )

        digit_count = len(
            re.findall(
                r"\d",
                text
            )
        )

        foreign_chars = len(
            self.FOREIGN_SCRIPT_PATTERN.findall(
                text
            )
        )

        return {
            "japanese_chars": japanese_chars,
            "latin_chars": latin_chars,
            "digit_count": digit_count,
            "foreign_chars": foreign_chars,
            "length": len(text)
        }


    # =========================================================
    # 4. LEGACY JAPANESE-CORE HELPER (NOT USED IN clean_pair)
    # =========================================================

    def extract_japanese_core(self, text):
        """
        First Japanese character se
        last Japanese character tak content retain karega.

        Example:

        English prefix...
        日本語の文章です。
        random English suffix

        -> 日本語の文章です
        """

        text = self.normalize_text(
            text
        )

        matches = list(
            self.JAPANESE_PATTERN.finditer(
                text
            )
        )

        if not matches:
            return ""

        start = (
            matches[0].start()
        )

        end = (
            matches[-1].end()
        )

        return text[
            start:end
        ].strip()
        
    # =============================================
    # remove more latin text and save tech word,API, url,etc.        
    def remove_copied_latin_edges(
        self,
        english,
        japanese
    ):
        """
        Remove long Latin prefix/suffix from Japanese target
        only when it strongly overlaps with the English source.

        Important:
        - Valid English names/titles/technical terms are preserved.
        - Short Latin text is preserved.
        - We do NOT blindly trim everything before the first
        Japanese character.
        """

        japanese = self.normalize_text(
            japanese
        )

        if not japanese:
            return japanese, False

        matches = list(
            self.JAPANESE_PATTERN.finditer(
                japanese
            )
        )

        if not matches:
            return japanese, False


        first_japanese = matches[0].start()
        last_japanese = matches[-1].end()


        # Keep original boundaries while inspecting the edge blocks.
        # This avoids introducing artificial spaces around Japanese
        # punctuation when the text is rebuilt.
        prefix = japanese[
            :first_japanese
        ]

        core = japanese[
            first_japanese:last_japanese
        ]

        suffix = japanese[
            last_japanese:
        ]


        english_lower = (
            self.normalize_text(
                english
            ).lower()
        )

        changed = False


        # -----------------------------------------------
        # Helper: word overlap with English source
        # -----------------------------------------------

        def source_overlap(
            latin_block
        ):

            latin_words = re.findall(
                r"[A-Za-z]+",
                latin_block.lower()
            )

            if not latin_words:
                return 0.0

            source_words = set(
                re.findall(
                    r"[A-Za-z]+",
                    english_lower
                )
            )

            if not source_words:
                return 0.0

            matched_words = sum(
                1
                for word in latin_words
                if word in source_words
            )

            return (
                matched_words
                /
                len(latin_words)
            )


        # -----------------------------------------------
        # PREFIX
        # -----------------------------------------------

        prefix_latin_chars = len(
            self.LATIN_PATTERN.findall(
                prefix
            )
        )

        prefix_overlap = source_overlap(
            prefix
        )

        prefix_word_count = len(
            re.findall(
                r"[A-Za-z]+",
                prefix
            )
        )

        prefix_has_title_markers = (
            ("「" in prefix and "」" in prefix)
            or
            ("『" in prefix and "』" in prefix)
        )


        # Remove only a clearly sentence/paragraph-like copied prefix.
        # Japanese title markers protect legitimate English titles.
        # Product/technical phrases are also protected by requiring
        # a reasonably large word count.

        if (
            prefix_latin_chars >= 60
            and
            prefix_word_count >= 12
            and
            (
                prefix_overlap >= 0.50
                or
                prefix_latin_chars >= 150
            )
        ):

            prefix = ""
            changed = True

        # -----------------------------------------------
        # SUFFIX
        # -----------------------------------------------

        suffix_latin_chars = len(
            self.LATIN_PATTERN.findall(
                suffix
            )
        )

        suffix_overlap = source_overlap(
            suffix
        )

        suffix_word_count = len(
            re.findall(
                r"[A-Za-z]+",
                suffix
            )
        )

        suffix_has_title_markers = (
            ("「" in suffix and "」" in suffix)
            or
            ("『" in suffix and "』" in suffix)
        )


        if (
            suffix_latin_chars >= 60
            and
            suffix_word_count >= 12
            and
            (
                suffix_overlap >= 0.50
                or
                suffix_latin_chars >= 150
            )
        ):

            suffix = ""
            changed = True
                

            
        # -----------------------------------------------
        # REBUILD TARGET
        # -----------------------------------------------
        # Direct concatenation preserves the original punctuation
        # boundaries. normalize_text() handles any leftover spacing.

        cleaned = self.normalize_text(
            prefix
            +
            core
            +
            suffix
        )


        return cleaned, changed


    # =========================================================
    # 5. REMOVE FOREIGN SCRIPT
    # =========================================================

    def remove_foreign_scripts(self, text):

        cleaned = (
            self.FOREIGN_SCRIPT_PATTERN.sub(
                "",
                str(text)
            )
        )

        cleaned = re.sub(
            r" {2,}",
            " ",
            cleaned
        )

        return self.normalize_text(
            cleaned
        )


    # =========================================================
    # 6. EMOJI / SYMBOL CORRESPONDENCE
    # =========================================================

    def remove_unmatched_items(
        self,
        en,
        ja,
        pattern
    ):

        en = self.normalize_text(
            en
        )

        ja = self.normalize_text(
            ja
        )

        en_items = (
            pattern.findall(en)
        )

        ja_items = (
            pattern.findall(ja)
        )

        if (
            not en_items
            and
            not ja_items
        ):

            return (
                en,
                ja,
                False
            )


        # Common items and common frequency
        common_counter = (
            Counter(en_items)
            &
            Counter(ja_items)
        )


        def clean_side(text):

            keep_remaining = (
                dict(
                    common_counter
                )
            )

            output = []

            for char in text:

                if (
                    pattern.fullmatch(
                        char
                    )
                ):

                    if (
                        keep_remaining.get(
                            char,
                            0
                        )
                        >
                        0
                    ):

                        output.append(
                            char
                        )

                        keep_remaining[
                            char
                        ] -= 1

                    # unmatched item -> skip

                else:

                    output.append(
                        char
                    )


            return self.normalize_text(
                "".join(output)
            )


        clean_en = clean_side(
            en
        )

        clean_ja = clean_side(
            ja
        )

        changed = (
            clean_en != en
            or
            clean_ja != ja
        )


        return (
            clean_en,
            clean_ja,
            changed
        )


    # =========================================================
    # 7. VERY SHORT / MEANINGLESS JAPANESE
    # =========================================================

    def insufficient_japanese(self, text):
        """
        Reject targets with almost no Japanese script.

        We intentionally do NOT use a Japanese/total-length ratio here.
        Valid Japanese can contain long English titles, product names,
        APIs or technical terms. Ratio-based removal caused useful
        mixed-language training examples to be discarded.
        """

        stats = self.text_stats(
            text
        )

        japanese_chars = (
            stats["japanese_chars"]
        )

        # Fewer than 3 Japanese-script characters is too weak
        # for this EN-JA target corpus.
        if japanese_chars < 3:
            return True

        return False


    # =========================================================
    # 8. EXCESSIVE LATIN CONTENT
    # =========================================================

    def excessive_latin(
        self,
        text
    ):
        """
        Detect only EXTREME Latin-dominant Japanese targets.

        Important:
        - Normal Latin terms such as API, Windows, product names,
          person names and English titles inside Japanese are valid.
        - Copied English prefixes/suffixes are handled separately by
          remove_copied_latin_edges().
        - Therefore this rule is intentionally conservative to avoid
          unnecessary information loss in language-model training data.
        """

        stats = self.text_stats(
            text
        )

        japanese_chars = (
            stats["japanese_chars"]
        )

        latin_chars = (
            stats["latin_chars"]
        )

        if japanese_chars == 0:
            return True

        language_chars = (
            japanese_chars
            +
            latin_chars
        )

        if language_chars == 0:
            return False

        japanese_ratio = (
            japanese_chars
            /
            language_chars
        )

        # Only remove very extreme mixed targets here.
        # Moderate mixed-script rows are preserved because they may
        # contain useful names, titles, code/API terms or products.
        if (
            latin_chars >= 120
            and
            japanese_ratio < 0.05
        ):
            return True

        return False


    # =========================================================
    # 9. EXCESSIVE NUMERIC NOISE
    # =========================================================

    def excessive_numbers(
        self,
        text
    ):

        text = str(text)

        stats = self.text_stats(
            text
        )

        digit_count = (
            stats["digit_count"]
        )

        total_length = max(
            stats["length"],
            1
        )

        digit_ratio = (
            digit_count
            /
            total_length
        )


        # Very long continuous digit garbage:
        #
        # 181920212223242526...
        if re.search(
            r"\d{12,}",
            text
        ):

            return True


        number_tokens = re.findall(
            r"\d+",
            text
        )


        # Large amount of numeric content
        if (
            digit_count >= 20
            and
            digit_ratio >= 0.20
        ):

            return True


        # Many separate numeric groups
        if (
            len(number_tokens) >= 12
            and
            digit_count >= 20
        ):

            return True


        return False


    # =========================================================
    # 10. EXCESSIVE SYMBOL / ASCII GARBAGE
    # =========================================================

    def excessive_symbol_noise(
        self,
        text
    ):

        text = str(text)

        if not text:
            return True


        # Normal Japanese punctuation.
        # Inko noise/symbol count me include nahi karenge.
        safe_japanese_punctuation = set(
            "。、！？「」『』（）【】［］〈〉《》・：；〜…"
        )


        symbol_count = 0


        for char in text:

            # Valid Japanese punctuation ko preserve karo
            if char in safe_japanese_punctuation:
                continue


            category = unicodedata.category(
                char
            )


            if (
                category.startswith("P")
                or
                category.startswith("S")
            ):
                symbol_count += 1


        total_length = max(
            len(text),
            1
        )


        symbol_ratio = (
            symbol_count
            /
            total_length
        )


        # -----------------------------------------------------
        # Long continuous garbage / ASCII-art section
        #
        # Examples:
        # =======////^^^^<<<<>>>>
        # ________********
        # -----------------------------------------------------

        repeated_noise = bool(
            re.search(
                r"[^A-Za-z0-9"
                r"\u3040-\u30ff"
                r"\u3400-\u9fff"
                r"\s。、！？「」『』（）【】［］〈〉《》・：；〜…"
                r"]{8,}",
                text
            )
        )


        # -----------------------------------------------------
        # Excessive symbol-heavy text
        # -----------------------------------------------------

        if (
            symbol_count >= 12
            and
            symbol_ratio >= 0.35
        ):
            return True


        # -----------------------------------------------------
        # Continuous ASCII / symbol garbage
        # -----------------------------------------------------

        if repeated_noise:
            return True


        return False



    # =========================================================
    # 11. FINAL POST-CLEAN VALIDATION
    # =========================================================

    def post_clean_validation(
        self,
        en,
        ja
    ):
        """
        Cleaning complete hone ke baad final safety check.

        Returns:
            (valid, reason)
        """

        en = self.normalize_text(
            en
        )

        ja = self.normalize_text(
            ja
        )


        if not en:

            return (
                False,
                "empty_english_after_cleaning"
            )


        if not ja:

            return (
                False,
                "empty_japanese_after_cleaning"
            )


        if not self.contains_japanese(
            ja
        ):

            return (
                False,
                "no_japanese_script_after_cleaning"
            )


        if self.insufficient_japanese(
            ja
        ):

            return (
                False,
                "insufficient_japanese_after_cleaning"
            )


        if self.excessive_latin(
            ja
        ):

            return (
                False,
                "excessive_latin_after_cleaning"
            )


        if self.excessive_numbers(
            ja
        ):

            return (
                False,
                "excessive_numeric_noise_after_cleaning"
            )


        if self.excessive_symbol_noise(
            ja
        ):

            return (
                False,
                "excessive_symbol_noise_after_cleaning"
            )


        remaining_foreign = (
            self.FOREIGN_SCRIPT_PATTERN.search(
                ja
            )
        )


        if remaining_foreign:

            return (
                False,
                "foreign_script_after_cleaning"
            )


        return (
            True,
            ""
        )

    # ==========================================================
    # remove repeated word like web xx sometings
    # ===========================================================

    def has_excessive_repeated_tokens(
        self,
        text,
        min_repeats=8
    ):
        """
        Detect repeated-token flooding such as:

        WEB WEB WEB WEB WEB WEB...
        X X X X X X X X...
        hello hello hello hello...

        Returns True when the same token repeats
        consecutively too many times.
        """

        if not text:
            return False

        tokens = re.findall(
            r"[A-Za-z0-9]+",
            text.lower()
        )

        if not tokens:
            return False

        repeat_count = 1

        for i in range(
            1,
            len(tokens)
        ):

            if tokens[i] == tokens[i - 1]:

                repeat_count += 1

                if repeat_count >= min_repeats:
                    return True

            else:
                repeat_count = 1

        return False


    # =========================================================
    # 12. CLEAN SINGLE PAIR
    # =========================================================

    def clean_pair(
        self,
        en,
        ja
    ):

        original_en = (
            self.normalize_text(
                en
            )
        )

        original_ja = (
            self.normalize_text(
                ja
            )
        )

        clean_en = original_en
        clean_ja = original_ja

        actions = []


        # -----------------------------------------------------
        # EMPTY PAIR
        # -----------------------------------------------------

        if (
            not clean_en
            or
            not clean_ja
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "empty_or_malformed_pair"
            }


        # -----------------------------------------------------
        # EXCESSIVE REPEATED TOKEN FLOODING
        # -----------------------------------------------------
        # Examples:
        # WEB WEB WEB WEB WEB...
        # X X X X X X X X...
        # hello hello hello hello...

        if (
            self.has_excessive_repeated_tokens(
                clean_en
            )
            or
            self.has_excessive_repeated_tokens(
                clean_ja
            )
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "excessive_repeated_tokens"
            }


        # -----------------------------------------------------
        # PURE ENGLISH / NO JAPANESE
        # -----------------------------------------------------

        if not self.contains_japanese(
            clean_ja
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "no_japanese_script"
            }


        # -----------------------------------------------------
        # SOURCE-AWARE LATIN EDGE CLEANING
        # -----------------------------------------------------

        clean_ja, removed_copied_edge = (
            self.remove_copied_latin_edges(
                clean_en,
                clean_ja
            )
        )

        if removed_copied_edge:

            actions.append(
                "removed_copied_latin_edge"
            )


        # -----------------------------------------------------
        # REMOVE FOREIGN SCRIPTS
        # -----------------------------------------------------

        foreign_cleaned = (
            self.remove_foreign_scripts(
                clean_ja
            )
        )

        if foreign_cleaned != clean_ja:

            clean_ja = foreign_cleaned

            actions.append(
                "removed_foreign_script"
            )


        # -----------------------------------------------------
        # EXCESSIVE REPEATED CHARACTER NOISE
        # -----------------------------------------------------

        if self.excessive_repeated_characters(
            clean_ja
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "excessive_repeated_characters"
            }


        # -----------------------------------------------------
        # EMOJI CORRESPONDENCE
        # -----------------------------------------------------

        (
            clean_en,
            clean_ja,
            emoji_changed

        ) = self.remove_unmatched_items(
            clean_en,
            clean_ja,
            self.EMOJI_PATTERN
        )

        if emoji_changed:

            actions.append(
                "removed_unmatched_emoji"
            )


        # -----------------------------------------------------
        # SPECIAL SYMBOL CORRESPONDENCE
        # -----------------------------------------------------

        (
            clean_en,
            clean_ja,
            symbol_changed

        ) = self.remove_unmatched_items(
            clean_en,
            clean_ja,
            self.SYMBOL_PATTERN
        )

        if symbol_changed:

            actions.append(
                "removed_unmatched_symbol"
            )


        # -----------------------------------------------------
        # BASIC CLEANING FILTERS
        # -----------------------------------------------------

        if self.insufficient_japanese(
            clean_ja
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "insufficient_japanese_content"
            }


        if self.excessive_latin(
            clean_ja
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "excessive_latin_in_japanese"
            }


        if self.excessive_numbers(
            clean_ja
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "excessive_numeric_noise"
            }


        if self.excessive_symbol_noise(
            clean_ja
        ):
            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    "excessive_symbol_noise"
            }


        # -----------------------------------------------------
        # FINAL POST-CLEAN VALIDATION
        # -----------------------------------------------------

        (
            valid_after_cleaning,
            validation_reason

        ) = self.post_clean_validation(
            clean_en,
            clean_ja
        )

        if not valid_after_cleaning:

            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "REMOVE",
                "cleaning_reason":
                    validation_reason
            }


        # -----------------------------------------------------
        # FINAL STATUS
        # -----------------------------------------------------

        if actions:

            return {
                "clean_english": clean_en,
                "clean_japanese": clean_ja,
                "cleaning_status": "CLEAN",
                "cleaning_reason":
                    ", ".join(
                        actions
                    )
            }


        return {
            "clean_english": clean_en,
            "clean_japanese": clean_ja,
            "cleaning_status": "KEEP",
            "cleaning_reason": ""
        }

    # ========================================================
    # 13. Clean Same Character repeated many time
    # =========================================================

    def excessive_repeated_characters(self, text):
    
        """
        Detect excessive repetition of the same character.

        Example:
            ぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇ...
            !!!!!!!!!!...
            ああああああああああああ...

        Normal expressive repetition is preserved.
        """

        if not text:
            return False

        repeated_pattern = re.compile(
            r"(.)\1{19,}"
        )

        return bool(
            repeated_pattern.search(text)
        )
    
    
    

    # =========================================================
    # 14. CLEAN FULL DATAFRAME
    # =========================================================

    def clean_dataframe(
        self,
        df
    ):

        cleaned_df = (
            df.copy()
        )

        results = []


        for _, row in (
            cleaned_df.iterrows()
        ):

            result = (
                self.clean_pair(
                    row["english"],
                    row["japanese"]
                )
            )

            results.append(
                result
            )


        cleaned_df[
            "clean_english"
        ] = [
            result[
                "clean_english"
            ]
            for result
            in results
        ]


        cleaned_df[
            "clean_japanese"
        ] = [
            result[
                "clean_japanese"
            ]
            for result
            in results
        ]


        cleaned_df[
            "cleaning_status"
        ] = [
            result[
                "cleaning_status"
            ]
            for result
            in results
        ]


        cleaned_df[
            "cleaning_reason"
        ] = [
            result[
                "cleaning_reason"
            ]
            for result
            in results
        ]


        return cleaned_df


    # =========================================================
    # 15. PAIR-LEVEL DEDUPLICATION
    # =========================================================

    def remove_duplicate_pairs(
        self,
        df
    ):

        before = len(
            df
        )

        cleaned_df = (
            df.drop_duplicates(
                subset=[
                    "clean_english",
                    "clean_japanese"
                ],
                keep="first"
            )
            .copy()
        )


        removed = (
            before
            -
            len(cleaned_df)
        )


        return (
            cleaned_df,
            removed
        )


    # =========================================================
    # 16. POST-CLEAN DATAFRAME REPORT
    # =========================================================

    def post_clean_summary(
        self,
        df
    ):

        print(
            "\n"
            + "=" * 100
        )

        print(
            "POST-CLEAN QUALITY CHECK"
        )

        print(
            "=" * 100
        )


        usable_df = df[
            df["cleaning_status"]
            !=
            "REMOVE"
        ]


        no_japanese = 0
        excessive_latin = 0
        numeric_noise = 0
        symbol_noise = 0
        foreign_script = 0


        for _, row in (
            usable_df.iterrows()
        ):

            ja = row[
                "clean_japanese"
            ]


            if not self.contains_japanese(
                ja
            ):

                no_japanese += 1


            if self.excessive_latin(
                ja
            ):

                excessive_latin += 1


            if self.excessive_numbers(
                ja
            ):

                numeric_noise += 1


            if self.excessive_symbol_noise(
                ja
            ):

                symbol_noise += 1


            if (
                self.FOREIGN_SCRIPT_PATTERN.search(
                    str(ja)
                )
            ):

                foreign_script += 1


        print(
            "Usable Records               :",
            len(usable_df)
        )

        print(
            "JA without Japanese script   :",
            no_japanese
        )

        print(
            "JA excessive Latin           :",
            excessive_latin
        )

        print(
            "JA excessive numeric noise   :",
            numeric_noise
        )

        print(
            "JA excessive symbol noise    :",
            symbol_noise
        )

        print(
            "JA remaining foreign script  :",
            foreign_script
        )