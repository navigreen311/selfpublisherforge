SelfPublisherForge
Specialty Books Module
Complete Technical Blueprint
Document
Technical Blueprint v3.0
Module
Specialty Books: Children's, Coloring & Puzzle Books
Classification
Confidential - Internal Development
Author
Green Companies LLC
Date
March 2026
Total Features
200+ across 3 book types + 9 shared systems
Database Tables
25+ new tables
API Endpoints
80+ new endpoints
Algorithms
6 puzzle generators (Word Search, Crossword, Maze, Sudoku, Scramble, Cryptogram)
Implementation
17 weeks across 7 phases

---
Table of Contents
1. Executive Summary
2. Product Vision & Navigation
3. Children's Book Studio - Complete Specification
3.1 Landing Page & Book Management
3.2 Creation Wizard (4 Steps)
3.3 Page Spread Editor
3.4 Character Consistency System
3.5 Text Readability & Pacing System
3.6 Bilingual Support
3.7 Safety & Provenance System
3.8 Book Preview & Look Inside Simulator
3.9 Export & Publish
4. Coloring Book Creator - Complete Specification
4.1 Landing Page & Templates
4.2 Creation Wizard (3 Steps)
4.3 Line Art Quality Pipeline (7 Steps)
4.4 Page Editor & Cleanup Tools
4.5 Batch Generation with Auto-QA
4.6 Book-Level Quality Dashboard
4.7 Volume Factory & Series Planning
4.8 Export (B&W; Print-Ready)
5. Puzzle Book Generator - Complete Specification
5.1 Landing Page & Templates
5.2 Creation Wizard (4 Steps)
5.3 Puzzle-Type Editors (Word Search, Crossword, Maze, Sudoku, etc.)
5.4 Difficulty Calibration Engine
5.5 Clue Quality Governance
5.6 Book-Level QA Dashboard
5.7 Answer Key System
5.8 Large Print Variant Generator
5.9 Export (Print-Ready)
6. Shared Platform Systems
6.1 Print Production Preflight v2
6.2 Asset Provenance & Rights Ledger
6.3 KDP Category & Metadata Advisor
6.4 Batch Factory Mode
6.5 Template & Pack Marketplace
7. Production-Grade Safety & Compliance
7.1 Low-Content / Duplicate-Content Safety Layer
7.2 KDP Spam Risk Detector

---
7.3 Originality Fingerprinting System
7.4 Volume Factory Anti-Duplicate Guardrails
8. Print Quality Systems
8.1 Print Cost & Pricing Engine
8.2 CMYK / Soft-Proof Workflow
8.3 Ink Coverage Analysis
9. Kindle & Digital Export
9.1 Fixed-Layout KPF/EPUB Pipeline
9.2 Device Preview System (6 Devices)
9.3 Read-Aloud Highlight Mode
10. Advanced Layout Protection
10.1 Safe-Zone Heatmap Overlay
10.2 Gutter Collision Detector
10.3 Auto-Reflow for Alternate Trim Sizes
11. Accessibility Pack
11.1 Dyslexia-Friendly Mode
11.2 Large Print Standards (APH)
11.3 High-Contrast Enforcement
12. Series & Monetization
12.1 Series Branding Manager
12.2 Back Matter CTA Engine
12.3 Bundle / Box Set Creator
12.4 ISBN & Barcode Management
12.5 Multi-Distributor Preflight
12.6 Review Feedback Loop
13. Database Schema (All Tables)
14. API Specification (All Endpoints)
15. Puzzle Generation Algorithms
16. Implementation Roadmap (17 Weeks / 7 Phases)
17. Testing Strategy (102 Test Cases)

