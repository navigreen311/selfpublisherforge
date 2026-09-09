"""Tests for Safety & Compliance service — originality, spam, trademark, sensitivity.

Exercises service_safety functions directly (no HTTP layer) using
lightweight in-memory data structures to avoid database dependencies.
"""

from __future__ import annotations

import pytest

from app.modules.specialty_books.service_safety import (
    SIMILARITY_THRESHOLD,
    TRADEMARK_BLOCKLIST,
    _compute_grid_hash,
    _compute_phash,
    _extract_ngrams,
    _jaccard_similarity,
    _ngram_fingerprint,
    _ngram_similarity,
    _sha256,
    check_content_sensitivity,
    check_trademark_safety,
)

# ═══════════════════════════════════════════════════════════════════════
# HELPER UTILITIES
# ═══════════════════════════════════════════════════════════════════════


class TestSha256:
    def test_deterministic(self):
        assert _sha256("hello") == _sha256("hello")

    def test_different_inputs(self):
        assert _sha256("a") != _sha256("b")


class TestPerceptualHash:
    def test_returns_none_for_none(self):
        assert _compute_phash(None) is None

    def test_returns_hash_string(self):
        h = _compute_phash("https://example.com/img.png")
        assert h is not None
        assert isinstance(h, str)
        assert len(h) == 16

    def test_deterministic(self):
        url = "https://example.com/img.png"
        assert _compute_phash(url) == _compute_phash(url)

    def test_different_urls_different_hash(self):
        assert _compute_phash("https://a.com/1.png") != _compute_phash("https://b.com/2.png")


class TestGridHash:
    def test_returns_none_for_none(self):
        assert _compute_grid_hash(None) is None

    def test_returns_hash_for_dict(self):
        h = _compute_grid_hash({"grid": [[1, 2], [3, 4]]})
        assert h is not None
        assert len(h) == 64  # SHA-256 hex

    def test_deterministic(self):
        grid = {"cells": [["A", "B"], ["C", "D"]]}
        assert _compute_grid_hash(grid) == _compute_grid_hash(grid)

    def test_different_grids_different_hash(self):
        g1 = {"cells": [[1, 2]]}
        g2 = {"cells": [[3, 4]]}
        assert _compute_grid_hash(g1) != _compute_grid_hash(g2)


class TestJaccardSimilarity:
    def test_identical_sets(self):
        s = {"cat", "dog", "bird"}
        assert _jaccard_similarity(s, s) == 1.0

    def test_disjoint_sets(self):
        assert _jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        a = {"cat", "dog", "bird"}
        b = {"cat", "fish", "bird"}
        # intersection = {cat, bird} = 2, union = {cat, dog, bird, fish} = 4
        assert _jaccard_similarity(a, b) == pytest.approx(0.5)

    def test_empty_sets(self):
        assert _jaccard_similarity(set(), set()) == 1.0

    def test_one_empty(self):
        assert _jaccard_similarity({"a"}, set()) == 0.0


class TestNgrams:
    def test_extract_trigrams(self):
        ngrams = _extract_ngrams("the quick brown fox jumps", n=3)
        assert "the quick brown" in ngrams
        assert "quick brown fox" in ngrams
        assert len(ngrams) == 3  # 5 words -> 3 trigrams

    def test_short_text(self):
        ngrams = _extract_ngrams("hi", n=3)
        assert ngrams == ["hi"]

    def test_fingerprint_deterministic(self):
        text = "Once upon a time there was a bear"
        assert _ngram_fingerprint(text) == _ngram_fingerprint(text)

    def test_fingerprint_none_for_none(self):
        assert _ngram_fingerprint(None) is None

    def test_ngram_similarity_identical(self):
        text = "the quick brown fox jumps over the lazy dog near the river"
        assert _ngram_similarity(text, text) == pytest.approx(1.0)

    def test_ngram_similarity_different(self):
        a = "the quick brown fox jumps over the lazy dog"
        b = "a completely different sentence about nothing related"
        sim = _ngram_similarity(a, b)
        assert sim < 0.3


