"""Unit tests for the listing analyzer module.

Tests title analysis, blurb analysis, keyword analysis, category analysis,
price analysis, mobile checking, and blurb generation.
"""

from __future__ import annotations

from app.modules.product_page_lab.analyzer import (
    _calculate_readability,
    _count_syllables,
    _has_hook,
    analyze_blurb,
    analyze_category,
    analyze_keywords,
    analyze_listing,
    analyze_price,
    analyze_title,
)
from app.modules.product_page_lab.blurb_generator import (
    build_blurb_generation_prompt,
    generate_blurb_variants_local,
)
from app.modules.product_page_lab.mobile_checker import (
    _check_truncation,
    _has_above_fold_hook,
    _strip_html,
    check_mobile_display,
)
from app.modules.product_page_lab.schemas import Genre

# ===========================================================================
# Title analysis tests
# ===========================================================================

class TestTitleAnalysis:
    """Tests for analyze_title()."""

    def test_good_title_scores_high(self):
        title = "The Secret Garden: A Captivating Tale of Discovery and Love"
        result = analyze_title(title, target_keywords=["garden", "love"])
        assert result.score >= 70
        assert result.has_keywords is True
        assert "garden" in result.keyword_matches
        assert "love" in result.keyword_matches

    def test_short_title_penalized(self):
        title = "My Book"
        result = analyze_title(title)
        assert result.score < 80
        assert any("short" in issue.lower() for issue in result.issues)

    def test_long_title_penalized(self):
        title = "A" * 120 + ": The Most Incredible Story Ever Written About Everything in the Universe"
        result = analyze_title(title)
        assert result.score <= 90
        assert any("long" in issue.lower() for issue in result.issues)

    def test_no_keywords_penalized(self):
        title = "A Simple Story"
        result = analyze_title(title, target_keywords=["romance", "thriller"])
        assert result.has_keywords is False
        assert any("keyword" in issue.lower() for issue in result.issues)

    def test_power_words_detected(self):
        title = "The Ultimate Secret: A Gripping Thriller"
        result = analyze_title(title)
        assert len(result.power_words) > 0
        assert "ultimate" in result.power_words or "secret" in result.power_words

    def test_no_power_words_penalized(self):
        title = "A Book About Cooking"
        result = analyze_title(title)
        assert any("power words" in issue.lower() for issue in result.issues)

    def test_excessive_caps_penalized(self):
        title = "THE MOST AMAZING BOOK EVER WRITTEN"
        result = analyze_title(title)
        assert any("caps" in issue.lower() for issue in result.issues)

    def test_subtitle_format_bonus(self):
        title_with_colon = "The Heir: A Royal Romance"
        title_without = "The Heir A Royal Romance"
        result_with = analyze_title(title_with_colon)
        result_without = analyze_title(title_without)
        # Subtitle format should score slightly higher (all else equal)
        assert result_with.score >= result_without.score

    def test_empty_keywords_no_penalty(self):
        title = "A Compelling Story"
        result = analyze_title(title, target_keywords=[])
        assert not any("keyword" in issue.lower() for issue in result.issues)

    def test_score_within_bounds(self):
        result = analyze_title("")
        assert 0 <= result.score <= 100

    def test_special_characters_penalized(self):
        title = "!!!AMAZING!!! Book @#$ Read Now!!!"
        result = analyze_title(title)
        assert any("special" in issue.lower() for issue in result.issues)


# ===========================================================================
# Blurb analysis tests
# ===========================================================================

