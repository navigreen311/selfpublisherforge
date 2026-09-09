"""
Maze puzzle generator.

Algorithm: Recursive backtracker (depth-first search) with shaped maze support.
Produces valid, solvable mazes with solution paths via BFS.
"""

import hashlib
import json
import math
import random
from collections import deque

# Wall bit flags for each cell
WALL_TOP = 1
WALL_RIGHT = 2
WALL_BOTTOM = 4
WALL_LEFT = 8
ALL_WALLS = WALL_TOP | WALL_RIGHT | WALL_BOTTOM | WALL_LEFT

# Opposite wall mapping
OPPOSITE_WALL = {
    WALL_TOP: WALL_BOTTOM,
    WALL_RIGHT: WALL_LEFT,
    WALL_BOTTOM: WALL_TOP,
    WALL_LEFT: WALL_RIGHT,
}

# Direction deltas: (row_delta, col_delta, wall_to_remove)
DIRECTIONS = [
    (-1, 0, WALL_TOP),  # Up
    (0, 1, WALL_RIGHT),  # Right
    (1, 0, WALL_BOTTOM),  # Down
    (0, -1, WALL_LEFT),  # Left
]


# --- Shape boundary functions ---


def _rect_mask(row: int, col: int, width: int, height: int) -> bool:
    """Rectangle: all cells are valid."""
    return True


def _circle_mask(row: int, col: int, width: int, height: int) -> bool:
    """Circle: cells within circular boundary."""
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    radius = min(cx, cy)
    dx = col - cx
    dy = row - cy
    return (dx * dx + dy * dy) <= (radius * radius)


def _heart_mask(row: int, col: int, width: int, height: int) -> bool:
    """Heart shape using parametric heart equation."""
    # Normalize coordinates to [-1, 1]
    nx = (col - (width - 1) / 2.0) / ((width - 1) / 2.0) * 1.2
    ny = ((height - 1) / 2.0 - row) / ((height - 1) / 2.0) * 1.3 - 0.2

    # Heart equation: (x^2 + y^2 - 1)^3 - x^2 * y^3 <= 0
    val = (nx * nx + ny * ny - 1) ** 3 - nx * nx * ny * ny * ny
    return val <= 0


def _star_mask(row: int, col: int, width: int, height: int) -> bool:
    """5-pointed star shape."""
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    dx = col - cx
    dy = cy - row  # Flip y so star points up
    r = math.sqrt(dx * dx + dy * dy)
    max_r = min(cx, cy)

    if r == 0:
        return True
    if r > max_r:
        return False

    angle = math.atan2(dy, dx)
    # 5-pointed star
    n = 5
    inner_ratio = 0.38
    # Angle to nearest star point
    sector = 2 * math.pi / n
    half_sector = sector / 2
    relative_angle = (angle + math.pi / 2) % sector

    if relative_angle < half_sector:
        t = relative_angle / half_sector
    else:
        t = (sector - relative_angle) / half_sector

    threshold = max_r * (inner_ratio + (1 - inner_ratio) * t)
    return r <= threshold


def _christmas_tree_mask(row: int, col: int, width: int, height: int) -> bool:
    """Christmas tree shape: triangular tree with trunk."""
    cx = (width - 1) / 2.0
    # Normalize
    ny = row / (height - 1)  # 0=top, 1=bottom
    nx = col / (width - 1)  # 0=left, 1=right

    # Trunk: bottom 15%, center 20% width
    if ny > 0.85:
        return abs(nx - 0.5) <= 0.1

    # Tree: triangle that widens from top to bottom
    # At ny=0 (top), width = 0.05; at ny=0.85, width = 0.48
    half_width = 0.05 + ny * 0.5

    # Add layered effect (3 tiers with slight widening)
    tier_bonus = 0.0
    if ny > 0.25:
        tier_bonus += 0.03
    if ny > 0.5:
        tier_bonus += 0.03

    return abs(nx - 0.5) <= (half_width + tier_bonus)


def _pumpkin_mask(row: int, col: int, width: int, height: int) -> bool:
    """Pumpkin shape: wide ellipse with stem."""
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    ny = row / (height - 1)
    nx = col / (width - 1)

    # Stem: top 12%, narrow center
    if ny < 0.12:
        return abs(nx - 0.5) <= 0.06

    # Pumpkin body: wide ellipse
    dx = (col - cx) / (cx * 0.95)
    dy = (row - cy * 1.1) / (cy * 0.85)
    return (dx * dx + dy * dy) <= 1.0


SHAPE_MASKS = {
    "rectangle": _rect_mask,
    "circle": _circle_mask,
    "heart": _heart_mask,
    "star": _star_mask,
    "christmas_tree": _christmas_tree_mask,
    "pumpkin": _pumpkin_mask,
}


