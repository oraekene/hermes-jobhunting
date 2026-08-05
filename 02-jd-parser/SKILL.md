---
name: job-hunting-jd-parser
description: "Parse a job posting URL or text into structured fields"
metadata:
  hermes:
    tags: [job-hunting, jd-parser]
    category: job-hunting
    related_skills:
      - job-hunting-discovery
      - job-hunting-resume-match
      - job-hunting-keyword-analysis
---

# Job Description Parser

## When this skill applies

Use this skill to extract and structure the full content of a job posting (from a URL or pasted text) into a standard analysis format — company, role, requirements, culture signals, stated values. Triggers: 'parse this job posting', 'analyze this JD', a pasted job description, or being handed a posting by 01-job-discovery. Do NOT use this for scoring how well Kene's resume matches (that's 03-resume-match) or for extracting ATS keywords (that's 04-keyword-analysis) — this skill only structures the raw posting.

Origin: Kene's original "Chat 1." Unchanged in substance — the thread
didn't touch this stage — but it now explicitly extracts the fields the
later, thread-derived stages need.

## Process

1. If given a URL, fetch it. If a plain fetch fails (many ATS platforms
   and job boards run behind Cloudflare or basic anti-bot checks) and
   the optional `research/scrapling` skill (stealth browsing, Cloudflare
   bypass) is installed, retry with that before giving up. Only ask
   Kene to paste the text once both have been tried — don't guess at
   posting content.

   **If given a PDF, read it — do not ask for a paste.** Real hunts
   involve PDF job descriptions constantly: recruiters attach them,
   companies publish specs as PDFs, and internal postings arrive as
   email attachments. The bundled `productivity/ocr-and-documents` skill
   handles this (`pymupdf` for text-layer PDFs, `marker-pdf` for scanned
   ones). Until now the pipeline had no route for a PDF at all — the
   only fallback was asking Kene to retype a document he already has,
   which is exactly the manual step this pipeline exists to remove.

   Order matters: try the text layer first, since it is fast, exact, and
   preserves the structure that step 2 depends on. Fall back to OCR only
   when the text layer is empty or garbled — OCR output is
   approximate, and an approximate requirement list feeds an approximate
   keyword analysis. When OCR was used, **say so in the output**, so a
   thin extraction reads as a extraction problem rather than as a thin
   posting.
2. Extract and structure:
   - Company name, role/title, location, recruiter email if listed
   - Required skills, sorted by apparent importance
   - Required experience level and education
   - Nice-to-have qualifications
   - Key responsibilities
   - **Stated company values** (verbatim list, if the posting names any —
     e.g. "Bold, Credible, Human, Together"). This feeds `06-cover-letter`
     and `05-resume-customizer`'s values-alignment section directly.
   - **Section headers used in the posting** (e.g. "Data Strategy &
     Leadership," "What You'll Do"). Feeds the structure-mirroring step
     in `05-resume-customizer`.
   - `posted_at` timestamp if the board shows one — feeds the speed
     priority logic in `01-job-discovery` / `00-orchestrator`.
3. Analyze:
   - Critical vs. optional requirements
   - Priority score per requirement (High/Medium/Low)
   - Unusual or unique requirements — flag these explicitly
   - Implied skills not directly stated but likely needed
4. Output structured markdown, ready to hand to `03-resume-match` and
   `04-keyword-analysis` without reformatting.

## Note on ATS platform

If the posting is on a recognizable ATS (Greenhouse, Workable, Lever,
Workday, etc.), record which one — `10-approval-and-submit` needs this to
know what the application form will look like.
