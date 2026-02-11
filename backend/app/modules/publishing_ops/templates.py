"""Built-in formatting templates for common book genres.

Each template provides optimised typography, margin, and layout settings
suitable for the target genre when generating EPUB or print-ready PDF.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.modules.publishing_ops.schemas import (
    FormattingTemplate,
    TemplateGenre,
    TemplateStyleSettings,
    TrimSize,
)

_NOW = datetime(2025, 1, 1, tzinfo=UTC)


def _builtin(
    name: str,
    genre: TemplateGenre,
    description: str,
    trim_size: TrimSize,
    style: TemplateStyleSettings,
) -> FormattingTemplate:
    return FormattingTemplate(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, f"template.{genre.value}"),
        org_id=None,
        name=name,
        genre=genre,
        description=description,
        trim_size=trim_size,
        style_settings=style,
        is_builtin=True,
        created_at=_NOW,
        updated_at=_NOW,
    )


ROMANCE_TEMPLATE = _builtin(
    name="Romance Standard",
    genre=TemplateGenre.ROMANCE,
    description="Elegant serif layout with generous margins and drop caps, "
    "ideal for romance and women's fiction.",
    trim_size=TrimSize.SIZE_5_5x8_5,
    style=TemplateStyleSettings(
        font_family="Garamond",
        font_size_pt=11.0,
        line_height=1.6,
        margin_top_in=0.8,
        margin_bottom_in=0.8,
        margin_inner_in=1.0,
        margin_outer_in=0.75,
        chapter_heading_font="Garamond",
        chapter_heading_size_pt=26.0,
        paragraph_indent_em=1.5,
        paragraph_spacing_pt=0.0,
        drop_cap=True,
        header_text="{title}",
        footer_text=None,
        page_numbers=True,
    ),
)


THRILLER_TEMPLATE = _builtin(
    name="Thriller Compact",
    genre=TemplateGenre.THRILLER,
    description="Tight, fast-paced layout with shorter paragraphs and compact "
    "line spacing for thrillers and crime fiction.",
    trim_size=TrimSize.SIZE_5_5x8_5,
    style=TemplateStyleSettings(
        font_family="Times New Roman",
        font_size_pt=11.0,
        line_height=1.4,
        margin_top_in=0.7,
        margin_bottom_in=0.7,
        margin_inner_in=0.9,
        margin_outer_in=0.7,
        chapter_heading_font="Helvetica",
        chapter_heading_size_pt=22.0,
        paragraph_indent_em=1.25,
        paragraph_spacing_pt=0.0,
        drop_cap=False,
        header_text="{author}",
        footer_text=None,
        page_numbers=True,
    ),
)


NONFICTION_TEMPLATE = _builtin(
    name="Nonfiction Professional",
    genre=TemplateGenre.NONFICTION,
    description="Clean, professional layout suited for business, self-help, "
    "and general nonfiction with section headings.",
    trim_size=TrimSize.SIZE_6x9,
    style=TemplateStyleSettings(
        font_family="Georgia",
        font_size_pt=11.5,
        line_height=1.5,
        margin_top_in=0.85,
        margin_bottom_in=0.85,
        margin_inner_in=1.0,
        margin_outer_in=0.8,
        chapter_heading_font="Helvetica",
        chapter_heading_size_pt=24.0,
        paragraph_indent_em=0.0,
        paragraph_spacing_pt=6.0,
        drop_cap=False,
        header_text="{title}",
        footer_text=None,
        page_numbers=True,
    ),
)


CHILDRENS_TEMPLATE = _builtin(
    name="Children's Illustrated",
    genre=TemplateGenre.CHILDRENS,
    description="Large print, wide margins for illustrations, suitable for "
    "middle-grade and early reader chapter books.",
    trim_size=TrimSize.SIZE_7x10,
    style=TemplateStyleSettings(
        font_family="Comic Sans MS",
        font_size_pt=14.0,
        line_height=1.8,
        margin_top_in=1.0,
        margin_bottom_in=1.0,
        margin_inner_in=1.25,
        margin_outer_in=1.0,
        chapter_heading_font="Comic Sans MS",
        chapter_heading_size_pt=28.0,
        paragraph_indent_em=0.0,
        paragraph_spacing_pt=8.0,
        drop_cap=False,
        header_text=None,
        footer_text=None,
        page_numbers=True,
    ),
)


SCIFI_TEMPLATE = _builtin(
    name="Sci-Fi / Fantasy",
    genre=TemplateGenre.SCIFI,
    description="Modern layout with slightly larger trim for epic stories; "
    "works well for science-fiction and fantasy.",
    trim_size=TrimSize.SIZE_6x9,
    style=TemplateStyleSettings(
        font_family="Palatino",
        font_size_pt=11.0,
        line_height=1.5,
        margin_top_in=0.8,
        margin_bottom_in=0.8,
        margin_inner_in=1.0,
        margin_outer_in=0.75,
        chapter_heading_font="Palatino",
        chapter_heading_size_pt=24.0,
        paragraph_indent_em=1.5,
        paragraph_spacing_pt=0.0,
        drop_cap=True,
        header_text="{title}",
        footer_text=None,
        page_numbers=True,
    ),
)


LITERARY_TEMPLATE = _builtin(
    name="Literary Fiction",
    genre=TemplateGenre.LITERARY,
    description="Classic typography for literary fiction with balanced whitespace.",
    trim_size=TrimSize.SIZE_5_25x8,
    style=TemplateStyleSettings(
        font_family="Baskerville",
        font_size_pt=11.0,
        line_height=1.55,
        margin_top_in=0.85,
        margin_bottom_in=0.85,
        margin_inner_in=1.0,
        margin_outer_in=0.8,
        chapter_heading_font="Baskerville",
        chapter_heading_size_pt=22.0,
        paragraph_indent_em=1.5,
        paragraph_spacing_pt=0.0,
        drop_cap=True,
        header_text="{author}",
        footer_text=None,
        page_numbers=True,
    ),
)


MEMOIR_TEMPLATE = _builtin(
    name="Memoir / Biography",
    genre=TemplateGenre.MEMOIR,
    description="Warm, inviting layout for memoir and biography with generous "
    "leading and readable serif type.",
    trim_size=TrimSize.SIZE_5_5x8_5,
    style=TemplateStyleSettings(
        font_family="Garamond",
        font_size_pt=11.5,
        line_height=1.6,
        margin_top_in=0.8,
        margin_bottom_in=0.8,
        margin_inner_in=1.0,
        margin_outer_in=0.75,
        chapter_heading_font="Garamond",
        chapter_heading_size_pt=24.0,
        paragraph_indent_em=1.25,
        paragraph_spacing_pt=0.0,
        drop_cap=False,
        header_text="{title}",
        footer_text=None,
        page_numbers=True,
    ),
)


BUSINESS_TEMPLATE = _builtin(
    name="Business / How-To",
    genre=TemplateGenre.BUSINESS,
    description="Structured, corporate-friendly layout with block paragraphs "
    "and sans-serif headings for business books.",
    trim_size=TrimSize.SIZE_6x9,
    style=TemplateStyleSettings(
        font_family="Calibri",
        font_size_pt=11.0,
        line_height=1.45,
        margin_top_in=0.85,
        margin_bottom_in=0.85,
        margin_inner_in=1.0,
        margin_outer_in=0.8,
        chapter_heading_font="Arial",
        chapter_heading_size_pt=24.0,
        paragraph_indent_em=0.0,
        paragraph_spacing_pt=6.0,
        drop_cap=False,
        header_text="{title}",
        footer_text=None,
        page_numbers=True,
    ),
)

# Lookup table keyed by genre
BUILTIN_TEMPLATES: dict[TemplateGenre, FormattingTemplate] = {
    TemplateGenre.ROMANCE: ROMANCE_TEMPLATE,
    TemplateGenre.THRILLER: THRILLER_TEMPLATE,
    TemplateGenre.NONFICTION: NONFICTION_TEMPLATE,
    TemplateGenre.CHILDRENS: CHILDRENS_TEMPLATE,
    TemplateGenre.SCIFI: SCIFI_TEMPLATE,
    TemplateGenre.LITERARY: LITERARY_TEMPLATE,
    TemplateGenre.MEMOIR: MEMOIR_TEMPLATE,
    TemplateGenre.BUSINESS: BUSINESS_TEMPLATE,
}

# Flat list for convenience
ALL_BUILTIN_TEMPLATES: list[FormattingTemplate] = list(BUILTIN_TEMPLATES.values())


def get_builtin_template(genre: TemplateGenre) -> FormattingTemplate | None:
    """Return the built-in template for a given genre, or None."""
    return BUILTIN_TEMPLATES.get(genre)


def get_all_templates() -> list[FormattingTemplate]:
    """Return all built-in templates."""
    return list(ALL_BUILTIN_TEMPLATES)
