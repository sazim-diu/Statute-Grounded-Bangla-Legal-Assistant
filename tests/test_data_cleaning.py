from backend.retrieval.data_cleaning import (
    MISSING_TITLE,
    PLACEHOLDER_TEXT,
    clean_chunks,
    is_valid_chapter,
    normalise_section_number,
)


def chunk(number, title, body, chapter="প্রথম অধ্যায় (প্রারম্ভিক)", **extra):
    return {
        "id": f"sec_{number}", "section_number": number, "section_title": title,
        "chapter": chapter, "raw_body": body, "legal_status": "সক্রিয় (Active)",
        "amendment_provenance": "x", **extra,
    }


def test_trailing_next_title_is_removed_but_text_is_kept():
    data = [
        chunk("১", "প্রথম শিরোনাম", "১। প্রথম ধারার পাঠ।\nদ্বিতীয় শিরোনাম"),
        chunk("২", "দ্বিতীয় শিরোনাম", "২। দ্বিতীয় ধারার পাঠ।"),
    ]
    records, report = clean_chunks(data)
    assert records[0]["text"] == "১। প্রথম ধারার পাঠ।"
    assert "trailing_next_title_removed" in records[0]["flags"]
    assert records[1]["text"] == "২। দ্বিতীয় ধারার পাঠ।"
    assert report["flag_counts"]["trailing_next_title_removed"] == 1


def test_real_text_is_never_dropped_when_last_line_is_not_next_title():
    data = [chunk("১", "ক", "১। পাঠ\nশেষ লাইন"), chunk("২", "খ", "২। পাঠ")]
    records, _ = clean_chunks(data)
    assert records[0]["text"] == "১। পাঠ\nশেষ লাইন"


def test_garbage_chapter_replaced_by_previous_valid_chapter():
    data = [
        chunk("১", "ক", "১। পাঠ", chapter="দ্বিতীয় অধ্যায় (নিয়োগ)"),
        chunk("২", "খ", "২। পাঠ", chapter="১৭৬৷ এই অধ্যায়ের বিধান সাপেক্ষে- ((ক) ..."),
        chunk("৩", "গ", "৩। পাঠ", chapter="অধ্যায়ের প্রয়োগ (284)"),
    ]
    records, _ = clean_chunks(data)
    assert records[1]["chapter"] == "দ্বিতীয় অধ্যায় (নিয়োগ)"
    assert records[2]["chapter"] == "দ্বিতীয় অধ্যায় (নিয়োগ)"
    assert "chapter_inferred" in records[1]["flags"]


def test_valid_chapter_detection():
    assert is_valid_chapter("একবিংশ অধ্যায় (বিবিধ)")
    assert is_valid_chapter("[ ষোড়শ-ক অধ্যায় (বিলুপ্ত ডক-শ্রমিক)")
    assert not is_valid_chapter("২৮৬৷ (১) কোন মালিক চতুর্থ অধ্যায়ের (322)")
    assert not is_valid_chapter("অধ্যায়ের প্রয়োগ")


def test_last_section_of_a_chapter_gets_its_own_chapter_back():
    # the chunker labelled section ৪৪ with chapter 4 and left chapter 4's subtitle at its end
    data = [
        chunk("৪৩", "ক", "৪৩। পাঠ", chapter="তৃতীয় অধ্যায় (কিশোর শ্রমিক নিয়োগ)"),
        chunk("৪৪", "খ", "৪৪। পাঠ\nপ্রসূতি কল্যাণ সুবিধা", chapter="চতুর্থ অধ্যায় (প্রসূতি কল্যাণ সুবিধা)"),
        chunk("৪৫", "গ", "৪৫। পাঠ", chapter="চতুর্থ অধ্যায় (প্রসূতি কল্যাণ সুবিধা)"),
    ]
    records, report = clean_chunks(data)
    assert records[1]["chapter"] == "তৃতীয় অধ্যায় (কিশোর শ্রমিক নিয়োগ)"
    assert records[1]["text"] == "৪৪। পাঠ"
    assert "chapter_boundary_fixed" in records[1]["flags"]
    assert records[2]["chapter"] == "চতুর্থ অধ্যায় (প্রসূতি কল্যাণ সুবিধা)"
    assert report["flag_counts"]["chapter_boundary_fixed"] == 1


def test_title_recovered_from_end_of_previous_section():
    data = [
        chunk("৪৩", "ক", "৪৩। পাঠ\nকতিপয় ক্ষেত্রে নিয়োগে বিধি-নিষেধ\n92"),
        chunk("৪৪", "92", "৪৪। প্রতিবন্ধী শ্রমিক নিয়োগ করা যাইবে না।"),
    ]
    records, report = clean_chunks(data)
    assert records[0]["text"] == "৪৩। পাঠ"
    assert records[1]["title"] == "কতিপয় ক্ষেত্রে নিয়োগে বিধি-নিষেধ"
    assert "title_recovered" in records[1]["flags"]
    assert report["flag_counts"]["title_recovered"] == 1


def test_both_unicode_spellings_of_yo_are_accepted():
    precomposed = "দ্বিতীয় \u0985\u09a7\u09cd\u09af\u09be\u09df (নিয়োগ)"  # য় as U+09DF
    decomposed = "দ্বিতীয় \u0985\u09a7\u09cd\u09af\u09be\u09af\u09bc (নিয়োগ)"  # য + ় 
    assert is_valid_chapter(precomposed)
    assert is_valid_chapter(decomposed)


def test_numeric_title_flagged():
    records, _ = clean_chunks([chunk("৪৪", "92", "৪৪। পাঠ")])
    assert records[0]["title"] == MISSING_TITLE
    assert "title_missing" in records[0]["flags"]


def test_duplicate_section_number_not_indexed():
    data = [chunk("৭", "ক", "৭। প্রথম"), chunk("৮", "খ", "৮। পাঠ"), chunk("৭", "গ", "৭। ভুল টুকরা")]
    records, report = clean_chunks(data)
    assert records[0]["is_indexed"] is True
    assert records[2]["is_indexed"] is False
    assert "duplicate_section_number" in records[2]["flags"]
    assert report["not_indexed_records"] == 1


def test_generated_placeholder_is_not_indexed_and_text_is_neutral():
    data = [
        chunk("১", "ক", "১। পাঠ"),
        chunk("২৫৩", "ডক-শ্রমিক (ধারাটি বিলুপ্ত)", "বানানো টেক্সট", chapter="পঞ্চদশ অধ্যায় (বিলুপ্ত)"),
    ]
    records, _ = clean_chunks(data)
    assert records[1]["is_indexed"] is False
    assert records[1]["text"] == PLACEHOLDER_TEXT
    assert "বানানো" not in records[1]["text"]


def test_missing_section_numbers_reported():
    data = [chunk("১", "ক", "১।"), chunk("২", "খ", "২।"), chunk("৪", "ঘ", "৪।")]
    _, report = clean_chunks(data)
    assert report["section_numbers_missing_from_source_parse"] == ["৩"]


def test_normalise_section_number():
    assert normalise_section_number(" 108 ") == "১০৮"
    assert normalise_section_number("৩ক") == "৩ক"
