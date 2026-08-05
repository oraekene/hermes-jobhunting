#!/usr/bin/env python3
"""
build_docs.py — render the user manual from the registries.

The manual you said you wanted: not dry feature descriptions, but worked
demonstrations of what actually happens. That is now mechanical, because the
demonstrations already exist as data — flows.yaml carries a `doc` scenario per
flow, and gates.yaml and settings.yaml each carry panel.when_on/when_off.

So the manual is GENERATED, never hand-written. Three consequences worth the
constraint:
  * it cannot drift from the package, because it is built from the same files
    the checkers validate
  * translation later is one pass over the registries, not a rewrite
  * obscuring internals is enforceable — leak_check() below fails the build if
    an internal name reaches user-facing prose

    python3 build_docs.py            # writes user-manual.html
"""
import html, re, sys, yaml

# Names a user must never see. Skill directory ids, file paths, gate ids,
# table names. The manual describes what happens, never what it is called.
LEAK = re.compile(
    r"(\b\d{2}-[a-z][a-z0-9-]{3,}\b"          # 05-resume-customizer
    r"|\bGATE-[A-Z-]+\b"                       # GATE-SUBMIT-APPLICATION
    r"|\bFLOW-[A-Z]\d+\b"                      # FLOW-B1
    r"|\b[a-z][a-z0-9_-]*\.(yaml|md|sql|py|db)\b"   # target-profile.yaml
    r"|\bRule \d+\b"                           # Rule 1
    r"|\bapplications\.db\b"
    r"|\bskill_manage\b|\bwrite_approval\b)")

# Plain-language replacements for the handful of internal terms that legitimately
# need to appear in user prose.
SOFTEN = [
    (r"\bSTAR (story )?bank\b", "story bank"),
    (r"\bTelegram approval message\b", "the approval message"),
    (r"\bapproval message\b", "the approval message"),
    (r"\bcron\b", "on a schedule"),
    (r"\bATS\b", "applicant tracking system"),
]

FAMILY_TITLE = {
    "setup":     ("Getting started",        "What happens the first time you run it."),
    "core":      ("Applying for jobs",      "The main loop, from a posting appearing to an application going out."),
    "outreach":  ("Reaching people directly", "For roles that were never advertised."),
    "interview": ("Interviews and offers",  "From the invite arriving to the decision."),
    "direction": ("Working out what to aim at", "When the question is which job, not which application."),
    "assets":    ("Your public presence",   "Portfolio, profile, and what you choose to share."),
    "learning":  ("How it improves",        "What changes over time, and what you approve first."),
    "failure":   ("When something goes wrong", "The situations you will actually hit, and what happens in each."),
}


def soften(text: str) -> str:
    for pat, rep in SOFTEN:
        text = re.sub(pat, rep, text)
    return " ".join(text.split())


def leak_check(label, text, leaks):
    for m in LEAK.finditer(text):
        leaks.append((label, m.group(0), text[:70]))


def esc(s):
    return html.escape(s, quote=False)


def main():
    flows = yaml.safe_load(open("flows.yaml"))
    gates = yaml.safe_load(open("gates.yaml"))
    sets_ = yaml.safe_load(open("settings.yaml"))

    leaks = []
    parts = []

    # ── demonstrations, one section per family ───────────────────────────────
    for fam, (title, blurb) in FAMILY_TITLE.items():
        fl = [f for f in flows["flows"] if f["family"] == fam]
        if not fl:
            continue
        parts.append(f'<section><h2>{esc(title)}</h2><p class="lede">{esc(blurb)}</p>')
        for f in fl:
            body = soften(f["doc"])
            leak_check(f["id"], body, leaks)
            parts.append('<article class="demo">')
            parts.append(f'<h3>{esc(f["name"])}</h3>')
            trig = soften(f["trigger"]["detail"])
            leak_check(f["id"] + "/trigger", trig, leaks)
            parts.append(f'<p class="trigger">{esc(trig)}</p>')
            parts.append(f"<p>{esc(body)}</p>")
            if f.get("variants"):
                parts.append('<ul class="variants">')
                for v in f["variants"]:
                    eff = soften(v["effect"])
                    leak_check(f["id"] + "/variant", eff, leaks)
                    parts.append(f'<li><b>{esc(v["name"])}</b> — {esc(eff)}</li>')
                parts.append("</ul>")
            parts.append("</article>")
        parts.append("</section>")

    # ── what you approve: gates, both sides ──────────────────────────────────
    CLASS_TITLE = {
        "irreversible_external": ("Things that cannot be undone",
            "A real thing happens to someone else. You can switch these off, but "
            "it takes a deliberate step and it expires."),
        "reversible_external": ("Things that reach outside",
            "Undoable or low-stakes. Switch these off freely."),
        "reversible_internal": ("Things that change your own setup",
            "Writes to your own files and memory."),
    }
    parts.append('<section><h2>What you get asked, and what happens if you stop being asked</h2>')
    parts.append('<p class="lede">Every one of these is a point where the tool stops '
                 'and waits for you. Each shows what happens either way.</p>')
    for cls, (title, blurb) in CLASS_TITLE.items():
        gl = [g for g in gates["gates"] if g["class"] == cls]
        parts.append(f'<h3>{esc(title)}</h3><p class="lede">{esc(blurb)}</p>')
        for g in gl:
            on = soften(str(g["panel"]["when_on"]))
            off = soften(str(g["panel"]["when_off"]))
            leak_check(g["id"], on, leaks)
            leak_check(g["id"], off, leaks)
            locked = "" if g.get("toggleable") else ' <span class="lock">always on</span>'
            parts.append(f'<article class="panel"><h4>{esc(g["label"])}{locked}</h4>')
            parts.append(f'<div class="side on"><span>On</span><p>{esc(on)}</p></div>')
            parts.append(f'<div class="side off"><span>Off</span><p>{esc(off)}</p></div>')
            parts.append("</article>")
    parts.append("</section>")

    # ── settings, same treatment ─────────────────────────────────────────────
    parts.append('<section><h2>Settings</h2>')
    for tier, blurb in [("SIMPLE", "Asked during setup. The tool cannot work without these."),
                        ("ADVANCED", "Sensible defaults already. Change them when you have a reason.")]:
        sl = [s for s in sets_["settings"] if s["tier"] == tier]
        parts.append(f'<h3>{esc(tier.title())}</h3><p class="lede">{esc(blurb)}</p>')
        for s in sl:
            on = soften(str(s["panel"]["when_on"]))
            off = soften(str(s["panel"]["when_off"]))
            leak_check(s["key"], on, leaks)
            leak_check(s["key"], off, leaks)
            parts.append(f'<article class="panel"><h4>{esc(s["label"])}</h4>')
            parts.append(f'<div class="side on"><span>Default</span><p>{esc(on)}</p></div>')
            parts.append(f'<div class="side off"><span>Changed</span><p>{esc(off)}</p></div>')
            parts.append("</article>")
    parts.append("</section>")

    n_demo = sum(1 for f in flows["flows"])
    doc = TEMPLATE.replace("__BODY__", "\n".join(parts)) \
                  .replace("__COUNT__", str(n_demo)) \
                  .replace("__GATES__", str(len(gates["gates"]))) \
                  .replace("__SETTINGS__", str(len(sets_["settings"])))
    open("user-manual.html", "w").write(doc)

    print(f"user-manual.html — {n_demo} demonstrations, "
          f"{len(gates['gates'])} decision points, {len(sets_['settings'])} settings")
    if leaks:
        print(f"\n{len(leaks)} internal names reached user-facing prose:")
        seen = set()
        for label, term, ctx in leaks:
            if term in seen:
                continue
            seen.add(term)
            print(f"  {label:<22} {term:<32} …{ctx}…")
        print("\nFAIL — rewrite these before shipping. The manual must describe what "
              "happens, never what it is called.")
        sys.exit(1)
    print("no internal names in user-facing prose")


TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Manual</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,600&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{--paper:#FBF8F3;--ink:#23201C;--soft:#6B635A;--rule:#E0D8CB;
      --on:#3F6B4F;--off:#9A5B3D;--tint:#F3EDE3}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--paper);color:var(--ink);
     font:400 17px/1.65 Newsreader,Georgia,serif;padding:0 24px 100px}
.wrap{max-width:680px;margin:0 auto}
header{padding:72px 0 40px;border-bottom:2px solid var(--ink);margin-bottom:8px}
h1{font-size:44px;line-height:1.05;font-weight:600;letter-spacing:-.02em}
.sub{font:400 15px/1.6 "IBM Plex Sans",sans-serif;color:var(--soft);margin-top:14px}
section{margin-top:56px}
h2{font-size:29px;font-weight:600;letter-spacing:-.01em;padding-bottom:10px;
   border-bottom:1px solid var(--rule)}
h3{font:600 13px/1.4 "IBM Plex Sans",sans-serif;letter-spacing:.1em;
   text-transform:uppercase;color:var(--soft);margin:34px 0 6px}
.lede{color:var(--soft);font-size:16px;margin-bottom:18px}
.demo{margin:26px 0 30px;padding-left:18px;border-left:2px solid var(--rule)}
.demo h3{font:600 20px/1.3 Newsreader,serif;text-transform:none;letter-spacing:0;
         color:var(--ink);margin:0 0 4px}
.trigger{font:400 13px/1.5 "IBM Plex Sans",sans-serif;color:var(--soft);
         margin-bottom:9px}
.trigger::before{content:"▸ "}
.variants{list-style:none;margin-top:12px;font-size:15.5px}
.variants li{padding:4px 0 4px 14px;border-left:1px solid var(--rule);
             margin-bottom:2px;color:var(--soft)}
.variants b{color:var(--ink);font-weight:600}
.panel{margin:22px 0;background:var(--tint);border-radius:3px;padding:16px 18px}
.panel h4{font:600 17px/1.35 Newsreader,serif;margin-bottom:12px}
.lock{font:600 10px/1 "IBM Plex Sans",sans-serif;letter-spacing:.09em;
      text-transform:uppercase;color:var(--off);border:1px solid var(--off);
      padding:3px 6px;border-radius:2px;vertical-align:2px;margin-left:6px}
.side{display:grid;grid-template-columns:74px 1fr;gap:12px;padding:7px 0}
.side+.side{border-top:1px solid var(--rule)}
.side span{font:600 11px/1.7 "IBM Plex Sans",sans-serif;letter-spacing:.09em;
           text-transform:uppercase}
.side.on span{color:var(--on)} .side.off span{color:var(--off)}
.side p{font-size:15.5px;line-height:1.55}
@media(max-width:560px){h1{font-size:34px}.side{grid-template-columns:1fr;gap:2px}}
</style></head><body><div class="wrap">
<header><h1>How this works</h1>
<p class="sub">__COUNT__ worked situations · __GATES__ points where it asks you first ·
__SETTINGS__ settings. Every one shown both ways, so you can see what the choice
actually costs.</p></header>
__BODY__
</div></body></html>"""


if __name__ == "__main__":
    main()
