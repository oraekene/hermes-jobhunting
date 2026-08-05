# Legal — a starting point, not final text

**I am not a lawyer and this is not legal advice.** Everything below is a draft
to take to one. Under Nigerian law a competent commercial lawyer will review
this for a few hours' fee, and at ₦35,000 a sale the review pays for itself the
first time someone disputes anything.

I flagged this layer as "genuinely good news" early on and then wrote nothing
for the rest of the build. That was the wrong order. **Watermarking tells you
who leaked a copy; copyright is what lets you do anything about it.** One
without the other is forensics with no remedy.

---

## 1. What you already own

**Copyright is automatic.** Under the Nigerian Copyright Act 2022 your skill
files, prompts, schemas and code are protected from the moment they are fixed in
tangible form. No registration is required for the right to exist.

**Registration with the Nigerian Copyright Commission is evidential, not
constitutive.** It does not create the right; it gives you a dated official
record, which is what makes enforcement practical rather than theoretical. Worth
doing before launch, not after a dispute.

**Building on Hermes does not oblige you to open-source anything.** The MIT
licence is permissive, not copyleft — no share-alike obligation attaches to your
own work. This is the genuinely good news, and it is why the whole proprietary
model is available to you at all.

Two obligations that do attach, and they are small: reproduce the MIT notice for
components you redistribute, and keep an inventory of every third-party
dependency and its licence. Add the inventory to your build now, while it is
five entries, rather than at fifty.

---

## 2. Draft EULA — clause outline

Written to match what the software actually does. Where a clause corresponds to
a mechanism, the mechanism is named so your lawyer can check the two agree.

**Licence grant.** A perpetual, non-exclusive, non-transferable licence to one
named individual for personal use. Perpetual matters: you sell lifetime access,
so the grant must not read as a subscription that lapses.

**Seats and machines.** One seat. Reasonable self-service moves between machines
— three a year, matching `REBIND_ALLOWANCE`. Say the number in the terms; a
limit the customer discovers only when they hit it feels like a trick.

**What they may not do.** Redistribute, resell, sublicense, publish the files, or
remove identifying markers. Say plainly that each copy carries markers
identifying the licensee, because a stated deterrent works and a secret one only
produces an awkward conversation later.

**Reverse engineering.** Prohibited except where local law grants a right that
cannot be contracted away. Do not overreach here — an unenforceable clause makes
the rest of the document look drafted rather than considered.

**Their data is theirs.** Their resume, memory, journal, applications and
outputs are their property, held on their machine, and you claim no rights over
any of it. State it explicitly. It is true, it is a selling point, and it is the
clause a cautious buyer looks for.

**Telemetry.** Aggregate counts only. No documents, no employer names, no text
they wrote. Opt-out available. Point at the staged-payload table they can read
before anything is sent — a promise you can demonstrate is worth more than one
you assert.

**The service component.** Licence checks and the shared learning ledger are
services, provided on reasonable endeavours, not guaranteed in perpetuity. The
software continues to function without them. **Be honest that "lifetime" covers
the software, not an eternal server commitment**, and say what happens if you
ever stop: the tool keeps working on local evidence alone, which is true and is
how it is built.

**Automated sending — the clause the permission design requires.** The user is
the applicant of record for everything sent from their account. Where they
switch off a confirmation, they accept responsibility for what goes out. This
must mirror `gates.yaml` exactly: applications, messages, connection requests,
public posts and profile edits. Reference the two gates that can never be
switched off and why, because a term that says "you accepted everything" when
the software demonstrably refuses some things reads as boilerplate.

**No employment outcome is promised.** Obvious to you; not to everyone. Say it.

**Refunds.** Fourteen days, no questions. This is commercial self-interest
before it is generosity: a refund costs $1 and a chargeback costs $30, which is
1.9× a ₦25,000 addon sale. Make the refund route easier to find than the
dispute route.

**Termination.** For breach — sharing, chargeback fraud, circumvention. Say what
happens to their data on termination: it stays on their machine and remains
readable. You are withdrawing a licence, not confiscating someone's job search.

**Governing law.** Nigerian, with courts in your state.

---

## 3. Privacy notice — required separately

You are a data controller under the **Nigeria Data Protection Act 2023** for
customer names, emails and payment references, and you have obligations
regardless of what the EULA says. Ask your lawyer about registration thresholds
with the NDPC — they turn on data volume and processing type, and both change.

The architecture already puts you in a good position, and the notice should say
so plainly:

- **Two databases that are never joined.** Licensing holds identity; the ledger
  holds pseudonymous counts. The only shared value is a random `node_id`.
- **A deletion request is executable** precisely because the ledger holds no
  personal data at all. Most companies cannot say this.
- **Application data never leaves the user's machine.**

Write the notice to describe the architecture rather than to obtain broad
consent. It is shorter, it is true, and it is checkable.

---

## 4. What to do, in order

1. **NCC registration** — dated record of authorship, before launch.
2. **Lawyer review** of the EULA outline and the privacy notice together. A few
   hours' fee.
3. **Dependency licence inventory** in the build, while it is small.
4. **Publish the terms at a stable URL** and link them from checkout. A term
   nobody was shown is a term you cannot rely on.
5. **Ask specifically about the automated-sending clause.** It is the one with
   real exposure — an application sent under a customer's name, with a claim
   they did not read, to an employer who may act on it. Your gates make that
   hard by design; the terms need to reflect that they exist and that switching
   them off is a deliberate act with a recorded audit trail.

---

## 5. What I would not spend money on

**Trademark registration before launch.** Useful once the name has value, an
expense before it does.

**Patents.** Nothing here is patentable and the process would cost more than the
product earns.

**Aggressive enforcement.** When the watermark identifies a leaker, the first
move is a polite message. Someone who shared a copy is still a customer, and at
your scale the relationship is worth more than the sale. Keep the legal remedy
in reserve for a competitor redistributing commercially — which is the only
case where it earns its cost.
