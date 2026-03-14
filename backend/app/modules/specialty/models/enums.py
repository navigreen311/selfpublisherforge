"""Enums for the Specialty Books module."""
import enum


class AgeRange(str, enum.Enum):
    """Target age range for children's books."""
    baby = "baby"              # 0-2
    toddler = "toddler"       # 2-4
    preschool = "preschool"   # 3-5
    early_reader = "early_reader"  # 5-7
    chapter_book = "chapter_book"  # 7-10
    middle_grade = "middle_grade"  # 9-12


class IllustrationStyle(str, enum.Enum):
    """Illustration style for children's books."""
    watercolor = "watercolor"
    cartoon = "cartoon"
    digital_painting = "digital_painting"
    flat_vector = "flat_vector"
    pencil_sketch = "pencil_sketch"
    collage = "collage"
    storybook_classic = "storybook_classic"
    anime = "anime"


class ColorPalette(str, enum.Enum):
    """Color palette for children's books."""
    bright = "bright"
    pastel = "pastel"
    earthy = "earthy"
    monochrome = "monochrome"
    neon = "neon"
    warm = "warm"
    cool = "cool"
    muted = "muted"


class StoryMode(str, enum.Enum):
    """Story generation mode."""
    ai_generated = "ai_generated"
    manual = "manual"
    hybrid = "hybrid"


class BilingualLayout(str, enum.Enum):
    """Layout for bilingual text."""
    side_by_side = "side_by_side"
    top_bottom = "top_bottom"
    alternating_pages = "alternating_pages"


class FearIntensity(str, enum.Enum):
    """Fear/intensity level for children's content."""
    none = "none"
    mild = "mild"
    moderate = "moderate"


class PageLayout(str, enum.Enum):
    """Page layout for children's book spreads."""
    full_bleed_image = "full_bleed_image"
    image_top_text_bottom = "image_top_text_bottom"
    image_left_text_right = "image_left_text_right"
    image_right_text_left = "image_right_text_left"
    text_overlay = "text_overlay"
    vignette = "vignette"
    split_panel = "split_panel"


class TextPosition(str, enum.Enum):
    """Text position on page."""
    top = "top"
    bottom = "bottom"
    left = "left"
    right = "right"
    center = "center"
    overlay = "overlay"


class BookStatus(str, enum.Enum):
    """Status of a book."""
    draft = "draft"
    in_progress = "in_progress"
    review = "review"
    approved = "approved"
    exported = "exported"
    published = "published"


class Audience(str, enum.Enum):
    """Target audience."""
    kids = "kids"
    teens = "teens"
    adults = "adults"
    seniors = "seniors"


class LineStyle(str, enum.Enum):
    """Line art style for coloring books."""
    fine = "fine"
    medium = "medium"
    bold = "bold"
    sketchy = "sketchy"
    clean = "clean"
    whimsical = "whimsical"


class ColoringPageType(str, enum.Enum):
    """Type of coloring book page."""
    illustration = "illustration"
    pattern = "pattern"
    mandala = "mandala"
    scene = "scene"
    border = "border"
    title_page = "title_page"


class PuzzleType(str, enum.Enum):
    """Type of puzzle."""
    word_search = "word_search"
    crossword = "crossword"
    maze = "maze"
    sudoku = "sudoku"
    word_scramble = "word_scramble"
    cryptogram = "cryptogram"
    number_search = "number_search"
    word_connect = "word_connect"


class Difficulty(str, enum.Enum):
    """Puzzle difficulty level."""
    easy = "easy"
    medium = "medium"
    hard = "hard"
    expert = "expert"


class DifficultyMode(str, enum.Enum):
    """How difficulty progresses through the book."""
    fixed = "fixed"
    progressive = "progressive"
    random = "random"
    chapter_based = "chapter_based"


class ClueStyle(str, enum.Enum):
    """Crossword clue style."""
    standard = "standard"
    trivia = "trivia"
    fill_in_blank = "fill_in_blank"
    thematic = "thematic"


class WordDifficulty(str, enum.Enum):
    """Word difficulty level."""
    simple = "simple"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class AnswerKeyPosition(str, enum.Enum):
    """Where to place answer keys."""
    back_of_book = "back_of_book"
    next_page = "next_page"
    same_page_upside_down = "same_page_upside_down"
    none = "none"


