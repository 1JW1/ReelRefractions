"""Tests for pure functions in new_post.py.

Covers format_front_matter, format_body, and extract_doc_id.
External dependencies (anthropic, Google APIs) are stubbed in conftest.py.
"""
import pytest
import yaml

from new_post import (
    _REVIEW_TYPE_TO_CATEGORY,
    extract_doc_id,
    format_body,
    format_front_matter,
)

TODAY = "2026-02-26"


def _parse(output: str) -> dict:
    """Parse the first YAML document from front matter output.

    Uses safe_load_all because format_front_matter produces two YAML document
    markers (opening and closing ---), which safe_load rejects as a multi-doc
    stream. safe_load_all reads them correctly.
    """
    return next(yaml.safe_load_all(output))


def _base_meta(**overrides: object) -> dict:
    """Return a fully populated meta dict, optionally overriding specific fields."""
    meta = {
        "title": "Test Film (2024)",
        "slug": "test-film-2024",
        "description": "A tense, stylish film that loses its nerve.",
        "summary": "Style over substance, but the style is very good.",
        "tags": ["Crime", "Director Name", "Lead Actor"],
        "cover_alt": "A moody promotional still with the lead actor in shadow.",
        "review_type": "new-release",
        "refraction_quote": "It dazzles until it doesn't.",
        "genre_lineage": [],
        "rating": "3 / 5",
        "spoiler": False,
    }
    meta.update(overrides)
    return meta


# ---------------------------------------------------------------------------
# format_front_matter — YAML validity
# ---------------------------------------------------------------------------


def test_output_is_valid_yaml():
    """The full output must be parseable as YAML without errors."""
    meta = _base_meta(
        genre_lineage=[
            {"title": "Heat (1995)", "note": "same kinetic dread"},
            {"title": "Sicario (2015)", "note": "violence with weight"},
        ]
    )
    output = format_front_matter(meta, "cover.jpg", TODAY)
    parsed = _parse(output)
    assert isinstance(parsed, dict)
    assert parsed["title"] == "Test Film (2024)"


def test_all_required_keys_present():
    """Every front matter field used by Hugo templates must be present."""
    parsed = _parse(format_front_matter(_base_meta(), "cover.jpg", TODAY))
    required = [
        "title", "date", "draft", "slug", "author", "description",
        "tags", "categories", "showToc", "cover", "letterboxd_url",
        "summary", "rating", "spoiler", "review_type",
        "refraction_quote", "genre_lineage",
    ]
    for key in required:
        assert key in parsed, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# format_front_matter — spoiler boolean
# ---------------------------------------------------------------------------


def test_spoiler_true_outputs_lowercase_true():
    """spoiler: True must render as 'spoiler: true', not 'spoiler: True'."""
    output = format_front_matter(_base_meta(spoiler=True), "cover.jpg", TODAY)
    assert "spoiler: true" in output
    assert "spoiler: True" not in output


def test_spoiler_false_outputs_lowercase_false():
    """spoiler: False must render as 'spoiler: false', not 'spoiler: False'."""
    output = format_front_matter(_base_meta(spoiler=False), "cover.jpg", TODAY)
    assert "spoiler: false" in output
    assert "spoiler: False" not in output


def test_spoiler_parses_as_python_bool():
    """yaml.safe_load must return a bool, not a string."""
    parsed = _parse(format_front_matter(_base_meta(spoiler=True), "cover.jpg", TODAY))
    assert parsed["spoiler"] is True
    assert isinstance(parsed["spoiler"], bool)


# ---------------------------------------------------------------------------
# format_front_matter — review_type → categories mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "review_type, expected_category",
    list(_REVIEW_TYPE_TO_CATEGORY.items()),
)
def test_review_type_maps_to_correct_category(review_type: str, expected_category: str):
    """Each review_type must produce the correct Hugo category."""
    parsed = _parse(
        format_front_matter(_base_meta(review_type=review_type), "cover.jpg", TODAY)
    )
    assert parsed["categories"] == [expected_category], (
        f"review_type '{review_type}' should map to '{expected_category}', "
        f"got {parsed['categories']}"
    )


# ---------------------------------------------------------------------------
# format_front_matter — refraction_quote escaping
# ---------------------------------------------------------------------------


def test_refraction_quote_with_double_quotes_produces_valid_yaml():
    """A refraction_quote containing double-quote characters must not break YAML."""
    meta = _base_meta(
        refraction_quote='He said "I quit" and meant it for the first time.'
    )
    parsed = _parse(format_front_matter(meta, "cover.jpg", TODAY))
    assert "quit" in parsed["refraction_quote"]


def test_summary_with_double_quotes_produces_valid_yaml():
    """A summary containing double-quote characters must not break YAML."""
    meta = _base_meta(summary='A film about "truth" wrapped in lies.')
    parsed = _parse(format_front_matter(meta, "cover.jpg", TODAY))
    assert "truth" in parsed["summary"]


# ---------------------------------------------------------------------------
# format_front_matter — genre_lineage
# ---------------------------------------------------------------------------


def test_genre_lineage_empty_outputs_empty_list():
    """An empty genre_lineage must render so YAML parses it as an empty list."""
    output = format_front_matter(_base_meta(genre_lineage=[]), "cover.jpg", TODAY)
    assert "genre_lineage: []" in output
    parsed = _parse(output)
    assert parsed["genre_lineage"] in ([], None)