# ═══════════════════════════════════════════════════════════════════════
# TRADEMARK SAFETY
# ═══════════════════════════════════════════════════════════════════════


class TestTrademarkSafety:
    def test_catches_disney(self):
        violations = check_trademark_safety("A Disney princess adventure", "title")
        assert len(violations) >= 1
        assert any(v["trademark"] == "disney" for v in violations)

    def test_catches_marvel(self):
        violations = check_trademark_safety("Marvel superhero coloring book", "title")
        assert len(violations) >= 1
        assert any(v["trademark"] == "marvel" for v in violations)

    def test_catches_peppa_pig(self):
        violations = check_trademark_safety("Peppa Pig activity book", "title")
        assert len(violations) >= 1
        assert any(v["trademark"] == "peppa pig" for v in violations)

    def test_catches_pokemon(self):
        violations = check_trademark_safety("Pokemon coloring pages", "title")
        assert len(violations) >= 1
        assert any(v["trademark"] == "pokemon" for v in violations)

    def test_catches_frozen(self):
        violations = check_trademark_safety("Frozen princess coloring book", "title")
        assert len(violations) >= 1
        assert any(v["trademark"] == "frozen" for v in violations)

    def test_catches_lego(self):
        violations = check_trademark_safety("LEGO building activity book", "title")
        assert len(violations) >= 1
        assert any(v["trademark"] == "lego" for v in violations)

    def test_catches_hello_kitty(self):
        violations = check_trademark_safety("Hello Kitty fun pages", "title")
        assert len(violations) >= 1
        assert any(v["trademark"] == "hello kitty" for v in violations)

    def test_catches_paw_patrol(self):
        violations = check_trademark_safety("Paw Patrol rescue adventure", "title")
        assert len(violations) >= 1

    def test_clean_text_passes(self):
        violations = check_trademark_safety("Fun Animals Coloring Book for Kids", "title")
        assert len(violations) == 0

    def test_style_of_artist_detected(self):
        violations = check_trademark_safety(
            "Draw a cat in the style of Pablo Picasso", "prompt"
        )
        assert len(violations) >= 1
        assert any(v["type"] == "style_imitation" for v in violations)

    def test_style_of_artist_captures_name(self):
        violations = check_trademark_safety(
            "Watercolor landscape in the style of Bob Ross", "prompt"
        )
        style_violations = [v for v in violations if v["type"] == "style_imitation"]
        assert len(style_violations) >= 1
        assert style_violations[0]["artist"] == "Bob Ross"

    def test_case_insensitive(self):
        violations = check_trademark_safety("disney MARVEL paw patrol", "title")
        assert len(violations) >= 3

    def test_includes_context(self):
        violations = check_trademark_safety("A Disney book", "description")
        assert violations[0]["context"] == "description"

    def test_violation_has_fix(self):
        violations = check_trademark_safety("Disney coloring", "title")
        assert all("fix" in v for v in violations)


# ═══════════════════════════════════════════════════════════════════════
# CONTENT SENSITIVITY
# ═══════════════════════════════════════════════════════════════════════


