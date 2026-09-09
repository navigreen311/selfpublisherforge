"""
Word Connect puzzle generator.

Algorithm: Two-column matching exercise where players draw lines connecting
related word pairs. Supports difficulty scaling via distractor words and
word count.
"""

import hashlib
import random

from .utils import generate_content_hash, svg_footer, svg_header, svg_rect, svg_text


def generate_word_connect(
    word_pairs: list[tuple[str, str]],
    difficulty: str = "medium",
    distractors: list[str] | None = None,
    seed: int | None = None,
) -> dict:
    """
    Generate a Word Connect puzzle.

    Players draw lines connecting related word pairs arranged in two columns
    (left and right). The right column is shuffled so matches aren't obvious.

    Args:
        word_pairs: List of (left_word, right_word) tuples representing matches.
                    e.g., [("CAT", "FELINE"), ("DOG", "CANINE")]
        difficulty: One of "easy", "medium", "hard". Controls distractor count
                    and shuffle aggressiveness.
        distractors: Optional extra words added to the right column that have
                     no match. If None, auto-generated based on difficulty.
        seed: Optional random seed for reproducibility.

    Returns:
        Dictionary with left_words, right_words, solution_pairs, distractors,
        content_hash, and difficulty_score.
    """
    if seed is not None:
        random.seed(seed)

    # Sanitize and deduplicate pairs
    clean_pairs: list[tuple[str, str]] = []
    seen_left: set[str] = set()
    seen_right: set[str] = set()

    for left, right in word_pairs:
        l_clean = _sanitize(left)
        r_clean = _sanitize(right)
        if not l_clean or not r_clean:
            continue
        if l_clean in seen_left or r_clean in seen_right:
            continue
        seen_left.add(l_clean)
        seen_right.add(r_clean)
        clean_pairs.append((l_clean, r_clean))

    if not clean_pairs:
        return _empty_result()

    # Build left column (stable order)
    left_words = [pair[0] for pair in clean_pairs]

    # Build right column (shuffled)
    right_words = [pair[1] for pair in clean_pairs]
    random.shuffle(right_words)

    # Ensure no word sits in its original matching index (derangement attempt)
    right_words = _derange(right_words, [p[1] for p in clean_pairs])

    # Determine distractors
    if distractors is not None:
        distractor_list = [_sanitize(d) for d in distractors if _sanitize(d)]
        # Remove any that collide with existing words
        all_existing = seen_left | seen_right
        distractor_list = [d for d in distractor_list if d not in all_existing]
    else:
        distractor_list = _auto_distractors(difficulty, clean_pairs)

    # Insert distractors into the right column at random positions
    for d in distractor_list:
        insert_pos = random.randint(0, len(right_words))
        right_words.insert(insert_pos, d)

    # Solution mapping: left_index -> right_index
    solution_pairs: list[dict] = []
    for l_word, r_word in clean_pairs:
        l_idx = left_words.index(l_word)
        r_idx = right_words.index(r_word)
        solution_pairs.append({
            "left_index": l_idx,
            "right_index": r_idx,
            "left_word": l_word,
            "right_word": r_word,
        })

    # Difficulty score
    difficulty_score = calculate_difficulty(
        pair_count=len(clean_pairs),
        distractor_count=len(distractor_list),
        avg_word_similarity=_avg_similarity(clean_pairs),
    )

    # Content hash
    content_data = {
        "left_words": left_words,
        "right_words": right_words,
        "solution_pairs": [(s["left_word"], s["right_word"]) for s in solution_pairs],
    }
    content_hash = generate_content_hash(content_data)

    return {
        "left_words": left_words,
        "right_words": right_words,
        "solution_pairs": solution_pairs,
        "distractors": distractor_list,
        "pair_count": len(clean_pairs),
        "distractor_count": len(distractor_list),
        "difficulty_score": difficulty_score,
        "content_hash": content_hash,
    }


