from itertools import zip_longest

from pathlib import Path

from config.config import EN_FILE, JA_FILE, PROJECT_ROOT


# ============================================================
# SETTINGS
# ============================================================

TEST_SIZE = 500_000

TEST_DIR = (
    PROJECT_ROOT
    / "data"
    / "test"
    / "raw"
)

TEST_EN_FILE = TEST_DIR / "test.en"
TEST_JA_FILE = TEST_DIR / "test.ja"


# ============================================================
# CREATE TEST SUBSET
# ============================================================

def create_test_subset():

    TEST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\n" + "=" * 80)
    print("CREATING TEST SUBSET")
    print("=" * 80)

    print("Source EN :", EN_FILE)
    print("Source JA :", JA_FILE)

    print(
        "Test Size :",
        f"{TEST_SIZE:,}"
    )

    written = 0

    with open(
        EN_FILE,
        "r",
        encoding="utf-8"
    ) as en_file, open(
        JA_FILE,
        "r",
        encoding="utf-8"
    ) as ja_file, open(
        TEST_EN_FILE,
        "w",
        encoding="utf-8"
    ) as test_en, open(
        TEST_JA_FILE,
        "w",
        encoding="utf-8"
    ) as test_ja:

        for record_no, (
            english,
            japanese
        ) in enumerate(

            zip_longest(
                en_file,
                ja_file,
                fillvalue=None
            ),

            start=1
        ):

            # Alignment protection
            if (
                english is None
                or japanese is None
            ):

                raise ValueError(
                    f"EN-JA alignment mismatch "
                    f"at record {record_no:,}"
                )

            test_en.write(
                english
            )

            test_ja.write(
                japanese
            )

            written += 1

            if written >= TEST_SIZE:
                break

    print(
        "\nTest subset created successfully."
    )

    print(
        "Records :",
        f"{written:,}"
    )

    print(
        "EN file :",
        TEST_EN_FILE
    )

    print(
        "JA file :",
        TEST_JA_FILE
    )

    print("=" * 80)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    create_test_subset()