class TestContentSensitivity:
    def test_detects_weapons(self):
        issues = check_content_sensitivity("The soldier fired his gun at the target", "3-5")
        weapon_issues = [i for i in issues if i["type"] == "weapons_violence"]
        assert len(weapon_issues) >= 1

    def test_detects_violence(self):
        issues = check_content_sensitivity("The villain launched an attack on the village", "3-5")
        assert any(i["type"] == "weapons_violence" for i in issues)

    def test_detects_mature_themes(self):
        issues = check_content_sensitivity("The character was drunk on alcohol", "8-12")
        mature = [i for i in issues if i["type"] == "mature_themes"]
        assert len(mature) >= 1
        # Mature themes should always be severity=block
        assert all(i["severity"] == "block" for i in mature)

    def test_detects_stereotypes(self):
        issues = check_content_sensitivity(
            "The savage people lived in primitive tribes", "6-8"
        )
        stereo = [i for i in issues if i["type"] == "stereotypes"]
        assert len(stereo) >= 1

    def test_clean_text_passes(self):
        issues = check_content_sensitivity(
            "The bunny hopped across the sunny meadow and found a carrot", "3-5"
        )
        assert len(issues) == 0

    def test_advanced_vocabulary_for_young_children(self):
        issues = check_content_sensitivity(
            "The philosophical bunny pondered the quintessential nature of carrots",
            "0-3",
        )
        vocab_issues = [i for i in issues if i["type"] == "advanced_vocabulary"]
        assert len(vocab_issues) >= 1
        terms = {i["term"] for i in vocab_issues}
        assert "philosophical" in terms or "quintessential" in terms

    def test_advanced_vocabulary_ok_for_older(self):
        """Words flagged for young children should not be flagged for older age ranges."""
        issues = check_content_sensitivity(
            "The philosophical nature of the quest",
            "12-16",
        )
        vocab_issues = [i for i in issues if i["type"] == "advanced_vocabulary"]
        assert len(vocab_issues) == 0

    def test_weapons_blocked_for_young_children(self):
        issues = check_content_sensitivity("He drew his sword", "3-5")
        weapon_issues = [i for i in issues if i["type"] == "weapons_violence"]
        assert len(weapon_issues) >= 1
        assert all(i["severity"] == "block" for i in weapon_issues)

    def test_weapons_warning_for_older_children(self):
        issues = check_content_sensitivity("He drew his sword", "10-12")
        weapon_issues = [i for i in issues if i["type"] == "weapons_violence"]
        assert len(weapon_issues) >= 1
        assert all(i["severity"] == "warning" for i in weapon_issues)


# ═══════════════════════════════════════════════════════════════════════
# SPAM DETECTION (metadata checks — unit-level, no DB needed)
# ═══════════════════════════════════════════════════════════════════════


class TestSpamMetadataHelpers:
    """Test the metadata quality check helper via a mock book-like object."""

    def test_keyword_stuffed_title_detected(self):
        from app.modules.specialty_books.service_safety import _check_metadata_quality

        class MockBook:
            title = "Coloring Book, Animals, Kids, Toddlers, Preschool, Art, Fun, Creative"
            description = "A great coloring book for kids."

        score, flags = _check_metadata_quality(MockBook())
        assert any(f["type"] == "keyword_stuffed_title" for f in flags)

    def test_long_title_flagged(self):
        from app.modules.specialty_books.service_safety import _check_metadata_quality

        class MockBook:
            title = "A" * 250
            description = "Decent description with enough content to pass."

        score, flags = _check_metadata_quality(MockBook())
        assert any(f["type"] == "title_too_long" for f in flags)

    def test_thin_description_flagged(self):
        from app.modules.specialty_books.service_safety import _check_metadata_quality

        class MockBook:
            title = "Good Title"
            description = "Short."

        score, flags = _check_metadata_quality(MockBook())
        assert any(f["type"] == "thin_description" for f in flags)

    def test_good_metadata_passes(self):
        from app.modules.specialty_books.service_safety import _check_metadata_quality

        class MockBook:
            title = "Amazing Animals Coloring Book"
            description = (
                "A beautifully illustrated coloring book featuring 30 adorable animals "
                "from around the world. Perfect for children ages 3-8. Each page features "
                "a different animal with thick outlines for easy coloring."
            )

        score, flags = _check_metadata_quality(MockBook())
        assert score == 100.0
        assert len(flags) == 0


# ═══════════════════════════════════════════════════════════════════════
# ANTI-DUPLICATE HELPERS (unit-level)
# ═══════════════════════════════════════════════════════════════════════


