"""Word Scramble generator."""
from __future__ import annotations
import hashlib, json, random

_COMMON_WORDS = None

def _load_dictionary():
    global _COMMON_WORDS
    if _COMMON_WORDS is not None: return _COMMON_WORDS
    _COMMON_WORDS = set()
    try:
        with open("/usr/share/dict/words") as f:
            for line in f:
                w = line.strip().upper()
                if w.isalpha() and len(w) >= 2: _COMMON_WORDS.add(w)
    except FileNotFoundError: pass
    _COMMON_WORDS.update({
        "THE","AND","FOR","ARE","BUT","NOT","YOU","ALL","ANY","CAN","HAD","HER","WAS",
        "ONE","OUR","OUT","DAY","GET","HAS","HIM","HIS","HOW","ITS","MAY","NEW","NOW",
        "OLD","SEE","WAY","WHO","DID","OIL","SIT","TOP","RED","RUN","USE","SAY","SHE",
        "TWO","EAT","FAR","LET","PUT","TOO","ALSO","BACK","BEEN","CALL","COME","EACH",
        "FIND","FROM","GIVE","GOOD","HAVE","HELP","HERE","HIGH","HOME","JUST","KNOW",
        "LAST","LIKE","LINE","LIVE","LONG","LOOK","MADE","MAKE","MORE","MOST","MUCH",
        "MUST","NAME","OVER","PART","SAID","SAME","SOME","SUCH","TAKE","TELL","THAN",
        "THAT","THEM","THEN","THIS","TIME","VERY","WHEN","WILL","WITH","WORD","WORK",
        "YEAR","ABOUT","AFTER","BEING","COULD","EVERY","FIRST","GREAT","LARGE","LATER",
        "NEVER","OTHER","PLACE","POINT","RIGHT","SMALL","SOUND","SPELL","STILL","STUDY",
        "THEIR","THERE","THESE","THING","THINK","THREE","WATER","WHERE","WHICH","WORLD",
        "WOULD","WRITE","HEART","STAR","LOVE","CARE","POTS","STOP","TOPS","SPOT","POST",
        "OPTS","PALE","LEAP","PLEA","PEAL","LAME","MALE","MEAL","VILE","LIVE","EVIL",
        "VEIL","RATS","TSAR","ARTS","TARS","MEAT","TEAM","MATE","TAME","META","LATE",
        "TALE","PEAR","REAP","PARE","RAPE","ACRE","RACE","LACE","DEAL","LEAD","DALE",
    })
    return _COMMON_WORDS

def _is_real_word(word): return word.upper() in _load_dictionary()

def _scramble_word(word, rng, max_attempts=100):
    letters = list(word.upper())
    if len(set(letters)) == 1: return None
    for _ in range(max_attempts):
        s = letters[:]; rng.shuffle(s); r = "".join(s)
        if r != word.upper() and not _is_real_word(r): return r
    for _ in range(max_attempts):
        s = letters[:]; rng.shuffle(s); r = "".join(s)
        if r != word.upper(): return r
    return None

def generate_word_scramble(words, difficulty="medium", category=None, seed=None):
    """Generate word scramble puzzles."""
    rng = random.Random(seed)
    clean = [w.strip().upper() for w in words if w.strip().isalpha() and len(w.strip()) >= 2]
    if not clean: raise ValueError("No valid words provided after sanitization.")
    seen = set(); unique = []
    for w in clean:
        if w not in seen: seen.add(w); unique.append(w)
    scrambles = []
    for word in unique:
        scrambled = _scramble_word(word, rng)
        if scrambled is None: continue
        hint = None
        if difficulty == "easy":
            hint = f"Category: {category}" if category else f"Starts with '{word[0]}' and ends with '{word[-1]}'"
        elif difficulty == "medium": hint = f"First letter: {word[0]}"
        entry = {"original": word, "scrambled": scrambled}
        if hint: entry["hint"] = hint
        scrambles.append(entry)
    if not scrambles: raise ValueError("Could not scramble any of the provided words.")
    avg = sum(len(w) for w in unique) / len(unique) if unique else 0
    base = {"easy":10,"medium":40,"hard":70}.get(difficulty, 40)
    score = max(0, min(100, int(base + min(avg/12,1)*30)))
    ch = hashlib.sha256(json.dumps({"scrambles":[(s["original"],s["scrambled"]) for s in scrambles]},sort_keys=True).encode()).hexdigest()
    return {"scrambles": scrambles, "difficulty_score": score, "content_hash": ch}