---
1. Executive Summary
1.1 Overview
The Specialty Books module adds three entirely new book creation studios to SelfPublisherForge, targeting the
highest-growth KDP categories: children's illustrated books, coloring books (kids and adult), and puzzle books
(word search, crossword, maze, sudoku, and more). These categories represent a combined market of millions
of monthly KDP sales and are uniquely suited to AI-powered creation at scale.
Unlike the existing Writing Studio (text-only), Specialty Books generates visual interior pages - AI illustrations
for children's books, algorithmically-generated line art for coloring books, and programmatically-constructed
puzzle grids with answer keys. Each studio includes a complete creation pipeline from concept to print-ready
PDF, with production-grade QA systems that prevent the most common KDP failures.
1.2 What Makes This Production-Grade
System
What It Prevents
Category
Originality Fingerprinting
KDP blocks for duplicate/low-content books
Safety
Character Consistency Engine
Inconsistent illustrations across pages
Quality
Line Art Quality Pipeline (7 steps)
Gray artifacts, open shapes, broken lines in coloring books
Quality
Puzzle Unique Solution Verifier
Unsolvable puzzles, duplicate grids, wrong answers
Quality
CMYK Soft-Proof
Washed-out colors in printed children's books
Print
Print Cost & Pricing Engine
Unprofitable pricing (especially color interiors)
Business
Trademark-Safe Prompt Enforcement
Accidental copyright/trademark infringement in AI art
Legal
Clue Ambiguity Tester
1-star reviews from wrong/ambiguous crossword clues
Quality
Word List Sanitization
Offensive/trademark words in puzzle books
Safety
KDP Spam Risk Detector
Account suspension from repeated/similar interiors
Safety
Fixed-Layout Kindle Export
Broken ebook layouts causing refunds
Format
Accessibility Pack
Missing large-print/dyslexia-friendly market segments
Revenue
Series Branding Lock
Inconsistent covers/spines across volume series
Brand
Back Matter CTA Engine
No reader capture for repeat purchases
Revenue
1.3 Scale of Implementation
Metric
Count
New sidebar section
1 (Specialty Books with 3 sub-items)
Book creation studios
3 (Children's, Coloring, Puzzle)
Illustration styles
8 for children's, 6 for coloring

---
Puzzle types
8+ (Word Search, Crossword, Maze, Sudoku, Scramble, Cryptogram, Number Search, Word Connec
Page layout options
7 for children's spread editor
Quick-start templates
8 for coloring, 8 for puzzles
QA systems
9 independent quality/safety systems
Database tables
25+ new tables
API endpoints
80+ new endpoints
Puzzle algorithms
6 algorithmic generators (not AI)
Device preview targets
6 (Kindle Fire HD 10/8, Paperwhite, iPad, iPad Mini, iPhone)
Accessibility variants
3 (Dyslexia-friendly, Large Print, High Contrast)
Export formats
Print PDF, KPF, Fixed-Layout EPUB, PNG, SVG
Distributor targets
3 (KDP, IngramSpark, B&N Press)
Test cases
102 across all modules
Implementation timeline
17 weeks across 7 phases

---
2. Product Vision & Navigation
2.1 Sidebar Structure
Add a new top-level sidebar item Specialty Books between Audiobook Studio and Style Profiles. This section
houses three specialized book creation tools with expandable sub-items:
Position
Item
Icon
Sub-Items
After Audiobook Studio
Specialty Books
Sparkles
Children's Books, Coloring Books, Puzzle Books
Before Style Profiles
(expandable)
Each sub-item is a full creation studio
2.2 Core Principle
Each sub-section is a complete book creation pipeline with its own project management, page editor, QA
system, and export pipeline. Unlike Writing Studio (text-only), these generate visual interior pages - the key
differentiator for specialty book categories on KDP.
2.3 Target KDP Categories
Book Type
KDP Category
Interior Type
Typical Price
Print Cost
Children's Picture Book
Children's Books > Ages 3-5
Premium Color
$9.99-$14.99
$2.50-$4.00
Children's Board Book
Children's Books > Ages 0-3
Premium Color
$7.99-$9.99
$2.00-$3.00
Adult Coloring Book
Activities > Coloring Books
Black & White
$7.99-$12.99
$1.50-$2.50
Kids Coloring Book
Children's > Coloring Books
Black & White
$5.99-$8.99
$1.00-$2.00
Word Search Book
Puzzles > Word Search
Black & White
$6.99-$9.99
$1.50-$2.50
Crossword Book
Puzzles > Crosswords
Black & White
$7.99-$12.99
$1.50-$3.00
Sudoku Book
Puzzles > Sudoku
Black & White
$6.99-$9.99
$1.50-$2.50
Maze Book
Activities > Mazes
Black & White
$5.99-$8.99
$1.00-$2.00
Large Print Puzzle
Large Print > Puzzles
Black & White
$9.99-$14.99
$2.00-$3.50

---
3. Children's Book Studio - Complete Specification
Create illustrated children's books with AI-generated artwork on every page. Supports board books (ages 0-3),
picture books (ages 3-5), early readers (ages 5-8), and chapter books (ages 8-12).
3.1 Landing Page
4 stat cards (Total Books, In Progress, Published, Pages Created). Book grid with cover thumbnails, age range,
page count, status badge, and QA score. Empty state with create button.
3.2 Creation Wizard (4 Steps)
Step 1: Book Details
Field
Type
Options / Notes
Title
Text input
Required
Subtitle
Text input
Optional
Author
Dropdown
User name or pen name
Age Range
Card selector (4 options)
Board (0-3, 10-16pg), Picture (3-5, 24-32pg), Early Reader (5-8, 32-48pg), Chapter (8-12, 48-80
Bilingual
Checkbox + config
Second language dropdown, Layout: Side-by-side / Alternating / Back section
Step 2: Format & Style
Field
Type
Options
Page Count
Dropdown
24/28/32 (picture), varies by age range
Trim Size
Dropdown
8.5x8.5 (Square), 8.5x11 (Portrait), 10x8 (Landscape), 6x9 (Chapter)
Illustration Style
Card selector (8)
Watercolor, Cartoon, Flat, Storybook, Realistic, Crayon/Pencil, Collage, Anime/Manga
Color Palette
Dropdown (5)
Bright & Vibrant, Soft & Pastel, Warm & Earthy, Cool & Dreamy, Monochrome + Accent
Step 3: Story Setup
Field
Type
Notes
Creation Mode
Radio (3)
AI Generate Full Story / Write My Own / Import Text
Story Prompt
Textarea
For AI generation mode
Theme/Moral
Text input
e.g., Courage / Overcoming fears
Main Character
Text input
e.g., Luna - a small orange tabby kitten
Setting
Text input
e.g., A cozy village with gardens and woods
Tone
Dropdown
Warm & reassuring, Exciting, Humorous, Educational

---
Story Mode
Radio (3)
Prose / Rhyming (AABB or ABAB) / Repetitive-Cumulative
Step 4: Content Safety Settings
Setting
Type
Default
Fear Intensity Level
Radio (None/Mild/Moderate)
None for Board/Picture
No weapons or violence
Checkbox (enforced)
Checked
No scary/dark imagery
Checkbox (enforced)
Checked
No trademarked characters
Checkbox (enforced)
Checked
No stereotypical depictions
Checkbox (enforced)
Checked
Age-appropriate vocabulary
Checkbox (enforced)
Checked
Trademark-safe prompt enforcement
Checkbox
Checked
Content sensitivity pre-check
Checkbox
Checked
Model/style provenance logging
Checkbox
Checked
When Create Book is clicked, AI generates: (1) Full story text divided across pages, (2) Illustration prompt per
page, (3) Character description sheet, (4) Age-band language check report, (5) Provenance metadata
initialized.

---
3.3 Page Spread Editor
The core experience. Three-panel layout: left thumbnail strip (all pages with drag-to-reorder), center two-page
spread view, right properties panel.
Layout Options (7 per page):
Layout
Description
Best For
Full Bleed
Illustration fills entire page, text overlaid
Dramatic moments, wordless spreads
Top Image / Bottom Text
Most common picture book layout
Standard narrative pages
Bottom Image / Top Text
Text above, illustration below
Establishing scenes
Left Image / Right Text
Side-by-side horizontal
Landscape spreads
Right Image / Left Text
Side-by-side horizontal
Dialogue-heavy pages
Text Only
No illustration
Title page, dedication, credits
Full Bleed No Text
Full illustration, no text overlay
Wordless spreads, dramatic reveals
Text Properties:
Font selector, Size (enforced minimum per age band), Color picker, Position (top/middle/bottom third).
Readability Features: Auto contrast checker (WCAG AA score), Auto text plate generator (adds subtle
background behind text when contrast fails), Minimum font enforcement by age band (Board: 24pt, Picture:
18pt, Early Reader: 14pt, Chapter: 12pt), Gutter safety check (no text within 0.5in of spine).
Illustration Properties:
Editable prompt textarea per page. Trademark check indicator. Buttons: Generate Illustration, Upload Own
Image, Regenerate, Edit Prompt, Generate 4 Variations. Character consistency toggle (auto-appends character
description to prompt). Provenance display (model, generation date, view details link).

---
3.4 Character Consistency System (Production-Grade)
The biggest challenge in AI-illustrated children's books. Each character gets a detailed description sheet plus 4
auto-generated reference images (front view, side view, happy face, scared face). The description
auto-appends to every page's illustration prompt.
Character Sheet Fields:
Field
Purpose
Name
Character identifier
Species/Type
Visual reference (e.g., orange tabby kitten)
Description (text)
Detailed visual description appended to all prompts
Reference Images (4)
Front view, side view, happy face, scared face
Clothing/Accessory Rules
What the character always wears (e.g., red collar with gold bell)
Scale Rules
Size relative to other characters/objects
Setting Continuity Rules
Persistent environmental details (e.g., blue gate, stone path)
Time-of-Day Rules
Tracks lighting changes across the story
Continuity QA System:
Analyzes all illustration prompts against character sheets and scene rules. Checks: clothing/accessories
mentioned consistently, character scale references match rules, time-of-day/location consistency, style drift
detection between generated images. Auto-fix Prompts button batch-updates all prompts to match rules.
Reports issues with page numbers and fix suggestions.
3.5 Text Readability & Pacing System
Age Range
Max Sentence
Max Word Length
Vocabulary
Total Words
Board (0-3)
5 words
5 letters
Top 500
50-150
Picture (3-5)
8 words
7 letters
Top 2000
300-500
Early Reader (5-8)
12 words
9 letters
Top 5000
500-2000
Chapter (8-12)
15 words
No limit
Grade-level
3000-10000
Additional Pacing Features:
* Read-Aloud Rhythm Score (0-100): sentence cadence, repetition patterns, page-turn momentum,
tongue-twister check
* Page-Turn Surprise Map: visual indicator showing where reveal moments land relative to page turns
* 'Look Inside' First-10% Optimizer: scores the Amazon preview pages for hook strength
* Rhyme Assistant (rhyming mode only): detects AABB/ABAB patterns, flags near-rhymes, checks meter
consistency, AI fix

---
3.6 Bilingual Support
For bilingual editions (massive KDP niche, especially English/Spanish). Three layout modes: Side-by-side (both
languages on same page), Alternating pages (L1 page then L2 page), Back section (full story in L2 after L1). AI
translation with cultural adaptation. Reading level validation in both languages. Sync changes button keeps
translations aligned.
3.7 Safety & Provenance
Trademark-Safe Enforcement: Blocks 'Disney,' 'Pixar,' 'Peppa Pig,' 'Bluey,' 'Paw Patrol,' 'Marvel,' 'Frozen,'
'Cocomelon,' 'Sesame Street,' 'in the style of [specific artist],' etc. Content Sensitivity: Scans for
weapons/violence, excessive fear, stereotypes, mature themes. Provenance Ledger: Per-image metadata
(model, prompt hash, seed, date, status). Exportable compliance report. Font Licensing: Verifies all fonts are
commercial print-safe with license details.
3.8 Preview & Look Inside Simulator
Three preview modes: Spread View (two-page as printed), Single Page, 'Look Inside' Simulator. The simulator
shows exactly what Amazon shoppers see in preview - mobile phone frame and desktop browser frame
rendering first 10% of pages. Hook Score calculated. Guide overlays: Bleed zone, Trim line, Safe zone, Gutter
zone.
3.9 Export & Publish
Format
Description
Use Case
Print-Ready PDF
KDP interior with bleed, trim, 300 DPI
Paperback on KDP
Fixed-Layout KPF
Kindle Package Format for tablets
Kindle Fire, iPad
Fixed-Layout EPUB 3
Standard fixed-layout ebook
Other ebook stores
Individual Pages
PNG/JPG per page at 300 DPI
Other print platforms
Enhanced Preflight: Checks all pages have illustrations, text within safe margins, 300+ DPI, gutter safety,
valid page count, font licensing, trademark safety, content sensitivity, language level, grayscale preview option.
Export includes interior PDF + provenance report + font license summary.

---
4. Coloring Book Creator - Complete Specification
4.1 Landing Page & Templates
8 quick-start templates: Animals & Wildlife, Mandalas & Patterns, Fantasy Worlds, Nature Scenes, Holidays &
Seasons, Space & Sci-Fi, Food & Desserts, Geometric Abstract. Each pre-fills wizard settings for 30 pages.
Series planning option for multi-volume branding.
4.2 Creation Wizard (3 Steps)
Step 1 - Book Details: Title, subtitle, audience (Kids 3-8 / Teens 9-14 / Adults 15+), series planning (name,
volume number).
Step 2 - Format & Style: Page count (20-60), trim size, 6 line art styles (Clean Outlines, Sketchy Hand-drawn,
Whimsical Decorative, Realistic Detailed, Zentangle, Bold & Simple), line weight, stroke uniformity enforcement,
complexity slider. ENFORCED: Single-sided (blank backs), coloring-safe inner margin (+0.25in at spine).
Step 3 - Content: Theme description, generation method (all at once / one at a time / mix), bonus pages (title,
belongs-to, color test, progress tracker, certificate, difficulty ratings).
4.3 Line Art Quality Pipeline (7 Steps)
Step
Process
What It Catches
1. Generate
AI creates illustration with line art prompts
Initial generation
2. Auto-Clean
Convert to pure black/white (threshold-based)
Gray artifacts, gradients
3. Stroke Uniformity
Normalize line thickness across page
Inconsistent line weights
4. Closed Shapes
Detect and flag open outlines
Shapes that can't be colored
5. Speck Removal
Remove stray marks and noise
Dots, artifacts, stray pixels
6. Background
Ensure pure #FFFFFF background
Off-white, textured backgrounds
7. Quality Check
Final verification report
Any remaining issues
Additional Quality Controls:
* Vectorization option (SVG/PDF paths) for ultra-crisp print
* Ink density limiter (prevents heavy blacks that look muddy)
* Duplicate-page detector (perceptual hash + structural similarity)
* Theme cohesion score (ensures pages feel like one series volume)
* Coloring simulation preview (marker, crayon, colored pencil texture)
* Page complexity histogram (visual overview of difficulty distribution)
4.4 Manual Cleanup Tool

---
Canvas-based editor with: Brush (white) for painting over marks, Pen (black) for fixing broken lines, Eraser, Fill
(white), Smooth Lines, Close Shape (connect endpoints), Normalize Stroke (even out thickness). Line weight
selector, zoom levels (25%-200%), undo/redo.
4.5 Batch Generation
Generate 30-60 pages at once with async queue. Edit page description list before generating. Progress bar with
per-page status. Auto-QA runs on each page after generation. Variation mode prevents similar compositions.
Cost estimate shown. Pause/Cancel controls.
4.6 Book-Level Quality Dashboard
Overall Quality Score (0-100). Complexity distribution histogram. Theme cohesion score. Print quality summary
(line quality, closed shapes, stroke uniformity, ink density, small areas). Fix All Issues and Re-run Full QA
buttons.
4.7 Volume Factory
Plan multi-volume series with consistent branding. Each volume card shows status. Series branding template
locks title font/position, author position, volume badge, spine layout. Auto-Generate Next Volume uses same
style + new theme. Batch Export All Volumes.
4.8 Export
Print-Ready PDF (KDP), Individual PNGs, SVG Vector Package, Digital PDF. B&W; interior standard.
Single-sided ENFORCED with auto-inserted blank backs. Coloring-safe inner margin applied. Total page count
includes coloring + blanks + bonus pages. Full preflight: pure B&W;, 300 DPI, stroke uniformity, closed shapes,
no specks, ink density, no duplicates, grayscale verified, font licensing.

---
5. Puzzle Book Generator - Complete Specification
5.1 Puzzle Types
Type
Grid
Difficulty Factors
Answer Key Format
Word Search
10x10 to 20x20
Grid size, direction count, overlap rate, word densityHighlighted grid
Crossword
Variable
Black-square density, avg word length, clue grade level
Filled grid
Maze
10x10 to 40x40
Solution path length, dead end count, branch factorPath highlighted
Sudoku
4x4, 6x6, 9x9
Given clues count, solving techniques required
Completed grid
Word Scramble
N/A
Word length, letter patterns
Word list
Cryptogram
N/A
Phrase complexity, letter frequency
Decoded text
Number Search
10x10 to 20x20
Same as word search but with numbers
Highlighted grid
Word Connect
Variable
Word count, intersection complexity
Solution lines
5.2 Creation Wizard (4 Steps)
Step 1 - Book Details: Title, subtitle (AI suggests including puzzle types + 'with answers'), audience (Kids /
Teens / Adults / Large Print at 150% scale), series planning.
Step 2 - Puzzle Selection: Multi-select puzzle types with independent quantities, difficulty, and grid size per
type. Difficulty calibration: Progressive (easy-to-hard ramp) / Fixed / Mixed Random. Puzzle mix templates for
mixed books (Balanced, Word-heavy, Custom percentages).
Step 3 - Themes & Words: AI Generate by Theme / Custom Word Lists / Mix. Theme categories (Animals,
Nature, Food, Sports, Science, History, etc.). Seasonal/holiday auto-theming (Christmas, Halloween, etc.
applies across all puzzle types). Word difficulty (Simple 3-6 letters / Standard 4-10 / Advanced 6-15). Word list
sanitization (offensive terms, trademarks, abbreviations).
Step 4 - Layout & Extras: Answer key at back / on reverse / none. TOC, instructions per type, difficulty
badges, section dividers. Hint system (crossword first letter, theme hints). Clue style (Standard / Kid-friendly /
Trivia / Themed). Layout (one puzzle per page / two per page).
5.3 Difficulty Calibration Engine
Puzzle Type
Easy
Medium
Hard
Scoring Factors
Word Search
10x10, 10 words, 2 dirs
15x15, 15 words, 4 dirs
20x20, 20 words, 8 dirs
Grid density, direction count, overlap
Crossword
Low black%, short words Moderate complexity
High black%, long words Black-square%, avg word length, clue grade
Sudoku
36-45 givens
27-35 givens
22-26 givens
Givens count, solving techniques needed
Maze
Small, few dead ends
Medium, many dead ends Large, complex branching Path length, dead ends, branch factor
Book-level pacing enforced: first 30% Easy, middle 40% Medium, last 30% Hard (for Progressive mode).
Difficulty score (0-100) calculated per puzzle. Distribution visualization shows ramp across the book.

---
5.4 Clue Quality Governance
Clue Ambiguity Tester: Scores every clue for ambiguity. Flags multi-answer clues (e.g., 'African river' could be
Nile, Congo, Niger). AI generates unambiguous alternatives. Book-Level Clue QA: No duplicate phrasings
across entire book, consistent tense, consistent style, grade level appropriate for audience. Word List
Sanitization Pipeline: (1) Offensive language filter, (2) Trademark filter, (3) Abbreviation filter, (4) Spelling
validator, (5) Duplicate remover, (6) Length validator. Regional English Packs: US/UK/CA/AU spelling
differences (color vs colour, center vs centre).
5.5 Large Print Variant Generator
One-click generate a Large Print edition from any existing puzzle book. Scale: 125%/150%/175%. Auto-adjusts:
grid size (may reduce to fit), words per puzzle (may reduce), letter spacing (increased), grid line thickness.
Creates a new book copy - original unchanged. Massive market, especially seniors.
5.6 Answer Key Verification
Post-generation verification: all keys generated, all keys match corresponding puzzles, puzzle numbering
matches between puzzle and key sections, no missing answers. Layout options: back of book (standard),
reverse of puzzle page, no answer key. Compact layout: 4 answers per page.

---
6-12. Shared Platform Systems & Production
Enhancements
System
Section
Key Components
Print Preflight v2
6.1
DPI + margin + bleed + gutter + spine calc, font licensing, grayscale preview, Look Inside simulator
Asset Provenance
6.2
Per-image metadata (model, prompt hash, seed), font license registry, compliance report export
KDP Metadata Advisor
6.3
AI-recommended BISAC categories, 7 KDP keywords, subtitle optimization, compliance checks
Batch Factory
6.4
Multi-volume pipeline, auto-QA per page, cost guardrails, queue with pause/cancel
Template Marketplace
6.5
Page layouts, theme packs, style packs (non-trademarked)
Originality Fingerprinting
7.1
pHash (images), grid hash (puzzles), Jaccard (word lists), n-gram (text), cross-book matrix
KDP Spam Detector
7.2
Interior originality, metadata quality, minor-edit detection, content substance check
Anti-Duplicate Guardrails
7.3
85% unique pages/volume (coloring), 100% unique grids (puzzle), 30% max word overlap
Print Cost Engine
8.1
KDP cost formula, price scenarios, ink coverage, margin guardrails, strategy advisor
CMYK Soft-Proof
8.2
RGB vs CMYK side-by-side, out-of-gamut warnings, auto-adjust, shadow crush, ink density
Fixed-Layout Kindle
9.1
KPF + EPUB 3 export, read order mapping, text pop-up, read-aloud sync
Device Preview
9.2
6 devices: Kindle Fire HD 10/8, Paperwhite, iPad, iPad Mini, iPhone
Safe-Zone Heatmap
10.1
Color-coded bleed/trim/safe/gutter zones + face/text detection overlay
Gutter Collision
10.2
Detects faces/text near fold, auto-shift capability
Auto-Reflow
10.3
Convert between trim sizes with auto-repositioned text and scaled illustrations
Dyslexia Mode
11.1
OpenDyslexic font, 1.5x line spacing, +15% letter spacing, left-aligned, off-white BG
Large Print Standards
11.2
18pt body min, 7:1 contrast (WCAG AAA), APH guidelines
High Contrast
11.3
Pure black on white, 2px min grid lines, bold numbers/instructions
Series Branding
12.1
Naming rules, cover template lock, spine preview, theme coherence scorer
Back Matter CTA
12.2
Also in Series, About Series, Email CTA with QR code, Review Request, About Author
Bundle Creator
12.3
Combine volumes into Complete Collection with dividers, combined TOC/answers
ISBN Manager
12.4
ISBN pool tracking, auto barcode generation, back cover placement
Multi-Distributor
12.5
KDP, IngramSpark, B&N Press preflight + per-distributor export (incl. PDF/X-1a)
Review Feedback
12.6
Maps complaints to fixes: 'pages thin' -> paper type, 'colors washed' -> CMYK, etc.

---
13. Database Schema
13.1 Children's Books Tables
Table
Key Columns
Purpose
childrens_books
id, org_id, title, age_range, page_count, trim_size, illustration_style, color_palette, story_mode, is_bilingual, fear_in
Master book record
childrens_book_pages
id, book_id, page_number, page_type, layout, text_content, translated_text, text_font/size/color/position, text_plate
Individual page content and metadata
childrens_book_characters
id, book_id, name, species, description, reference_images[], auto_append, clothing_rules JSONB, scale_rules JSO
Character consistency sheets
13.2 Coloring Books Tables
Table
Key Columns
Purpose
coloring_books
id, org_id, title, audience, page_count, trim_size, line_style, line_weight, complexity, stroke_uniformity, single_sided
Master coloring book record
coloring_book_pages
id, book_id, page_number, page_type, illustration_prompt/url, cleaned_url, vectorized_url, illustration_model/seed, 
Individual coloring page with QA data
13.3 Puzzle Books Tables
Table
Key Columns
Purpose
puzzle_books
id, org_id, title, audience, puzzle_config JSONB, difficulty_mode, themes[], seasonal_theme, word_difficulty, clue_s
Master puzzle book record
puzzles
id, book_id, puzzle_type, puzzle_number, theme, difficulty, difficulty_score, grid_size, grid_data JSONB, word_list[]
Individual puzzle with solution and QA data
13.4 Shared Tables
Table
Key Columns
Purpose
asset_provenance
id, org_id, book_type, book_id, page_id, asset_type, model, prompt_text, prompt_hash, seed, settings JSONB, genera
Every generated asset tracked for legal protection
font_licenses
id, font_name, license_type, commercial_print, source, license_url
Font licensing registry
batch_jobs
id, org_id, book_type, batch_config JSONB, budget_limit_cents, spent_cents, status, volumes_total/completed, pages_
Batch factory job tracking
content_fingerprints
id, org_id, book_type, book_id, page_id, content_type, phash, data_hash, ngram_fingerprint, jaccard_vector JSONB
Originality fingerprinting
originality_reports
id, org_id, book_type, book_id, overall_score, component_scores JSONB, cross_book_similarities JSONB, spam_risk_
KDP compliance reports
book_series
id, org_id, name, book_type, naming_format, branding_config JSONB, branding_locked, volume_count
Series branding management
back_matter_templates
id, org_id, template_type, content, cta_url, qr_code_url
Reusable back matter pages
isbn_pool
id, org_id, isbn, publisher_name, assigned_to_book_type/id, barcode_url, status
ISBN inventory management
distributor_preflights
id, book_type, book_id, distributor, status, checks JSONB, issues JSONB, exported_url
Per-distributor validation
book_bundles
id, org_id, title, book_type, volume_ids[], series_id, config JSONB, total_pages
Combined volume bundles

---
accessibility_variants
id, source_book_type/id, variant_type, variant_book_id, settings JSONB
Tracks accessible editions
word_list_sources
id, org_id, name, source_type, license, word_count, dictionaryWord list provenance

---
14. API Specification (All Endpoints)
14.1 Children's Books API
Method
Endpoint
Purpose
GET/POST
/api/v1/specialty/childrens-books
List / Create books
GET/PATCH/DELETE
/api/v1/specialty/childrens-books/{id}
Read / Update / Delete book
GET/POST
.../{id}/pages
List / Create pages
PATCH/DELETE
.../{id}/pages/{page_id}
Update / Delete page
POST
.../{id}/pages/reorder
Reorder pages
POST
.../{id}/pages/{page_id}/generate-illustration
AI generate illustration
POST
.../{id}/pages/{page_id}/generate-variations
Generate 4 variations
POST
.../{id}/pages/{page_id}/upload-image
Upload own image
GET/POST/PATCH/DELETE
.../{id}/characters[/{char_id}]
Character CRUD
POST
.../{id}/characters/{char_id}/generate-references
Generate reference images
POST
.../{id}/generate-story
AI generate full story
POST
.../{id}/analyze-text
Reading level, rhythm, pacing analysis
POST
.../{id}/continuity-check
Check illustration prompt consistency
POST
.../{id}/auto-fix-prompts
Batch-fix prompts to match rules
POST
.../{id}/safety-check
Trademark + content sensitivity check
POST
.../{id}/translate
Generate bilingual translation
POST
.../{id}/export
Generate export file
POST
.../{id}/export-kindle
Fixed-layout KPF/EPUB export
POST
.../{id}/device-preview
Device-accurate preview images
POST
.../{id}/preflight
Run full preflight check
POST
.../{id}/gutter-check
Check for gutter collisions
POST
.../{id}/reflow
Generate alternate trim size version
14.2 Coloring Books API
Method
Endpoint
Purpose
GET/POST
/api/v1/specialty/coloring-books
List / Create books
GET/PATCH/DELETE
.../{id}
Read / Update / Delete book
GET
.../{id}/pages
List pages

---
POST
.../{id}/pages/{page_id}/generate
Generate line art
POST
.../{id}/pages/{page_id}/upload
Upload own art
POST
.../{id}/pages/{page_id}/clean-lines
Run line art cleanup pipeline
POST
.../{id}/pages/{page_id}/vectorize
Convert to SVG vectors
POST
.../{id}/pages/{page_id}/quality-check
Per-page quality check
POST
.../{id}/pages/{page_id}/coloring-simulation
Preview colored-in versions
POST
.../{id}/batch-generate
Batch generate all pages (async)
GET
.../{id}/batch-generate/{job_id}/status
Poll batch progress
POST
.../{id}/quality-check
Book-level quality dashboard data
POST
.../{id}/plan-series
Create volume series plan
POST
.../{id}/generate-next-volume
Auto-generate next volume
POST
.../{id}/export
Generate export file
POST
.../{id}/preflight
Run full preflight
14.3 Puzzle Books API
Method
Endpoint
Purpose
GET/POST
/api/v1/specialty/puzzle-books
List / Create books
GET/PATCH/DELETE
.../{id}
Read / Update / Delete book
GET
.../{id}/puzzles
List puzzles
POST
.../{id}/puzzles/generate
Generate puzzle
POST
.../{id}/puzzles/{puzzle_id}/regenerate
Regenerate with same params
PATCH/DELETE
.../{id}/puzzles/{puzzle_id}
Update / Delete puzzle
POST
.../{id}/puzzles/{puzzle_id}/verify
Verify solvable + unique solution
POST
/api/v1/specialty/puzzle-books/generate-word-list
AI generate themed word list
POST
/api/v1/specialty/puzzle-books/sanitize-word-list
Run sanitization pipeline
POST
.../{id}/puzzles/{puzzle_id}/generate-clues
AI generate clues in style
POST
.../{id}/puzzles/{puzzle_id}/qa-clues
Check clue quality
POST
.../{id}/auto-fix-clues
AI fix ambiguous clues
POST
.../{id}/generate-answer-key
Generate answer key section
POST
.../{id}/verify-answer-key
Verify keys match puzzles
POST
.../{id}/quality-check
Book-level QA dashboard
POST
.../{id}/calibrate-difficulty
Calculate difficulty scores + pacing
POST
.../{id}/generate-large-print
Create large print variant

---
POST
.../{id}/export
Generate export file
POST
.../{id}/preflight
Run full preflight
14.4 Shared API
Method
Endpoint
Purpose
POST
/api/v1/specialty/metadata-advisor
AI recommend categories + keywords
GET/POST
/api/v1/specialty/{type}/{id}/provenance[/export]
View / Export provenance report
POST
/api/v1/specialty/originality/fingerprint
Generate originality fingerprint
POST
/api/v1/specialty/originality/compare
Compare two books
POST
/api/v1/specialty/originality/spam-check
Run KDP spam risk analysis
POST
/api/v1/specialty/pricing/calculate
Calculate print cost + scenarios
POST
/api/v1/specialty/pricing/ink-coverage
Analyze ink coverage per page
POST
/api/v1/specialty/color/soft-proof
CMYK soft-proof simulation
POST
/api/v1/specialty/color/auto-adjust
Auto-fix gamut/ink/shadow issues
POST/GET
/api/v1/specialty/batch[/{id}/status]
Create / Monitor batch jobs
GET
/api/v1/specialty/templates
List available templates/packs
POST/GET
/api/v1/specialty/series[/{id}]
Create / View series
POST
/api/v1/specialty/series/{id}/coherence-check
Check series consistency
POST
/api/v1/specialty/{type}/{id}/generate-back-matter
Generate back matter pages
POST
/api/v1/specialty/{type}/{id}/generate-qr-code
Generate QR code from URL
POST
/api/v1/specialty/{type}/{id}/generate-accessible-variant
Create accessible edition

---
15. Puzzle Generation Algorithms
All puzzles are generated algorithmically, NOT by AI. AI assists with word lists and clue generation only. Each
algorithm must: accept parameters (size, difficulty, theme), return both puzzle and solution data as JSON, verify
solvability, verify unique solutions where applicable, calculate difficulty score (0-100), generate content hash for
duplicate detection, and support SVG rendering for print-quality output.
Algorithm
Method
Key Steps
Word Search
Backtracking placement 1) Sanitize word list, 2) For each word try random position+direction, 3) Check conflicts (overlap OK if sa
Crossword
Intersection-based
1) Sort words longest first, 2) Place first word in center, 3) Find intersecting letters with placed words, 4) 
Maze
Recursive backtracker
1) Create grid, all walls up, 2) For shaped mazes mask cells outside boundary, 3) Start random cell, 4) C
Sudoku
Generate + Remove
1) Generate complete valid solution (backtracking), 2) Remove numbers one at a time randomly, 3) After
Word Scramble
Shuffle + Verify
1) Sanitize list, 2) Randomly shuffle letters, 3) Verify different from original, 4) Verify not another valid wo
Cryptogram
Substitution cipher
1) Generate random A->X mapping (no self-maps), 2) Apply cipher, 3) Provide encoded text + blanks, 4)

