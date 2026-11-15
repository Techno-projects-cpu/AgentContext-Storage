#!/usr/bin/env python3
"""Build and validate the ZeroVast (NEZAAD Industries) claude-ads artifacts.

Run with the claude-ads checkout on PYTHONPATH so the validator is the real
upstream one, not a reimplementation:

    PYTHONPATH=/home/user/claude-ads python3 build_artifacts.py \
        --claude-ads /home/user/claude-ads \
        --site /home/user/ZeroVast \
        --out /home/user/AgentContext-Storage/works/ads/zero-vast

Outputs, all validated against claude_ads_core before writing:
  brand/brand-profile.json      <- claude-ads ads-dna contract
  creative/creative-brief.json  <- claude-ads ads-create contract
  creative/copy-deck.md         <- human-readable rendeck of the same brief
Every value is either lifted verbatim from the site source or marked as an
inference with approval_status=pending.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import sys

RUN_ID = "zv-2026-11-09-01"
CREATED_AT = "2026-11-09T12:00:00Z"
URL = "https://zero-vast.vercel.app"


def lifecycle():
    return {
        "schema_version": "1.0.0",
        "lifecycle_id": "zv-ad-run-1",
        "classification": "public",
        "retention": {
            "minimum_seconds": 0,
            "mode": "operator-defined",
            "delete_after": None,
            "purpose": "public website copy and ad creative; no personal data, no "
                       "credentials, no analytics identifiers handled",
            "exception_reason": None,
        },
        "encryption": {
            "at_rest": "not-applicable",
            "in_transit": "not-applicable",
            "evidence_refs": [
                "source is a public static site read from the owner's repository",
                "no form submission, no account data, no credentials in this run",
            ],
        },
        "access": {
            "owner": "NEZAAD Industries",
            "authorized_roles": ["site owner"],
            "access_log_locator": None,
        },
        "deletion": {
            "status": "scheduled",
            "method": "delete the run directory",
            "verification_required": True,
            "verification_artifact_locator": None,
        },
        "incident": {
            "owner": "NEZAAD Industries",
            "reporting_channel": "site owner email in the repository footer",
            "status": "not-triggered",
            "record_locator": None,
        },
    }


def obs(field, value, refs, confidence="high"):
    return {"field": field, "value": value, "evidence_refs": refs, "confidence": confidence}


def inf(field, value, refs, confidence="medium"):
    return {
        "field": field,
        "value": value,
        "evidence_refs": refs,
        "confidence": confidence,
        "approval_status": "pending",
    }


def build_brand(site: pathlib.Path):
    idx = site / "index.html"
    caps = site / "capabilities.html"
    about = site / "about.html"
    css = site / "assets" / "styles.css"
    for p in (idx, caps, about, css):
        if not p.exists():
            raise SystemExit(f"missing source file: {p}")

    idx_s = idx.read_text(encoding="utf-8")
    css_s = css.read_text(encoding="utf-8")
    h1 = re.search(r'<h1 class="display[^"]*">(.*?)</h1>', idx_s, re.S).group(1)
    h1_text = re.sub(r"<[^>]+>", " ", h1).replace("  ", " ").strip()
    tokens = dict(re.findall(r"--(ink|panel|paper|muted):\s*(#[0-9a-fA-F]{6})", css_s))

    return {
        "schema_version": "1.0.0",
        "artifact_type": "brand-profile",
        "run_id": RUN_ID,
        "created_at": CREATED_AT,
        "brand_name": "NEZAAD Industries",
        "website_url": URL,
        "observations": [
            obs("brand_name", "NEZAAD Industries",
                ["index.html: <title>, header wordmark alt text"]),
            obs("operator", "Nezaad, an independent web developer",
                ["about.html: 'I'm Nezaad. I design, build and maintain websites'"]),
            obs("location", "Kalluru, Khammam, Telangana",
                ["index.html footer: 'Kalluru, Khammam, Telangana'"]),
            obs("hero_headline", h1_text, ["index.html: h1.display"]),
            obs("positioning", "Hand-written semantic HTML, modern CSS and vanilla "
                               "JavaScript; no framework by default",
                ["index.html: hero lede", "capabilities.html: 'What I don't do' 02"]),
            obs("services", [
                "Marketing & business sites",
                "Web apps & internal tools",
                "Redesigns & performance rescue",
                "Care & maintenance",
            ], ["capabilities.html: section 01"]),
            obs("measurement_promise", "Core Web Vitals budgets (LCP, CLS, INP) "
                                       "agreed before the build starts",
                ["index.html: hero stat 'Performance first'", "capabilities.html: 05 / Performance"]),
            obs("accessibility_promise", "WCAG 2.2 AA, keyboard and screen-reader checks",
                ["capabilities.html: 06 / Accessibility"]),
            obs("process", ["Brief", "Scope", "Build", "Handover"],
                ["index.html: section 03 / How I work"]),
            obs("handover_terms", "Source code passed to the client; hosting and "
                                  "domain registered in the client's name and billed directly",
                ["capabilities.html: 'How projects run'"]),
            obs("revision_policy", "Up to three revision rounds included on every project",
                ["capabilities.html: 'How projects run'"]),
            obs("stated_limits", [
                "No templates sold as custom work",
                "No framework by default",
                "No work the developer cannot stand behind",
                "No surprise invoices",
            ], ["capabilities.html: section 03 / What I don't do"]),
            obs("visual_tokens", tokens, ["assets/styles.css: :root custom properties"]),
            obs("typography", "System sans stack for body; UI monospace stack for labels",
                ["assets/styles.css: --sans and --mono"]),
            obs("contact_channels", [
                "themerchantofdeath2011@gmail.com",
                "themerchantofdeath2000@gmail.com",
                "contact.html enquiry form (opens a mail draft, nothing sent server-side)",
            ], ["index.html footer", "README.md: Enquiry flow"]),
            obs("cta_label", "Start a project", ["index.html nav .nav-cta"]),
            obs("missing_offers", [
                "no prices or price ranges published",
                "no testimonials published",
                "no client count, project count or years-in-business figure published",
                "no named portfolio items published on the site",
                "no availability dates or lead times published",
            ], ["index.html", "capabilities.html", "about.html", "contact.html"]),
        ],
        "inferences": [
            inf("audience", "Small business owners and sole traders in and around "
                            "Khammam / Telangana who need a site that loads on cheap "
                            "Android hardware",
                ["about.html: 'Most small businesses do not need a bigger website. "
                 "They need a faster one'", "index.html: hero lede"]),
            inf("voice", "Direct, technical, unhyped. Shorter sentences, no superlatives, "
                         "limits stated before promises",
                ["capabilities.html: section 03", "about.html: 03 / Plain communication"]),
            inf("primary_objective", "Qualified project enquiries (email or call), not "
                                     "e-commerce sales",
                ["contact.html: mail draft flow", "index.html: 'Start a project' CTA"]),
            inf("price_sensitivity", "Price is a live objection; the site pre-empts it "
                                     "by removing markup on hosting and by refusing "
                                     "templates",
                ["capabilities.html: 'I do not mark them up'", "04 / Surprise invoices"]),
            inf("language", "English only; Telugu is the local language but is not used "
                            "on the site",
                ["all pages: lang=\"en\"", "no Telugu copy in any page"]),
            inf("visual_style", "Monochrome instrument-panel aesthetic: near-black ground, "
                                "paper-white type, mono labels, hairline rules, one accent",
                ["assets/styles.css tokens", "index.html: marquee and step numbering"]),
            inf("competes_on", "Speed, handover of real source code, and plain dealing",
                ["about.html: 01-03 principles", "capabilities.html: 04 / Testing"]),
        ],
        "source_ids": [
            "site:index.html", "site:capabilities.html", "site:about.html",
            "site:contact.html", "site:assets/styles.css", "site:README.md",
        ],
        "source_assets_authorized": True,
        "missing_fields": [
            "no verified live URL from this environment (vercel.app unreachable); "
            "page contents read from the repository that deploys to it",
            "no prices, so no price-led offer can be tested",
            "no testimonials or client names, so no social proof can be used",
            "no analytics or ad account data supplied, so no performance claim is possible",
            "no confirmation from the owner on the inferences above",
        ],
        "status": "partial",
        "data_lifecycle": lifecycle(),
    }


def field(name, value):
    return {"name": name, "value": value}


def build_brief():
    """Three materially distinct strategic concepts, then a copy deck per platform."""
    return {
        "schema_version": "1.0.0",
        "artifact_type": "creative-brief",
        "run_id": RUN_ID,
        "created_at": CREATED_AT,
        "objective": "Drive qualified project enquiries (email or phone) for NEZAAD "
                     "Industries from small-business owners in Telangana",
        "audience": "Owners of small businesses and shops in Khammam and wider Telangana "
                    "who have a slow site, an outdated one, or none, and who reach the "
                    "web mostly on mid-range Android phones",
        "offer": "A website written by hand — semantic HTML, modern CSS, vanilla "
                 "JavaScript — with Core Web Vitals budgets agreed before the build "
                 "starts, source code handed over, and hosting billed to the client "
                 "at cost",
        "approved_claims": [
            {"claim": "Websites are hand-written in semantic HTML, modern CSS and "
                      "vanilla JavaScript, with no framework by default",
             "evidence_refs": ["brand-profile: positioning", "site:index.html hero lede"]},
            {"claim": "Core Web Vitals budgets for LCP, CLS and INP are agreed before "
                      "the build starts",
             "evidence_refs": ["brand-profile: measurement_promise", "site:capabilities.html 05"]},
            {"claim": "WCAG 2.2 AA, full keyboard support and screen-reader checks are "
                      "part of the build",
             "evidence_refs": ["brand-profile: accessibility_promise", "site:capabilities.html 06"]},
            {"claim": "The client receives the source code and deploy steps at handover",
             "evidence_refs": ["brand-profile: handover_terms", "site:index.html step 04"]},
            {"claim": "Hosting and domain are registered in the client's name and billed "
                      "to them directly by the provider",
             "evidence_refs": ["brand-profile: handover_terms", "site:capabilities.html 'How projects run'"]},
            {"claim": "Up to three revision rounds are included on every project",
             "evidence_refs": ["brand-profile: revision_policy"]},
            {"claim": "No prices are published, and scope changes are quoted and approved "
                      "before the work happens",
             "evidence_refs": ["brand-profile: missing_offers", "site:capabilities.html 04"]},
        ],
        "hypotheses": [
            {
                "id": "h1-speed",
                "insight": "A visitor on a mid-range Android phone abandons a slow page "
                           "before it renders; the owner never sees the loss because it "
                           "does not show up as a complaint.",
                "promise": "A site that appears on a cheap phone on a patchy connection, "
                           "because the weight was budgeted before the first line of code.",
                "hook": "\"Your website is slow. Your customers don't tell you — they leave.\"",
                "cta": "Start a project",
                "platforms": ["google", "meta", "youtube", "linkedin"],
                "experiment_hypothesis": "A loss-framed speed hook beats a capability "
                                         "statement on qualified-enquiry rate for the same "
                                         "budget and the same landing page.",
            },
            {
                "id": "h2-ownership",
                "insight": "Small-business owners have been burned by a site they cannot "
                           "edit and cannot leave; lock-in is the real objection behind "
                           "\"I'll think about it\".",
                "promise": "You get the repository, the deploy steps and a walkthrough. "
                           "Hosting is in your name, billed at cost, no markup.",
                "hook": "\"Can you edit your own website, or do you have to call someone?\"",
                "cta": "See what handover includes",
                "platforms": ["google", "meta", "linkedin"],
                "experiment_hypothesis": "An ownership/exiting framing produces fewer but "
                                         "better-qualified enquiries than a speed framing, "
                                         "measurable as enquiry-to-reply rate.",
            },
            {
                "id": "h3-limit",
                "insight": "Everyone in this market promises everything. Stating what you "
                           "will not do is the cheapest way to be believed.",
                "promise": "No templates sold as custom work. No framework unless the "
                           "problem needs one. No invoice for work that was not agreed in "
                           "writing first.",
                "hook": "\"Four things this developer will refuse to do.\"",
                "cta": "Read the limits",
                "platforms": ["google", "reddit", "x", "linkedin"],
                "experiment_hypothesis": "A negative/limits-first creative earns a higher "
                                         "click-through and a lower bounce than a "
                                         "benefit-first creative, because the destination "
                                         "page states the same limits.",
            },
        ],
        "copy_deck": [
            # --- h1 speed to lead -------------------------------------------------
            {"hypothesis_id": "h1-speed", "platform": "google", "placement": "search_rsa",
             "fields": [
                 field("headline_1", "Your site is too slow"),
                 field("headline_2", "Hand-written websites"),
                 field("headline_3", "Built for cheap phones"),
                 field("description_1", "Semantic HTML, modern CSS, vanilla JS. Speed "
                                        "budgets set before the build, not after."),
                 field("description_2", "Source code and deploy steps handed to you. Hosting "
                                        "billed at cost, in your name."),
                 field("path_1", "khammam"), field("path_2", "site-speed"),
             ]},
            {"hypothesis_id": "h1-speed", "platform": "meta", "placement": "feed_1x1_and_4x5",
             "fields": [
                 field("primary_text", "A page that takes three seconds to appear has "
                                       "already lost the visitor. Most small-business sites "
                                       "are heavy because nobody set a weight budget — no "
                                       "framework, no build step, no dependency tax is still "
                                       "the fastest way to ship. Hand-written in Khammam."),
                 field("headline", "Websites built to perform"),
                 field("description", "Speed budgets before the first commit."),
                 field("cta", "Learn more → site"),
             ]},
            {"hypothesis_id": "h1-speed", "platform": "youtube", "placement": "in_stream_16x9",
             "fields": [
                 field("script_0_5s", "Your website is slow. Your customers don't tell you."),
                 field("script_5_15s", "Every build starts with a weight budget: how fast it "
                                       "must draw, how much it may shift, how much "
                                       "JavaScript it may ship."),
                 field("script_15_20s", "Hand-written HTML, CSS and JavaScript. Khammam. "
                                        "NEZAAD Industries."),
                 field("end_card", "Start a project"),
             ]},
            {"hypothesis_id": "h1-speed", "platform": "linkedin", "placement": "single_image",
             "fields": [
                 field("intro", "Most small-business sites are not badly designed. They are "
                                "heavy. A weight budget set before the first commit fixes "
                                "more than a redesign does."),
                 field("headline", "Speed is part of the brief, not a later pass"),
                 field("cta", "Learn more"),
             ]},
            # --- h2 ownership -----------------------------------------------------
            {"hypothesis_id": "h2-ownership", "platform": "google", "placement": "search_rsa",
             "fields": [
                 field("headline_1", "You get the source code"),
                 field("headline_2", "No lock-in, no seat fees"),
                 field("headline_3", "Hand-written websites"),
                 field("description_1", "Repository, deploy steps and a walkthrough at "
                                        "handover. The site is yours outright."),
                 field("description_2", "Hosting and domain in your name, billed at cost. "
                                        "One person writes the code."),
             ]},
            {"hypothesis_id": "h2-ownership", "platform": "meta", "placement": "feed_1x1_and_4x5",
             "fields": [
                 field("primary_text", "Ask a simple question before you hire anyone: can I "
                                       "edit this myself, and can I leave? You get the "
                                       "repository, the deploy steps and a walkthrough, so "
                                       "the answer is yes to both."),
                 field("headline", "The site is yours outright"),
                 field("description", "Source code handed over. Hosting at cost."),
                 field("cta", "Learn more → capabilities"),
             ]},
            {"hypothesis_id": "h2-ownership", "platform": "linkedin", "placement": "single_image",
             "fields": [
                 field("intro", "A website you cannot edit is a subscription, not an asset. "
                                "Handover here means the repository, the deploy steps and a "
                                "walkthrough — and hosting registered in your name."),
                 field("headline", "Handover without the hostage-taking"),
                 field("cta", "Learn more"),
             ]},
            # --- h3 limits -------------------------------------------------------
            {"hypothesis_id": "h3-limit", "platform": "google", "placement": "search_rsa",
             "fields": [
                 field("headline_1", "Four things I won't do"),
                 field("headline_2", "No template as custom work"),
                 field("headline_3", "No surprise invoices"),
                 field("description_1", "Scope, deliverables and timeline agreed in writing "
                                        "before any code. Up to three revisions included."),
                 field("description_2", "If an idea does not hold together you hear it "
                                        "before an invoice exists."),
             ]},
            {"hypothesis_id": "h3-limit", "platform": "reddit", "placement": "promoted_post",
             "fields": [
                 field("title", "The four things I refuse to do as a web developer in "
                                "Telangana"),
                 field("body", "No templates sold as custom work. No framework unless the "
                               "problem needs one. No project I cannot explain line by "
                               "line. No invoice for work that was not agreed first. "
                               "That is the whole pitch."),
             ]},
            {"hypothesis_id": "h3-limit", "platform": "x", "placement": "single_image",
             "fields": [
                 field("post", "Four things this developer will refuse to do: sell you a "
                               "template as custom work. Add a framework you don't need. "
                               "Take a project he can't explain line by line. Invoice for "
                               "anything you didn't approve in writing."),
             ]},
        ],
        "specification_source_ids": [
            "claude-ads:ads/references/google-creative-specs.md",
            "claude-ads:ads/references/meta-creative-specs.md",
            "claude-ads:ads/references/youtube-creative-specs.md",
            "claude-ads:ads/references/linkedin-creative-specs.md",
            "claude-ads:ads/references/copy-frameworks.md",
            "claude-ads:ads/references/compliance.md",
        ],
        "human_review": "pending",
        "status": "draft",
        "data_lifecycle": lifecycle(),
    }


def validate(contract, payload, claude_ads):
    sys.path.insert(0, str(claude_ads))
    from claude_ads_core.contracts import validate_contract  # noqa: E402
    return validate_contract(contract, payload)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claude-ads", required=True)
    ap.add_argument("--site", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ca, site, out = pathlib.Path(a.claude_ads), pathlib.Path(a.site), pathlib.Path(a.out)

    brand = build_brand(site)
    brief = build_brief()

    for name, contract, payload in (
        ("brand/brand-profile.json", "brand-profile", brand),
        ("creative/creative-brief.json", "creative-brief", brief),
    ):
        validate(contract, payload, ca)          # raises on any contract violation
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"validated + wrote {p}")

    # Copy-deck render: character counts are MEASURED, not assumed.
    lines = ["# ZeroVast / NEZAAD — copy deck", "",
             f"Run `{RUN_ID}` · generated {CREATED_AT} · human review: **pending**", "",
             "Character counts are measured on the string below. claude-ads ships no",
             "frozen platform limits on purpose — its contracts require the current",
             "official spec per placement — so any limit column here would be invented.", ""]
    for h in brief["hypotheses"]:
        lines += [f"## {h['id']} — {h['insight'][:70]}…" if len(h['insight']) > 70
                  else f"## {h['id']}", "", f"**Hook:** {h['hook']}", "",
                  f"**Promise:** {h['promise']}", "", f"**CTA:** {h['cta']}", "",
                  f"**Hypothesis:** {h['experiment_hypothesis']}", ""]
        for c in [c for c in brief["copy_deck"] if c["hypothesis_id"] == h["id"]]:
            lines += [f"### {c['platform']} · {c['placement']}", "",
                      "| field | chars | copy |", "|---|---|---|"]
            for f in c["fields"]:
                v = f["value"].replace("|", "\\|")
                lines.append(f"| `{f['name']}` | {len(f['value'])} | {v} |")
            lines.append("")
    (out / "creative").mkdir(parents=True, exist_ok=True)
    (out / "creative" / "copy-deck.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote creative/copy-deck.md")


if __name__ == "__main__":
    main()