def calculate_difficulty(
    pair_count: int,
    distractor_count: int,
    avg_word_similarity: float = 0.0,
) -> float:
    """
    Calculate Word Connect difficulty score (0-100).

    Factors:
    - pair_count: More pairs = harder (0-40 points).
    - distractor_count: More distractors = harder (0-35 points).
    - avg_word_similarity: Higher similarity among words = harder (0-25 points).
    """
    # Pair count: 3 pairs = 0, 15 pairs = 40
    pair_score = min(40.0, max(0.0, (pair_count - 3) / 12 * 40))

    # Distractor count: 0 = 0, 8 = 35
    distractor_score = min(35.0, max(0.0, distractor_count / 8 * 35))

    # Word similarity: 0.0 = 0, 1.0 = 25
    similarity_score = min(25.0, max(0.0, avg_word_similarity * 25))

    total = pair_score + distractor_score + similarity_score
    return round(min(100.0, max(0.0, total)), 1)


def render_to_svg(
    puzzle: dict,
    show_solution: bool = False,
    font_family: str = "Arial, Helvetica, sans-serif",
    row_height: int = 36,
    column_width: int = 180,
    padding: int = 30,
) -> str:
    """
    Render a Word Connect puzzle to SVG.

    Shows two columns of words. When show_solution is True, draws lines
    connecting matched pairs.

    Args:
        puzzle: Result from generate_word_connect().
        show_solution: If True, draw solution lines between matched pairs.
        font_family: CSS font family.
        row_height: Vertical spacing between words.
        column_width: Width allocated for each column.
        padding: Padding around the content.

    Returns:
        SVG string.
    """
    left_words = puzzle["left_words"]
    right_words = puzzle["right_words"]
    solution_pairs = puzzle["solution_pairs"]

    max_rows = max(len(left_words), len(right_words))
    gap = 120  # horizontal gap between columns

    svg_w = 2 * padding + 2 * column_width + gap
    svg_h = 2 * padding + max_rows * row_height + row_height  # extra for title

    parts: list[str] = []
    parts.append(svg_header(svg_w, svg_h))

    # Background
    parts.append(svg_rect(0, 0, svg_w, svg_h, fill="white", stroke="none"))

    # Title
    title_y = padding + 10
    parts.append(svg_text(
        svg_w // 2, title_y, "Word Connect",
        font_size=18, anchor="middle", font_family=font_family,
        font_weight="bold",
    ))

    # Column headers
    header_y = title_y + 30
    left_x = padding + 10
    right_x = padding + column_width + gap + 10

    parts.append(svg_text(
        left_x, header_y, "Column A",
        font_size=13, anchor="start", font_family=font_family,
        font_weight="bold", fill="#555555",
    ))
    parts.append(svg_text(
        right_x, header_y, "Column B",
        font_size=13, anchor="start", font_family=font_family,
        font_weight="bold", fill="#555555",
    ))

    content_start_y = header_y + 28

    # Draw left column words with index labels
    left_positions: list[tuple[int, int]] = []
    for i, word in enumerate(left_words):
        y = content_start_y + i * row_height
        label = f"{i + 1}. {word}"
        parts.append(svg_text(
            left_x, y, _escape_xml(label),
            font_size=14, anchor="start", font_family=font_family,
        ))
        # Connection point at right edge of left column
        left_positions.append((padding + column_width - 5, y))

    # Draw right column words with letter labels
    right_positions: list[tuple[int, int]] = []
    for i, word in enumerate(right_words):
        y = content_start_y + i * row_height
        letter_label = chr(65 + i) if i < 26 else str(i + 1)
        label = f"{letter_label}. {word}"
        parts.append(svg_text(
            right_x, y, _escape_xml(label),
            font_size=14, anchor="start", font_family=font_family,
        ))
        # Connection point at left edge of right column
        right_positions.append((padding + column_width + gap + 5, y))

    # Draw solution lines if requested
    if show_solution:
        colors = [
            "#E74C3C", "#3498DB", "#2ECC71", "#F39C12", "#9B59B6",
            "#1ABC9C", "#E67E22", "#34495E", "#16A085", "#C0392B",
            "#2980B9", "#27AE60", "#D35400", "#8E44AD", "#F1C40F",
        ]
        for idx, sol in enumerate(solution_pairs):
            l_idx = sol["left_index"]
            r_idx = sol["right_index"]
            if l_idx < len(left_positions) and r_idx < len(right_positions):
                lx, ly = left_positions[l_idx]
                rx, ry = right_positions[r_idx]
                color = colors[idx % len(colors)]
                parts.append(
                    f'  <line x1="{lx}" y1="{ly}" x2="{rx}" y2="{ry}" '
                    f'stroke="{color}" stroke-width="2" '
                    f'stroke-dasharray="6,3" opacity="0.8"/>\n'
                )

    # Instructions at bottom
    instr_y = content_start_y + max_rows * row_height + 10
    parts.append(svg_text(
        svg_w // 2, instr_y,
        "Draw a line from each word on the left to its match on the right.",
        font_size=11, anchor="middle", font_family=font_family,
        fill="#888888",
    ))

    parts.append(svg_footer())
    return "".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _empty_result() -> dict:
    """Return an empty puzzle result when no valid pairs are provided."""
    return {
        "left_words": [],
        "right_words": [],
        "solution_pairs": [],
        "distractors": [],
        "pair_count": 0,
        "distractor_count": 0,
        "difficulty_score": 0.0,
        "content_hash": hashlib.sha256(b"empty").hexdigest(),
    }