def test_genre_lineage_with_entries_produces_valid_yaml():
    """Two genre_lineage entries must parse into a list of dicts with title and note."""
    meta = _base_meta(
        genre_lineage=[
            {"title": "Heat (1995)", "note": "same kinetic dread"},
            {"title": "Thief (1981)", "note": "Mann's own blueprint"},
        ]
    )
    parsed = _parse(format_front_matter(meta, "cover.jpg", TODAY))
    assert isinstance(parsed["genre_lineage"], list)
    assert len(parsed["genre_lineage"]) == 2
    assert parsed["genre_lineage"][0]["title"] == "Heat (1995)"
    assert parsed["genre_lineage"][1]["note"] == "Mann's own blueprint"


def test_genre_lineage_double_quotes_in_note_escaped():
    """Double quotes inside genre_lineage note must be escaped to keep YAML valid."""
    meta = _base_meta(
        genre_lineage=[{"title": "Film (2000)", "note": 'note with "quotes" inside'}]
    )
    parsed = _parse(format_front_matter(meta, "cover.jpg", TODAY))
    assert len(parsed["genre_lineage"]) == 1
    assert "quotes" in parsed["genre_lineage"][0]["note"]


# ---------------------------------------------------------------------------
# format_front_matter — single_image
# ---------------------------------------------------------------------------


def test_single_image_appears_in_cover_block():
    """When single_image is provided, singleImage must appear in the output."""
    output = format_front_matter(
        _base_meta(), "listing.jpg", TODAY, single_image="hero.jpg"
    )
    assert 'singleImage: "hero.jpg"' in output


def test_no_single_image_omits_singleImage_key():
    """When single_image is omitted, singleImage must not appear in the output."""
    output = format_front_matter(_base_meta(), "listing.jpg", TODAY)
    assert "singleImage" not in output


# ---------------------------------------------------------------------------
# format_front_matter — known issues (documented, not bugs to fix here)
# ---------------------------------------------------------------------------


def test_empty_tags_list_parses_as_none():
    """Empty tags list renders as 'tags:' with blank content, which YAML reads as None.

    This is a known issue — Hugo templates should guard with `if .Params.tags`.
    """
    parsed = _parse(format_front_matter(_base_meta(tags=[]), "cover.jpg", TODAY))
    assert parsed["tags"] is None


def test_double_quotes_in_title_break_yaml():
    """Double quotes in title are not escaped, which breaks YAML parsing.

    This documents a known issue. Film titles with embedded quotes (rare) would
    cause Hugo build failures. A future fix should apply replace('\"', '\\\\"') to title.
    """
    meta = _base_meta(title='A Film "Subtitle" (2024)')
    output = format_front_matter(meta, "cover.jpg", TODAY)
    with pytest.raises(yaml.YAMLError):
        _parse(output)


# ---------------------------------------------------------------------------
# format_body
# ---------------------------------------------------------------------------


def test_format_body_no_images_joins_paragraphs():
    """Without secondary images, paragraphs are joined by double newlines."""
    body = "Para one.\n\nPara two.\n\nPara three."
    assert format_body(body, []) == "Para one.\n\nPara two.\n\nPara three."


def test_format_body_strips_extra_whitespace():
    """Leading/trailing whitespace on paragraphs is stripped."""
    body = "  Para one.  \n\n  Para two.  "
    assert format_body(body, []) == "Para one.\n\nPara two."


def test_format_body_with_image_inserts_shortcode():
    """With one secondary image, a Hugo figure shortcode is inserted between paragraphs."""
    body = "Para one.\n\nPara two.\n\nPara three.\n\nPara four."
    result = format_body(body, ["still.jpg"])
    assert '{{< figure src="still.jpg" alt="" caption="" >}}' in result
    # Shortcode must appear between paragraphs, not at start or end
    parts = result.split("\n\n")
    shortcode_index = next(i for i, p in enumerate(parts) if "still.jpg" in p)
    assert 0 < shortcode_index < len(parts) - 1


def test_format_body_two_images_both_inserted():
    """Two secondary images must both appear in the output."""
    body = "\n\n".join(f"Para {i}." for i in range(1, 7))
    result = format_body(body, ["img1.jpg", "img2.jpg"])
    assert "img1.jpg" in result
    assert "img2.jpg" in result


# ---------------------------------------------------------------------------
# extract_doc_id
# ---------------------------------------------------------------------------


def test_extract_doc_id_standard_url():
    """A standard Google Docs URL must yield the document ID."""
    url = "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit"
    assert extract_doc_id(url) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"


def test_extract_doc_id_url_without_edit_segment():
    """A URL with no /edit suffix must still return the correct ID."""
    url = "https://docs.google.com/document/d/DOCID123"
    assert extract_doc_id(url) == "DOCID123"


def test_extract_doc_id_invalid_url_raises_system_exit():
    """A URL with no /d/<id> segment must cause SystemExit(1)."""
    with pytest.raises(SystemExit) as exc_info:
        extract_doc_id("https://docs.google.com/document/not-a-valid-path")
    assert exc_info.value.code == 1
