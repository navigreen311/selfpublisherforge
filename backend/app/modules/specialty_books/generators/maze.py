"""Maze generator using recursive backtracker algorithm."""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import deque
from typing import Any

VALID_SHAPES = ("rectangle", "circle", "star", "christmas_tree", "pumpkin", "heart")
GRID_SIZE_PRESETS: dict[str, int] = {"easy": 10, "medium": 20, "hard": 40}

def _make_mask_rectangle(size):
    return [[True]*size for _ in range(size)]

def _make_mask_circle(size):
    mask = [[False]*size for _ in range(size)]
    cx = cy = (size-1)/2.0; radius = size/2.0 - 0.5
    for r in range(size):
        for c in range(size):
            if (r-cy)**2 + (c-cx)**2 <= radius**2: mask[r][c] = True
    return mask

def _make_mask_star(size):
    mask = [[False]*size for _ in range(size)]
    cx = cy = (size-1)/2.0; outer_r = size/2.0-0.5; inner_r = outer_r*0.38; points = 5
    for r in range(size):
        for c in range(size):
            dx, dy = c-cx, r-cy; angle = math.atan2(dy, dx); dist = math.sqrt(dx*dx+dy*dy)
            seg = math.pi/points; rel = angle % (2*seg)
            if rel > seg: rel = 2*seg - rel
            edge = inner_r + (outer_r-inner_r)*(1-rel/seg)
            if dist <= edge: mask[r][c] = True
    return mask