class TestBlurbAnalysis:
    """Tests for analyze_blurb()."""

    def test_good_blurb_scores_high(self):
        blurb = (
            "What if everything you believed was a lie?\n\n"
            "<b>A gripping thriller</b> that will keep you on the edge of your seat.\n\n"
            "When detective Sarah discovers a shocking secret, her world shatters. "
            "Now she must race against time to uncover the truth before it's too late.\n\n"
            "- A pulse-pounding mystery\n"
            "- Unforgettable characters\n"
            "- A twist you won't see coming\n\n"
            "<i>Fans of Gone Girl and The Girl on the Train will love this.</i>\n\n"
            "Buy now and start reading today!"
        )
        result = analyze_blurb(blurb)
        assert result.score >= 60
        assert result.has_hook is True
        assert result.has_bullet_points is True
        assert result.has_cta is True
        assert result.has_html_formatting is True

    def test_short_blurb_penalized(self):
        blurb = "A book about love and loss. It is a wonderful story."
        result = analyze_blurb(blurb)
        assert result.score < 80
        assert any("short" in issue.lower() for issue in result.issues)

    def test_no_hook_penalized(self):
        blurb = (
            "This is a story about a person who does things. "
            "They go places and meet other people. "
            "Eventually something happens and the story ends. "
            "The characters are developed throughout the narrative. "
            "The setting is described in detail for the reader. "
            "There are plot twists and turns along the way. "
            "The theme explores important topics about life."
        )
        result = analyze_blurb(blurb)
        assert result.has_hook is False
        assert any("hook" in issue.lower() for issue in result.issues)

    def test_no_cta_penalized(self):
        blurb = (
            "What if the world ended tomorrow? "
            "This gripping story follows Jane as she navigates "
            "a post-apocalyptic landscape, searching for meaning in chaos. "
            "With danger at every turn, she must find the courage to survive. "
            "A tale of love, loss, and resilience."
        )
        result = analyze_blurb(blurb)
        assert result.has_cta is False
        assert any("call-to-action" in issue.lower() or "cta" in issue.lower() for issue in result.issues)

    def test_no_html_penalized(self):
        blurb = (
            "Discover the secret! A thrilling adventure awaits. "
            "Join our hero as they embark on the journey of a lifetime. "
            "Twists, turns, and surprises at every corner. "
            "Will they survive? Buy now to find out!"
        )
        result = analyze_blurb(blurb)
        assert result.has_html_formatting is False
        assert any("html" in issue.lower() for issue in result.issues)

    def test_no_bullet_points_flagged(self):
        blurb = (
            "Discover the truth! A compelling narrative about love and betrayal. "
            "Join the adventure today. Buy now!"
        )
        result = analyze_blurb(blurb)
        assert result.has_bullet_points is False

    def test_emotional_words_detected(self):
        blurb = (
            "A story of love and betrayal, where passion meets revenge. "
            "Fear grips the city as an ancient evil awakens. "
            "Can hope prevail? Scroll up and buy now!"
        )
        result = analyze_blurb(blurb)
        assert len(result.emotional_words) > 0
        assert "love" in result.emotional_words or "betrayal" in result.emotional_words

    def test_word_count_calculated(self):
        blurb = "One two three four five."
        result = analyze_blurb(blurb)
        assert result.word_count == 5

    def test_score_within_bounds(self):
        result = analyze_blurb("Short.")
        assert 0 <= result.score <= 100


# ===========================================================================
# Keyword analysis tests
# ===========================================================================

class TestKeywordAnalysis:
    """Tests for analyze_keywords()."""

    def test_keywords_found(self):
        text = "This romance novel features a love story with a billionaire hero"
        result = analyze_keywords(text, target_keywords=["romance", "love", "billionaire"])
        assert "romance" in result.keywords_found
        assert "love" in result.keywords_found
        assert "billionaire" in result.keywords_found

    def test_missing_keywords(self):
        text = "A simple book about cooking."
        result = analyze_keywords(text, target_keywords=["romance", "thriller"])
        assert "romance" in result.missing_high_value_keywords
        assert "thriller" in result.missing_high_value_keywords

    def test_keyword_stuffing_detected(self):
        text = "romance romance romance romance romance " * 5
        result = analyze_keywords(text, target_keywords=["romance"])
        assert result.over_stuffed is True

    def test_empty_keywords_acceptable(self):
        text = "Just a normal book description."
        result = analyze_keywords(text, target_keywords=[])
        assert result.score >= 50
        assert result.keyword_density == 0.0

    def test_keyword_density_calculated(self):
        text = "romance is great and romance is wonderful"
        result = analyze_keywords(text, target_keywords=["romance"])
        assert result.keyword_density > 0

    def test_score_within_bounds(self):
        result = analyze_keywords("test", target_keywords=["missing1", "missing2", "missing3"])
        assert 0 <= result.score <= 100


# ===========================================================================
# Category analysis tests
# ===========================================================================

class TestCategoryAnalysis:
    """Tests for analyze_category()."""

    def test_with_categories(self):
        result = analyze_category(
            current_categories=["Kindle Store > Romance", "Books > Romance"],
            genre="romance",
        )
        assert result.score > 50
        assert len(result.suggested_categories) > 0

    def test_without_categories(self):
        result = analyze_category(current_categories=[], genre="romance")
        assert result.score < 70

    def test_genre_suggestions(self):
        result = analyze_category(genre="thriller")
        assert len(result.suggested_categories) > 0
        assert any("thriller" in c.lower() for c in result.suggested_categories)

    def test_no_genre_no_categories(self):
        result = analyze_category()
        assert result.score >= 0
        assert result.score <= 100

    def test_multiple_categories_bonus(self):
        result_one = analyze_category(current_categories=["Books > Fiction"])
        result_two = analyze_category(current_categories=["Books > Fiction", "Kindle > Fiction"])
        assert result_two.score >= result_one.score


# ===========================================================================
# Price analysis tests
# ===========================================================================

