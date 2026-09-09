"""Seed example Style Profiles via the running API.

Creates a handful of vivid, distinct writing-voice profiles so the
/style-profiles page has real data to show. Idempotent: profiles whose
name already exists are skipped.

Usage (with the backend server running on :8000):
    backend/.venv/Scripts/python.exe backend/scripts/seed_style_profiles.py \
        --email ivannextlevel@yahoo.com --password 'DevPass123!'
"""

from __future__ import annotations

import argparse
import sys

import httpx

BASE = "http://127.0.0.1:8000/api/v1"

# Each profile gets multiple, substantial sample passages so the local NLP
# pipeline (syntax / rhythm / vocabulary / tone analyzers) produces a
# meaningful fingerprint and a non-trivial confidence score.
PROFILES = [
    {
        "name": "Hardboiled Noir",
        "genre": "Crime / Detective",
        "description": "Terse, punchy first-person detective voice. Short sentences, " "wry cynicism, sensory grit.",
        "sample_texts": [
            "The rain came down like it had a grudge. I lit a cigarette and watched the "
            "gutter swallow the city's sins. She walked in at half past nothing, heels "
            "loud as gunfire, eyes that had seen the wrong end of too many promises. "
            "Trouble. I could smell it under the cheap perfume. I poured two fingers of "
            "rye and didn't offer her any. People who bring trouble can buy their own drinks.",
            "He said he was clean. They always say that. Clean as a church floor on Sunday "
            "and twice as quiet about what gets swept under it. I leaned back. The chair "
            "complained. Somewhere down the hall a phone rang and nobody answered, because "
            "in this town nobody ever answers the thing you actually want them to. I let it "
            "ring. Some questions are better left bleeding out in the dark.",
            "The body was in the alley, folded up neat like a letter nobody wanted to read. "
            "Cops everywhere, flashbulbs popping, a detective named Hollis chewing a "
            "toothpick like it owed him money. I knew the dead man. We'd had drinks once. "
            "He laughed too easy and trusted too quick, and now he was learning the only "
            "lesson this city ever really teaches.",
        ],
    },
    {
        "name": "Whimsical Children's",
        "genre": "Children's Picture Book",
        "description": "Playful, bouncy, rhythmic voice for ages 4-8. Simple words, gentle "
        "repetition, warm and silly.",
        "sample_texts": [
            "Pip the penguin had a problem. A big, wobbly, tippy-toe problem! His scarf was "
            "too long and his feet were too small, and every time he tried to slide he went "
            "splat in the snow. But Pip did not cry. Oh no, not Pip! He wiggled and he "
            "giggled and he tried, tried again. Because that is what brave little penguins do.",
            "Up on the hill lived a fuzzy orange cat named Marmalade, who loved three things "
            "best of all: warm milk, soft pillows, and chasing butterflies that were much, "
            "much too fast. One sunny morning a butterfly with sparkly blue wings fluttered "
            "right past his nose. 'Hello!' said Marmalade. 'Will you be my friend?' And off "
            "they went, over the daisies and under the apple tree, laughing all the way.",
            "It was bedtime in the Bumble house, but Baby Bumble was not sleepy. Not even a "
            "little. 'One more story!' he buzzed. 'One more hug! One more drink of water!' "
            "Mama Bumble smiled her softest smile. 'All right, little one. One more. But "
            "then it is time for dreams.' And do you know what? Baby Bumble was snoring "
            "before the very last word.",
        ],
    },
    {
        "name": "Lyrical Literary",
        "genre": "Literary Fiction",
        "description": "Long, flowing sentences, rich and precise vocabulary, contemplative "
        "interiority and layered imagery.",
        "sample_texts": [
            "In the slow gold of late afternoon, when the light came sideways through the "
            "orchard and lay across the grass like something spilled and forgiven, she "
            "understood for the first time that memory was not a room one could return to "
            "but a country one had emigrated from, its borders closed, its language slowly "
            "forgetting itself on the tongue. She had spent years believing she could go "
            "back. She could not. One never could.",
            "The house held its silences the way old people hold their griefs, carefully, "
            "with a kind of practiced dignity that fools no one. Each room had learned a "
            "different absence. The kitchen remembered her mother's hands; the stairwell "
            "kept the particular weight of a child descending; and the study, dust-soft and "
            "amber, still seemed to expect a man who had been dead for nineteen autumns and "
            "who, even now, she half-listened for.",
            "What is a life, he wondered, but a sequence of departures we mistake for "
            "arrivals? He watched the train uncouple itself from the platform with that "
            "tender, mechanical reluctance, and felt the old vertigo, the sense that the "
            "world was always leaving and he was always the one left standing, hat in hand, "
            "composing farewells to people who had already turned the corner of their own "
            "becoming.",
        ],
    },
    {
        "name": "Fast Techno-Thriller",
        "genre": "Thriller / Suspense",
        "description": "Propulsive present-tense action voice. Clipped sentences, technical "
        "detail, escalating tension.",
        "sample_texts": [
            "Forty seconds. The countdown burns red on her retina display. Reyes is in the "
            "ventilation shaft, climbing, the maintenance schematic ghosting across her left "
            "eye. Below, two guards sweep the server floor with thermal scopes. She freezes. "
            "Breathes through her nose. Thirty-one seconds. The encryption key is on the "
            "fourth rack from the door and the door is the only thing between her and a "
            "kill order with her name typed neatly at the top.",
            "The drone wakes. She hears it before she sees it, that insect whine spinning up "
            "behind the parking structure, and she runs. Concrete, then gravel, then the "
            "hard slap of the river path. Rotors closing. Twelve meters. Eight. She cuts "
            "left through the market stalls, scattering crates, and the drone overcorrects, "
            "clips an awning, spirals. Not dead. Just angry. She does not slow down.",
            "He plugs the drive in and the terminal floods with green. Forty thousand "
            "records, every one a name, every name a person who trusted the wrong "
            "institution. The transfer bar crawls. Sixty percent. A footstep in the "
            "corridor. He kills the monitor, draws the sidearm, counts his own heartbeats "
            "like rounds in a magazine. The handle turns. Seventy percent. Come on. Come on.",
        ],
    },
]


