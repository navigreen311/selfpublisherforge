"""
Shared utilities for puzzle generation algorithms.

Provides SVG rendering helpers, content hashing, and a common English word set
used by Word Scramble verification.
"""

import hashlib
import json


def generate_content_hash(data: dict) -> str:
    """Generate a SHA-256 hash from puzzle data for duplicate detection."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# SVG rendering helpers
# ---------------------------------------------------------------------------

def svg_header(width: int, height: int) -> str:
    """Return the opening <svg> tag with the given dimensions."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
    )


def svg_footer() -> str:
    """Return the closing </svg> tag."""
    return "</svg>\n"


def svg_grid(rows: int, cols: int, cell_size: int,
             offset_x: int = 0, offset_y: int = 0) -> str:
    """
    Render a grid of *rows* x *cols* cells as SVG <line> elements.

    Returns horizontal and vertical lines that form the grid.
    """
    lines: list[str] = []
    total_w = cols * cell_size
    total_h = rows * cell_size

    # Horizontal lines
    for r in range(rows + 1):
        y = offset_y + r * cell_size
        lines.append(
            f'  <line x1="{offset_x}" y1="{y}" '
            f'x2="{offset_x + total_w}" y2="{y}" '
            f'stroke="black" stroke-width="1"/>'
        )

    # Vertical lines
    for c in range(cols + 1):
        x = offset_x + c * cell_size
        lines.append(
            f'  <line x1="{x}" y1="{offset_y}" '
            f'x2="{x}" y2="{offset_y + total_h}" '
            f'stroke="black" stroke-width="1"/>'
        )

    return "\n".join(lines) + "\n"


def svg_text(x: int, y: int, text: str, font_size: int = 16,
             anchor: str = "middle", font_family: str = "monospace",
             font_weight: str = "normal", fill: str = "black") -> str:
    """Render a single <text> element."""
    return (
        f'  <text x="{x}" y="{y}" font-size="{font_size}" '
        f'font-family="{font_family}" font-weight="{font_weight}" '
        f'text-anchor="{anchor}" fill="{fill}" '
        f'dominant-baseline="central">{text}</text>\n'
    )


def svg_rect(x: int, y: int, w: int, h: int,
             fill: str = "none", stroke: str = "black",
             stroke_width: int = 1) -> str:
    """Render an SVG <rect>."""
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>\n'
    )


# ---------------------------------------------------------------------------
# Common English words (~1000) for Word Scramble verification
# ---------------------------------------------------------------------------

