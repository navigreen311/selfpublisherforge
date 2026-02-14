"""Pydantic schemas for the Style Cloning Engine."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProfileStatus(str, Enum):
    pending = "pending"
    analyzing = "analyzing"
    ready = "ready"
    failed = "failed"


class ManuscriptFormat(str, Enum):
    docx = "docx"
    epub = "epub"
    pdf = "pdf"
    txt = "txt"


# ---------------------------------------------------------------------------
# Voice Fingerprint sub-models
# ---------------------------------------------------------------------------

class VocabularyMetrics(BaseModel):
    unique_word_count: int = Field(0, description="Number of unique words (types)")
    total_word_count: int = Field(0, description="Total words (tokens)")
    lexical_density: float = Field(0.0, description="Ratio of content words to total words")
    type_token_ratio: float = Field(0.0, description="Unique words / total words")
    rare_word_frequency: float = Field(0.0, description="% of words not in top-5000 common English")
    reading_level: float = Field(0.0, description="Flesch-Kincaid grade level")
    avg_word_length: float = Field(0.0, description="Average word length in characters")
    top_words: list[tuple[str, int]] = Field(default_factory=list, description="Top 30 most frequent content words")


class SentenceMetrics(BaseModel):
    avg_length: float = Field(0.0, description="Average sentence length in words")
    length_variance: float = Field(0.0, description="Variance of sentence lengths")
    min_length: int = Field(0)
    max_length: int = Field(0)
    simple_ratio: float = Field(0.0, description="Fraction of simple sentences (1 clause)")
    compound_ratio: float = Field(0.0, description="Fraction of compound sentences")
    complex_ratio: float = Field(0.0, description="Fraction of complex sentences")
    question_ratio: float = Field(0.0, description="Fraction ending with ?")
    exclamation_ratio: float = Field(0.0, description="Fraction ending with !")


class ParagraphMetrics(BaseModel):
    avg_length: float = Field(0.0, description="Average paragraph length in sentences")
    avg_word_count: float = Field(0.0, description="Average paragraph word count")
    transition_word_density: float = Field(0.0, description="Transition words per paragraph")
    short_paragraph_ratio: float = Field(0.0, description="Paragraphs with <= 2 sentences")
    long_paragraph_ratio: float = Field(0.0, description="Paragraphs with >= 8 sentences")


class RhetoricalMetrics(BaseModel):
    metaphor_density: float = Field(0.0, description="Estimated metaphors per 1000 words")
    simile_density: float = Field(0.0, description="Similes per 1000 words")
    humor_marker_density: float = Field(0.0, description="Humor markers per 1000 words")
    emotional_intensity: float = Field(0.0, description="0-1 scale of emotional word density")
    alliteration_density: float = Field(0.0, description="Alliterative phrases per 1000 words")
    rhetorical_question_density: float = Field(0.0, description="Rhetorical questions per 1000 words")


class DialogueMetrics(BaseModel):
    dialogue_ratio: float = Field(0.0, description="Ratio of dialogue to narrative text")
    avg_dialogue_length: float = Field(0.0, description="Average dialogue segment word count")
    said_tag_ratio: float = Field(0.0, description="Fraction using 'said' vs other tags")
    action_beat_ratio: float = Field(0.0, description="Fraction of dialogue with action beats vs tags")
    dialogue_to_narrative_ratio: float = Field(0.0, description="Dialogue words / narrative words")


class VoiceFingerprint(BaseModel):
    vocabulary: VocabularyMetrics = Field(default_factory=lambda: VocabularyMetrics())  # type: ignore[call-arg]
    sentence: SentenceMetrics = Field(default_factory=lambda: SentenceMetrics())  # type: ignore[call-arg]
    paragraph: ParagraphMetrics = Field(default_factory=lambda: ParagraphMetrics())  # type: ignore[call-arg]
    rhetorical: RhetoricalMetrics = Field(default_factory=lambda: RhetoricalMetrics())  # type: ignore[call-arg]
    dialogue: DialogueMetrics = Field(default_factory=lambda: DialogueMetrics())  # type: ignore[call-arg]
    voice_vector: list[float] = Field(default_factory=list, description="200+ dimension numeric vector")
    dimension_labels: list[str] = Field(default_factory=list, description="Label for each vector dimension")


class StyleCard(BaseModel):
    summary: str = Field("", description="Natural-language style description")
    tone: str = Field("")
    pacing: str = Field("")
    vocabulary_level: str = Field("")
    sentence_style: str = Field("")
    paragraph_style: str = Field("")
    rhetorical_style: str = Field("")
    dialogue_style: str = Field("")
    example_prompts: list[str] = Field(default_factory=list)
    key_metrics: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------

class CreateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Profile name")
    description: str = Field("", max_length=2000)
    genre: str = Field("", max_length=100)
    sample_texts: list[str] = Field(
        default_factory=list,
        description="Raw sample texts (if not uploading files)",
    )
    file_format: ManuscriptFormat = Field(ManuscriptFormat.txt, description="Format when uploading a file")


class AnalyzeRequest(BaseModel):
    sample_texts: list[str] = Field(
        default_factory=list,
        description="Additional sample texts to incorporate",
    )


class GenerateSampleRequest(BaseModel):
    prompt: str = Field("Write a short passage in this author's style.", max_length=2000)
    max_words: int = Field(300, ge=50, le=5000)


class ConformityCheckRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to check against the profile")


class ConformityCheckResult(BaseModel):
    overall_score: float = Field(0.0, description="0-100 match score")
    vocabulary_score: float = Field(0.0)
    sentence_score: float = Field(0.0)
    paragraph_score: float = Field(0.0)
    rhetorical_score: float = Field(0.0)
    dialogue_score: float = Field(0.0)
    feedback: list[str] = Field(default_factory=list, description="Actionable feedback items")


class ProfileResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str
    genre: str
    status: ProfileStatus
    word_count: int
    sample_count: int
    confidence: float
    style_card: StyleCard | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileListResponse(BaseModel):
    items: list[ProfileResponse]
    total: int


class FingerprintResponse(BaseModel):
    profile_id: uuid.UUID
    fingerprint: VoiceFingerprint


class AddSampleRequest(BaseModel):
    text: str = Field(..., min_length=1)
    label: str | None = None
    source_type: str = "paste"  # paste, upload, chapter
    source_reference: uuid.UUID | None = None


class SampleResponse(BaseModel):
    id: uuid.UUID
    profile_id: uuid.UUID
    label: str | None
    source_type: str | None
    word_count: int
    file_name: str | None
    created_at: datetime


class TuneRequest(BaseModel):
    formality_adjust: float = Field(0, ge=-1, le=1)
    warmth_adjust: float = Field(0, ge=-1, le=1)
    sentence_length_adjust: float = Field(0, ge=-1, le=1)
    complexity_adjust: float = Field(0, ge=-1, le=1)


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    genre: str | None = None
    preset: str | None = None
    voice_description: str | None = None