class TestPriceAnalysis:
    """Tests for analyze_price()."""

    def test_sweet_spot_price(self):
        result = analyze_price(current_price=3.99, genre="romance")
        assert result.score >= 70

    def test_too_cheap(self):
        result = analyze_price(current_price=0.50, genre="romance")
        assert result.score < 70
        assert any("$0.99" in issue or "below" in issue.lower() for issue in result.issues)

    def test_too_expensive(self):
        result = analyze_price(current_price=14.99, genre="romance")
        assert result.score < 80
        assert any("above" in issue.lower() or "$9.99" in issue for issue in result.issues)

    def test_no_price(self):
        result = analyze_price(current_price=None, genre="romance")
        assert result.score == 50
        assert any("no price" in issue.lower() for issue in result.issues)

    def test_genre_avg_price_set(self):
        result = analyze_price(current_price=4.99, genre="thriller")
        assert result.genre_avg_price == 4.99

    def test_suggested_range_present(self):
        result = analyze_price(current_price=4.99, genre="romance")
        assert result.suggested_range is not None


# ===========================================================================
# Full listing analysis tests
# ===========================================================================

class TestListingAnalysis:
    """Tests for analyze_listing() end-to-end."""

    def test_full_analysis(self):
        result = analyze_listing(
            title="The Secret Heir: A Gripping Romance Novel",
            blurb=(
                "What if you discovered you were heir to a fortune?\n\n"
                "<b>A captivating romance</b> that will steal your heart.\n\n"
                "- Passion and intrigue\n"
                "- Unforgettable love story\n"
                "- A shocking twist\n\n"
                "Buy now and start reading!"
            ),
            keywords=["romance", "heir", "love"],
            categories=["Kindle > Romance"],
            price=3.99,
            genre="romance",
            asin="B09V2KKG1D",
        )
        assert result.overall_score > 0
        assert result.overall_score <= 100
        assert result.asin == "B09V2KKG1D"
        assert result.title_score > 0
        assert result.blurb_score > 0
        assert len(result.recommendations) >= 0

    def test_empty_listing_has_scores(self):
        result = analyze_listing(title="", blurb="")
        assert result.overall_score >= 0
        assert result.title_score >= 0
        assert result.blurb_score >= 0

    def test_recommendations_generated(self):
        result = analyze_listing(
            title="Short",
            blurb="Bad blurb.",
            keywords=["missing_keyword"],
        )
        assert len(result.recommendations) > 0

    def test_weighted_overall_score(self):
        result = analyze_listing(
            title="A" * 60,
            blurb="A compelling story. " * 20,
        )
        # Overall should be weighted combination
        expected_approx = (
            result.title_score * 0.20
            + result.blurb_score * 0.30
            + result.keyword_score * 0.20
            + result.category_score * 0.15
            + result.price_score * 0.15
        )
        assert abs(result.overall_score - round(expected_approx, 1)) < 1.0


# ===========================================================================
# Mobile checker tests
# ===========================================================================

class TestMobileChecker:
    """Tests for mobile_checker module."""

    def test_title_truncation_detected(self):
        long_title = "This Is An Extremely Long Book Title That Will Definitely Be Truncated On Mobile Devices"
        result = check_mobile_display(
            title=long_title,
            blurb="A great book about something interesting. Buy now to find out more!",
            author_name="John Smith",
        )
        assert result.title_display.is_truncated is True
        assert result.overall_score < 100

    def test_short_title_not_truncated(self):
        short_title = "Short Title"
        result = check_mobile_display(
            title=short_title,
            blurb="A great book about something interesting. Buy now to find out more!",
            author_name="John Smith",
        )
        assert result.title_display.is_truncated is False

    def test_blurb_fold_point(self):
        long_blurb = "This is a sentence. " * 50
        result = check_mobile_display(
            title="My Book",
            blurb=long_blurb,
            author_name="Jane Doe",
        )
        assert result.blurb_fold_point > 0
        assert len(result.blurb_above_fold) <= result.blurb_fold_point + 10

    def test_subtitle_truncation(self):
        result = check_mobile_display(
            title="My Book",
            blurb="A great read. Buy now!",
            author_name="Author",
            subtitle="A Very Long Subtitle That Goes On And On And Will Be Cut Off",
        )
        assert result.subtitle_display is not None

    def test_device_previews_generated(self):
        result = check_mobile_display(
            title="My Book Title",
            blurb="A wonderful story. Buy now!",
            author_name="Author Name",
        )
        assert len(result.device_previews) > 0
        assert "iphone_14" in result.device_previews

    def test_score_within_bounds(self):
        result = check_mobile_display(
            title="T",
            blurb="Short blurb for testing.",
            author_name="A",
        )
        assert 0 <= result.overall_score <= 100

    def test_strip_html(self):
        assert _strip_html("<b>Bold</b> text") == "Bold text"
        assert _strip_html("<p>Paragraph</p>") == "Paragraph"
        assert _strip_html("No HTML here") == "No HTML here"

    def test_check_truncation(self):
        result = _check_truncation("test", "Hello World", 5)
        assert result.is_truncated is True
        assert result.visible_length == 5

        result2 = _check_truncation("test", "Hi", 10)
        assert result2.is_truncated is False

    def test_above_fold_hook_detection(self):
        assert _has_above_fold_hook("What if you could change everything?") is True
        assert _has_above_fold_hook("Discover the truth!") is True
        assert _has_above_fold_hook("A book about cooking recipes for dinner") is False

    def test_long_author_name_flagged(self):
        result = check_mobile_display(
            title="My Book",
            blurb="A great read. Buy now!",
            author_name="Professor Doctor Sir Maximilian Von Hertfordshire III Esquire",
        )
        assert any("author" in r.area for r in result.recommendations)