def _make_mask_christmas_tree(size):
    mask = [[False]*size for _ in range(size)]; cx = size/2.0; th = int(size*0.80)
    for r in range(th):
        hw = ((r+1)/th)*(size/2.0-1)
        for c in range(size):
            if abs(c-cx+0.5) <= hw: mask[r][c] = True
    trunk = max(1, size//8)
    for r in range(th, size):
        for c in range(size):
            if abs(c-cx+0.5) <= trunk: mask[r][c] = True
    return mask

def _make_mask_pumpkin(size):
    mask = [[False]*size for _ in range(size)]
    cx = (size-1)/2.0; cy = (size-1)/2.0+size*0.05; rx = size/2.0-0.5; ry = size/2.3
    for r in range(size):
        for c in range(size):
            if ((r-cy)/ry)**2+((c-cx)/rx)**2 <= 1.0: mask[r][c] = True
    sh = max(1, size//10); st = max(0, int(cy-ry)-max(1, size//8)); sb = max(0, int(cy-ry))
    for r in range(st, sb+1):
        for c in range(size):
            if abs(c-cx) <= sh and 0 <= r < size: mask[r][c] = True
    return mask

def _make_mask_heart(size):
    mask = [[False]*size for _ in range(size)]
    cx = (size-1)/2.0; cy = (size-1)/2.0; scale = size/2.0-1
    for r in range(size):
        for c in range(size):
            x = (c-cx)/scale; y = -(r-cy)/scale
            if (x*x+y*y-1)**3 - x*x*y*y*y <= 0.05: mask[r][c] = True
    return mask

_MASK_BUILDERS: dict[str, Any] = {
    "rectangle": _make_mask_rectangle, "circle": _make_mask_circle, "star": _make_mask_star,
    "christmas_tree": _make_mask_christmas_tree, "pumpkin": _make_mask_pumpkin, "heart": _make_mask_heart,
}

def _new_cell(masked=False):
    return {"top": True, "right": True, "bottom": True, "left": True, "masked": masked}

_NEIGHBOURS = [(-1,0,"top","bottom"),(0,1,"right","left"),(1,0,"bottom","top"),(0,-1,"left","right")]

def _generate_maze_grid(size, mask, rng):
    grid = [[_new_cell(masked=not mask[r][c]) for c in range(size)] for r in range(size)]
    visited = [[False]*size for _ in range(size)]
    start = None
    for r in range(size):
        for c in range(size):
            if mask[r][c]: start = (r,c); break
        if start: break
    if not start: return grid
    stack = [start]; visited[start[0]][start[1]] = True
    while stack:
        r,c = stack[-1]; nbrs = []
        for dr,dc,wf,wt in _NEIGHBOURS:
            nr,nc = r+dr, c+dc
            if 0<=nr<size and 0<=nc<size and mask[nr][nc] and not visited[nr][nc]:
                nbrs.append((nr,nc,wf,wt))
        if nbrs:
            nr,nc,wf,wt = rng.choice(nbrs); grid[r][c][wf]=False; grid[nr][nc][wt]=False
            visited[nr][nc]=True; stack.append((nr,nc))
        else: stack.pop()
    return grid

def _find_start_end(size, mask):
    start = end = None
    for r in range(size):
        for c in range(size):
            if mask[r][c]:
                if start is None: start = (r,c)
                end = (r,c)
    assert start and end; return start, end

def _solve_bfs(grid, size, start, end):
    visited = [[False]*size for _ in range(size)]
    parent = {start: None}; queue = deque([start]); visited[start[0]][start[1]] = True
    wm = [("top",-1,0),("right",0,1),("bottom",1,0),("left",0,-1)]
    while queue:
        r,c = queue.popleft()
        if (r,c) == end:
            path = []; cur = end
            while cur is not None: path.append(cur); cur = parent[cur]
            path.reverse(); return path
        for wn,dr,dc in wm:
            if grid[r][c][wn]: continue
            nr,nc = r+dr, c+dc
            if 0<=nr<size and 0<=nc<size and not visited[nr][nc] and not grid[nr][nc]["masked"]:
                visited[nr][nc]=True; parent[(nr,nc)]=(r,c); queue.append((nr,nc))
    return []

def _count_dead_ends(grid, size):
    count = 0
    for r in range(size):
        for c in range(size):
            if grid[r][c]["masked"]: continue
            if sum(1 for w in ("top","right","bottom","left") if not grid[r][c][w]) == 1: count += 1
    return count

def _branch_factor(grid, size):
    tp = cc = 0
    for r in range(size):
        for c in range(size):
            if grid[r][c]["masked"]: continue
            o = sum(1 for w in ("top","right","bottom","left") if not grid[r][c][w])
            if o > 1: tp += o; cc += 1
    return tp/cc if cc else 0

def _difficulty_score(pl, de, bf, size):
    tc = size*size; pr = pl/tc if tc else 0; dr = de/tc if tc else 0
    return max(0, min(100, int(pr*40+dr*30+min(bf/4,1)*30)))

def _content_hash(grid, size, shape):
    wd = []
    for r in range(size):
        rd = []
        for c in range(size):
            cell = grid[r][c]; rd.append((cell["top"],cell["right"],cell["bottom"],cell["left"],cell["masked"]))
        wd.append(rd)
    return hashlib.sha256(json.dumps({"walls":wd,"size":size,"shape":shape},sort_keys=True).encode()).hexdigest()

def generate_maze(grid_size=20, difficulty="medium", shape="rectangle", seed=None):
    """Generate a maze puzzle."""
    rng = random.Random(seed)
    if shape not in VALID_SHAPES: raise ValueError(f"Invalid shape '{shape}'. Must be one of {VALID_SHAPES}")
    if grid_size == 20: grid_size = GRID_SIZE_PRESETS.get(difficulty, 20)
    mask = _MASK_BUILDERS[shape](grid_size); grid = _generate_maze_grid(grid_size, mask, rng)
    start, end = _find_start_end(grid_size, mask); sp = _solve_bfs(grid, grid_size, start, end)
    de = _count_dead_ends(grid, grid_size); bf = _branch_factor(grid, grid_size)
    score = _difficulty_score(len(sp), de, bf, grid_size); ch = _content_hash(grid, grid_size, shape)
    return {"grid": [[grid[r][c] for c in range(grid_size)] for r in range(grid_size)],
            "size": grid_size, "start": list(start), "end": list(end),
            "solution_path": [list(p) for p in sp], "dead_ends": de,
            "difficulty_score": score, "content_hash": ch, "shape": shape}
