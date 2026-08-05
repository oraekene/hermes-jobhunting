#!/usr/bin/env python3
"""
build_gepa_golden_set.py — builds golden.jsonl evaluation datasets for
hermes-agent-self-evolution's GEPA skill optimizer, grounded in this
pipeline's own real application outcomes.

See 11-analytics-and-learning/references/gepa-self-evolution.md for the
full picture (what this feeds into, why the deployment step is manual,
and the mandatory safety-constraint patch to apply before running GEPA
on any of these skills at all). This script only builds the dataset —
it does not run any optimization itself, and makes no network or LLM
calls.

Design choices, deliberate:

- Reads ONLY structured columns already in applications.db (company,
  role_title, industry, seniority, remote_type, scores, tactic counts,
  outcome, response_type) — never a raw job-description or resume/cover-
  letter text, because those aren't persisted anywhere in this schema
  (by design — see shared/applications_db_schema.sql), and reconstructing
  or storing verbatim third-party posting text here isn't something this
  script should start doing as a side effect of building an eval set.
  `task_input` is therefore a realistic-but-synthesized prompt built from
  the structured fields, not the original posting.
- `expected_behavior` is built from the SAME application's own recorded
  tactic counts (exact_phrase_count, title_matched, quantified_bullet_count,
  etc.) for applications with a clearly positive outcome — this is what
  makes the resulting golden set "outcome-grounded" rather than a generic
  synthetic guess, even though the tool's own fitness scoring (see the
  reference doc's "the keyword-overlap reality" section) is cruder than
  its documentation implies.
- Requires a minimum sample size (default 12) before writing anything,
  and prints a warning instead of a silent thin dataset — GEPA can
  technically run on 3 examples, but a golden set built from a handful
  of applications is fitting noise, not a real pattern.
"""
import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".hermes" / "skills" / "job-hunting" / "shared" / "applications.db"

# response_type values this pipeline's schema actually uses (see
# shared/applications_db_schema.sql's comment on that column) — treated
# as a clear positive signal worth learning from.
POSITIVE_RESPONSE_TYPES = ("interview_request", "screen_request")

MIN_SAMPLE_SIZE = 12


def fetch_positive_applications(conn: sqlite3.Connection) -> list[dict]:
    placeholders = ",".join("?" for _ in POSITIVE_RESPONSE_TYPES)
    rows = conn.execute(
        f"""
        SELECT company, role_title, industry, seniority, remote_type,
               overall_match_score, keyword_match_score, exact_phrase_count,
               title_matched, title_original, title_displayed,
               values_alignment_included, quantified_bullet_count,
               cover_letter_word_count, recruiter_named, structure_mirrored,
               response_type
        FROM applications
        WHERE response_type IN ({placeholders})
        """,
        POSITIVE_RESPONSE_TYPES,
    ).fetchall()
    columns = [
        "company", "role_title", "industry", "seniority", "remote_type",
        "overall_match_score", "keyword_match_score", "exact_phrase_count",
        "title_matched", "title_original", "title_displayed",
        "values_alignment_included", "quantified_bullet_count",
        "cover_letter_word_count", "recruiter_named", "structure_mirrored",
        "response_type",
    ]
    return [dict(zip(columns, row)) for row in rows]


def _role_context(app: dict) -> str:
    bits = []
    if app.get("seniority"):
        bits.append(app["seniority"])
    bits.append(app.get("role_title") or "the role")
    context = " ".join(bits)
    if app.get("industry"):
        context += f" in the {app['industry']} industry"
    if app.get("remote_type"):
        context += f" ({app['remote_type']})"
    return context


def build_resume_customizer_example(app: dict) -> dict:
    task_input = (
        f"Tailor resume bullets for a {_role_context(app)} posting. "
        f"The role's keyword-match score against Kene's base resume was "
        f"{app.get('keyword_match_score', 'unknown')}."
    )
    expectations = []
    if (app.get("exact_phrase_count") or 0) > 0:
        expectations.append(
            f"mirror exact JD phrasing where evidence supports it "
            f"(this real application used {app['exact_phrase_count']} such phrases)"
        )
    if app.get("title_matched"):
        expectations.append(
            "match the displayed title to the posting's title only when a "
            "genuine equivalence exists, never an unsupported upgrade"
        )
    else:
        expectations.append("keep the original title unchanged when no clear equivalence exists")
    if (app.get("quantified_bullet_count") or 0) > 0:
        expectations.append(
            f"quantify outcomes with specific numbers wherever memory supports one "
            f"(this application quantified {app['quantified_bullet_count']} bullets)"
        )
    if app.get("values_alignment_included"):
        expectations.append("include a brief values-alignment note tied to something Kene has actually done")
    expected_behavior = (
        "A resume tailoring pass that: " + "; ".join(expectations) + ". "
        "This combination of tactics is drawn from a real application that "
        f"received a {app['response_type']} — not a synthetic guess."
    )
    return {
        "task_input": task_input,
        "expected_behavior": expected_behavior,
        "difficulty": "medium",
        "category": app.get("industry") or "general",
        "source": "golden",
    }