class TestAntiDuplicateHelpers:
    def test_identical_grids_detected(self):
        """Two identical grids should hash identically."""
        grid = {"cells": [["A", "B", "C"], ["D", "E", "F"]]}
        h1 = _compute_grid_hash(grid)
        h2 = _compute_grid_hash(grid)
        assert h1 == h2

    def test_different_grids_distinct(self):
        g1 = {"cells": [["A", "B"], ["C", "D"]]}
        g2 = {"cells": [["X", "Y"], ["Z", "W"]]}
        assert _compute_grid_hash(g1) != _compute_grid_hash(g2)

    def test_word_overlap_within_limit(self):
        """Less than 30% word overlap should be acceptable."""
        set_a = {"cat", "dog", "bird", "fish", "horse", "cow", "pig", "goat", "sheep", "duck"}
        set_b = {"ant", "bee", "wasp", "fly", "moth", "spider", "snail", "worm", "slug", "cat"}
        sim = _jaccard_similarity(set_a, set_b)
        assert sim <= 0.30  # only "cat" overlaps

    def test_word_overlap_exceeds_limit(self):
        """More than 30% word overlap should be flagged."""
        set_a = {"cat", "dog", "bird", "fish", "horse"}
        set_b = {"cat", "dog", "bird", "snake", "lizard"}
        sim = _jaccard_similarity(set_a, set_b)
        assert sim > 0.30  # 3/7 = 0.428


# ═══════════════════════════════════════════════════════════════════════
# ORIGINALITY FINGERPRINT CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════


class TestOriginalityFingerprint:
    def test_phash_consistent(self):
        url = "https://example.com/coloring/page1.png"
        h1 = _compute_phash(url)
        h2 = _compute_phash(url)
        assert h1 == h2

    def test_ngram_fingerprint_consistent(self):
        text = "Once upon a time in a land far far away there lived a little bear"
        fp1 = _ngram_fingerprint(text)
        fp2 = _ngram_fingerprint(text)
        assert fp1 == fp2

    def test_grid_hash_consistent(self):
        grid = {"size": "15x15", "cells": [["A"] * 15 for _ in range(15)]}
        h1 = _compute_grid_hash(grid)
        h2 = _compute_grid_hash(grid)
        assert h1 == h2


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON DETECTS HIGH OVERLAP
# ═══════════════════════════════════════════════════════════════════════


class TestComparisonOverlap:
    def test_identical_texts_high_similarity(self):
        text = "the quick brown fox jumps over the lazy dog near the river"
        sim = _ngram_similarity(text, text)
        assert sim > SIMILARITY_THRESHOLD

    def test_different_texts_low_similarity(self):
        a = "the quick brown fox jumps over the lazy dog"
        b = "a completely unrelated paragraph about space exploration and rockets"
        sim = _ngram_similarity(a, b)
        assert sim < SIMILARITY_THRESHOLD

    def test_identical_word_sets_full_jaccard(self):
        words = {"apple", "banana", "cherry", "date", "elderberry"}
        assert _jaccard_similarity(words, words) == 1.0


# ═══════════════════════════════════════════════════════════════════════
# BLOCKLIST COVERAGE
# ═══════════════════════════════════════════════════════════════════════


class TestBlocklistCoverage:
    """Ensure major brands are in the blocklist."""

    @pytest.mark.parametrize(
        "brand",
        [
            "disney",
            "pixar",
            "peppa pig",
            "bluey",
            "paw patrol",
            "marvel",
            "frozen",
            "cocomelon",
            "sesame street",
            "pokemon",
            "hello kitty",
            "barbie",
            "lego",
        ],
    )
    def test_brand_in_blocklist(self, brand: str):
        assert brand in TRADEMARK_BLOCKLIST

    @pytest.mark.parametrize(
        "brand",
        [
            "Disney",
            "Marvel",
            "Peppa Pig",
            "LEGO",
            "Pokemon",
            "Barbie",
        ],
    )
    def test_brand_detected_case_insensitive(self, brand: str):
        violations = check_trademark_safety(f"A {brand} themed book", "title")
        assert len(violations) >= 1