def _sanitize(word: str) -> str:
    """Uppercase, strip non-alphanumeric (keep spaces for multi-word terms)."""
    cleaned = "".join(ch for ch in word.strip() if ch.isalpha() or ch == " ")
    return cleaned.upper()


def _escape_xml(text: str) -> str:
    """Escape XML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _derange(shuffled: list[str], original: list[str]) -> list[str]:
    """
    Try to ensure no element sits at its original index.
    Best-effort: if the list has only 1 element, derangement is impossible.
    """
    if len(shuffled) <= 1:
        return shuffled

    for _ in range(50):  # attempt limit
        conflicts = [i for i in range(len(shuffled)) if shuffled[i] == original[i]]
        if not conflicts:
            return shuffled
        # Swap each conflicting element with a random other position
        for idx in conflicts:
            swap_candidates = [j for j in range(len(shuffled)) if j != idx]
            swap = random.choice(swap_candidates)
            shuffled[idx], shuffled[swap] = shuffled[swap], shuffled[idx]

    return shuffled


def _auto_distractors(
    difficulty: str,
    pairs: list[tuple[str, str]],
) -> list[str]:
    """
    Generate distractor words based on difficulty level.

    Distractors are plausible-looking words that don't match anything in the
    left column, making the puzzle harder.
    """
    distractor_counts = {
        "easy": 0,
        "medium": 2,
        "hard": 5,
    }
    count = distractor_counts.get(difficulty, 2)
    if count == 0:
        return []

    # Build distractors from a pool of generic decoy words
    # These are thematically neutral so they work across topics
    decoy_pool = [
        "PHANTOM", "RIDDLE", "PRISM", "VORTEX", "NEBULA",
        "CIPHER", "QUARTZ", "MOSAIC", "RELIC", "SPHINX",
        "BEACON", "MIRAGE", "ZENITH", "FOSSIL", "NEXUS",
        "AURORA", "TEMPO", "FLUX", "MATRIX", "ORBIT",
    ]

    # Exclude words already used
    existing = {p[0] for p in pairs} | {p[1] for p in pairs}
    available = [w for w in decoy_pool if w not in existing]

    random.shuffle(available)
    return available[:count]


def _avg_similarity(pairs: list[tuple[str, str]]) -> float:
    """
    Compute average character-level similarity between all right-column words.

    Higher similarity means it's harder to distinguish the correct match.
    Uses a simple ratio of shared characters to total characters.
    """
    right_words = [p[1] for p in pairs]
    if len(right_words) < 2:
        return 0.0

    total_sim = 0.0
    comparisons = 0

    for i in range(len(right_words)):
        for j in range(i + 1, len(right_words)):
            w1 = right_words[i]
            w2 = right_words[j]
            # Character set overlap ratio
            set1 = set(w1)
            set2 = set(w2)
            if not set1 or not set2:
                continue
            overlap = len(set1 & set2)
            union = len(set1 | set2)
            total_sim += overlap / union if union > 0 else 0.0
            comparisons += 1

    return total_sim / comparisons if comparisons > 0 else 0.0
