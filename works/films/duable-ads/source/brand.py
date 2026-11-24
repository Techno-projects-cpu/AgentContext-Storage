"""
brand.py — what duableindustries.vercel.app actually says.

Scraped from the live production alias (duableindustries.vercel.app, Vercel project
`duableindustries`, deployment dpl_D7puXA4semWYFT7Nz3qXDoNKLxWp).

RULE FOR THIS FILE: every string here is either a direct quote from the site or a
restatement of a number the site prints. No prices, no client counts, no testimonials,
no "trusted by". If it is not below, it does not go on screen.
"""

NAME = "DUABLE"
DESCRIPTOR = "INDEPENDENT CREATIVE TECHNOLOGY STUDIO"
TAGLINE_1 = "A STUDIO WITH"
TAGLINE_2 = "A SERVICE FOR THAT."
URL = "duableindustries.vercel.app"
URL_SHORT = "DUABLEINDUSTRIES.VERCEL.APP"

# The site's own category split, with its own counts.
CATEGORIES = [
    ("WEB & TECHNOLOGY", 8),
    ("AI & AUTOMATION", 4),
    ("CREATIVE & MEDIA", 5),
    ("MARKETING & GROWTH", 7),
]
TOTAL_SERVICES = 24          # printed on the site: "24 services"

# The site's four process steps, verbatim.
PROCESS = ["TALK IT THROUGH", "SET THE SCOPE", "MAKE THE WORK", "HAND IT OVER"]

# Two claims the site makes about itself, quoted.
QUOTE_NO_MAGIC = "WITHOUT PROMISING MAGIC NUMBERS"
QUOTE_LOCAL = "YOUR ANSWERS STAY IN THIS BROWSER"
QUOTE_TEAM = "SMALL TEAM, HANDS-ON WORK"
QUOTE_PLACE = "BASED IN INDIA \u00b7 WORKING EVERYWHERE"

# The site is explicit that the two names are labels, not people's legal names.
ALIAS_NOTE = "CREATIVE ALIASES, NOT LEGAL NAMES"

# ---------------------------------------------------------------- ad 1: THE MENU
# Angle: the breadth is the product. Numbers forward, fast, dark.
MENU = dict(
    hook_num="24",
    hook_word="SERVICES",
    hook_sub="ONE STUDIO",
    cats=[("WEB &", "TECHNOLOGY", 8), ("AI &", "AUTOMATION", 4),
          ("CREATIVE &", "MEDIA", 5), ("MARKETING &", "GROWTH", 7)],
    mid_1="BROWSE BY CATEGORY.",
    mid_2="OPEN THE PAGE FOR THE EXACT THING YOU NEED.",
    end_1="A STUDIO WITH",
    end_2="A SERVICE FOR THAT.",
)

# ------------------------------------------------------------- ad 2: HONEST MODE
# Angle: the things it refuses to do. Light, quiet, generous holds.
HONEST = dict(
    open_1="NO MAGIC",
    open_2="NUMBERS.",
    open_sub="THAT IS THE PROMISE.",
    body_1="POSITIONING, CONTENT, CAMPAIGNS \u2014",
    body_2="PLANNED, NOT GUESSED.",
    body_3="YOUR PROJECT NOTE",
    body_4="STAYS IN THIS BROWSER.",
    body_sub="NOTHING IS SENT. NOTHING IS SAVED.",
    team_1="SMALL TEAM.",
    team_2="HANDS-ON WORK.",
    team_sub="BASED IN INDIA \u00b7 WORKING EVERYWHERE",
)
