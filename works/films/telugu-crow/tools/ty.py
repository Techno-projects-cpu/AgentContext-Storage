"""Telugu (and Latin) text, shaped by HarfBuzz and drawn as glyph outlines.

Skia's own text path here has no HarfBuzz shaping, so `drawString` scrambles Telugu conjuncts
(కీ, పో, తో all come out wrong) and puts vowel signs in the wrong place. Everything spoken or
written in this film therefore goes through this module: uharfbuzz shapes, skia draws the glyph
outlines, and because the result is a list of clusters with x positions, word-by-word highlighting,
letter popping and measuring all become easy.

  line = layout("నాకు ఒక ఐడియా వచ్చింది!", FONT_BOLD, 300)
  draw(c, line, x, y, rgb=(30, 26, 30), rgb_word=lambda wi, col: ORANGE if wi == 2 else col)
"""
import functools

import skia
import uharfbuzz as hb

from engine import clamp, ease_out_back, ramp

_FACES = {}


def _hbfont(path):
    if path not in _FACES:
        blob = hb.Blob.from_file_path(str(path))
        face = hb.Face(blob)
        _FACES[path] = (face, hb.Font(face))
    return _FACES[path]


@functools.lru_cache(maxsize=64)
def _skfont(path, size):
    tf = skia.Typeface.MakeFromFile(str(path))
    if tf is None:
        raise SystemExit(f"cannot open typeface {path}")
    f = skia.Font(tf, size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    f.setLinearMetrics(True)
    return f


@functools.lru_cache(maxsize=40000)
def _glyph_path(path, size, gid):
    return _skfont(path, size).getPath(gid)


class Word:
    __slots__ = ("i", "text", "x", "w", "chars")

    def __init__(self, i):
        self.i, self.text, self.x, self.w, self.chars = i, "", 0.0, 0.0, set()


class Cluster:
    __slots__ = ("i", "text", "x", "w", "glyphs", "chars", "word", "path")

    def __init__(self, i, x):
        self.i, self.text, self.x, self.w, self.glyphs, self.chars, self.word = i, "", x, 0.0, [], set(), -1
        self.path = None


class Line:
    """A shaped string: clusters (in visual order) and words, with x positions and measurements."""

    def __init__(self, text, path, size):
        self.text, self.path, self.size = text, str(path), float(size)
        face, hbfont = _hbfont(self.path)
        em = self.size / face.upem
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(hbfont, buf)
        infos, poss = buf.glyph_infos, buf.glyph_positions

        # uharfbuzz clusters on character offsets (add_str encodes to utf-8 but clusters stay in
        # codepoints), and they ascend monotonically for this text
        starts = sorted({min(i.cluster, len(text)) for i in infos})
        end_of = {}
        for k, c0 in enumerate(starts):
            end_of[c0] = starts[k + 1] if k + 1 < len(starts) else len(text)

        # walk the shaped glyphs in the order HarfBuzz emitted them (never re-sort: that scrambles
        # Indic text); consecutive glyphs sharing a cluster become one cluster
        self.clusters = []
        cursor = 0.0
        prev = None
        for info, pos in zip(infos, poss):
            ci = min(info.cluster, len(text) - 1)
            g = (info.codepoint, pos.x_advance * em, pos.x_offset * em, pos.y_offset * em)
            adv = g[1]
            if ci != prev:
                cl = Cluster(len(self.clusters), cursor)
                cl.chars = set(range(ci, end_of[ci]))
                cl.text = text[ci:end_of[ci]]
                self.clusters.append(cl)
            cl = self.clusters[-1]
            cl.glyphs.append(g)
            cl.w += adv
            cursor += adv
            prev = ci
        self.width = cursor

        # words: split the source on spaces, then give each cluster to the word its first real
        # character belongs to (never by comparing x positions: clusters can start at the same x)
        word_of_char, wi = {}, 0
        for ci, ch in enumerate(text):
            if ch.isspace():
                wi += 1
            else:
                word_of_char[ci] = wi
        self.words = []
        by_w = {}
        for cl in self.clusters:
            real = [c for c in sorted(cl.chars) if c in word_of_char]
            if not real:
                continue
            w = word_of_char[real[0]]
            if w not in by_w:
                by_w[w] = Word(len(by_w))
                by_w[w].x = cl.x
            wd = by_w[w]
            wd.chars.update(real)
            wd.x = min(wd.x, cl.x)
            wd.w = max(wd.w, cl.x + cl.w - wd.x)
            wd.text += cl.text
            cl.word = wd.i
        self.words = [by_w[k] for k in sorted(by_w)]
        for k, wd in enumerate(self.words):
            wd.i = k
            wd.text = "".join(text[c] for c in sorted(wd.chars))

    # ---- queries
    def word_at(self, idx):
        return self.words[idx] if 0 <= idx < len(self.words) else None

    def index_of(self, sub, nth=0):
        """Word index containing the nth occurrence of substring `sub`."""
        pos, start = -1, 0
        for _ in range(nth + 1):
            pos = self.text.find(sub, start)
            if pos < 0:
                return -1
            start = pos + 1
        for wd in self.words:
            if pos in wd.chars:
                return wd.i
        return -1

    def char_x(self, ci):
        """x of the cluster that starts at character ci (for a playhead under a syllable)."""
        for cl in self.clusters:
            if ci in cl.chars:
                return cl.x
        return self.width


@functools.lru_cache(maxsize=4096)
def layout(text, path, size):
    return Line(text, path, size)


def measure(text, path, size):
    return layout(text, path, size).width


def _paint(rgb, a):
    return skia.Paint(AntiAlias=True, Color=skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(255 * clamp(a))))


