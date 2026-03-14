"""Pydantic v2 schemas for the Specialty Books module."""

# ---------------------------------------------------------------------------
# Children's Book Studio
# ---------------------------------------------------------------------------
from .childrens import (
    AgeRange,
    AnalyzeTextRequest,
    BilingualLayout,
    BookStatus,
    CharacterCreate,
    CharacterResponse,
    CharacterSheet,
    CharacterUpdate,
    ChildrensBookCreate,
    ChildrensBookResponse,
    ChildrensBookUpdate,
    ColorPalette,
    ContentIssue,
    ContinuityCheckRequest,
    ContinuityIssue,
    ContinuityReport,
    CreationMode,
    DevicePreviewRequest,
    DevicePreviewResponse,
    DeviceType,
)
from .childrens import ExportFormat as ChildrensExportFormat
from .childrens import (
    ExportRequest as ChildrensExportRequest,
)
from .childrens import (
    ExportResponse as ChildrensExportResponse,
)
from .childrens import (
    FearIntensity,
    GenerateStoryRequest,
    IllustrationStyle,
    LanguageReport,
    PageCreate,
    PageLayout,
    PageReorderRequest,
    PageResponse,
    PageTurnEvent,
    PageType,
    PageUpdate,
)
from .childrens import PreflightCheck as ChildrensPreflightCheck
from .childrens import PreflightReport as ChildrensPreflightReport
from .childrens import PreflightRequest as ChildrensPreflightRequest
from .childrens import (
    SafetyCheckRequest,
    SafetyReport,
    StoryGenerationResponse,
    StoryMode,
    StoryPageContent,
    TextAnalysisResponse,
    TextIssue,
    TextPosition,
    TrademarkIssue,
    TranslateRequest,
    TranslateResponse,
)

# ---------------------------------------------------------------------------
# Coloring Book Creator
# ---------------------------------------------------------------------------
from .coloring import (
    Audience,
    BatchGenerateRequest,
)
from .coloring import BatchStatusResponse as ColoringBatchStatusResponse
from .coloring import (
    CleanLinesRequest,
    ColoringBookCreate,
    ColoringBookResponse,
    ColoringBookStatus,
    ColoringBookUpdate,
)
from .coloring import ColoringExportFormat
from .coloring import (
    ColoringPageResponse,
    ColoringPageType,
    ColoringSimulationMedia,
    ComplexityBucket,
)
from .coloring import ExportRequest as ColoringExportRequest
from .coloring import (
    GenerateLineArtRequest,
    LineStyle,
    PageBatchStatus,
    PlanSeriesRequest,
)
from .coloring import PreflightCheck as ColoringPreflightCheck
from .coloring import PreflightReport as ColoringPreflightReport
from .coloring import PreflightRequest as ColoringPreflightRequest
from .coloring import (
    PrintQualitySummary,
    QualityCheckResponse,
    QualityDashboardResponse,
    QualityIssue,
    QualityStep,
    QualityStepResult,
    SeriesPlanResponse,
    VariationMode,
    VectorizeRequest,
    VolumePlan,
)

# ---------------------------------------------------------------------------
# Puzzle Book Generator
# ---------------------------------------------------------------------------
from .puzzles import (
    AmbiguousClue,
    AnswerKeyPosition,
    AnswerKeyResponse,
    ClueQAIssue,
    ClueQAResponse,
    ClueStyle,
    Difficulty,
    DifficultyCalibrationResponse,
    DifficultyMode,
)
from .puzzles import ExportRequest as PuzzleExportRequest
from .puzzles import (
    GenerateLargePrintRequest,
    GeneratePuzzleRequest,
    GenerateWordListRequest,
    LargePrintResponse,
    LargePrintScale,
    LayoutMode,
    PacingAnalysis,
)
from .puzzles import PreflightCheck as PuzzlePreflightCheck
from .puzzles import PreflightReport as PuzzlePreflightReport
from .puzzles import PreflightRequest as PuzzlePreflightRequest
from .puzzles import (
    PuzzleAudience,
    PuzzleBookCreate,
    PuzzleBookResponse,
    PuzzleBookStatus,
    PuzzleBookUpdate,
    PuzzleClue,
    PuzzleDifficultyScore,
)
from .puzzles import PuzzleExportFormat
from .puzzles import (
    PuzzleResponse,
    PuzzleType,
    PuzzleTypeConfig,
    PuzzleVerification,
    RemovedWord,
    SanitizeWordListRequest,
    SanitizeWordListResponse,
    VerifyAnswerKeyResponse,
    WordDifficulty,
    WordListResponse,
)

