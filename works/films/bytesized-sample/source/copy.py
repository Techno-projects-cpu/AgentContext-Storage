"""
copy.py — the script for "Every TV Screen Explained", in Byte Sized Explainer's grammar.

What the channel actually does, and what is copied here:

  1. Cold open. No logo, no intro. Within one second the topic is named and framed
     as a number: "EVERY TV SCREEN EXPLAINED".
  2. One screen technology per beat, always in the same order of filling:
     a big index number, the term, then one line saying HOW IT MAKES LIGHT.
     Never what it is. Always the mechanism.
  3. A flat schematic drawing of the mechanism, drawn as it is described.
     Nothing photoreal, nothing decorative.
  4. A spec chip row: one number and one tradeoff per beat.
  5. A comparison table at the end that pays off the "every" in the title.
  6. A question sign-off, because the channel's comments are the distribution.

Facts below are the standard, uncontested ones from display engineering; no claim
here is speculative. Every figure is a typical value, not a guarantee.
"""

TITLE = "EVERY TV SCREEN"
TITLE_2 = "EXPLAINED"
SUB = "Five ways to make a picture out of nothing"

BEATS = [
    dict(
        n="01",
        term="CRT",
        kicker="CATHODE RAY TUBE · 1934",
        line="An electron gun paints\none glowing dot at a time.",
        detail=[
            "A heated filament fires electrons.",
            "Magnets steer the beam across a",
            "phosphor screen, line by line, 25×/s.",
        ],
        chips=[("ONE BEAM", "per colour"), ("DEEP BLACK", "void, not off"), ("HEAVY", "30 kg, 32 inch")],
        kind="crt",
        color=(37, 99, 235),
    ),
    dict(
        n="02",
        term="LCD",
        kicker="LIQUID CRYSTAL DISPLAY · 1973",
        line="The crystals never make light.\nThey only let it through.",
        detail=[
            "A backlight shines constantly.",
            "Crystals twist to block or pass",
            "it, through two crossed polarisers.",
        ],
        chips=[("SHUTTER", "not emitter"), ("GREY BLACK", "light leaks"), ("CHEAP", "and everywhere")],
        kind="lcd",
        color=(14, 165, 233),
    ),
    dict(
        n="03",
        term="PLASMA",
        kicker="GAS DISCHARGE · 1997",
        line="Tiny pockets of gas\nbecome tiny lamps.",
        detail=[
            "Each cell holds neon and xenon.",
            "A voltage turns it to plasma,",
            "which fires UV into phosphor.",
        ],
        chips=[("SELF-LIT", "every cell"), ("TRUE BLACK", "cell off"), ("HOT", "and power hungry")],
        kind="plasma",
        color=(217, 70, 239),
    ),
    dict(
        n="04",
        term="OLED",
        kicker="ORGANIC LED · 2007",
        line="Every pixel is its own lamp.\nOff means actually off.",
        detail=[
            "An organic film emits light",
            "when current passes through it.",
            "No backlight, so no light leaks.",
        ],
        chips=[("PER PIXEL", "control"), ("INFINITE", "contrast"), ("BURNS IN", "blue wears out")],
        kind="oled",
        color=(16, 185, 129),
    ),
    dict(
        n="05",
        term="MICROLED",
        kicker="INORGANIC LED · 2020s",
        line="What OLED does, with\ncrystals that do not fade.",
        detail=[
            "Each pixel is a real LED,",
            "microns wide, assembled onto",
            "the panel individually.",
        ],
        chips=[("NO BURN-IN", "inorganic"), ("VERY BRIGHT", "daylight safe"), ("EXPENSIVE", "the catch")],
        kind="microled",
        color=(245, 158, 11),
    ),
]

# The payoff table. Columns: black level, brightness, burn-in risk, first sale year.
TABLE = [
    ("CRT", "perfect", "dim", "no", "1934"),
    ("LCD", "grey", "high", "no", "1973"),
    ("PLASMA", "perfect", "medium", "yes", "1997"),
    ("OLED", "perfect", "medium", "yes", "2007"),
    ("MICROLED", "perfect", "very high", "no", "2020s"),
]
TABLE_HEAD = ("SCREEN", "BLACKS", "BRIGHT", "BURNS IN", "FROM")

SIGN = "WHICH ONE DID YOU GROW UP WITH?"

FOOTER = "BYTE SIZED · EVERY TV SCREEN EXPLAINED"