def cluster_path(line, cl):
    """The cluster's glyph outline as one path, in text-relative coordinates (origin at its start)."""
    if cl.path is not None:
        return cl.path
    acc, cur = None, 0.0
    size = round(line.size, 2)
    for (gid, adv, xoff, yoff) in cl.glyphs:
        g = _glyph_path(line.path, size, gid)
        if g is not None and not g.isEmpty():
            gg = skia.Path(g)
            gg.offset(cur + xoff, yoff)
            if acc is None:
                acc = gg
            else:
                acc.addPath(gg)
        cur += adv
    cl.path = acc
    return acc


def draw(c, line, x, y, rgb=(28, 24, 28), a=1.0, align="left", a_cluster=None, rgb_cluster=None,
         a_word=None, rgb_word=None, pop_word=-1, pop_t=0.0, pop_dur=0.32, outline=None, ow=None,
         shadow=None, sway=None, alpha=None):
    """Draw a shaped line, baseline-start at (x, y); align center/right shift it.

    Hooks, all optional:
      a_cluster(ci)->float / rgb_cluster(ci, col)->rgb        light up single letters
      a_word(wi)->float / rgb_word(wi, col)->rgb              light up whole words
      pop_word wi, pop_t: that word scales in at t (comic emphasis)
      outline rgb + ow: thick outline behind the glyphs (kids' caption look); shadow likewise
      sway(ci)->(dx, dy): nudge a glyph, for a wobble or a bounce
    """
    x0 = x - (line.width if align == "right" else line.width / 2 if align == "center" else 0)
    base_alpha = a if alpha is None else a * alpha
    for cl in line.clusters:
        if not cl.text.strip():
            continue
        al = base_alpha if a_cluster is None else base_alpha * a_cluster(cl.i)
        if a_word is not None and cl.word >= 0:
            al *= a_word(cl.word)
        col = rgb
        if rgb_cluster is not None:
            col = rgb_cluster(cl.i, col)
        if rgb_word is not None and cl.word >= 0:
            col = rgb_word(cl.word, col)
        if al <= 0.004:
            continue
        dx = dy = 0.0
        if sway is not None:
            dx, dy = sway(cl.i)
        cx = x0 + cl.x
        path = cluster_path(line, cl)
        if path is None:
            continue
        sc = 1.0
        pivot = (x0 + line.word_at(cl.word).x + line.word_at(cl.word).w / 2) if cl.word >= 0 else cx
        if cl.word >= 0 and cl.word == pop_word:
            u = ramp(pop_t, 0.0, pop_dur)
            sc = 0.55 + 0.45 * ease_out_back(u, 2.4)
        if sc != 1.0:
            c.save()
            c.translate(pivot, y - line.size * 0.30)
            c.scale(sc, sc)
            c.translate(-pivot, -(y - line.size * 0.30))
        if outline is not None:
            op = _paint(outline, al)
            op.setStyle(skia.Paint.kStroke_Style)
            op.setStrokeWidth(ow if ow is not None else line.size * 0.11)
            op.setStrokeJoin(skia.Paint.kRound_Join)
            c.save(); c.translate(cx + dx, y + dy); c.drawPath(path, op); c.restore()
        if shadow is not None:
            sp = _paint(shadow, al * 0.55)
            c.save(); c.translate(cx + dx + line.size * 0.03, y + dy + line.size * 0.055)
            c.drawPath(path, sp); c.restore()
        c.save(); c.translate(cx + dx, y + dy); c.drawPath(path, _paint(col, al)); c.restore()
        if sc != 1.0:
            c.restore()


def line_height(size):
    return size * 1.52


def wrap(text, path, size, max_width):
    """Greedy wrap into a list of shaped Lines that each fit max_width."""
    out, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if cur and measure(trial, path, size) > max_width:
            out.append(layout(cur, path, size))
            cur = w
        else:
            cur = trial
    if cur:
        out.append(layout(cur, path, size))
    return out


def fit(text, path, size, max_width, min_size=16):
    """Largest size (starting from `size`) at which `text` fits max_width."""
    while size > min_size and measure(text, path, size) > max_width:
        size *= 0.96
    return size
