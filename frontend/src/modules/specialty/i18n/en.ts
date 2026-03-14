/**
 * English i18n strings for the Specialty Books module.
 */

const en = {
  // ---------------------------------------------------------------------------
  // Common / shared
  // ---------------------------------------------------------------------------
  common: {
    specialty_books: "Specialty Books",
    childrens_books: "Children's Books",
    coloring_books: "Coloring Books",
    puzzle_books: "Puzzle Books",
    create: "Create",
    save: "Save",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit",
    duplicate: "Duplicate",
    export: "Export",
    preview: "Preview",
    publish: "Publish",
    back: "Back",
    next: "Next",
    finish: "Finish",
    loading: "Loading...",
    saving: "Saving...",
    generating: "Generating...",
    processing: "Processing...",
    search: "Search...",
    no_results: "No results found",
    confirm_delete: "Are you sure you want to delete this?",
    status: "Status",
    draft: "Draft",
    in_progress: "In Progress",
    published: "Published",
    created_at: "Created",
    updated_at: "Updated",
    actions: "Actions",
    view_details: "View Details",
    download: "Download",
    close: "Close",
    retry: "Retry",
    page: "Page",
    pages: "Pages",
    of: "of",
  },

  // ---------------------------------------------------------------------------
  // Children's Book Studio
  // ---------------------------------------------------------------------------
  childrens: {
    // Landing page
    title: "Children's Book Studio",
    subtitle: "Create illustrated children's books with AI-generated artwork",
    stat_total_books: "Total Books",
    stat_in_progress: "In Progress",
    stat_published: "Published",
    stat_pages_created: "Pages Created",
    create_book: "Create Children's Book",
    empty_state: "No children's books yet. Create your first illustrated book!",
    empty_state_cta: "Create Your First Book",

    // Wizard steps
    wizard_title: "Create Children's Book",
    step_book_details: "Book Details",
    step_format_style: "Format & Style",
    step_story_setup: "Story Setup",
    step_safety_settings: "Content Safety",

    // Step 1: Book Details
    field_title: "Title",
    field_title_placeholder: "Enter book title",
    field_subtitle: "Subtitle",
    field_subtitle_placeholder: "Optional subtitle",
    field_author: "Author",
    field_author_placeholder: "Select author or pen name",
    field_age_range: "Age Range",
    age_board: "Board Book (0-3)",
    age_board_desc: "10-16 pages",
    age_picture: "Picture Book (3-5)",
    age_picture_desc: "24-32 pages",
    age_early_reader: "Early Reader (5-8)",
    age_early_reader_desc: "32-48 pages",
    age_chapter: "Chapter Book (8-12)",
    age_chapter_desc: "48-80 pages",
    field_bilingual: "Bilingual Edition",
    field_bilingual_language: "Second Language",
    field_bilingual_layout: "Bilingual Layout",
    bilingual_side_by_side: "Side by Side",
    bilingual_alternating: "Alternating Pages",
    bilingual_back_section: "Back Section",

    // Step 2: Format & Style
    field_page_count: "Page Count",
    field_trim_size: "Trim Size",
    trim_square: "8.5x8.5 (Square)",
    trim_portrait: "8.5x11 (Portrait)",
    trim_landscape: "10x8 (Landscape)",
    trim_chapter: "6x9 (Chapter)",
    field_illustration_style: "Illustration Style",
    style_watercolor: "Watercolor",
    style_cartoon: "Cartoon",
    style_flat: "Flat",
    style_storybook: "Storybook",
    style_realistic: "Realistic",
    style_crayon_pencil: "Crayon/Pencil",
    style_collage: "Collage",
    style_anime_manga: "Anime/Manga",
    field_color_palette: "Color Palette",
    palette_bright: "Bright & Vibrant",
    palette_pastel: "Soft & Pastel",
    palette_earthy: "Warm & Earthy",
    palette_dreamy: "Cool & Dreamy",
    palette_monochrome: "Monochrome + Accent",

    // Step 3: Story Setup
    field_creation_mode: "Creation Mode",
    mode_ai_generate: "AI Generate Full Story",
    mode_write_own: "Write My Own",
    mode_import: "Import Text",
    field_story_prompt: "Story Prompt",
    field_story_prompt_placeholder: "Describe the story you want AI to generate...",
    field_theme_moral: "Theme / Moral",
    field_theme_moral_placeholder: "e.g., Courage / Overcoming fears",
    field_main_character: "Main Character",
    field_main_character_placeholder: "e.g., Luna - a small orange tabby kitten",
    field_setting: "Setting",
    field_setting_placeholder: "e.g., A cozy village with gardens and woods",
    field_tone: "Tone",
    tone_warm: "Warm & Reassuring",
    tone_exciting: "Exciting",
    tone_humorous: "Humorous",
    tone_educational: "Educational",
    field_story_mode: "Story Mode",
    mode_prose: "Prose",
    mode_rhyming: "Rhyming (AABB or ABAB)",
    mode_repetitive: "Repetitive-Cumulative",

    // Step 4: Safety Settings
    field_fear_intensity: "Fear Intensity Level",
    fear_none: "None",
    fear_mild: "Mild",
    fear_moderate: "Moderate",
    safety_no_weapons: "No weapons or violence",
    safety_no_scary: "No scary/dark imagery",
    safety_no_trademarks: "No trademarked characters",
    safety_no_stereotypes: "No stereotypical depictions",
    safety_age_vocab: "Age-appropriate vocabulary",
    safety_trademark_prompts: "Trademark-safe prompt enforcement",
    safety_sensitivity: "Content sensitivity pre-check",
    safety_provenance: "Model/style provenance logging",

    // Page Spread Editor
    editor_title: "Page Spread Editor",
    editor_thumbnail_strip: "Pages",
    editor_spread_view: "Spread View",
    editor_properties: "Properties",
    editor_reorder_tooltip: "Drag to reorder pages",

    // Layout options
    layout_full_bleed: "Full Bleed",
    layout_top_image: "Top Image / Bottom Text",
    layout_bottom_image: "Bottom Image / Top Text",
    layout_left_image: "Left Image / Right Text",
    layout_right_image: "Right Image / Left Text",
    layout_text_only: "Text Only",
    layout_full_bleed_no_text: "Full Bleed No Text",

    // Text properties
    text_font: "Font",
    text_size: "Size",
    text_color: "Color",
    text_position: "Position",
    text_contrast: "Contrast Score",
    text_plate: "Text Plate",
    text_plate_tooltip: "Adds subtle background behind text when contrast is low",

    // Illustration properties
    illustration_prompt: "Illustration Prompt",
    illustration_prompt_placeholder: "Describe what this page should look like...",
    btn_generate: "Generate Illustration",
    btn_upload: "Upload Own Image",
    btn_regenerate: "Regenerate",
    btn_edit_prompt: "Edit Prompt",
    btn_generate_variations: "Generate 4 Variations",
    character_consistency: "Character Consistency",
    character_consistency_tooltip: "Auto-appends character description to prompt",
    provenance_info: "Provenance",

    // Character system
    characters_title: "Characters",
    character_add: "Add Character",
    character_name: "Name",
    character_species: "Species / Type",
    character_description: "Description",
    character_references: "Reference Images",
    character_generate_refs: "Generate Reference Images",
    character_auto_append: "Auto-append to prompts",
    character_clothing_rules: "Clothing / Accessory Rules",
    character_scale_rules: "Scale Rules",
    character_setting_rules: "Setting Continuity Rules",
    character_time_rules: "Time-of-Day Rules",

    // Text analysis
    text_analysis_title: "Text Analysis",
    readability_score: "Readability Score",
    read_aloud_rhythm: "Read-Aloud Rhythm Score",
    page_turn_surprise: "Page-Turn Surprise Map",
    look_inside_score: "Look Inside Score",
    rhyme_assistant: "Rhyme Assistant",

    // Continuity
    continuity_title: "Continuity Check",
    btn_check_continuity: "Check Continuity",
    btn_auto_fix_prompts: "Auto-Fix Prompts",

    // Safety
    safety_title: "Safety Check",
    btn_check_safety: "Run Safety Check",
    trademark_clear: "Trademark Clear",
    content_clear: "Content Clear",

    // Preview
    preview_title: "Preview",
    preview_spread: "Spread View",
    preview_single: "Single Page",
    preview_look_inside: "Look Inside Simulator",
    preview_mobile: "Mobile Preview",
    preview_desktop: "Desktop Preview",
    preview_hook_score: "Hook Score",
    preview_guides: "Guide Overlays",
    guide_bleed: "Bleed Zone",
    guide_trim: "Trim Line",
    guide_safe: "Safe Zone",
    guide_gutter: "Gutter Zone",

    // Export
    export_title: "Export & Publish",
    export_print_pdf: "Print-Ready PDF",
    export_kpf: "Fixed-Layout KPF",
    export_epub: "Fixed-Layout EPUB 3",
    export_pages: "Individual Pages (PNG)",
    btn_run_preflight: "Run Preflight",
    btn_export: "Export",
    preflight_title: "Preflight Check",
    preflight_all_clear: "All preflight checks passed",
    preflight_issues: "Issues found - please review before export",
  },

  // ---------------------------------------------------------------------------
  // Coloring Book Creator
  // ---------------------------------------------------------------------------
  coloring: {
    // Landing page
    title: "Coloring Book Creator",
    subtitle: "Create professional coloring books with AI-generated line art",
    stat_total_books: "Total Books",
    stat_in_progress: "In Progress",
    stat_published: "Published",
    stat_pages_created: "Pages Created",
    create_book: "Create Coloring Book",
    empty_state: "No coloring books yet. Start with a template or create from scratch!",
    empty_state_cta: "Create Your First Coloring Book",

    // Templates
    templates_title: "Quick Start Templates",
    template_animals: "Animals & Wildlife",
    template_mandalas: "Mandalas & Patterns",
    template_fantasy: "Fantasy Worlds",
    template_nature: "Nature Scenes",
    template_holidays: "Holidays & Seasons",
    template_space: "Space & Sci-Fi",
    template_food: "Food & Desserts",
    template_geometric: "Geometric Abstract",

    // Wizard steps
    wizard_title: "Create Coloring Book",
    step_book_details: "Book Details",
    step_format_style: "Format & Style",
    step_content: "Content",

    // Step 1
    field_title: "Title",
    field_subtitle: "Subtitle",
    field_audience: "Audience",
    audience_kids: "Kids (3-8)",
    audience_teens: "Teens (9-14)",
    audience_adults: "Adults (15+)",
    field_series: "Series",
    field_series_name: "Series Name",
    field_volume_number: "Volume Number",

    // Step 2
    field_page_count: "Page Count",
    field_trim_size: "Trim Size",
    field_line_style: "Line Art Style",
    style_clean: "Clean Outlines",
    style_sketchy: "Sketchy Hand-drawn",
    style_whimsical: "Whimsical Decorative",
    style_realistic: "Realistic Detailed",
    style_zentangle: "Zentangle",
    style_bold: "Bold & Simple",
    field_line_weight: "Line Weight",
    field_stroke_uniformity: "Stroke Uniformity Enforcement",
    field_complexity: "Complexity",
    complexity_low: "Low",
    complexity_medium: "Medium",
    complexity_high: "High",
    enforced_single_sided: "Single-sided printing (enforced)",
    enforced_coloring_margin: "Coloring-safe inner margin (+0.25in at spine)",

    // Step 3
    field_theme: "Theme Description",
    field_theme_placeholder: "Describe the overall theme for your coloring book...",
    field_generation_method: "Generation Method",
    method_all: "All at Once",
    method_one: "One at a Time",
    method_mix: "Mix",
    field_bonus_pages: "Bonus Pages",
    bonus_title: "Title Page",
    bonus_belongs_to: "This Book Belongs To",
    bonus_color_test: "Color Test Page",
    bonus_progress: "Progress Tracker",
    bonus_certificate: "Certificate of Completion",
    bonus_difficulty: "Difficulty Ratings",

    // Line art quality
    quality_pipeline_title: "Line Art Quality Pipeline",
    quality_step_generate: "Generate",
    quality_step_auto_clean: "Auto-Clean",
    quality_step_stroke: "Stroke Uniformity",
    quality_step_closed_shapes: "Closed Shapes",
    quality_step_speck: "Speck Removal",
    quality_step_background: "Background",
    quality_step_final: "Quality Check",
    btn_vectorize: "Vectorize (SVG)",
    btn_coloring_simulation: "Coloring Simulation",
    simulation_marker: "Marker",
    simulation_crayon: "Crayon",
    simulation_pencil: "Colored Pencil",

    // Editor
    editor_title: "Page Editor",
    tool_brush: "Brush (White)",
    tool_pen: "Pen (Black)",
    tool_eraser: "Eraser",
    tool_fill: "Fill (White)",
    tool_smooth: "Smooth Lines",
    tool_close_shape: "Close Shape",
    tool_normalize: "Normalize Stroke",

    // Batch generation
    batch_title: "Batch Generation",
    batch_description_list: "Page Descriptions",
    batch_progress: "Progress",
    batch_cost_estimate: "Estimated Cost",
    btn_pause: "Pause",
    btn_resume: "Resume",
    btn_cancel_batch: "Cancel",

    // Quality dashboard
    dashboard_title: "Quality Dashboard",
    dashboard_overall_score: "Overall Quality Score",
    dashboard_complexity: "Complexity Distribution",
    dashboard_theme_cohesion: "Theme Cohesion Score",
    dashboard_print_quality: "Print Quality",
    metric_line_quality: "Line Quality",
    metric_closed_shapes: "Closed Shapes",
    metric_stroke_uniformity: "Stroke Uniformity",
    metric_ink_density: "Ink Density",
    metric_small_areas: "Small Areas",
    btn_fix_all: "Fix All Issues",
    btn_rerun_qa: "Re-run Full QA",

    // Volume factory
    volume_title: "Volume Factory",
    volume_plan_series: "Plan Series",
    volume_generate_next: "Auto-Generate Next Volume",
    volume_batch_export: "Batch Export All Volumes",
    volume_branding_locked: "Branding Locked",

    // Export
    export_title: "Export",
    export_print_pdf: "Print-Ready PDF (KDP)",
    export_png: "Individual PNGs",
    export_svg: "SVG Vector Package",
    export_digital: "Digital PDF",
    btn_run_preflight: "Run Preflight",
    btn_export: "Export",
  },

  // ---------------------------------------------------------------------------
  // Puzzle Book Generator
  // ---------------------------------------------------------------------------
  puzzles: {
    // Landing page
    title: "Puzzle Book Generator",
    subtitle: "Generate professional puzzle books with algorithmic precision",
    stat_total_books: "Total Books",
    stat_in_progress: "In Progress",
    stat_published: "Published",
    stat_puzzles_created: "Puzzles Created",
    create_book: "Create Puzzle Book",
    empty_state: "No puzzle books yet. Choose a template or create from scratch!",
    empty_state_cta: "Create Your First Puzzle Book",

    // Puzzle types
    type_word_search: "Word Search",
    type_crossword: "Crossword",
    type_maze: "Maze",
    type_sudoku: "Sudoku",
    type_word_scramble: "Word Scramble",
    type_cryptogram: "Cryptogram",
    type_number_search: "Number Search",
    type_word_connect: "Word Connect",

    // Wizard steps
    wizard_title: "Create Puzzle Book",
    step_book_details: "Book Details",
    step_puzzle_selection: "Puzzle Selection",
    step_themes_words: "Themes & Words",
    step_layout_extras: "Layout & Extras",

    // Step 1
    field_title: "Title",
    field_subtitle: "Subtitle",
    field_subtitle_hint: "AI suggests including puzzle types + 'with answers'",
    field_audience: "Audience",
    audience_kids: "Kids",
    audience_teens: "Teens",
    audience_adults: "Adults",
    audience_large_print: "Large Print (150% scale)",
    field_series: "Series",
    field_series_name: "Series Name",
    field_volume_number: "Volume Number",

    // Step 2
    field_puzzle_types: "Puzzle Types",
    field_quantity: "Quantity",
    field_difficulty: "Difficulty",
    field_grid_size: "Grid Size",
    difficulty_easy: "Easy",
    difficulty_medium: "Medium",
    difficulty_hard: "Hard",
    field_difficulty_mode: "Difficulty Calibration",
    mode_progressive: "Progressive (easy to hard)",
    mode_fixed: "Fixed",
    mode_mixed: "Mixed Random",
    field_puzzle_mix: "Puzzle Mix Template",
    mix_balanced: "Balanced",
    mix_word_heavy: "Word-heavy",
    mix_custom: "Custom Percentages",

    // Step 3
    field_theme_method: "Theme Method",
    method_ai: "AI Generate by Theme",
    method_custom: "Custom Word Lists",
    method_mix: "Mix",
    field_theme_categories: "Theme Categories",
    theme_animals: "Animals",
    theme_nature: "Nature",
    theme_food: "Food",
    theme_sports: "Sports",
    theme_science: "Science",
    theme_history: "History",
    field_seasonal: "Seasonal / Holiday Theme",
    field_word_difficulty: "Word Difficulty",
    word_simple: "Simple (3-6 letters)",
    word_standard: "Standard (4-10 letters)",
    word_advanced: "Advanced (6-15 letters)",
    field_word_list: "Word List",
    btn_generate_word_list: "Generate Word List",
    btn_sanitize: "Sanitize Word List",
    sanitize_removed: "Removed {count} problematic words",
    sanitize_clean: "Word list is clean",

    // Step 4
    field_answer_key: "Answer Key Position",
    answer_back: "Back of Book",
    answer_reverse: "Reverse of Puzzle Page",
    answer_none: "No Answer Key",
    field_extras: "Extras",
    extra_toc: "Table of Contents",
    extra_instructions: "Instructions per Type",
    extra_difficulty_badges: "Difficulty Badges",
    extra_section_dividers: "Section Dividers",
    field_hints: "Hint System",
    hint_first_letter: "First Letter (Crosswords)",
    hint_theme: "Theme Hints",
    field_clue_style: "Clue Style",
    clue_standard: "Standard",
    clue_kid_friendly: "Kid-Friendly",
    clue_trivia: "Trivia",
    clue_themed: "Themed",
    field_layout: "Layout",
    layout_one: "One Puzzle Per Page",
    layout_two: "Two Puzzles Per Page",

    // Puzzle editor
    editor_title: "Puzzle Editor",
    btn_generate_puzzle: "Generate Puzzle",
    btn_regenerate: "Regenerate",
    btn_verify: "Verify Solution",
    btn_generate_clues: "Generate Clues",
    btn_qa_clues: "QA Clues",
    verified: "Verified",
    not_verified: "Not Verified",
    solvable: "Solvable",
    unique_solution: "Unique Solution",

    // Difficulty calibration
    calibration_title: "Difficulty Calibration",
    calibration_score: "Difficulty Score",
    calibration_pacing: "Pacing Score",
    calibration_distribution: "Difficulty Distribution",

    // Clue governance
    clue_qa_title: "Clue Quality",
    clue_ambiguity: "Ambiguity Score",
    clue_duplicates: "Duplicate Phrasings",
    clue_grade_level: "Grade Level",
    btn_auto_fix_clues: "Auto-Fix Clues",

    // Answer key
    answer_key_title: "Answer Key",
    btn_generate_answer_key: "Generate Answer Key",
    btn_verify_answer_key: "Verify Answer Key",
    answer_key_verified: "All answer keys verified",
    answer_key_issues: "Answer key issues found",

    // Large print
    large_print_title: "Large Print Variant",
    btn_generate_large_print: "Generate Large Print Edition",
    large_print_scale: "Scale",
    scale_125: "125%",
    scale_150: "150%",
    scale_175: "175%",

    // Quality dashboard
    dashboard_title: "Quality Dashboard",
    dashboard_overall_score: "Overall Quality Score",
    dashboard_duplicate_grids: "Duplicate Grids",
    dashboard_word_overlap: "Word List Overlap",
    dashboard_all_verified: "All Puzzles Verified",
    dashboard_unverified: "Unverified Puzzles",
    btn_rerun_qa: "Re-run Full QA",

    // Word list manager
    word_list_title: "Word List Manager",
    btn_add_words: "Add Words",
    btn_remove_word: "Remove",
    btn_import_list: "Import List",

    // Export
    export_title: "Export",
    export_print_pdf: "Print-Ready PDF",
    export_png: "Individual PNGs",
    btn_run_preflight: "Run Preflight",
    btn_export: "Export",
  },

  // ---------------------------------------------------------------------------
  // Shared systems
  // ---------------------------------------------------------------------------
  shared: {
    // Provenance
    provenance_title: "Asset Provenance",
    provenance_model: "Model",
    provenance_prompt_hash: "Prompt Hash",
    provenance_seed: "Seed",
    provenance_date: "Generation Date",
    provenance_status: "Status",
    btn_export_provenance: "Export Provenance Report",

    // Originality
    originality_title: "Originality Check",
    originality_score: "Originality Score",
    originality_fingerprint: "Content Fingerprint",
    btn_run_fingerprint: "Generate Fingerprint",
    btn_compare: "Compare Books",
    btn_spam_check: "Run Spam Check",
    spam_risk: "Spam Risk Level",
    spam_risk_low: "Low Risk",
    spam_risk_medium: "Medium Risk",
    spam_risk_high: "High Risk",
    spam_risk_critical: "Critical Risk",

    // Pricing
    pricing_title: "Print Cost & Pricing",
    pricing_print_cost: "Print Cost",
    pricing_min_price: "Minimum List Price",
    pricing_recommended: "Recommended Price",
    pricing_royalty: "Estimated Royalty",
    pricing_margin: "Margin",
    btn_calculate_pricing: "Calculate Pricing",
    btn_ink_coverage: "Analyze Ink Coverage",
    ink_coverage_title: "Ink Coverage Analysis",
    ink_coverage_average: "Average Coverage",

    // Color management
    color_title: "Color Management",
    soft_proof_title: "CMYK Soft-Proof",
    btn_soft_proof: "Generate Soft-Proof",
    btn_auto_adjust: "Auto-Adjust Colors",
    gamut_warnings: "Out-of-Gamut Warnings",
    shadow_crush: "Shadow Crush",
    ink_density: "Ink Density",

    // Batch factory
    batch_title: "Batch Factory",
    batch_status: "Status",
    batch_progress: "Progress",
    batch_budget: "Budget",
    batch_spent: "Spent",
    btn_create_batch: "Create Batch Job",
    btn_pause_batch: "Pause",
    btn_cancel_batch: "Cancel",

    // Templates
    templates_title: "Templates & Packs",
    templates_empty: "No templates available for this book type",

    // Series
    series_title: "Series Manager",
    series_name: "Series Name",
    series_naming_format: "Naming Format",
    series_branding: "Branding",
    series_branding_locked: "Branding Locked",
    btn_create_series: "Create Series",
    btn_coherence_check: "Check Coherence",
    coherence_score: "Coherence Score",

    // Back matter
    back_matter_title: "Back Matter",
    back_matter_about_author: "About the Author",
    back_matter_also_by: "Also in This Series",
    back_matter_review: "Review Request",
    back_matter_newsletter: "Newsletter Signup",
    btn_generate_back_matter: "Generate Back Matter",
    btn_generate_qr: "Generate QR Code",

    // ISBN
    isbn_title: "ISBN Management",
    isbn_number: "ISBN",
    isbn_publisher: "Publisher",
    isbn_status: "Status",
    btn_assign_isbn: "Assign ISBN",
    btn_generate_barcode: "Generate Barcode",

    // Distributor preflight
    preflight_title: "Distributor Preflight",
    distributor_kdp: "Amazon KDP",
    distributor_ingram: "IngramSpark",
    distributor_bn: "Barnes & Noble Press",
    btn_run_preflight: "Run Preflight",
    preflight_passed: "Passed",
    preflight_failed: "Failed",
    preflight_warnings: "Warnings",

    // Accessibility
    accessibility_title: "Accessibility",
    variant_dyslexia: "Dyslexia-Friendly",
    variant_large_print: "Large Print",
    variant_high_contrast: "High Contrast",
    btn_generate_variant: "Generate Accessible Variant",

    // Device preview
    device_preview_title: "Device Preview",
    device_kindle_fire_10: "Kindle Fire HD 10",
    device_kindle_fire_8: "Kindle Fire HD 8",
    device_paperwhite: "Kindle Paperwhite",
    device_ipad: "iPad",
    device_ipad_mini: "iPad Mini",
    device_iphone: "iPhone",

    // Layout protection
    safe_zone_title: "Safe Zone Heatmap",
    gutter_check_title: "Gutter Check",
    btn_safe_zone: "Generate Heatmap",
    btn_gutter_check: "Run Gutter Check",
    btn_auto_shift: "Auto-Shift",
    reflow_title: "Auto-Reflow",
    btn_reflow: "Reflow to Trim Size",

    // Kindle export
    kindle_export_title: "Kindle Export",
    kindle_format_kpf: "KPF (Kindle Package Format)",
    kindle_format_epub: "EPUB 3 (Fixed Layout)",
    btn_export_kindle: "Export for Kindle",
    read_aloud: "Read-Aloud Mode",
    text_popup: "Text Pop-Up",

    // Font licensing
    font_license_title: "Font Licensing",
    font_name: "Font Name",
    font_license_type: "License Type",
    font_commercial: "Commercial Print Safe",
    font_source: "Source",

    // Metadata advisor
    metadata_title: "KDP Metadata Advisor",
    btn_get_recommendations: "Get Recommendations",
    metadata_categories: "Recommended BISAC Categories",
    metadata_keywords: "Suggested Keywords",
    metadata_subtitle: "Subtitle Suggestions",
    metadata_compliance: "Compliance Issues",
  },

  // ---------------------------------------------------------------------------
  // Error messages
  // ---------------------------------------------------------------------------
  errors: {
    generic: "Something went wrong. Please try again.",
    load_failed: "Failed to load data",
    save_failed: "Failed to save changes",
    generate_failed: "Generation failed. Please try again.",
    export_failed: "Export failed. Please check preflight issues.",
    upload_failed: "Upload failed. Please check file format and size.",
    delete_failed: "Failed to delete item",
    preflight_failed: "Preflight check failed. Please resolve issues before exporting.",
    fingerprint_failed: "Failed to generate fingerprint",
    pricing_failed: "Failed to calculate pricing",
    batch_failed: "Batch job failed",
    word_list_empty: "Word list cannot be empty",
    invalid_grid_size: "Invalid grid size for this puzzle type",
    no_puzzles: "No puzzles to export. Generate puzzles first.",
    trademark_detected: "Trademark detected in content. Please remove before proceeding.",
    spam_risk_high: "High spam risk detected. Please review originality score.",
  },

  // ---------------------------------------------------------------------------
  // Tooltips
  // ---------------------------------------------------------------------------
  tooltips: {
    age_range: "Determines page count limits, font size minimums, and vocabulary rules",
    illustration_style: "Sets the visual style for all AI-generated illustrations",
    color_palette: "Controls the color scheme used in illustrations",
    story_mode: "Prose for standard text, Rhyming for AABB/ABAB patterns, Repetitive for cumulative stories",
    fear_intensity: "Controls the level of mild fear/tension in the story",
    bilingual: "Create a dual-language edition for wider market reach",
    line_weight: "Thickness of drawn lines. Thicker is better for younger audiences",
    stroke_uniformity: "Normalize line thickness across all pages for consistent quality",
    complexity: "How detailed the illustrations should be. Higher = more intricate patterns",
    difficulty_mode: "Progressive ramps easy-to-hard, Fixed stays constant, Mixed randomizes",
    word_difficulty: "Simple: 3-6 letters, Standard: 4-10, Advanced: 6-15",
    clue_style: "Standard for adults, Kid-Friendly for children, Trivia for fun facts",
    answer_key: "Where answer keys appear in the final book",
    puzzle_mix: "Controls the ratio of different puzzle types in mixed books",
    soft_proof: "Preview how colors will look when printed (RGB vs CMYK difference)",
    ink_coverage: "High ink coverage increases print cost. Keep below 60% for best pricing",
    provenance: "Track AI model, prompt, and seed for legal compliance",
    originality: "Fingerprint content to detect duplicates and avoid KDP rejection",
    spam_check: "Analyze if content might trigger KDP's spam detection",
    series_branding: "Lock visual branding across all volumes for consistent look",
  },
} as const;

export default en;

export type SpecialtyI18n = typeof en;
