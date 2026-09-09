"""Seed example data across all DB-backed sections of SelfPublisherForge.

Populates the modules that are real-database-backed and creatable via JSON so the
dashboard shows realistic example data on a fresh local (SQLite) install.

Sections that already return built-in mock/stub data (e.g. Books list, Market
Research, Seasonal trends) need no seeding. Sections blocked locally
(Knowledge Vault = Postgres-only, Billing = Stripe, Storage = S3, some Admin/Org
views = code bug) are skipped and reported.

Each POST is fault-tolerant: a failure is recorded and reported, never fatal.

Usage (backend server must be running on :8000):
    backend/.venv/Scripts/python.exe backend/scripts/seed_all.py \
        --email ivannextlevel@yahoo.com --password 'DevPass123!'
"""

from __future__ import annotations

import argparse
import base64
import sys
from datetime import UTC, date, datetime, timedelta

import httpx

BASE = "http://127.0.0.1:8000/api/v1"
results: list[tuple[str, str, str]] = []  # (section, status, detail)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    args = ap.parse_args()

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        r = client.post(
            f"{BASE}/auth/login",
            json={"email": args.email, "password": args.password},
        )
        r.raise_for_status()
        token = r.json()["tokens"]["access_token"]
        H = {"Authorization": f"Bearer {token}"}

        def post(section: str, path: str, payload, ok=(200, 201)):
            try:
                resp = client.post(f"{BASE}{path}", headers=H, json=payload)
                if resp.status_code in ok:
                    results.append((section, "OK", f"{resp.status_code}"))
                    return resp.json()
                results.append((section, "FAIL", f"{resp.status_code} {resp.text[:90]}"))
            except Exception as exc:
                results.append((section, "ERR", str(exc)[:90]))
            return None

        def get(path: str):
            try:
                return client.get(f"{BASE}{path}", headers=H).json()
            except Exception:
                return None

        def project_items(resp):
            if isinstance(resp, list):
                return resp
            if isinstance(resp, dict):
                return resp.get("projects") or resp.get("items") or []
            return []

        # ---- Projects / Books (parent entities) ------------------------------
        items = project_items(get("/projects/"))
        have = {p.get("title") for p in items}
        books = [
            {"title": "The Last Lighthouse", "book_type": "fiction", "genre": "Literary Fiction",
             "subgenre": "Mystery", "target_word_count": 80000, "keywords": ["lighthouse", "mystery", "sea"]},
            {"title": "Cozy Cabin Murders", "book_type": "fiction", "genre": "Cozy Mystery",
             "subgenre": "Whodunit", "target_word_count": 70000, "keywords": ["cozy", "mystery", "cabin"]},
            {"title": "Six-Figure Self-Publishing", "book_type": "nonfiction", "genre": "Business",
             "subgenre": "Marketing", "target_word_count": 45000, "keywords": ["kdp", "marketing", "indie"]},
            {"title": "Starlight Academy", "book_type": "fiction", "genre": "YA Fantasy",
             "subgenre": "Magic School", "target_word_count": 90000, "keywords": ["fantasy", "ya", "magic"]},
        ]
        project_ids: list[str] = []
        for b in books:
            payload = {"project_type": "book", "language": "en", "content_rating": "general",
                       "marketplace": "kdp", "target_audience": "Adult", **b}
            if b["title"] in have:
                results.append(("projects", "SKIP", f"exists: {b['title']}"))
            else:
                res = post("projects", "/projects/", payload)
                if res and res.get("id"):
                    project_ids.append(res["id"])
        # gather all project ids (incl. pre-existing) for child modules
        allitems = project_items(get("/projects/"))
        project_ids = [p["id"] for p in allitems] or project_ids
        book_id = project_ids[0] if project_ids else None
        titles = [p["title"] for p in allitems] or [b["title"] for b in books]

        # ---- Competitor Finder ----------------------------------------------
        for asin in ["B08N5WRWNW", "B07PXGQC1Q", "B09TESTAB1"]:
            post("competitors", "/market/competitors/track", {"asin": asin, "marketplace": "US"})

        # ---- Publishing accounts --------------------------------------------
        for plat, name in [("kdp", "My KDP Account"), ("ingram_spark", "IngramSpark Print"),
                            ("draft2digital", "D2D Wide")]:
            post("publishing", "/publishing/accounts",
                 {"platform": plat, "account_name": name, "account_email": args.email,
                  "credentials": {"key": "demo-key"}})

        # ---- Production Pipelines -------------------------------------------
        if book_id:
            pl = post("pipelines", "/pipelines",
                      {"name": "The Last Lighthouse — Launch Plan",
                       "description": "Manuscript to market production workflow",
                       "book_id": book_id,
                       "deadline": (datetime.now(UTC) + timedelta(days=75)).isoformat()})
            if pl and pl.get("id"):
                for i, t in enumerate(["Final copyedit", "Cover finalization", "EPUB + PDF export",
                                       "KDP metadata upload"]):
                    post("pipelines", f"/pipelines/{pl['id']}/tasks",
                         {"title": t, "order": i, "status": "pending"})

        # ---- Cover Design ----------------------------------------------------
        for t, g, mood in [("The Last Lighthouse", "literary-fiction", "atmospheric, melancholic"),
                           ("Cozy Cabin Murders", "mystery", "cozy, intriguing"),
                           ("Starlight Academy", "fantasy", "magical, epic")]:
            post("covers", "/covers/generate",
                 {"title": t, "author_name": "Ivan Carter", "genre": g,
                  "platform": "amazon-kdp", "mood": mood})

        # ---- Product Page Lab (blurb A/B test) ------------------------------
        if book_id:
            post("product-page", "/product-page/blurb/ab-test",
                 {"book_id": book_id, "name": "Lighthouse Blurb Test",
                  "variant_a": "A gripping tale of loss and redemption set on a remote island.",
                  "variant_b": "When the lighthouse goes dark, one keeper must face her past."})

        # ---- Marketing (email sequence) -------------------------------------
        post("marketing", "/marketing/email-sequences",
             {"name": "Pre-Launch Warmup", "description": "Build buzz before release day",
              "trigger_event": "signup",
              "emails": [
                  {"template_type": "launch_announcement", "subject": "My new book is coming!",
                   "body_html": "<p>Big news — release day is near.</p>", "body_text": "Big news.",
                   "delay_days": 0, "order_index": 0},
                  {"template_type": "follow_up", "subject": "3 days to launch",
                   "body_html": "<p>Almost here!</p>", "body_text": "Almost here!",
                   "delay_days": 4, "order_index": 1},
              ]})

        # ---- Advertising (Facebook campaign; amazon path 500s without creds) -
        for name, ctype in [("Holiday Promo — Facebook", "facebook_feed"),
                            ("Series Awareness — Stories", "facebook_stories")]:
            post("ads", "/ads/campaigns",
                 {"name": name, "platform": "facebook", "campaign_type": ctype,
                  "daily_budget": 25.0, "total_budget": 500.0, "bid_strategy": "manual",
                  "targeting_keywords": ["mystery novel", "thriller", "cozy mystery"]})

        # ---- Pricing Automation (rules) -------------------------------------
        for name, strat, fmt, tgt in [("Competitive eBook Pricing", "competitive_match", "ebook", 4.99),
                                      ("Premium Paperback", "value_based", "paperback", 14.99)]:
            post("pricing", "/pricing/rules",
                 {"name": name, "description": "Auto pricing strategy", "strategy": strat,
                  "book_format": fmt, "min_price": 2.99, "max_price": 19.99,
                  "target_price": tgt, "is_auto_apply": False})

        # ---- Specialty book types -------------------------------------------
        post("specialty:childrens", "/specialty/childrens-books",
             {"title": "Luna and the Midnight Garden", "author": "Ivan Carter", "age_range": "picture",
              "page_count": 24, "trim_size": "8.5x8.5", "illustration_style": "watercolor",
              "color_palette": "soft-pastel", "story_mode": "prose", "is_bilingual": False,
              "fear_intensity": "none"})
        post("specialty:coloring", "/specialty/coloring-books",
             {"title": "Calm Forest Coloring", "audience": "adults", "page_count": 30,
              "trim_size": "8.5x11", "line_style": "clean-outlines", "line_weight": 2.0,
              "complexity": 0.5, "stroke_uniformity": True, "single_sided": True,
              "theme_description": "Woodland animals and botanicals"})
        post("specialty:puzzle", "/specialty/puzzle-books",
             {"title": "Big Book of Word Search", "audience": "adults",
              "puzzle_config": [{"puzzle_type": "word-search", "quantity": 20,
                                 "difficulty": "medium", "grid_size": "15x15"}],
              "difficulty_mode": "progressive", "trim_size": "8.5x11", "word_difficulty": "standard",
              "clue_style": "standard", "answer_key_position": "back-of-book",
              "layout_mode": "one-per-page"})
        post("specialty:comic", "/specialty/comic-books",
             {"title": "Nova Patrol #1", "author": "Ivan Carter", "artist": "Ivan Carter",
              "format": "graphic_novel", "art_style": "american_classic", "color_mode": "full_color",
              "ink_style": "clean", "pacing": "balanced", "genre": "sci-fi", "page_count": 24,
              "trim_size": "6.625x10.25", "target_audience": "all_ages"})
        post("specialty:cookbook", "/specialty/cookbook-books",
             {"title": "Weeknight Comfort Kitchen", "author": "Ivan Carter", "cookbook_type": "general",
              "cuisine": "American", "trim_size": "8x10", "page_count": 100,
              "include_nutrition": True, "include_index": True, "dietary_tags": ["vegetarian"]})
        post("specialty:series", "/specialty/series",
             {"name": "Calm Forest Collection", "book_type": "coloring",
              "naming_format": "{series_name} Vol. {volume} - {theme}"})

        # ---- Audiobook Studio (needs a real book_id; may fail) --------------
        if book_id:
            post("audiobooks", "/audiobooks/projects/",
                 {"book_id": book_id, "title": "The Last Lighthouse (Audiobook)",
                  "output_format": "mp3", "sample_rate": 44100, "bit_rate": 192,
                  "channels": 1, "target_platform": "acx"})

        # ---- Dictation -------------------------------------------------------
        post("dictation", "/dictation/sessions", {"title": "Chapter 1 dictation", "language": "en"})

        # ---- Analytics: royalty import (CSV) --------------------------------
        rows = ["Title,Marketplace,Units Sold,Net Units Sold,Avg List Price,Royalty,Currency,Royalty Date"]
        base = date.today().replace(day=1)
        for m in range(6):  # six months of history
            d = (base - timedelta(days=30 * m)).replace(day=1)
            for t, units, price in [(titles[0] if titles else "The Last Lighthouse", 120 - m * 8, 4.99),
                                    ("Six-Figure Self-Publishing", 60 - m * 4, 9.99)]:
                roy = round(units * price * 0.7, 2)
                rows.append(f"{t},Amazon.com,{units},{units},{price},{roy},USD,{d.isoformat()}")
        csv_b64 = base64.b64encode("\n".join(rows).encode()).decode()
        post("analytics:royalties", "/analytics/royalties/import",
             {"platform": "kdp", "file_name": "kdp_royalties.csv", "file_content": csv_b64})

        # ---- Analytics: events + report -------------------------------------
        for et in ["book_view", "sample_download", "purchase"]:
            post("analytics:events", "/analytics/events",
                 {"event_type": et, "event_source": "system", "data": {"book": titles[0] if titles else "x"}})
        # NOTE: /analytics/reports/generate is skipped — it has a backend bug
        # (MissingGreenlet: lazy attribute load after commit) and hangs/500s.

        # ---- AI Agents: tasks + workflow ------------------------------------
        agents = get("/agents") or {}
        alist = agents.get("items") if isinstance(agents, dict) else (agents if isinstance(agents, list) else [])
        agent_id = next((a.get("id") for a in (alist or []) if a.get("id")), None)
        if agent_id:
            post("agents:tasks", "/agents/tasks",
                 {"agent_id": agent_id, "title": "Research cozy mystery market 2026",
                  "description": "Analyze trends and comps", "priority": "medium",
                  "input_data": {"genre": "cozy mystery"}})
            post("agents:workflows", "/agents/workflows",
                 {"name": "Launch Prep", "description": "Multi-step pre-launch",
                  "steps": [{"agent_id": agent_id, "title": "Keyword research", "input_data": {}}]})
        else:
            results.append(("agents", "SKIP", "no agent_id found in /agents"))

        # ---- Settings: API key ----------------------------------------------
        post("settings:api-keys", "/settings/api-keys",
             {"name": "Local Dev Key", "permissions": ["read", "write"]})

    # ---- Report -------------------------------------------------------------
    print("\n================ SEED SUMMARY ================")
    width = max(len(s) for s, _, _ in results) if results else 10
    ok = sum(1 for _, st, _ in results if st in ("OK", "SKIP"))
    for section, st, detail in results:
        mark = {"OK": "+", "SKIP": "=", "FAIL": "!", "ERR": "x"}.get(st, "?")
        print(f" {mark} {section.ljust(width)}  {st:4s}  {detail}")
    print("=" * 46)
    print(f" {ok}/{len(results)} calls succeeded or skipped-existing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