class BookType(str, enum.Enum):
    """Type of specialty book."""
    childrens = "childrens"
    coloring = "coloring"
    puzzle = "puzzle"
    comic = "comic"
    cookbook = "cookbook"


class CookbookType(str, enum.Enum):
    """Type of cookbook."""
    general = "general"
    baking = "baking"
    vegetarian = "vegetarian"
    vegan = "vegan"
    keto = "keto"
    paleo = "paleo"
    gluten_free = "gluten_free"
    regional = "regional"
    international = "international"
    holiday = "holiday"
    quick_easy = "quick_easy"
    gourmet = "gourmet"
    meal_prep = "meal_prep"
    kids = "kids"
    desserts = "desserts"
    family = "family"
    quick_meals = "quick_meals"


class ChapterOrganization(str, enum.Enum):
    """How cookbook chapters are organized."""
    by_meal = "by_meal"                # Breakfast, Lunch, Dinner
    by_course = "by_course"            # Appetizer, Main, Dessert
    by_ingredient = "by_ingredient"    # Chicken, Beef, Seafood
    by_cuisine = "by_cuisine"          # Italian, Mexican, Thai
    by_season = "by_season"            # Spring, Summer, Fall, Winter
    by_technique = "by_technique"      # Grilling, Baking, Slow Cooking
    by_occasion = "by_occasion"        # Weeknight, Party, Holiday
    custom = "custom"


class RecipeLayout(str, enum.Enum):
    """Layout style for recipe pages."""
    classic = "classic"                # Photo top, recipe below
    magazine = "magazine"              # Side-by-side photo and recipe
    minimal = "minimal"               # Text-focused, small photo
    full_photo = "full_photo"          # Full-page photo, recipe on next page
    step_by_step = "step_by_step"      # Photo for each step
    card = "card"                      # Recipe card format
    two_column = "two_column"          # Two recipes per page


class IllustrationMethod(str, enum.Enum):
    """How illustrations/photos are handled."""
    ai_generated = "ai_generated"
    stock_photos = "stock_photos"
    user_uploaded = "user_uploaded"
    illustrated = "illustrated"
    no_illustrations = "no_illustrations"
    mixed = "mixed"


class CookbookInteriorType(str, enum.Enum):
    """Interior printing type."""
    full_color = "full_color"
    black_and_white = "black_and_white"
    color_inserts = "color_inserts"     # B&W with color photo section


class RecipeDifficulty(str, enum.Enum):
    """Difficulty level for a recipe."""
    beginner = "beginner"
    easy = "easy"
    intermediate = "intermediate"
    advanced = "advanced"
    expert = "expert"


class MealPlanType(str, enum.Enum):
    """Type of meal plan."""
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"
    custom = "custom"


class ChapterType(str, enum.Enum):
    """Type of cookbook chapter."""
    recipes = "recipes"
    introduction = "introduction"
    techniques = "techniques"
    ingredients_guide = "ingredients_guide"
    meal_plans = "meal_plans"
    index = "index"
    about_author = "about_author"
    acknowledgments = "acknowledgments"
    conversion_charts = "conversion_charts"


class AssetType(str, enum.Enum):
    """Type of generated asset."""
    illustration = "illustration"
    line_art = "line_art"
    puzzle_grid = "puzzle_grid"
    cover = "cover"
    reference_image = "reference_image"


class BatchStatus(str, enum.Enum):
    """Status of a batch job."""
    pending = "pending"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class ISBNStatus(str, enum.Enum):
    """Status of an ISBN."""
    available = "available"
    assigned = "assigned"
    used = "used"


class DistributorName(str, enum.Enum):
    """Supported distributors."""
    kdp = "kdp"
    ingram_spark = "ingram_spark"
    bn_press = "bn_press"


class PreflightStatus(str, enum.Enum):
    """Status of a preflight check."""
    pending = "pending"
    passed = "passed"
    failed = "failed"
    warnings = "warnings"


class VariantType(str, enum.Enum):
    """Accessibility variant type."""
    dyslexia_friendly = "dyslexia_friendly"
    large_print = "large_print"
    high_contrast = "high_contrast"