# Confidence in the app is word_count / 50_000 (capped at 1.0). The handwritten
# passages above are only ~600 words/profile, which renders as 0% confidence.
# To make the demo cards look healthy we repeat each passage until the profile
# reaches roughly TARGET_WORDS. Repetition preserves the stylistic ratios the
# analyzers measure (sentence length, rhythm, tone), so the fingerprint stays
# representative even though lexical diversity is understated.
TARGET_WORDS = 25_000  # -> ~50% confidence


def _expand(sample_texts: list[str]) -> list[str]:
    per_sample_target = TARGET_WORDS // len(sample_texts)
    expanded = []
    for passage in sample_texts:
        words = len(passage.split())
        reps = max(1, per_sample_target // max(1, words))
        expanded.append("\n\n".join([passage] * reps))
    return expanded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--password", required=True)
    ap.add_argument(
        "--replace",
        action="store_true",
        help="Delete existing profiles with the same name before recreating them.",
    )
    args = ap.parse_args()

    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            f"{BASE}/auth/login",
            json={"email": args.email, "password": args.password},
        )
        r.raise_for_status()
        token = r.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        existing = client.get(f"{BASE}/style-profiles", headers=headers).json()
        existing_by_name = {p["name"]: p["id"] for p in existing.get("items", [])}

        created = 0
        for p in PROFILES:
            if p["name"] in existing_by_name:
                if args.replace:
                    client.delete(
                        f"{BASE}/style-profiles/{existing_by_name[p['name']]}",
                        headers=headers,
                    )
                    print(f"~ replacing: {p['name']}")
                else:
                    print(f"= skip (exists, use --replace to refresh): {p['name']}")
                    continue
            payload = {**p, "sample_texts": _expand(p["sample_texts"])}
            resp = client.post(f"{BASE}/style-profiles", headers=headers, json=payload)
            if resp.status_code in (200, 201):
                body = resp.json()
                print(
                    f"+ created: {body['name']:24s} "
                    f"status={body['status']:9s} "
                    f"words={body['word_count']:5d} "
                    f"confidence={body['confidence']:.2f}"
                )
                created += 1
            else:
                print(f"! failed: {p['name']} -> {resp.status_code} {resp.text[:200]}")

        total = client.get(f"{BASE}/style-profiles", headers=headers).json().get("total", 0)
        print(f"\nDone. Created {created} new profile(s). Total now: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
