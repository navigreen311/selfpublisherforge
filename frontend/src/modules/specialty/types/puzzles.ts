/**
 * TypeScript types for the Puzzle Book Generator.
 *
 * Covers puzzle types, difficulty calibration, clue governance, answer keys,
 * large print variants, word list management, and export.
 *
 * Blueprint refs: 5.1-5.9, 13.3, 14.3
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type PuzzleType =
  | "word_search"
  | "crossword"
  | "maze"
  | "sudoku"
  | "word_scramble"
  | "cryptogram"
  | "number_search"
  | "word_connect"
  | "trivia";

export type Audience = "kids" | "teens" | "adults" | "large_print";

export type Difficulty = "easy" | "medium" | "hard";

export type DifficultyMode = "progressive" | "fixed" | "mixed";

export type WordDifficulty = "simple" | "standard" | "advanced";

export type ClueStyle = "standard" | "kid_friendly" | "trivia" | "themed";

export type AnswerKeyPosition = "back" | "reverse" | "none";

export type PuzzleMixTemplate = "balanced" | "word_heavy" | "custom";

export type PuzzleBookStatus = "draft" | "in_progress" | "published";

export type PuzzleStatus =
  | "pending"
  | "generating"
  | "generated"
  | "verified"
  | "failed";

export type PuzzleLayout = "one_per_page" | "two_per_page";

export type LargePrintScale = "125" | "150" | "175";

// ---------------------------------------------------------------------------
// Core interfaces
// ---------------------------------------------------------------------------

export interface PuzzleTypeConfig {
  type: PuzzleType;
  quantity: number;
  difficulty: Difficulty;
  grid_size: string;
}

export interface PuzzleBook {
  id: string;
  org_id: string;
  title: string;
  subtitle?: string;
  audience: Audience;
  status: PuzzleBookStatus;
  puzzle_config: PuzzleTypeConfig[];
  difficulty_mode: DifficultyMode;
  themes: string[];
  seasonal_theme?: string;
  word_difficulty: WordDifficulty;
  clue_style: ClueStyle;
  answer_key_position: AnswerKeyPosition;
  layout: PuzzleLayout;
  extras: string[];
  hint_config?: Record<string, string>;
  puzzle_mix_template?: PuzzleMixTemplate;
  custom_percentages?: Record<string, number>;
  total_puzzles: number;
  puzzles_created: number;
  series_id?: string;
  series_name?: string;
  volume_number?: number;
  quality_score?: number;
  cover_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Clue {
  clue: string;
  answer: string;
}

export interface Puzzle {
  id: string;
  book_id: string;
  puzzle_type: PuzzleType;
  puzzle_number: number;
  theme?: string;
  difficulty: Difficulty;
  difficulty_score: number;
  grid_size?: string;
  grid_data?: Record<string, unknown>;
  word_list?: string[];
  clues?: Clue[];
  solution_data?: Record<string, unknown>;
  answer_key_url?: string;
  content_hash?: string;
  status: PuzzleStatus;
  quality_issues?: string[];
  created_at: string;
}

// ---------------------------------------------------------------------------
// Word list management
// ---------------------------------------------------------------------------

export interface WordList {
  words: string[];
  theme?: string;
  difficulty: WordDifficulty;
  source: "ai_generated" | "user_provided" | "curated";
}

export interface SanitizeWordListResult {
  clean_words: string[];
  removed: { word: string; reason: string }[];
}

// ---------------------------------------------------------------------------
// Wizard / creation payloads
// ---------------------------------------------------------------------------

export interface CreatePuzzleBookRequest {
  title: string;
  subtitle?: string;
  audience: Audience;
  puzzle_config: PuzzleTypeConfig[];
  difficulty_mode: DifficultyMode;
  themes: string[];
  seasonal_theme?: string;
  word_difficulty: WordDifficulty;
  clue_style: ClueStyle;
  answer_key_position: AnswerKeyPosition;
  layout: PuzzleLayout;
  extras: string[];
  hint_config?: Record<string, string>;
  puzzle_mix_template?: PuzzleMixTemplate;
  custom_percentages?: Record<string, number>;
  theme_input_method?: string;
  series_name?: string;
  volume_number?: number;
  template_id?: string;
}

export interface GeneratePuzzleRequest {
  puzzle_type: PuzzleType;
  difficulty: Difficulty;
  grid_size?: string;
  theme?: string;
  word_list?: string[];
}

export interface GenerateWordListRequest {
  theme: string;
  word_difficulty: WordDifficulty;
  count?: number;
}

export interface GenerateCluesRequest {
  puzzle_id: string;
  style: ClueStyle;
}

// ---------------------------------------------------------------------------
// Difficulty calibration
// ---------------------------------------------------------------------------

export interface DifficultyDistribution {
  puzzle_number: number;
  difficulty: Difficulty;
  difficulty_score: number;
}

export interface DifficultyCalibrationResult {
  mode: DifficultyMode;
  distribution: DifficultyDistribution[];
  pacing_score: number;
  issues: string[];
}

// ---------------------------------------------------------------------------
// Clue quality governance
// ---------------------------------------------------------------------------

export interface ClueQAIssue {
  clue: string;
  issue: string;
  suggestion: string;
}

export interface ClueQAResult {
  score: number;
  issues: ClueQAIssue[];
  duplicate_phrasings: string[];
  grade_level: number;
}

// ---------------------------------------------------------------------------
// Answer key verification
// ---------------------------------------------------------------------------

export interface AnswerKeyVerification {
  all_keys_generated: boolean;
  all_keys_match: boolean;
  numbering_correct: boolean;
  missing_answers: number[];
  mismatched_puzzles: number[];
}

// ---------------------------------------------------------------------------
// Large print variant
// ---------------------------------------------------------------------------

export interface LargePrintRequest {
  scale: LargePrintScale;
}

export interface LargePrintResult {
  new_book_id: string;
  scale: LargePrintScale;
  puzzles_adjusted: number;
  grids_resized: number;
  words_reduced: number;
}

// ---------------------------------------------------------------------------
// Quality dashboard
// ---------------------------------------------------------------------------

export interface PuzzleBookQAResult {
  overall_score: number;
  duplicate_grids: { puzzle_a: number; puzzle_b: number; similarity: number }[];
  word_list_overlap: { puzzle_a: number; puzzle_b: number; overlap_percent: number }[];
  difficulty_distribution: DifficultyDistribution[];
  render_qa: {
    font_size_pass: boolean;
    grid_legibility_pass: boolean;
    writing_space_pass: boolean;
  };
  all_verified: boolean;
  unverified_puzzles: number[];
}

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export interface PuzzleExportOptions {
  format: "pdf" | "png";
  dpi?: number;
  include_answers?: boolean;
}

export interface PuzzleExportResult {
  download_url: string;
  format: string;
  file_size: number;
  page_count: number;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export interface PuzzleBookStats {
  total_books: number;
  in_progress: number;
  published: number;
  puzzles_created: number;
}

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export interface PuzzleTemplate {
  id: string;
  name: string;
  description: string;
  thumbnail_url: string;
  audience: Audience;
  puzzle_types: PuzzleType[];
  difficulty_mode: DifficultyMode;
  page_count: number;
}