def build_cover_letter_example(app: dict) -> dict:
    task_input = (
        f"Write a cover letter for a {_role_context(app)} posting, following "
        f"the 5-paragraph formula (Hook / Technical Match / Story / Why This "
        f"Company / Close)."
    )
    expectations = ["never open with a generic 'I am writing to express my interest' line"]
    if app.get("cover_letter_word_count"):
        expectations.append(
            f"land close to {app['cover_letter_word_count']} words, matching "
            f"what this real, successful application used"
        )
    if app.get("recruiter_named"):
        expectations.append("address the recruiter by name when one was findable")
    if app.get("values_alignment_included"):
        expectations.append("connect a stated company value to something concrete Kene has done")
    expected_behavior = (
        "A cover letter that: " + "; ".join(expectations) + ". Drawn from a real "
        f"application that received a {app['response_type']}."
    )
    return {
        "task_input": task_input,
        "expected_behavior": expected_behavior,
        "difficulty": "medium",
        "category": app.get("industry") or "general",
        "source": "golden",
    }


def build_application_qa_example(app: dict) -> dict:
    task_input = (
        f"Answer a free-text application question for a {_role_context(app)} posting, "
        f"selecting the best-fit STAR story and weaving in relevant keywords."
    )
    expectations = ["write in Kene's own voice, not generic corporate phrasing"]
    if (app.get("exact_phrase_count") or 0) > 0:
        expectations.append("weave in exact JD terminology naturally where a [PASS] tactic supports it")
    if app.get("structure_mirrored"):
        expectations.append("mirror the question's own structure/framing back in the answer")
    expected_behavior = (
        "An application answer that: " + "; ".join(expectations) + ". Drawn from a real "
        f"application that received a {app['response_type']}."
    )
    return {
        "task_input": task_input,
        "expected_behavior": expected_behavior,
        "difficulty": "medium",
        "category": app.get("industry") or "general",
        "source": "golden",
    }


BUILDERS = {
    "05-resume-customizer": build_resume_customizer_example,
    "06-cover-letter": build_cover_letter_example,
    "08-application-qa": build_application_qa_example,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--output-dir", default="./gepa-golden-sets")
    parser.add_argument(
        "--min-sample-size",
        type=int,
        default=MIN_SAMPLE_SIZE,
        help="Refuse to write a dataset with fewer positive-outcome applications than this",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"applications.db not found at {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(db_path))
    applications = fetch_positive_applications(conn)
    conn.close()

    print(f"Found {len(applications)} application(s) with a positive response_type "
          f"({', '.join(POSITIVE_RESPONSE_TYPES)}).")

    if len(applications) < args.min_sample_size:
        print(
            f"Fewer than --min-sample-size ({args.min_sample_size}) qualifying "
            f"applications — refusing to write a golden set that would just be "
            f"fitting noise. Come back once more real outcomes have accumulated.",
            file=sys.stderr,
        )
        return 1

    random.shuffle(applications)
    output_root = Path(args.output_dir)

    for skill_dir, builder in BUILDERS.items():
        examples = [builder(app) for app in applications]
        skill_output = output_root / skill_dir
        skill_output.mkdir(parents=True, exist_ok=True)
        golden_path = skill_output / "golden.jsonl"
        with open(golden_path, "w") as f:
            for ex in examples:
                f.write(json.dumps(ex) + "\n")
        print(f"  Wrote {len(examples)} examples to {golden_path}")

    print(
        "\nDone. See 11-analytics-and-learning/references/gepa-self-evolution.md "
        "for how to point evolve_skill.py at these files, and read the "
        "mandatory safety-constraint section before running it on any of "
        "these skills."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
