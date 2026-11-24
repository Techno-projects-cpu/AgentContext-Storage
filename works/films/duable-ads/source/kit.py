"""
kit.py — the brag-standard renderer: type, motion, and the two visual systems.

This implements the craft floor from agent-context/BRAG-PROMPT.md as code, so the
rules are measured rather than remembered:

    type floor      >= 28 px at the 1080 short side  (MIN_PT below)
    entrance        0.45 s, ease-out cubic
    hold            0.5 s + 0.3 s per word             (hold_for)
    transitions     0.30 s cross-fade                  (CUT)
    frame 0         carries ink — no fade from nothing

Two looks, deliberately different from each other and from anything else in this
repo. Both are drawn from the subject: Duable is a service catalogue, so one ad is
built out of grid and numbers, the other out of paper and quiet.
"""
import math

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
M = 84                     # margin (chrome sits at 84 px, inside the QC safe box)
MIN_PT = 28                # type floor
CUT = 0.30                 # cross-fade, seconds

_FONT_DIRS = [
    "/home/user/AgentContext-Storage/skills/video-to-shorts-skill/fonts",
    "/home/user/AgentContext-Storage/works/films/bytesized-sample/assets/fonts",
]
_cache = {}


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def hold_for(text, minimum=0.9):
    """0.5 s + 0.3 s per word, the brag hold rule."""
    return max(minimum, 0.5 + 0.3 * len(text.split()))


def font(kind, size):
    size = max(MIN_PT, int(size))
    key = (kind, size)
    if key in _cache:
        return _cache[key]
    names = {
        "black": ["Poppins-ExtraBold.ttf", "Display.ttf"],
        "bold": ["Poppins-Bold.ttf", "LabelBold.ttf", "Label.ttf"],
        "body": ["Poppins-Bold.ttf", "UI.ttf"],
    }[kind]
    picked = None
    for d in _FONT_DIRS:
        for n in names:
            try:
                picked = ImageFont.truetype(f"{d}/{n}", size)
                break
            except OSError:
                continue
        if picked:
            break
    _cache[key] = picked or ImageFont.load_default()
    return _cache[key]


def tw(d, s, f, tracking=0.0):
    if not tracking:
        return d.textlength(s, font=f)
    return sum(d.textlength(ch, font=f) for ch in s) + tracking * max(0, len(s) - 1)


def text(d, xy, s, f, fill, tracking=0.0, anchor=None):
    x, y = xy
    if not tracking:
        d.text((x, y), s, font=f, fill=fill, anchor=anchor)
        return
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill, anchor=anchor)
        x += d.textlength(ch, font=f) + tracking


def wrap(d, s, f, max_w):
    out, cur = [], ""
    for w in s.split():
        cand = (cur + " " + w).strip()
        if not cur or d.textlength(cand, font=f) <= max_w:
            cur = cand
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def fit_size(d, strings, kind, start, max_w, floor=MIN_PT):
    """Largest size at which every string fits. Never below the type floor."""
    size = int(start)
    while size > floor:
        f = font(kind, size)
        if max(d.textlength(s, font=f) for s in strings) <= max_w:
            return size
        size -= 2
    return floor