---
16. Implementation Roadmap (17 Weeks / 7 Phases)
Phase
Weeks
Deliverables
1. Foundation
1-2
Sidebar navigation, Provenance ledger, Preflight v2, Font licensing registry, Metadata advisor, Originality fingerprin
2. Children's Books
3-6
Landing page, 4-step wizard, AI story generation, Page spread editor (7 layouts), Text readability system, Illustratio
3. Coloring Books
7-9
Landing page + 8 templates, 3-step wizard, Line art generation, 7-step quality pipeline, Manual cleanup tool, Colori
4. Puzzle Books
10-13
Landing page + 8 templates, 4-step wizard, Word Search generator, Crossword generator + clue system, Maze ge
5. Print Quality
14
Print cost engine, Ink coverage estimator, Margin guardrails, CMYK soft-proof, Out-of-gamut warnings, Shadow cru
6. Kindle + Accessibility15-16
Fixed-layout KPF/EPUB, Read order mapping, Device preview (6 devices), Safe-zone heatmap, Gutter collision de
7. Series + Scale
17
Series branding manager, Back matter CTA engine, Bundle creator, ISBN management, Multi-distributor preflight, 

---
17. Testing Strategy (102 Test Cases)
17.1 Children's Books (32 tests)
1. Wizard flows through all 4 steps correctly
2. Age range adjusts page count, font size, and language rules
3. Bilingual option shows language selector and layout choice
4. Story modes (Prose, Rhyming, Repetitive) generate correctly
5. AI story splits across pages with per-page illustration prompts
6. Age-band language gate flags advanced vocabulary and long sentences
7. Read-aloud rhythm score calculates cadence and repetition
8. Page-turn surprise map shows pacing visualization
9. Rhyme assistant detects patterns and suggests fixes
10. Look Inside optimizer scores first 10% of pages
11. All 7 layout options render correctly in spread editor
12. Text contrast checker scores readability
13. Auto text plate adds background when needed
14. Minimum font size enforced per age band
15. Gutter safety flags content near spine
16. Illustration generation creates image from prompt
17. Trademark enforcement blocks 'Disney-like' etc.
18. Content sensitivity flags inappropriate content
19. Character sheet with references and continuity rules works
20. Continuity QA detects prompt inconsistencies
21. Auto-fix prompts batch-updates all prompts
22. Style drift detection compares visual similarity
23. Provenance logs model, prompt hash, seed per image
24. Font licensing verifies commercial safety
25. Bilingual translation with age-appropriate language
26. Preview shows spread with bleed/trim/safe/gutter guides
27. Look Inside simulator shows mobile Amazon preview
28. Export generates print-ready PDF at 300 DPI
29. Fixed-layout KPF validates
30. Device preview renders for all 6 devices
31. Enhanced preflight catches all issues
32. Export includes provenance report and font summary
17.2 Coloring Books (28 tests)
1. 8 quick-start templates pre-fill wizard
2. Series planning creates branded volume sequence
3. Single-sided mode ENFORCED with blank backs