def _build_grid(
    width: int,
    height: int,
    shape: str,
) -> tuple[list[list[int]], list[list[bool]]]:
    """
    Build initial grid with all walls up and shape mask applied.

    Returns:
        (walls grid, active mask) where walls[r][c] is wall bitfield,
        active[r][c] is True if cell is part of the maze.
    """
    mask_fn = SHAPE_MASKS.get(shape, _rect_mask)

    walls = [[ALL_WALLS for _ in range(width)] for _ in range(height)]
    active = [[False] * width for _ in range(height)]

    for r in range(height):
        for c in range(width):
            active[r][c] = mask_fn(r, c, width, height)

    return walls, active


def _find_entrance_exit(
    active: list[list[bool]],
    width: int,
    height: int,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Find entrance (top-left area) and exit (bottom-right area) cells
    that are within the active mask.
    """
    entrance = None
    exit_cell = None

    # Entrance: scan from top-left
    for r in range(height):
        for c in range(width):
            if active[r][c]:
                entrance = (r, c)
                break
        if entrance:
            break

    # Exit: scan from bottom-right
    for r in range(height - 1, -1, -1):
        for c in range(width - 1, -1, -1):
            if active[r][c]:
                exit_cell = (r, c)
                break
        if exit_cell:
            break

    if entrance is None or exit_cell is None:
        raise ValueError("No active cells found in maze grid")

    # Make sure entrance != exit
    if entrance == exit_cell:
        # Try to find a different exit
        for r in range(height - 1, -1, -1):
            for c in range(width - 1, -1, -1):
                if active[r][c] and (r, c) != entrance:
                    exit_cell = (r, c)
                    break
            if exit_cell != entrance:
                break

    return entrance, exit_cell


def _recursive_backtrack(
    walls: list[list[int]],
    active: list[list[bool]],
    visited: list[list[bool]],
    width: int,
    height: int,
    start_row: int,
    start_col: int,
) -> None:
    """
    Recursive backtracker maze generation (iterative implementation to avoid
    stack overflow on large grids).
    """
    stack = [(start_row, start_col)]
    visited[start_row][start_col] = True

    while stack:
        r, c = stack[-1]

        # Get unvisited neighbors
        neighbors = []
        for dr, dc, wall in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < height and 0 <= nc < width and active[nr][nc] and not visited[nr][nc]:
                neighbors.append((nr, nc, wall))

        if neighbors:
            # Choose random neighbor
            nr, nc, wall = random.choice(neighbors)

            # Remove wall between current and neighbor
            walls[r][c] &= ~wall
            walls[nr][nc] &= ~OPPOSITE_WALL[wall]

            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            # Backtrack
            stack.pop()


def _solve_bfs(
    walls: list[list[int]],
    active: list[list[bool]],
    width: int,
    height: int,
    entrance: tuple[int, int],
    exit_cell: tuple[int, int],
) -> list[tuple[int, int]]:
    """
    Solve maze using BFS (breadth-first search) to find shortest path.

    Returns list of (row, col) tuples from entrance to exit.
    """
    queue = deque()
    queue.append(entrance)
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {entrance: None}

    while queue:
        r, c = queue.popleft()

        if (r, c) == exit_cell:
            # Reconstruct path
            path = []
            current: tuple[int, int] | None = (r, c)
            while current is not None:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for dr, dc, wall in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and active[nr][nc]
                and (nr, nc) not in came_from
                and not (walls[r][c] & wall)  # No wall in this direction
            ):
                came_from[(nr, nc)] = (r, c)
                queue.append((nr, nc))

    # No path found (shouldn't happen with recursive backtracker)
    return []


def _count_dead_ends(
    walls: list[list[int]],
    active: list[list[bool]],
    width: int,
    height: int,
) -> int:
    """Count cells with exactly 3 walls (dead ends)."""
    count = 0
    for r in range(height):
        for c in range(width):
            if not active[r][c]:
                continue
            # Count walls
            wall_count = bin(walls[r][c]).count("1")
            if wall_count == 3:
                count += 1
    return count


def _calculate_branch_factor(
    walls: list[list[int]],
    active: list[list[bool]],
    width: int,
    height: int,
) -> float:
    """
    Calculate average branching factor (average number of open passages per cell).
    """
    total_openings = 0
    cell_count = 0
    for r in range(height):
        for c in range(width):
            if not active[r][c]:
                continue
            openings = 4 - bin(walls[r][c]).count("1")
            total_openings += openings
            cell_count += 1
    return total_openings / cell_count if cell_count > 0 else 0.0


def generate_maze(
    width: int = 20,
    height: int = 20,
    shape: str = "rectangle",
    seed: int | None = None,
) -> dict:
    """
    Generate a maze using recursive backtracker (depth-first search).

    Args:
        width: Grid width in cells.
        height: Grid height in cells.
        shape: Shape of the maze boundary.
            Options: rectangle, circle, heart, star, christmas_tree, pumpkin.
        seed: Optional random seed for reproducibility.

    Returns:
        Dictionary with grid data, solution path, entrance, exit,
        dead end count, difficulty score, content_hash.
    """
    if seed is not None:
        random.seed(seed)

    if shape not in SHAPE_MASKS:
        raise ValueError(f"Unknown shape '{shape}'. " f"Options: {', '.join(SHAPE_MASKS.keys())}")

    walls, active = _build_grid(width, height, shape)
    visited = [[False] * width for _ in range(height)]

    # Find a starting cell within the active region
    active_cells = [(r, c) for r in range(height) for c in range(width) if active[r][c]]
    if not active_cells:
        raise ValueError("No active cells for the given shape and dimensions")

    start = random.choice(active_cells)
    _recursive_backtrack(walls, active, visited, width, height, start[0], start[1])

    # Handle disconnected active cells (can happen with complex shapes)
    # Run backtracker from any unvisited active cell
    for r in range(height):
        for c in range(width):
            if active[r][c] and not visited[r][c]:
                _recursive_backtrack(walls, active, visited, width, height, r, c)

    # Find entrance and exit
    entrance, exit_cell = _find_entrance_exit(active, width, height)

    # Solve with BFS
    solution_path = _solve_bfs(walls, active, width, height, entrance, exit_cell)

    # If no path (disconnected regions), connect them and re-solve
    if not solution_path:
        # Force connection by removing a wall between regions
        # This is a fallback for edge cases with complex shapes
        for r in range(height):
            for c in range(width):
                if not active[r][c]:
                    continue
                for dr, dc, wall in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and active[nr][nc] and (walls[r][c] & wall):
                        # Check if they're in different regions
                        # Simple check: try removing wall and solving
                        walls[r][c] &= ~wall
                        walls[nr][nc] &= ~OPPOSITE_WALL[wall]
        solution_path = _solve_bfs(walls, active, width, height, entrance, exit_cell)

    dead_end_count = _count_dead_ends(walls, active, width, height)
    branch_factor = _calculate_branch_factor(walls, active, width, height)
    active_count = len(active_cells)

    difficulty = calculate_difficulty(
        path_length=len(solution_path),
        dead_end_count=dead_end_count,
        branch_factor=branch_factor,
        grid_size=max(width, height),
    )

    # Serialize wall data as list of lists of integers
    grid_data = []
    for r in range(height):
        row = []
        for c in range(width):
            if active[r][c]:
                row.append(walls[r][c])
            else:
                row.append(-1)  # -1 = masked/inactive cell
        grid_data.append(row)

    # Content hash
    content_data = {
        "grid": grid_data,
        "entrance": list(entrance),
        "exit": list(exit_cell),
        "shape": shape,
    }
    content_hash = hashlib.sha256(json.dumps(content_data, sort_keys=True).encode()).hexdigest()

    return {
        "grid": grid_data,
        "width": width,
        "height": height,
        "shape": shape,
        "entrance": list(entrance),
        "exit": list(exit_cell),
        "solution_path": [list(p) for p in solution_path],
        "dead_end_count": dead_end_count,
        "branch_factor": round(branch_factor, 3),
        "active_cell_count": active_count,
        "difficulty_score": difficulty,
        "content_hash": content_hash,
    }


def calculate_difficulty(
    path_length: int,
    dead_end_count: int,
    branch_factor: float,
    grid_size: int,
) -> float:
    """
    Calculate maze difficulty score (0-100).

    Factors:
    - Path length: longer solution path = harder
    - Dead end count: more dead ends = harder
    - Branch factor: more branching = harder (more choices)
    - Grid size: larger grid = harder
    """
    # Path length (0-30): normalize by grid_size^2
    max_path = grid_size * grid_size
    path_ratio = min(1.0, path_length / max_path) if max_path > 0 else 0
    path_score = path_ratio * 30.0

    # Dead end count (0-25): more dead ends = harder
    # Normalize by total cells
    total_cells = grid_size * grid_size
    dead_ratio = min(1.0, dead_end_count / (total_cells * 0.4)) if total_cells > 0 else 0
    dead_score = dead_ratio * 25.0

    # Branch factor (0-20): higher = more choices = harder
    # Perfect maze has branch factor ~2.0, max is 4.0
    branch_score = min(20.0, max(0.0, (branch_factor - 1.5) / 1.5 * 20))

    # Grid size (0-25): 10=0, 40=25
    size_score = min(25.0, max(0.0, (grid_size - 10) / 30 * 25))

    total = path_score + dead_score + branch_score + size_score
    return round(min(100.0, max(0.0, total)), 1)


def render_to_svg(
    puzzle: dict,
    cell_size: int = 20,
    show_solution: bool = False,
    wall_color: str = "#333333",
    path_color: str = "#4CAF50",
    entrance_color: str = "#2196F3",
    exit_color: str = "#F44336",
    wall_thickness: int = 2,
) -> str:
    """
    Render a maze puzzle to SVG string for print output.

    Args:
        puzzle: Result from generate_maze().
        cell_size: Size of each grid cell in pixels.
        show_solution: If True, draw the solution path.
        wall_color: Color for maze walls.
        path_color: Color for solution path.
        entrance_color: Color for entrance marker.
        exit_color: Color for exit marker.
        wall_thickness: Width of wall lines.

    Returns:
        SVG string.
    """
    grid = puzzle["grid"]
    w = puzzle["width"]
    h = puzzle["height"]
    entrance = tuple(puzzle["entrance"])
    exit_cell = tuple(puzzle["exit"])
    solution_path = [tuple(p) for p in puzzle["solution_path"]]

    padding = 20
    svg_width = w * cell_size + 2 * padding
    svg_height = h * cell_size + 2 * padding

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_width}" height="{svg_height}" '
        f'viewBox="0 0 {svg_width} {svg_height}">'
    )
    parts.append(f'<rect width="{svg_width}" height="{svg_height}" fill="white"/>')

    # Draw solution path first (behind walls)
    if show_solution and solution_path:
        path_points = []
        for r, c in solution_path:
            cx = padding + c * cell_size + cell_size // 2
            cy = padding + r * cell_size + cell_size // 2
            path_points.append(f"{cx},{cy}")

        parts.append(
            f'<polyline points="{" ".join(path_points)}" '
            f'fill="none" stroke="{path_color}" stroke-width="{cell_size // 3}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="0.6"/>'
        )

    # Draw cells and walls
    for r in range(h):
        for c in range(w):
            cell_walls = grid[r][c]
            if cell_walls == -1:
                # Masked cell - fill with gray
                x = padding + c * cell_size
                y = padding + r * cell_size
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" ' f'fill="#EEEEEE" stroke="none"/>'
                )
                continue

            x = padding + c * cell_size
            y = padding + r * cell_size

            # Draw walls
            if cell_walls & WALL_TOP:
                parts.append(
                    f'<line x1="{x}" y1="{y}" x2="{x + cell_size}" y2="{y}" '
                    f'stroke="{wall_color}" stroke-width="{wall_thickness}" stroke-linecap="round"/>'
                )
            if cell_walls & WALL_RIGHT:
                parts.append(
                    f'<line x1="{x + cell_size}" y1="{y}" '
                    f'x2="{x + cell_size}" y2="{y + cell_size}" '
                    f'stroke="{wall_color}" stroke-width="{wall_thickness}" stroke-linecap="round"/>'
                )
            if cell_walls & WALL_BOTTOM:
                parts.append(
                    f'<line x1="{x}" y1="{y + cell_size}" '
                    f'x2="{x + cell_size}" y2="{y + cell_size}" '
                    f'stroke="{wall_color}" stroke-width="{wall_thickness}" stroke-linecap="round"/>'
                )
            if cell_walls & WALL_LEFT:
                parts.append(
                    f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + cell_size}" '
                    f'stroke="{wall_color}" stroke-width="{wall_thickness}" stroke-linecap="round"/>'
                )

    # Draw entrance and exit markers
    er, ec = entrance
    ex = padding + ec * cell_size + cell_size // 2
    ey = padding + er * cell_size + cell_size // 2
    marker_r = cell_size // 4
    parts.append(f'<circle cx="{ex}" cy="{ey}" r="{marker_r}" ' f'fill="{entrance_color}" opacity="0.8"/>')
    parts.append(
        f'<text x="{ex}" y="{ey + 4}" text-anchor="middle" '
        f'font-family="Arial" font-size="{marker_r}" '
        f'fill="white" font-weight="bold">S</text>'
    )

    xr, xc = exit_cell
    xx = padding + xc * cell_size + cell_size // 2
    xy = padding + xr * cell_size + cell_size // 2
    parts.append(f'<circle cx="{xx}" cy="{xy}" r="{marker_r}" ' f'fill="{exit_color}" opacity="0.8"/>')
    parts.append(
        f'<text x="{xx}" y="{xy + 4}" text-anchor="middle" '
        f'font-family="Arial" font-size="{marker_r}" '
        f'fill="white" font-weight="bold">E</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)