class TemplateType(str, enum.Enum):
    """Back matter template type."""
    about_author = "about_author"
    also_by = "also_by"
    review_request = "review_request"
    newsletter_signup = "newsletter_signup"
    custom = "custom"


class WordListSourceType(str, enum.Enum):
    """Source type for word lists."""
    built_in = "built_in"
    user_uploaded = "user_uploaded"
    api = "api"
    curated = "curated"


class CookbookType(str, enum.Enum):
    """Type of cookbook."""
    general = "general"
    baking = "baking"
    vegetarian = "vegetarian"
    vegan = "vegan"
    keto = "keto"
    paleo = "paleo"
    gluten_free = "gluten_free"
    regional = "regional"
    holiday = "holiday"
    meal_prep = "meal_prep"
    kids = "kids"
    desserts = "desserts"


class RecipeDifficulty(str, enum.Enum):
    """Difficulty level for recipes."""
    easy = "easy"
    medium = "medium"
    hard = "hard"
    expert = "expert"


class LicenseType(str, enum.Enum):
    """Font license type."""
    open_source = "open_source"
    commercial = "commercial"
    personal = "personal"
    sil_ofl = "sil_ofl"


class ComicFormat(str, enum.Enum):
    """Comic book format/type."""
    single_issue = "single_issue"          # Standard 22-32 pages
    graphic_novel = "graphic_novel"        # 48-200+ pages
    manga = "manga"                        # Japanese style, right-to-left
    webcomic = "webcomic"                  # Digital-first format
    mini_series = "mini_series"            # 4-6 issue limited series
    one_shot = "one_shot"                  # Single standalone issue
    trade_paperback = "trade_paperback"    # Collected edition
    minicomic = "minicomic"


class ComicArtStyle(str, enum.Enum):
    """Art style for comic book illustrations."""
    american_classic = "american_classic"
    manga = "manga"
    franco_belgian = "franco_belgian"
    indie = "indie"
    cartoon = "cartoon"
    realistic = "realistic"
    noir = "noir"
    watercolor = "watercolor"
    pixel_art = "pixel_art"
    minimalist = "minimalist"


class ColorMode(str, enum.Enum):
    """Color mode for comic art."""
    full_color = "full_color"
    grayscale = "grayscale"
    black_and_white = "black_and_white"
    duotone = "duotone"
    limited_palette = "limited_palette"
    spot_color = "spot_color"


class InkStyle(str, enum.Enum):
    """Inking style for comic art."""
    clean = "clean"
    hatching = "hatching"
    cross_hatching = "cross_hatching"
    brush = "brush"
    digital = "digital"
    woodcut = "woodcut"
    stipple = "stipple"


class ComicPacing(str, enum.Enum):
    """Pacing style for comic storytelling."""
    action = "action"
    dialogue_heavy = "dialogue_heavy"
    balanced = "balanced"
    cinematic = "cinematic"
    decompressed = "decompressed"
    compressed = "compressed"


class TargetAudience(str, enum.Enum):
    """Target audience for comic books."""
    all_ages = "all_ages"
    kids = "kids"               # 6-12
    teen = "teen"                # 13-17
    young_adult = "young_adult" # 16-25
    mature = "mature"           # 18+


class PanelType(str, enum.Enum):
    """Type of comic panel."""
    standard = "standard"
    wide = "wide"
    tall = "tall"
    splash = "splash"           # Full page
    double_splash = "double_splash"  # Two-page spread
    inset = "inset"             # Small panel inside another
    borderless = "borderless"
    circular = "circular"
    diagonal = "diagonal"


class BubbleType(str, enum.Enum):
    """Type of speech/text bubble."""
    speech = "speech"
    thought = "thought"
    narration = "narration"
    whisper = "whisper"
    shout = "shout"
    radio = "radio"             # Electronic/radio communication
    caption = "caption"
    sfx = "sfx"                 # Sound effect


class BorderStyle(str, enum.Enum):
    """Panel border style."""
    solid = "solid"
    dashed = "dashed"
    wavy = "wavy"
    jagged = "jagged"
    none = "none"
    double = "double"
    rough = "rough"


class GutterStyle(str, enum.Enum):
    """Gutter (space between panels) style."""
    standard = "standard"
    narrow = "narrow"
    wide = "wide"
    none = "none"
    bleeding = "bleeding"
