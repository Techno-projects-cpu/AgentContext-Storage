#!/usr/bin/env python3
"""Message-match + landing checks for the ZeroVast ad set.

claude-ads' `ads-landing` skill wants every ad promise checked against the
destination page. Its own fetcher is blocked here (vercel.app is unreachable from
this sandbox), so this runs the same checks statically against the repository
that deploys that URL, and says so in the output rather than pretending it
fetched the live page.

    python3 landing_check.py --site /home/user/ZeroVast --brief creative/creative-brief.json

Deliberately NOT checked (and reported as unknown, not passed):
  - Core Web Vitals (needs a browser on the live origin)
  - mobile rendering, screenshots, redirects
  - anything about the deployed build vs the repo
"""
import argparse
import html
import json
import pathlib
import re
import sys

PAGES = ["index.html", "capabilities.html", "about.html", "contact.html"]


def text_of(path: pathlib.Path) -> str:
    s = path.read_text(encoding="utf-8")
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--brief", required=True)
    a = ap.parse_args()
    site = pathlib.Path(a.site)
    brief = json.load(open(a.brief))

    pages = {p: text_of(site / p) for p in PAGES}
    all_text = " ".join(pages.values())

    # Each claim in the brief must be traceable to page text.
    claim_probes = {
        "hand-written": ["hand-written", "hand written", "vanilla javascript"],
        "weight budgets": ["core web vitals", "lcp", "budget"],
        "wcag": ["wcag"],
        "source code at handover": ["repository", "source code", "handover"],
        "hosting in client name": ["registered in your name", "do not mark them up"],
        "three revisions": ["three revision"],
    }
    print("## Claim presence on the destination pages\n")
    print("| claim | found on | evidence term |")
    print("|---|---|---|")
    for claim, probes in claim_probes.items():
        hit_page, hit_term = None, None
        for p, t in pages.items():
            for probe in probes:
                if probe in t:
                    hit_page, hit_term = p, probe
                    break
            if hit_page:
                break
        print(f"| {claim} | {hit_page or '**MISSING**'} | `{hit_term}` |" if hit_page
              else f"| {claim} | **MISSING** | — |")

    # Ad hook -> page headline continuity.
    print("\n## Hook to landing continuity\n")
    h1 = re.search(r"Websites built\s*to perform", pages["index.html"] or "", re.I)
    lede_speed = "core web vitals" in all_text or "lcp" in all_text
    rows = [
        ("h1-speed", "Your site is too slow / They leave",
         "page opens on 'Websites built to perform' and promises speed budgets",
         bool(h1) and lede_speed),
        ("h2-ownership", "Can you edit your own site?",
         "capabilities states hosting in the client's name, no markup, source handover",
         "registered in your name" in all_text and "repository" in all_text),
        ("h3-limit", "Four things I won't do",
         "capabilities has a four-item 'What I don't do' section",
         all(k in all_text for k in ("templates sold as custom work", "a framework by default",
                                    "surprise invoices"))),
    ]
    print("| concept | ad hook | what the page says | match |")
    print("|---|---|---|---|")
    for cid, hook, page_says, ok in rows:
        print(f"| {cid} | {hook} | {page_says} | {'PASS' if ok else '**FAIL**'} |")

    # Conversion surface.
    contact = pages["contact.html"]
    fields = len(re.findall(r"<(input|textarea|select)\b", (site / "contact.html").read_text(encoding="utf-8")))
    # mailto: lives in an href, so it is gone once the tags are stripped:
    # count it on the raw sources, not the extracted text.
    raw = " ".join((site / p).read_text(encoding="utf-8") for p in PAGES)
    mailtos = len(re.findall(r"mailto:", raw))
    print("\n## Conversion surface\n")
    print(f"- form controls on contact.html: **{fields}**")
    print(f"- mailto links across the site: **{mailtos}**")
    print(f"- 'start a project' occurrences: **{all_text.count('start a project')}**")

    print("\n## Not checked\n")
    print("- Core Web Vitals, mobile rendering, redirects: the live origin")
    print("  (`zero-vast.vercel.app`) is unreachable from this sandbox, and claude-ads'")
    print("  guarded fetcher refuses without an egress attestation. These are recorded as")
    print("  **unknown**, not passed.")
    print("- deployed build vs this repository: unverified for the same reason.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