COMMON_WORDS: set[str] = {
    "a", "able", "about", "above", "accept", "across", "act", "add", "afraid",
    "after", "again", "age", "ago", "agree", "air", "all", "allow", "almost",
    "alone", "along", "already", "also", "always", "am", "among", "an", "and",
    "anger", "animal", "answer", "any", "appear", "apple", "area", "arm",
    "army", "around", "arrive", "art", "as", "ask", "at", "atom", "attach",
    "away", "baby", "back", "bad", "ball", "band", "bank", "bar", "base",
    "basic", "bat", "be", "bear", "beat", "beauty", "became", "because",
    "become", "bed", "been", "before", "began", "begin", "behind", "believe",
    "bell", "below", "beside", "best", "better", "between", "big", "bird",
    "bit", "black", "block", "blood", "blow", "blue", "board", "boat", "body",
    "bone", "book", "born", "both", "bottom", "box", "boy", "brain", "branch",
    "bread", "break", "bridge", "brief", "bright", "bring", "broad", "broke",
    "brother", "brought", "brown", "build", "burn", "bus", "busy", "but",
    "buy", "by", "call", "came", "camp", "can", "capital", "captain", "car",
    "card", "care", "carry", "case", "cat", "catch", "cause", "cell", "cent",
    "center", "certain", "chair", "chance", "change", "chapter", "charge",
    "chart", "check", "chief", "child", "children", "choose", "church",
    "circle", "city", "claim", "class", "clean", "clear", "climb", "clock",
    "close", "cloud", "coast", "coat", "cold", "collect", "colony", "color",
    "column", "come", "common", "company", "compare", "complete", "condition",
    "connect", "consider", "contain", "continent", "continue", "control",
    "cook", "cool", "copy", "corn", "corner", "correct", "cost", "cotton",
    "could", "count", "country", "course", "cover", "create", "cross", "crowd",
    "cry", "cup", "current", "cut", "dad", "dance", "danger", "dark",
    "daughter", "day", "dead", "deal", "dear", "death", "decide", "decimal",
    "deep", "degree", "depend", "describe", "desert", "design", "develop",
    "did", "die", "differ", "difficult", "direct", "discuss", "distant",
    "divide", "do", "doctor", "does", "dog", "dollar", "done", "door",
    "double", "down", "draw", "dream", "dress", "drink", "drive", "drop",
    "dry", "during", "dust", "duty", "each", "ear", "early", "earth", "ease",
    "east", "eat", "edge", "effect", "egg", "eight", "either", "electric",
    "element", "else", "end", "enemy", "energy", "engine", "enough", "enter",
    "equal", "escape", "even", "evening", "event", "ever", "every", "exact",
    "example", "except", "excite", "exercise", "expect", "experience",
    "experiment", "explain", "eye", "face", "fact", "fair", "fall", "family",
    "famous", "far", "farm", "fast", "fat", "father", "favor", "fear", "feed",
    "feel", "feet", "fell", "felt", "few", "field", "fig", "fight", "fill",
    "final", "find", "fine", "finger", "finish", "fire", "first", "fish",
    "fit", "five", "flat", "floor", "flow", "flower", "fly", "follow", "food",
    "foot", "for", "force", "forest", "form", "forward", "found", "four",
    "free", "fresh", "friend", "from", "front", "fruit", "full", "fun",
    "game", "garden", "gas", "gather", "gave", "general", "gentle", "get",
    "girl", "give", "glad", "glass", "go", "god", "gold", "gone", "good",
    "got", "govern", "grand", "grass", "gray", "great", "green", "grew",
    "ground", "group", "grow", "guess", "guide", "gun", "had", "hair", "half",
    "hand", "happen", "happy", "hard", "has", "hat", "have", "he", "head",
    "hear", "heart", "heat", "heavy", "held", "help", "her", "here", "high",
    "hill", "him", "his", "history", "hit", "hold", "hole", "home", "hope",
    "horse", "hot", "hour", "house", "how", "huge", "human", "hundred",
    "hunt", "hurry", "hurt", "husband", "ice", "idea", "if", "imagine", "in",
    "inch", "include", "increase", "indicate", "industry", "insect", "inside",
    "instead", "instrument", "interest", "into", "iron", "is", "island", "it",
    "job", "join", "joy", "jump", "just", "keep", "kept", "key", "kill",
    "kind", "king", "knew", "know", "labor", "lady", "lake", "land",
    "language", "large", "last", "late", "laugh", "law", "lay", "lead",
    "learn", "least", "leave", "led", "left", "leg", "length", "less", "let",
    "letter", "level", "lie", "life", "lift", "light", "like", "line", "list",
    "listen", "little", "live", "long", "look", "lost", "lot", "loud", "love",
    "low", "machine", "made", "main", "major", "make", "man", "many", "map",
    "mark", "market", "mass", "master", "match", "material", "matter", "may",
    "me", "mean", "measure", "meat", "meet", "melody", "men", "metal",
    "method", "middle", "might", "mile", "milk", "million", "mind", "mine",
    "minute", "miss", "mix", "modern", "molecule", "moment", "money", "month",
    "moon", "more", "morning", "most", "mother", "motion", "mount", "mountain",
    "mouth", "move", "much", "multiply", "music", "must", "my", "name",
    "nation", "natural", "nature", "near", "necessary", "neck", "need", "new",
    "next", "night", "nine", "no", "noise", "none", "nor", "north", "nose",
    "note", "nothing", "notice", "noun", "now", "number", "numeral", "object",
    "observe", "occur", "ocean", "of", "off", "offer", "office", "often",
    "oh", "oil", "old", "on", "once", "one", "only", "open", "operate",
    "opinion", "opposite", "or", "order", "organ", "original", "other", "our",
    "out", "over", "own", "oxygen", "page", "paint", "pair", "paper",
    "paragraph", "parent", "part", "particular", "party", "pass", "past",
    "path", "pattern", "pay", "people", "perhaps", "period", "person",
    "phrase", "pick", "picture", "piece", "place", "plain", "plan", "plane",
    "planet", "plant", "play", "please", "plural", "poem", "point", "poor",
    "populate", "position", "possible", "post", "pound", "power", "practice",
    "prepare", "present", "president", "press", "pretty", "print", "probable",
    "problem", "process", "produce", "product", "program", "proper", "property",
    "protect", "prove", "provide", "pull", "push", "put", "quarter", "queen",
    "question", "quick", "quiet", "quite", "quotient", "race", "radio",
    "rain", "raise", "ran", "range", "rather", "reach", "read", "ready",
    "real", "reason", "receive", "record", "red", "region", "remember",
    "repeat", "reply", "represent", "require", "rest", "result", "rich",
    "ride", "right", "ring", "rise", "river", "road", "rock", "roll", "room",
    "root", "rope", "rose", "round", "row", "rub", "rule", "run", "safe",
    "said", "sail", "salt", "same", "sand", "sat", "save", "saw", "say",
    "scale", "school", "science", "score", "sea", "search", "season", "seat",
    "second", "section", "see", "seed", "seem", "segment", "select", "self",
    "sell", "send", "sense", "sentence", "separate", "serve", "set", "settle",
    "seven", "several", "shall", "shape", "share", "sharp", "she", "shell",
    "shine", "ship", "shoe", "shop", "shore", "short", "should", "shoulder",
    "shout", "show", "side", "sight", "sign", "silent", "silver", "similar",
    "simple", "since", "sing", "single", "sister", "sit", "six", "size",
    "skill", "skin", "sleep", "slip", "slow", "small", "smell", "smile",
    "snow", "so", "soft", "soil", "soldier", "solution", "some", "son",
    "song", "soon", "sort", "sound", "south", "space", "speak", "special",
    "speed", "spell", "spend", "spoke", "spot", "spread", "spring", "square",
    "stage", "stand", "star", "start", "state", "station", "stay", "steam",
    "steel", "step", "stick", "still", "stone", "stood", "stop", "store",
    "story", "straight", "strange", "stream", "street", "stretch", "string",
    "strong", "student", "study", "subject", "substance", "subtract",
    "success", "such", "sudden", "suffix", "sugar", "suggest", "suit",
    "summer", "sun", "supply", "support", "sure", "surface", "surprise",
    "swim", "symbol", "system", "table", "tail", "take", "talk", "tall",
    "teach", "team", "teeth", "tell", "ten", "tend", "term", "test", "than",
    "thank", "that", "the", "their", "them", "then", "there", "these", "they",
    "thick", "thin", "thing", "think", "third", "this", "those", "though",
    "thought", "thousand", "three", "through", "throw", "tie", "time", "tiny",
    "tire", "to", "together", "told", "tone", "too", "took", "tool", "top",
    "total", "touch", "toward", "town", "track", "trade", "train", "travel",
    "tree", "triangle", "trip", "trouble", "truck", "true", "trust", "try",
    "tube", "turn", "twenty", "two", "type", "under", "unit", "until", "up",
    "upon", "us", "use", "usual", "valley", "value", "vary", "verb", "very",
    "view", "village", "visit", "voice", "vowel", "wait", "walk", "wall",
    "want", "war", "warm", "was", "wash", "watch", "water", "wave", "way",
    "we", "wear", "weather", "week", "weight", "well", "went", "were", "west",
    "western", "what", "wheel", "when", "where", "whether", "which", "while",
    "white", "who", "whole", "whose", "why", "wide", "wife", "wild", "will",
    "win", "wind", "window", "wing", "winter", "wire", "wish", "with",
    "woman", "women", "won", "wonder", "wood", "word", "work", "world",
    "would", "write", "written", "wrong", "wrote", "yard", "year", "yellow",
    "yes", "yet", "you", "young", "your",
    # Additional words to reach ~1000
    "account", "achieve", "address", "admit", "adult",
    "advance", "advice", "affair", "afford", "agent", "ahead", "alarm",
    "album", "alert", "alive", "amount", "amuse", "angle", "angry", "annual",
    "apart", "appeal", "apply", "appoint", "approach", "approve", "argue",
    "arrange", "arrest", "aside", "asset", "assume", "attack", "attempt",
    "attend", "attract", "autumn", "average", "avoid", "award", "aware",
    "awful", "background", "balance", "barrier", "basket", "battle", "beach",
    "bedroom", "behalf", "belong", "bench", "benefit", "bind",
    "birthday", "blame", "blank", "blast", "blend", "blind", "bomb", "bond", "boot", "border", "bother", "bottle", "bound",
    "bowl", "brand", "brave", "breath", "breed", "brick", "brilliant",
    "brush", "budget", "burden", "burst", "button",
    "cabin", "cable", "cake", "calculate", "calm", "camera", "campaign",
    "capable", "capture", "carbon", "career", "careful", "carpet", "cash",
    "cast", "casual", "cattle", "caught", "ceiling", "celebrate", "chain",
    "chamber", "champion", "channel", "charity", "cheap", "cheese",
    "chest", "chicken", "chip", "citizen", "civil",
    "client", "climate", "clinic", "cloth", "clothes",
    "coach", "coalition", "code", "coffee", "collapse", "colleague",
    "combat", "combine", "comfort", "command",
    "commission", "commit", "committee", "communicate", "community",
    "compete", "complain", "complex", "component", "compose",
    "computer", "concentrate", "concept", "concern", "conclude", "concrete",
    "conduct", "conference", "confidence", "confirm", "conflict", "confuse",
    "congress", "conscious", "consequence", "conservative",
    "consist", "constant", "construct", "consult", "consumer",
    "contact", "content", "contest", "context", "contract",
    "contrast", "contribute", "convention", "conversation", "convert",
    "convince", "cooperate", "core", "corporate", "council",
    "counter", "couple", "courage", "cousin", "crack", "craft", "crash",
    "crazy", "cream", "credit", "crew", "crime", "criminal", "crisis",
    "critic", "crop", "crucial", "crush", "crystal", "cultural", "culture",
    "curious", "currency", "custom", "customer", "cycle", "daily", "damage",
    "damp", "dare", "data", "database", "date", "dawn", "debate", "debt",
    "decade", "decent", "declare", "decline", "decrease", "defeat", "defend",
    "define", "delight", "deliver", "demand", "democracy", "demonstrate",
    "deny", "depart", "deploy", "deposit", "deprive", "derive", "deserve",
    "desk", "desperate", "destroy", "detail", "detect", "determine",
    "device", "devote", "diamond", "diet", "digital", "dimension", "dinner",
    "dirt", "disable", "disagree", "disappear", "disaster", "discipline",
    "discount", "discover", "discrimination", "dish", "dismiss", "disorder",
    "display", "dispute", "distance", "distinct", "distribute", "district",
    "diverse", "dock", "document", "domestic", "dominant", "dominate", "dose", "doubt", "draft", "drag", "drain", "drama", "dramatic", "drift",
    "driver", "drought", "drug", "drum", "drunk", "due", "dumb",
    "dump", "eager", "earn", "eastern", "economic", "economy",
    "edition", "editor", "educate", "efficient", "effort", "elderly",
    "elect", "electronic", "elsewhere", "embrace", "emerge", "emission",
    "emotion", "emphasis", "empire", "employ", "empty", "enable", "encounter",
    "encourage", "enforce", "engage", "engineer", "enhance", "enjoy",
    "enormous", "ensure", "enterprise", "entire", "entrance", "entry",
    "envelope", "environment", "episode", "equip", "era", "error", "essay",
    "essential", "establish", "estate", "estimate", "ethics", "evaluate",
    "eventually", "evidence", "evil", "evolve", "examine", "exceed",
    "excellent", "exchange", "exclude", "executive", "exhibit", "exist",
    "expand", "expense", "expert", "exploit", "explore", "export", "expose",
    "extend", "extent", "external", "extra", "extreme", "fabric", "facility",
    "factor", "factory", "faculty", "fade", "fail", "failure", "faith",
    "fame", "familiar", "fan", "fancy", "fare", "fashion", "fate", "fault",
    "feature", "federal", "fee", "female", "fence", "festival", "fewer",
    "fiction", "fierce", "fifth", "fifty", "file", "film", "filter",
    "finance", "finding", "firm", "fix", "flag", "flame", "flash", "flavor",
    "flee", "fleet", "flesh", "flight", "float", "flood", "flour",
    "fluid", "fold", "folk", "football", "forecast", "foreign", "forever",
    "forget", "formal", "formula", "fortune", "forum", "foster", "foundation",
    "frame", "framework", "freeze", "frequency", "frequent", "friendly",
    "friendship", "fuel", "function", "fund", "fundamental", "funeral",
    "furniture", "furthermore", "future", "gain", "galaxy", "gallery", "gap",
    "garage", "gate", "gear", "gender", "gene", "generate", "generation",
    "genetic", "genius", "genre", "genuine", "gesture", "ghost", "giant",
    "gift", "girlfriend", "glance", "global", "glory", "goal",
    "golden", "golf", "grab", "grace", "grade", "graduate", "grain", "grant", "grateful", "grave", "grocery", "gross", "guarantee", "guard",
    "guest", "guilty", "guitar", "gulf", "gut", "guy", "habit", "habitat",
    "halt", "handful", "handle", "hang", "harbor", "harm", "harsh", "harvest",
    "hate", "headquarters", "heal", "healthy", "heap", "heaven", "height",
    "hello", "helpful", "hence", "heritage", "hero", "hide", "highway",
    "hint", "hire", "historian", "historic", "holy", "honest", "honor", "hook",
    "horizon", "horror", "host", "hostile", "household", "housing", "hunger",
    "ideal", "identify", "identity", "ignore", "illegal", "illness",
    "illustrate", "image", "imagination", "immediate", "immigrant", "immune",
    "impact", "implement", "implication", "imply", "import", "impose",
    "impossible", "impress", "impression", "impressive", "improve", "incident",
    "income", "incorporate", "index", "infant", "infection", "inflation",
    "influence", "inform", "initial", "initiative", "injury", "inner",
    "innocent", "innovation", "input", "inquiry", "insert", "insight",
    "inspect", "inspiration", "install", "instance", "institute",
    "institution", "insurance", "intellectual", "intelligence", "intend",
    "intense", "intention", "interaction", "interior", "internal",
    "international", "internet", "interpret", "intervention", "interview",
    "introduce", "introduction", "invade", "invasion", "invest",
    "investigation", "investor", "invisible", "invitation", "involve",
    "isolation", "issue", "item", "jacket", "jail", "jam", "jet", "joint",
    "joke", "journal", "journey", "judge", "judgment", "juice", "junior",
    "jury", "justice", "justify", "keen", "kid", "kidney", "kiss", "kit",
    "kitchen", "knee", "knife", "knock", "lab", "label", "lack", "lamp",
    "landscape", "lane", "lap", "launch", "lawn", "lawyer", "layer",
    "leadership", "leaf", "league", "lean", "leap", "leather", "lecture",
    "legacy", "legend", "legislation", "legitimate", "lemon", "lesson",
    "liberal", "liberty", "library", "license", "lid", "lifetime", "likewise",
    "limit", "link", "lip", "liquid", "load", "loan", "lobby", "local",
    "locate", "lock", "log", "logic", "lonely", "loose", "lord", "lover", "loyal", "luck", "lunch", "lung", "luxury",
}