# ---------------------------------------------------------------------------
# Shared / Cross-Cutting Systems
# ---------------------------------------------------------------------------
from .shared import (
    AccessibleVariantRequest,
    AccessibleVariantResponse,
    AccessibleVariantType,
    BackMatterRequest,
    BackMatterResponse,
    BackMatterType,
    BatchCreateRequest,
    BatchCreateResponse,
    BatchJobStatus,
)
from .shared import BatchStatusResponse as SharedBatchStatusResponse
from .shared import (
    BookType,
    CategorySuggestion,
    CoherenceCheckResponse,
    CoherenceIssue,
    ColorAutoAdjustRequest,
    ColorAutoAdjustResponse,
    ColorProfile,
    CompareRequest,
    CompareResponse,
    Distributor,
    FingerprintRequest,
    FingerprintResponse,
    GamutWarning,
    InkCoverageRequest,
    InkCoverageResponse,
    MarginAnalysis,
    MetadataAdvisorRequest,
    MetadataAdvisorResponse,
    PageInkCoverage,
    PricingCalculateRequest,
    PricingCalculateResponse,
    PricingScenario,
    ProvenanceExportResponse,
    ProvenanceResponse,
    QRCodeRequest,
    QRCodeResponse,
    SeriesCreate,
    SeriesResponse,
    SimilarityDetail,
    SoftProofRequest,
    SoftProofResponse,
    SpamCheckRequest,
    SpamCheckResponse,
    SpamRiskLevel,
    TemplateResponse,
)

