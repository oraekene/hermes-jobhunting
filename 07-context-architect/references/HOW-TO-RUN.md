# How to Actually Run This, Start to Finish

Everything below runs from the Hermes box (Oracle Cloud) or your
laptop — anywhere with real internet access, not from a chat tool. You
can either type these commands yourself over SSH, or just tell Hermes
"run the question bank crawler" and hand it this file — it can execute
every step here directly.

## Step 0 — one-time setup

```bash
cd ~/.hermes/skills/job-hunting/07-context-architect/reference
pip install requests pyyaml --break-system-packages
pip install scikit-learn --break-system-packages   # optional but recommended —
                                                     # better paraphrase clustering
cp ../templates/seed_companies.yaml seed_companies.yaml
```

Open `seed_companies.yaml` and expand it — the example ships with 6
companies as a *format* reference, not a real seed list. Fifteen to
twenty-five companies per batch, spread deliberately across the tag
matrix in `question-bank-pipeline.md`, is a reasonable starting size.
Where to find slugs: a Greenhouse board's slug is the path segment in
`boards.greenhouse.io/<slug>`; Lever's is in `jobs.lever.co/<slug>`.

## Step 1 — three crawl batches

```bash
# Batch 1
python question_bank_crawler.py crawl \
  --seed seed_companies.yaml \
  --limit 100 \
  --out question_bank_raw.jsonl

# Expand seed_companies.yaml with new companies (rotate in
# underrepresented tag cells — check what batch 1 skewed toward),
# then:

# Batch 2
python question_bank_crawler.py crawl \
  --seed seed_companies.yaml \
  --limit 100 \
  --out question_bank_raw.jsonl \
  --skip-crawled

# Expand again, then:

# Batch 3
python question_bank_crawler.py crawl \
  --seed seed_companies.yaml \
  --limit 100 \
  --out question_bank_raw.jsonl \
  --skip-crawled
```

`--skip-crawled` means each batch only hits *new* company slugs — by
batch 3, `question_bank_raw.jsonl` has ~300 rows spanning whatever
spread you built into the seed list across the three rounds. This is
the only genuinely manual/judgment-requiring part of the whole
process — the crawling and clustering are mechanical, but *which
companies to add* between batches benefits from you noticing "batch 1
was all US tech, let me add some healthcare and some Nigerian
fintech."

## Step 2 — curate down to the live bank

```bash
python question_bank_crawler.py curate \
  --raw question_bank_raw.jsonl \
  --top 100 \
  --out ../shared/question_bank.yaml
```

## Step 3 — the one human pass

Open `shared/question_bank.yaml` and read through it once. You're
checking for: questions that got mis-clustered (two genuinely different
questions collapsed into one canonical form — rare, but check), tags
that look wrong, and anything you'd rather not have in the bank at all
(delete the entry). This is the only manual review step in the whole
pipeline — after this, `07-context-architect` Phase 1.5 reads the file
and starts using it.

## Step 4 — tell Hermes it exists

Nothing to configure — `07-context-architect` already reads
`shared/question_bank.yaml` if present. Just run the context-architect
skill (or wait for it to trigger on the next relevant flow) and Phase
1.5 will start cross-referencing it automatically.

## Total time cost

Realistically: 20–40 minutes of your own attention (writing the seed
list across three rounds, one read-through of the final 100), plus
however long the crawler itself takes running in the background
(mostly rate-limit sleep time — with the default 1-second delay and
~25 postings capped per company, expect roughly 5–15 minutes of wall
-clock crawl time per batch depending on seed list size, not compute-
bound).

See `bank-refresh-automation.md` for keeping this fresh afterward
without repeating the full process from scratch every time.
