# Anti-Slop Checklist — Cover Letters & Application Answers

A companion to the bundled `creative/humanizer` skill referenced in
`06-cover-letter/SKILL.md`'s Process and `08-application-qa/SKILL.md`'s
Process: humanizer catches general LLM phrasing tells across any text;
this file is the job-application-specific list on top of that — the
clichés a recruiter reading 40 cover letters a day has seen so many
times they've stopped registering as words. Run down this list on the
finished draft, same phase as the humanizer pass, not as a separate step.

## Openers to never use

If the first sentence could be pasted into any cover letter for any
company, it isn't doing its job. Specifically banned, no exceptions:

- "I am writing to express my interest in..."
- "I am excited to apply for..." / "I was thrilled to see..."
- "With # years of experience in..."
- "As a highly motivated [role] professional..."

Test: could this sentence survive with the company/role name deleted and
still read as generic praise? If yes, rewrite it around something only
true of *this* posting — something `02-jd-parser` or
`12-company-research` actually surfaced, not a category the role belongs
to.

## Closers to never use

- "I look forward to the opportunity to discuss further."
- "Please don't hesitate to contact me."
- "I am confident that I would be a great fit / valuable asset to your
  team."
- "Thank you for your time and consideration."

These aren't wrong so much as weightless — they say nothing an
application form doesn't already imply. Close on the specific thing this
letter argued, not on a formality.

## Self-description words that replace evidence instead of pointing to it

The tell isn't the word itself, it's using it *in place of* the concrete
example the STAR bank already has. If one of these appears with no
adjacent number, project name, or outcome within the same sentence,
that's the signal to go find the concrete version instead:

`results-driven` · `proven track record` · `team player` · `go-getter` ·
`detail-oriented` · `hardworking` · `passionate about` ·
`self-starter` · `strategic thinker` · `dynamic` · `hit the ground
running`

Every one of these has a concrete version already sitting in
`memory/star-story-bank.md` — say the thing, not the label for the
thing. ("Results-driven" → "cut deploy time from 40 minutes to 6.")

## Structural tells

- **The three-adjective sentence.** "A collaborative, innovative, and
  detail-oriented professional" — three vague adjectives in a row is
  almost always a sign the sentence has no actual content yet. Pick the
  one true thing and say it plainly.
- **Symmetric paragraph openers.** If paragraph 2 and paragraph 3 both
  start "In my role at X, I..." the letter reads templated even if the
  content isn't. Vary the entry point.
- **The em-dash pileup.** One well-placed em-dash reads natural. Three in
  one paragraph reads like a pattern, not a voice.
- **Over-qualifying every claim.** "This experience has helped equip me
  with the skills necessary to potentially contribute..." — say what
  happened, not a hedge about what it might enable.

## Structural bans — the constructions, not the words

The lists above ban specific phrases. These ban shapes, which is what
survives a find-and-replace and is the reason text still reads as
generated after every banned word is gone.

**Rhetorical scaffolding**

- **No antithesis.** "Not X, but Y." The shape performs insight without
  supplying any.
- **No corrective negation.** "It isn't about the tools — it's about the
  thinking." Setting up a wrong idea to knock down is filler.
- **No negative parallelism, no negative anaphora.** "No meetings. No
  process. No excuses." Rhythm standing in for content.
- **No contrasting pairs.** Not every idea has an opposite worth naming.
- **No rule of three.** Three examples because three sounds complete is
  padding. Use the number of examples you have.
- **No setup/payoff.** A sentence that exists to make the next one land
  is a sentence with nothing in it.
- **No landing sentences.** The short closer that restates the paragraph
  with gravitas. Stop when the point is made.
- **No summary beats.** Do not tell the reader what they just read.

**Sentence and paragraph mechanics**

- **No paragraph pinning.** Every paragraph opening on the same
  structural note.
- **No parallel structures inside a paragraph.** Three sentences with
  the same shape reads as a template.
- **No parataxis.** Stacked short declaratives for effect. "We shipped.
  It worked. They noticed."
- **Vary sentence length unpredictably.** Not long-short-long — that is
  its own pattern. Unpredictably.
- **No stacked noun phrases.** "Cross-functional stakeholder alignment
  strategy" is four nouns pretending to be a thing.
- **No em dashes.** Comma, full stop, or restructure.
- **No throat-clearing openers.** Start at the first real word.

**Word-level**

- **No filler intensifiers** — genuinely, really, truly, actually. If
  the sentence needs one, the sentence is weak.
- **No corporate-register verbs** — leverage, underscore, reflect,
  showcase, spearhead, drive, enable, facilitate.
- **No nominalization.** "Made a decision" is "decided". "Provided
  assistance" is "helped".
- **No hedging qualifiers** — somewhat, arguably, fairly, quite,
  relatively — unless the hedge is the actual claim.
- **No performed enthusiasm.** Excitement you do not have reads as sales
  copy. This is the one most cover letters fail.

**Write for the spoken voice.** The test: read it aloud. Anything you
would not say to someone across a table comes out.

### Why this list runs before the humanizer, not after

`humanizer` is a *phrasing* pass — it rewrites what is already there.
Generate against these rules and there is less to rewrite, and the
rewrite is less likely to reintroduce a banned shape while fixing a
banned word. Running it the other way round means humanizing text built
on scaffolding, which produces fluent scaffolding.

Order, in both `05` and `06`:

1. Draft **against** this list.
2. `humanizer` pass for anything the draft still carries.
3. Check the result against this list again — the humanizer is a general
   skill and does not know these specific bans.

Step 3 is not optional and is the step most likely to be skipped.

## Quick gut-check before handoff

Read the closing paragraph out loud. If it sounds like something Kene
would actually say to a person, not recite from a template, it's ready
for `09-risk-tactics-gate`. If it sounds like every other cover letter
this recruiter opened today, it isn't — go back to the STAR bank for
something more specific, not to the thesaurus for a fancier synonym.
