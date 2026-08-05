<!-- STATUS: ABSORBED. This file is preserved as a record, not as instructions.
Content lives in 10-approval-and-submit/SKILL.md (site-access model 3 made explicit).
Do not follow it as a procedure; the host file named above is authoritative. -->

# 10-approval-and-submit — Addendum: making an implicit assumption explicit

`10-approval-and-submit`'s form-fill step already has to interact with
an actual application portal to submit anything on Kene's behalf — that
was always implicitly some version of `shared/site-access-model.md`'s
model 3 (Kene's own authenticated session/browser state, driven rather
than independently established by Hermes), since submitting a real
application as Kene requires being *in* whatever account context that
submission expects (an ATS login, an email-linked application flow,
etc.). This addendum doesn't change this skill's behavior — it makes
that assumption a stated fact rather than an unstated one, consistent
with why `site-access-model.md` got written in the first place: several
skills across this package were quietly assuming an access model
without any of them saying so.

No change to Rule 1 or to this skill's own approval-before-submit
discipline — this is purely a documentation correction, not new
behavior.
