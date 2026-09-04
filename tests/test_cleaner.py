import pytest

from src.cleaner import DataCleaner


@pytest.fixture
def cleaner():
    return DataCleaner()


def test_pure_english_target_should_remove(cleaner):

    result = cleaner.clean_pair(
        "This is a simple English sentence.",
        "This is also English only."
    )

    assert result["cleaning_status"] == "REMOVE"
    assert result["cleaning_reason"] == "no_japanese_script"


def test_valid_mixed_title_should_keep(cleaner):

    en = (
        "Toby Keith releases "
        "A Little Less Talk And A Lot More Action."
    )

    ja = (
        "Toby Keith "
        "「A Little Less Talk And A Lot More Action」"
        "を配信！"
    )

    result = cleaner.clean_pair(en, ja)

    assert result["cleaning_status"] != "REMOVE"
    assert "Toby Keith" in result["clean_japanese"]


def test_copied_english_prefix_should_be_cleaned(cleaner):

    en = (
        "Because thou art lukewarm, "
        "and neither cold nor hot, "
        "I will spew thee out of my mouth."
    )

    ja = (
        "Because thou art lukewarm, "
        "and neither cold nor hot, "
        "I will spew thee out of my mouth. "
        "あなたは冷たくもなく熱くもないので、"
        "私はあなたを口から吐き出す。"
    )

    result = cleaner.clean_pair(en, ja)

    assert result["cleaning_status"] == "CLEAN"
    assert (
        "removed_copied_latin_edge"
        in result["cleaning_reason"]
    )
    assert result["clean_japanese"] != ja


def test_technical_latin_content_should_be_preserved(cleaner):

    en = (
        "Update 1910 for Microsoft Endpoint "
        "Configuration Manager current branch "
        "is now available."
    )

    ja = (
        "Update 1910 for Microsoft Endpoint "
        "Configuration Manager current branch "
        "が利用可能になりました。"
    )

    result = cleaner.clean_pair(en, ja)

    assert result["cleaning_status"] != "REMOVE"


def test_excessive_repeated_characters_should_remove(cleaner):

    result = cleaner.clean_pair(
        "This is extremely noisy.",
        "うるせぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇぇ！"
    )

    assert result["cleaning_status"] == "REMOVE"
    assert (
        result["cleaning_reason"]
        ==
        "excessive_repeated_characters"
    )


def test_valid_japanese_punctuation_should_not_remove(cleaner):

    en = (
        "Who made this? "
        "It was heaven and earth."
    )

    ja = (
        "孰（たれ）か此（こ）れを為（な）す者（もの）ぞ、"
        "天地（てんち）なり。"
    )

    result = cleaner.clean_pair(en, ja)

    assert result["cleaning_status"] != "REMOVE"


def test_foreign_script_should_be_removed(cleaner):

    result = cleaner.clean_pair(
        "This is a Japanese translation.",
        "مرحباこれは日本語の文章です。"
    )

    assert result["cleaning_status"] == "CLEAN"
    assert (
        "removed_foreign_script"
        in result["cleaning_reason"]
    )
    assert "مرحبا" not in result["clean_japanese"]


def test_excessive_numeric_noise_should_remove(cleaner):

    result = cleaner.clean_pair(
        "Numeric garbage example.",
        "日本語 123456789012345678901234567890"
    )

    assert result["cleaning_status"] == "REMOVE"
    assert (
        result["cleaning_reason"]
        ==
        "excessive_numeric_noise"
    )