# ===========================================================================
# Blurb generator tests
# ===========================================================================

class TestBlurbGenerator:
    """Tests for blurb_generator module."""

    def test_local_generation(self):
        result = generate_blurb_variants_local(
            current_blurb="A thrilling tale of love and adventure. Two hearts collide in a world of danger. Will they survive?",
            genre=Genre.ROMANCE,
            num_variants=3,
        )
        assert result.original_score > 0
        assert len(result.variants) == 3
        assert result.generation_metadata["method"] == "template_based"

    def test_variants_have_unique_ids(self):
        result = generate_blurb_variants_local(
            current_blurb="A great book about an important topic. The author explores many themes throughout the narrative.",
            genre=Genre.NON_FICTION,
            num_variants=3,
        )
        ids = [v.variant_id for v in result.variants]
        assert len(set(ids)) == 3

    def test_variants_have_different_styles(self):
        result = generate_blurb_variants_local(
            current_blurb="An exciting story full of twists and turns. The hero must face impossible odds.",
            genre=Genre.THRILLER,
            num_variants=3,
        )
        styles = [v.style for v in result.variants]
        # At least some should differ since we cycle through styles
        assert len(set(styles)) >= 2

    def test_single_variant(self):
        result = generate_blurb_variants_local(
            current_blurb="A simple story about finding your way home. The journey is more important than the destination.",
            genre=Genre.LITERARY_FICTION,
            num_variants=1,
        )
        assert len(result.variants) == 1

    def test_prompt_builder(self):
        prompt = build_blurb_generation_prompt(
            current_blurb="An old blurb text about a romance story.",
            genre=Genre.ROMANCE,
            target_audience="Women 25-45",
            keywords=["romance", "billionaire"],
            tone="emotional",
            variant_index=0,
        )
        assert "romance" in prompt.lower()
        assert "Women 25-45" in prompt
        assert "billionaire" in prompt
        assert "emotional" in prompt

    def test_generation_with_keywords(self):
        result = generate_blurb_variants_local(
            current_blurb="A book about self improvement. Learn the techniques that experts use to be successful in life.",
            genre=Genre.SELF_HELP,
            keywords=["productivity", "habits", "success"],
            num_variants=2,
        )
        assert len(result.variants) == 2

    def test_variant_scores(self):
        result = generate_blurb_variants_local(
            current_blurb="An intriguing mystery that keeps you guessing. Who committed the crime?",
            genre=Genre.MYSTERY,
            num_variants=2,
        )
        for variant in result.variants:
            assert 0 <= variant.estimated_conversion_score <= 100


# ===========================================================================
# Helper function tests
# ===========================================================================

class TestHelpers:
    """Tests for internal helper functions."""

    def test_count_syllables(self):
        assert _count_syllables("hello") == 2
        assert _count_syllables("the") == 1
        assert _count_syllables("beautiful") == 3
        assert _count_syllables("a") == 1

    def test_calculate_readability(self):
        # Simple text should have low readability grade
        simple = "The cat sat on the mat. The dog ran fast."
        grade = _calculate_readability(simple)
        assert grade < 10

        # Complex text should have higher grade
        complex_text = (
            "The quintessential manifestation of philosophical enlightenment "
            "permeates throughout the extraordinary circumstances of metaphysical "
            "consciousness and transcendental meditation."
        )
        complex_grade = _calculate_readability(complex_text)
        assert complex_grade > grade

    def test_has_hook_question(self):
        assert _has_hook("What if the world ended tomorrow?") is True

    def test_has_hook_exclamation(self):
        assert _has_hook("Everything changed in an instant!") is True

    def test_has_hook_trigger_words(self):
        assert _has_hook("Discover the incredible secret that will transform your life.") is True

    def test_has_hook_no_hook(self):
        assert _has_hook("This is a regular sentence about normal things.") is False