---
4. Coloring-safe inner margin applied
5. Stroke uniformity normalizes line width
6. AI generates line art with coloring-specific prompts
7. 7-step quality pipeline runs automatically
8. Closed-shape detection flags open outlines
9. Speck removal cleans stray marks
10. Vectorization (SVG) available
11. Ink density limiter prevents heavy blacks
12. Manual cleanup tool works at all zoom levels
13. Coloring simulation shows marker/crayon/pencil previews
14. Batch generation processes pages with auto-QA
15. Variation mode prevents similar compositions
16. Duplicate detection flags near-identical pages
17. Theme cohesion score validates consistency
18. Quality dashboard shows complexity histogram
19. Complexity distribution balanced across difficulty
20. Volume factory plans multi-volume series
21. Bonus pages generate correctly
22. Export generates B&W; print-ready PDF
23. Page count includes coloring + blanks + bonus
24. Grayscale verified (no accidental color)
25. Coloring margin applied in export
26. All quality checks pass in preflight
27. Provenance tracked for every page
28. Originality score calculates correctly
17.3 Puzzle Books (30 tests)
1. 8 templates including Large Print
2. 4-step wizard flows correctly
3. Large Print audience scales content 150%
4. Difficulty calibration modes work (Progressive/Fixed/Mixed)
5. Word Search generates valid grids with configurable directions
6. Word Search difficulty score calculated correctly
7. Crossword generates valid intersecting grids
8. Crossword clue styles all generate (Standard/Kid/Trivia/Themed)
9. Crossword clue QA catches ambiguity and repeats
10. Maze generates solvable mazes with shape variants
11. Seasonal maze shapes work (Christmas tree, pumpkin)
12. Sudoku generates with verified unique solutions
13. Sudoku difficulty calibrated by technique required
14. Sudoku 4x4/6x6 kids variants work
15. Word Scramble generates valid scrambles

