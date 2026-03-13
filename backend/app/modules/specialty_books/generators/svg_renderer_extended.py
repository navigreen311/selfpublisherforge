"""SVG renderers for Maze, Sudoku, Word Scramble, and Cryptogram puzzles."""
from __future__ import annotations
from xml.sax.saxutils import escape

def render_maze_svg(puzzle_data, show_solution=False):
    grid=puzzle_data["grid"]; size=puzzle_data["size"]
    cell_px=max(8,400//size); margin=20; total=size*cell_px+margin*2
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{total}" viewBox="0 0 {total} {total}">',
           f'<rect width="{total}" height="{total}" fill="white"/>']
    for r in range(size):
        for c in range(size):
            cell=grid[r][c]
            if cell["masked"]: continue
            x,y=margin+c*cell_px,margin+r*cell_px
            for wall,x1,y1,x2,y2 in [("top",x,y,x+cell_px,y),("right",x+cell_px,y,x+cell_px,y+cell_px),
                                       ("bottom",x,y+cell_px,x+cell_px,y+cell_px),("left",x,y,x,y+cell_px)]:
                if cell[wall]:
                    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black" stroke-width="1.5" stroke-linecap="round"/>')
    s,e=puzzle_data["start"],puzzle_data["end"]; dr=max(2,cell_px//4)
    parts.append(f'<circle cx="{margin+s[1]*cell_px+cell_px/2}" cy="{margin+s[0]*cell_px+cell_px/2}" r="{dr}" fill="green"/>')
    parts.append(f'<circle cx="{margin+e[1]*cell_px+cell_px/2}" cy="{margin+e[0]*cell_px+cell_px/2}" r="{dr}" fill="red"/>')
    if show_solution and puzzle_data.get("solution_path"):
        pts=" ".join(f"{margin+pc*cell_px+cell_px/2},{margin+pr*cell_px+cell_px/2}" for pr,pc in puzzle_data["solution_path"])
        parts.append(f'<polyline points="{pts}" fill="none" stroke="blue" stroke-width="2" opacity="0.6"/>')
    parts.append("</svg>"); return "\n".join(parts)

def render_sudoku_svg(puzzle_data, show_solution=False):
    grid=puzzle_data["grid"]; sol=puzzle_data.get("solution",[]); size=puzzle_data["size"]
    cell_px=40; margin=20; total=size*cell_px+margin*2
    box_r,box_c=(2,2) if size==4 else (2,3) if size==6 else (3,3)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="{total}" viewBox="0 0 {total} {total}">',
           f'<rect width="{total}" height="{total}" fill="white"/>']
    for i in range(size+1):
        x=margin+i*cell_px; sw=2.5 if i%box_c==0 else 0.5
        parts.append(f'<line x1="{x}" y1="{margin}" x2="{x}" y2="{margin+size*cell_px}" stroke="black" stroke-width="{sw}"/>')
    for i in range(size+1):
        y=margin+i*cell_px; sw=2.5 if i%box_r==0 else 0.5
        parts.append(f'<line x1="{margin}" y1="{y}" x2="{margin+size*cell_px}" y2="{y}" stroke="black" stroke-width="{sw}"/>')
    fs=max(12,cell_px//2); display=sol if show_solution and sol else grid
    for r in range(size):
        for c in range(size):
            v=display[r][c]
            if v==0: continue
            x,y=margin+c*cell_px+cell_px/2,margin+r*cell_px+cell_px/2+fs/3
            ig=grid[r][c]!=0; w="bold" if ig else "normal"; clr="black" if ig else "blue"
            parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial" font-size="{fs}" font-weight="{w}" fill="{clr}">{v}</text>')
    parts.append("</svg>"); return "\n".join(parts)

def render_word_scramble_svg(puzzle_data, show_solution=False):
    sc=puzzle_data["scrambles"]; lh=50; m=30; w=500; h=m*2+len(sc)*lh+40
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f'<rect width="{w}" height="{h}" fill="white"/>',
           f'<text x="{w/2}" y="{m}" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold">Word Scramble</text>']
    for i,entry in enumerate(sc):
        y=m+40+i*lh
        parts.append(f'<text x="{m}" y="{y}" font-family="Courier New" font-size="18" font-weight="bold">{i+1}. {escape(entry["scrambled"])}</text>')
        if show_solution:
            parts.append(f'<text x="{w-m}" y="{y}" text-anchor="end" font-family="Arial" font-size="14" fill="blue">{escape(entry["original"])}</text>')
        elif entry.get("hint"):
            parts.append(f'<text x="{w-m}" y="{y}" text-anchor="end" font-family="Arial" font-size="11" fill="gray">({escape(entry["hint"])})</text>')
        parts.append(f'<line x1="{m}" y1="{y+18}" x2="{w-m}" y2="{y+18}" stroke="#ccc" stroke-width="0.5" stroke-dasharray="4,2"/>')
    parts.append("</svg>"); return "\n".join(parts)

def render_cryptogram_svg(puzzle_data, show_solution=False):
    enc=puzzle_data["encoded"]; orig=puzzle_data.get("original","")
    hints={h["encoded_letter"]:h["decoded_letter"] for h in puzzle_data.get("hints",[])}
    cw,lc,m,lh=20,30,30,60; lines=[]; cur=[]
    for ch in enc:
        cur.append(ch)
        if len(cur)>=lc and ch==" ": lines.append("".join(cur)); cur=[]
    if cur: lines.append("".join(cur))
    w=m*2+lc*cw; h=m*2+len(lines)*lh+60
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
           f'<rect width="{w}" height="{h}" fill="white"/>',
           f'<text x="{w/2}" y="{m}" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold">Cryptogram</text>']
    oi=0
    for li,line in enumerate(lines):
        by=m+50+li*lh
        for ci,ch in enumerate(line):
            x=m+ci*cw
            if ch.isalpha():
                parts.append(f'<text x="{x+cw/2}" y="{by}" text-anchor="middle" font-family="Courier New" font-size="16" font-weight="bold">{escape(ch.upper())}</text>')
                bly=by+20; uc=ch.upper()
                if show_solution and oi<len(orig):
                    parts.append(f'<text x="{x+cw/2}" y="{bly}" text-anchor="middle" font-family="Arial" font-size="14" fill="blue">{escape(orig[oi].upper())}</text>')
                elif uc in hints:
                    parts.append(f'<text x="{x+cw/2}" y="{bly}" text-anchor="middle" font-family="Arial" font-size="14" fill="green">{escape(hints[uc])}</text>')
                else:
                    parts.append(f'<line x1="{x+2}" y1="{bly}" x2="{x+cw-2}" y2="{bly}" stroke="black" stroke-width="1"/>')
            else:
                parts.append(f'<text x="{x+cw/2}" y="{by}" text-anchor="middle" font-family="Courier New" font-size="16">{escape(ch)}</text>')
            oi+=1
    parts.append("</svg>"); return "\n".join(parts)