def vgrad(size, top, bottom):
    w, h = size
    img = Image.new("RGB", (1, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        u = y / max(1, h - 1)
        d.point((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * u) for i in range(3)))
    return img.resize((w, h), Image.BILINEAR)


def grain(img, amount=6, seed=1):
    import numpy as np
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.int16)
    n = rng.integers(-amount, amount + 1, size=a.shape[:2], dtype=np.int16)[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


# ============================================================ look A: THE MENU
# Near-black ink with a phosphor-green accent, grid paper, numbers as the hero.
# Every element sits on an 8-column modular grid because the subject is a catalogue.
MENU_BG_TOP = (10, 12, 14)
MENU_BG_BOT = (18, 22, 24)
MENU_INK = (245, 247, 240)
MENU_GREEN = (184, 255, 74)
MENU_DIM = (120, 132, 128)
MENU_RULE = (46, 54, 52)


def menu_base(grid_phase=0.0, grid_alpha=26):
    img = vgrad((W, H), MENU_BG_TOP, MENU_BG_BOT)
    d = ImageDraw.Draw(img)
    # modular grid, drifting very slowly so the frame is never static
    step = 108
    off = int((grid_phase * step) % step)
    for x in range(-step, W + step, step):
        d.line([(x + off, 0), (x + off, H)], fill=MENU_RULE, width=1)
    for y in range(-step, H + step, step):
        d.line([(0, y + off), (W, y + off)], fill=MENU_RULE, width=1)
    # corner ticks, held a little inside the margin so they clear a 90 % safe box
    ti = 26
    for (cx, cy, sx, sy) in ((M + ti, M + ti, 1, 1), (W - M - ti, M + ti, -1, 1),
                             (M + ti, H - M - ti, 1, -1), (W - M - ti, H - M - ti, -1, -1)):
        d.line([(cx, cy), (cx + 26 * sx, cy)], fill=MENU_GREEN, width=3)
        d.line([(cx, cy), (cx, cy + 26 * sy)], fill=MENU_GREEN, width=3)
    return img, d


def menu_header(d, left, right):
    f = font("bold", 30)
    text(d, (M, M + 14), left, f, MENU_DIM, tracking=3)
    w = tw(d, right, f, 3)
    text(d, (W - M - w, M + 14), right, f, MENU_DIM, tracking=3)
    d.line([(M, M + 66), (W - M, M + 66)], fill=MENU_RULE, width=2)


def menu_footer(d, progress):
    f = font("bold", 28)
    d.line([(M, H - 180), (W - M, H - 180)], fill=MENU_RULE, width=2)
    text(d, (M, H - 160), "DUABLE  \u00b7  DUABLEINDUSTRIES.VERCEL.APP", f, MENU_DIM, tracking=2)
    x0, x1 = W - M - 220, W - M
    d.rectangle([x0, H - 126, x1, H - 120], fill=MENU_RULE)
    d.rectangle([x0, H - 126, x0 + int(220 * progress), H - 120], fill=MENU_GREEN)


# ========================================================== look B: HONEST MODE
# Warm paper, one deep-green ink, a single hairline rule. Nothing blinks, nothing
# shouts. The subject is a studio that refuses to promise numbers.
PAPER = (243, 238, 228)
PAPER_2 = (232, 225, 212)
DEEP = (18, 48, 42)
DEEP_SOFT = (86, 110, 102)
PAPER_RULE = (198, 189, 172)


def paper_base(phase=0.0):
    img = vgrad((W, H), PAPER, PAPER_2)
    d = ImageDraw.Draw(img)
    # a single hairline frame, inset
    inset = 96          # inside the QC safe box (54 px at --safe 0.90)
    d.rectangle([inset, inset, W - inset, H - inset], outline=PAPER_RULE, width=2)
    return img, d


def paper_header(d, left, right):
    f = font("bold", 28)
    text(d, (M + 24, M + 62), left, f, DEEP_SOFT, tracking=4)
    w = tw(d, right, f, 4)
    text(d, (W - M - 24 - w, M + 62), right, f, DEEP_SOFT, tracking=4)


def paper_footer(d, progress):
    f = font("bold", 26)
    text(d, (M + 24, H - M - 84), "DUABLE  \u00b7  DUABLEINDUSTRIES.VERCEL.APP", f, DEEP_SOFT, tracking=3)
    d.line([(M + 24, H - M - 116), (W - M - 24, H - M - 116)], fill=PAPER_RULE, width=2)
    d.rectangle([M + 24, H - M - 116, M + 24 + int(200 * progress), H - M - 116], fill=DEEP)


# ------------------------------------------------------------------ layout help
def ink(f, s):
    """The visible box of a string: (left, top, right, bottom) offsets from the pen origin."""
    return f.getbbox(s or "Ag")


def measure(items, gap=10):
    """Height of a stack, measured on INK boxes so nothing under- or overlaps."""
    h = 0
    for it in items:
        f = it[1]
        bb = ink(f, it[0])
        h += (it[3] if len(it) > 3 else 0) + (bb[3] - bb[1]) + gap
    return max(0, h - gap)


def draw_block(d, items, x, y, gap=10):
    """Stack items top-down, each aligned by its ink box, not its em box.

    PIL positions text by the ascender, so a 360 px numeral has ~108 px of empty
    space above it. Advancing by the ink box instead is what stops lines colliding.
    Returns the y after the last line.
    """
    for it in items:
        s, f, rgb = it[0], it[1], it[2]
        y += it[3] if len(it) > 3 else 0
        bb = ink(f, s)
        d.text((x, y - bb[1]), s, font=f, fill=rgb)
        y += (bb[3] - bb[1]) + gap
    return y


def stack(d, items, x, y, t, gap=10, stagger=0.13, dur=0.45, slide=26, align="left", t0=0.0):
    """draw_block plus the brag entrance: rise 26 px, ease out, staggered per line."""
    for i, it in enumerate(items):
        s, f, rgb = it[0], it[1], it[2]
        y += it[3] if len(it) > 3 else 0
        bb = ink(f, s)
        a = ease_out((t - t0 - stagger * i) / dur)
        if a > 0:
            dx = 0
            if align == "center":
                dx = -d.textlength(s, font=f) / 2
            d.text((x + dx, y - bb[1] + (1 - a) * slide), s, font=f, fill=rgb)
        y += (bb[3] - bb[1]) + gap
    return y