---
16. Cryptogram applies substitution cipher correctly
17. Word list sanitization removes offensive/trademark terms
18. AI suggests themed word lists by category
19. Seasonal auto-theming applies across all puzzle types
20. Hint system configurable per puzzle type
21. Book-level QA: no duplicate grids or word lists
22. Difficulty distribution visualization shows progressive ramp
23. Render QA: font size, grid legibility, writing space pass
24. Answer key generates for all puzzle types
25. Answer key verification: keys match, numbering correct
26. Large print variant generator creates scaled edition
27. TOC with difficulty badges generates
28. All puzzles verified solvable + unique before export
29. Export includes puzzles + answers with correct page count
30. Preflight catches font size, margin, sanitization issues
17.4 Shared Systems (12 tests)
1. Preflight v2: DPI, margins, bleed, gutter, spine calculations correct
2. Font licensing registry identifies commercial-safe fonts
3. Grayscale preview shows B&W; rendering of color content
4. Look Inside simulator renders mobile and desktop views
5. Provenance ledger exports compliance report PDF
6. Metadata Advisor recommends correct BISAC categories + 7 keywords
7. Batch factory processes multi-volume jobs with cost guardrails
8. Originality fingerprint generates for all content types
9. Cross-book similarity correctly identifies >40% overlap
10. KDP spam detector flags keyword-stuffed titles
11. Series branding lock enforces template on new volumes
12. Back matter QR code generates from CTA URL

---
End of Blueprint
This document is the complete technical blueprint for the SelfPublisherForge Specialty Books module. It should
be used in conjunction with the two detailed specification documents:
1. Specialty-Books-v2-Claude-Code-Prompt.md (178KB) - Core feature specifications with ASCII wireframes
2. Specialty-Books-v3-Addendum-Claude-Code-Prompt.md (93KB) - Production-grade safety, print, Kindle,
accessibility, and series enhancements
Document generated March 2026
SelfPublisherForge - Specialty Books Module v3.0
Green Companies LLC - Confidential

---
