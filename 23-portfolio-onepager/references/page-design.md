# Page design

The reasoning behind `assets/portfolio-template.html`. Read this before
changing it, so a change is a decision rather than a drift.

## The brief

One page. The reader arrives from a link — a cold email, a CV, a social
bio — usually knowing nothing, often with no role in mind. **Its single
job is to get them from "who is this" to clicking one artifact in under
sixty seconds.**

Everything below follows from that. It is not a personal site, not a
blog, not a CV in HTML.

## The signature: the receipt rail

Each work item is a two-column grid — a narrow left rail carrying an
index and a vertical hairline, and the claim on the right with its
artifact links attached directly beneath.

This encodes the page's actual thesis. A CV can only assert; a portfolio
can show, and that difference is the reason to build one at all. So the
layout makes "nothing asserted without something attached" visible: the
rail runs the height of the item and closes under the artifacts, which
reads as a receipt stapled to a claim rather than a card with links in
its footer.

It is also the only bold move on the page. Everything else is quiet by
design — a page whose job is to make artifacts clickable should not
compete with them.

**If a work item has no artifacts**, the receipt rail is visibly empty and
the item looks weaker than the ones around it. That is correct and
deliberate. It is the page telling Kene something true, and it is a
better prompt than a warning in a log.

## Palette

| Token | Value | Why |
|---|---|---|
| `--ground` | `#F1F0EC` | Warm-neutral pushed toward grey. Deliberately *not* the near-`#F4F1EA` cream that has become the default AI-generated background. |
| `--ink` | `#16181D` | Slightly blue-black. Reads cleaner than pure black on a warm ground. |
| `--accent` | `#1B4D3E` | Deep forest. Structural, used on rules, capability labels and hover states — never as a decorative wash. Chosen against the terracotta/clay accent that pairs with the cream default and now reads as a tell. |
| `--live` / `--dead` | greens/red | **Functional only.** These appear on artifact status dots and nowhere else. Colour that means something outranks colour that decorates. |

Dark mode via `prefers-color-scheme`, with the accent lightened to hold
contrast rather than the palette simply inverted.

## Type

Three faces, three jobs:

- **Fraunces** (display) — name and item titles. Variable, with optical
  sizing and its `WONK` axis on at display size. Characterful without
  being a costume, and not the Playfair/Instrument Serif that any
  "professional but warm" brief lands on by default.
- **Public Sans** (body) — open, plain, and legible at 17px. Chosen over
  Inter because Inter is the reflexive answer and is on a large share of
  the pages this one sits alongside.
- **JetBrains Mono** (utility) — indices, dates, artifact type labels,
  the footer, and the figure in each result.

**The mono face is doing real work, not adding texture.** It marks
everything that is *data* — a period, a URL, a number — and separates it
from everything that is *claim*. That distinction is the page's content
model, so it earns a typeface.

The one place mono touches prose is the result figure, which gets a
tinted background. On a page built to make numbers verifiable, the number
should be the thing your eye lands on.

## Layout

Single column, `66ch` measure. No grid of cards, no sidebar, no hero
image.

A card grid is the default for anything called a portfolio, and it is
wrong here: cards imply parallel items to browse and this page has an
*argument* with an order. The manifest's ordering is meaningful and a
grid would throw it away.

Scroll depth is fine. A reader who scrolls is engaged; a reader who has
to click into a sub-page to see the work is one who leaves.

## Details that matter more than they look

- **`scroll-margin-top` on items.** Cold outreach deep-links to
  `#item-slug`. Without this the anchor lands with the heading flush
  against the viewport edge and looks broken.
- **Stable anchors.** Once a variant is published, item `id`s do not
  change. Links already sent keep working only if they don't.
- **Open Graph tags.** This URL gets pasted into DMs and Slack, and the
  preview card is the first thing many readers see. It is content.
- **A print stylesheet, with URLs expanded.** Someone will print this,
  usually a recruiter, and a printed link is dead unless its href is
  written out. Items avoid breaking across pages.
- **Dead links stay visible**, in red. The alternative — dropping them —
  means the page quietly gets weaker with nobody noticing. Better to see
  the failure.
- **No JavaScript.** Nothing here needs it. A page that works with JS
  disabled, on a slow connection, in a preview pane, and in Reader mode
  is more robust than one that animates.

## Editing it

Kene will want to change a line without regenerating, and that is
expected — the file is plain HTML with no build step for exactly this
reason.

Two things to preserve when editing by hand:

1. **Don't add a second accent colour.** The restraint is what makes the
   forest green mean something. A second accent turns both into
   decoration.
2. **Don't let an item exceed roughly six lines of body text.** Past
   that, the reader stops reading and the artifacts stop getting clicked,
   which is the only outcome this page is optimising for.

Regenerating a variant preserves hand edits to copy where it can and says
plainly what it could not preserve. It never silently overwrites a line
Kene wrote.