__all__ = [
    # Children's enums
    "AgeRange",
    "IllustrationStyle",
    "ColorPalette",
    "StoryMode",
    "BilingualLayout",
    "FearIntensity",
    "PageLayout",
    "TextPosition",
    "BookStatus",
    "ChildrensExportFormat",
    "DeviceType",
    "CreationMode",
    "PageType",
    # Children's book CRUD
    "ChildrensBookCreate",
    "ChildrensBookUpdate",
    "ChildrensBookResponse",
    # Children's pages
    "PageCreate",
    "PageUpdate",
    "PageResponse",
    "PageReorderRequest",
    # Children's characters
    "CharacterCreate",
    "CharacterUpdate",
    "CharacterResponse",
    "CharacterSheet",
    # Children's story generation
    "GenerateStoryRequest",
    "StoryGenerationResponse",
    "StoryPageContent",
    "LanguageReport",
    # Children's text analysis
    "AnalyzeTextRequest",
    "TextAnalysisResponse",
    "TextIssue",
    "PageTurnEvent",
    # Children's continuity
    "ContinuityCheckRequest",
    "ContinuityReport",
    "ContinuityIssue",
    # Children's safety
    "SafetyCheckRequest",
    "SafetyReport",
    "TrademarkIssue",
    "ContentIssue",
    # Children's translation
    "TranslateRequest",
    "TranslateResponse",
    # Children's export & preflight
    "ChildrensExportRequest",
    "ChildrensExportResponse",
    "DevicePreviewRequest",
    "DevicePreviewResponse",
    "ChildrensPreflightRequest",
    "ChildrensPreflightReport",
    "ChildrensPreflightCheck",
    # Coloring enums
    "Audience",
    "LineStyle",
    "ColoringPageType",
    "QualityStep",
    "ColoringBookStatus",
    "ColoringExportFormat",
    "VariationMode",
    "ColoringSimulationMedia",
    # Coloring book CRUD
    "ColoringBookCreate",
    "ColoringBookUpdate",
    "ColoringBookResponse",
    # Coloring pages
    "ColoringPageResponse",
    # Coloring line art
    "GenerateLineArtRequest",
    "CleanLinesRequest",
    "VectorizeRequest",
    # Coloring quality
    "QualityCheckResponse",
    "QualityStepResult",
    "QualityIssue",
    # Coloring batch
    "BatchGenerateRequest",
    "ColoringBatchStatusResponse",
    "PageBatchStatus",
    # Coloring series
    "PlanSeriesRequest",
    "SeriesPlanResponse",
    "VolumePlan",
    # Coloring dashboard
    "QualityDashboardResponse",
    "ComplexityBucket",
    "PrintQualitySummary",
    # Coloring export & preflight
    "ColoringExportRequest",
    "ColoringPreflightRequest",
    "ColoringPreflightReport",
    "ColoringPreflightCheck",
    # Puzzle enums
    "PuzzleType",
    "Difficulty",
    "DifficultyMode",
    "ClueStyle",
    "WordDifficulty",
    "AnswerKeyPosition",
    "LayoutMode",
    "PuzzleBookStatus",
    "PuzzleAudience",
    "PuzzleExportFormat",
    "LargePrintScale",
    # Puzzle book CRUD
    "PuzzleBookCreate",
    "PuzzleBookUpdate",
    "PuzzleBookResponse",
    "PuzzleTypeConfig",
    # Puzzle individual
    "PuzzleResponse",
    "PuzzleClue",
    "PuzzleVerification",
    # Puzzle generation
    "GeneratePuzzleRequest",
    # Puzzle word lists
    "GenerateWordListRequest",
    "WordListResponse",
    "SanitizeWordListRequest",
    "SanitizeWordListResponse",
    "RemovedWord",
    # Puzzle clues
    "ClueQAResponse",
    "ClueQAIssue",
    "AmbiguousClue",
    # Puzzle answer key
    "AnswerKeyResponse",
    "VerifyAnswerKeyResponse",
    # Puzzle difficulty
    "DifficultyCalibrationResponse",
    "PuzzleDifficultyScore",
    "PacingAnalysis",
    # Puzzle large print
    "GenerateLargePrintRequest",
    "LargePrintResponse",
    # Puzzle export & preflight
    "PuzzleExportRequest",
    "PuzzlePreflightRequest",
    "PuzzlePreflightReport",
    "PuzzlePreflightCheck",
    # Shared enums
    "BookType",
    "Distributor",
    "AccessibleVariantType",
    "BackMatterType",
    "BatchJobStatus",
    "SpamRiskLevel",
    "ColorProfile",
    # Shared metadata
    "MetadataAdvisorRequest",
    "MetadataAdvisorResponse",
    "CategorySuggestion",
    # Shared provenance
    "ProvenanceResponse",
    "ProvenanceExportResponse",
    # Shared originality
    "FingerprintRequest",
    "FingerprintResponse",
    "CompareRequest",
    "CompareResponse",
    "SimilarityDetail",
    "SpamCheckRequest",
    "SpamCheckResponse",
    # Shared pricing
    "PricingCalculateRequest",
    "PricingCalculateResponse",
    "PricingScenario",
    "MarginAnalysis",
    # Shared ink & color
    "InkCoverageRequest",
    "InkCoverageResponse",
    "PageInkCoverage",
    "SoftProofRequest",
    "SoftProofResponse",
    "GamutWarning",
    "ColorAutoAdjustRequest",
    "ColorAutoAdjustResponse",
    # Shared batch
    "BatchCreateRequest",
    "BatchCreateResponse",
    "SharedBatchStatusResponse",
    # Shared series
    "SeriesCreate",
    "SeriesResponse",
    "CoherenceCheckResponse",
    "CoherenceIssue",
    # Shared back matter & QR
    "BackMatterRequest",
    "BackMatterResponse",
    "QRCodeRequest",
    "QRCodeResponse",
    # Shared accessibility
    "AccessibleVariantRequest",
    "AccessibleVariantResponse",
    # Shared templates
    "TemplateResponse",
]
