# Dependency Graph — job-hunting package

Mechanically extracted from all 171 shipped files. Every edge below traces to a literal string in a file; nothing is inferred.

## What's in the package

| Node type | Count |
|---|---|
| doc | 99 |
| table | 40 |
| skill | 25 |
| cronjob | 24 |
| schema | 21 |
| script | 14 |
| config | 12 |
| area | 6 |
| view | 6 |

| Edge type | Count | Meaning |
|---|---|---|
| references | 1765 | file/skill cites another by name or path |
| touches_table | 286 | names a DB table or view |
| contains | 166 | component owns this file |
| declared_related | 85 | `related_skills:` frontmatter |
| defines | 46 | SQL file creates this table/view |
| schedules | 14 | cron job invokes this skill |
| blueprint | 4 | skill carries a cron blueprint |

## Coupling — every skill, ranked by how connected it is

| Skill | Frontmatter name | Out | In | Cron blueprint |
|---|---|---|---|---|
| `07-context-architect` | job-hunting-context-architect | 38 | 86 | — |
| `09-risk-tactics-gate` | job-hunting-risk-tactics-gate | 18 | 54 | — |
| `11-analytics-and-learning` | job-hunting-analytics | 21 | 44 | 0 8 * * 1 |
| `01-job-discovery` | job-hunting-discovery | 23 | 41 | 0 7,10,13,16,19,22 * * 1-6 |
| `14-social-discovery-outreach` | job-hunting-social-discovery-outreach | 23 | 40 | — |
| `05-resume-customizer` | job-hunting-resume-customizer | 19 | 40 | — |
| `16-career-pulse` | job-hunting-career-pulse | 22 | 36 | — |
| `17-cold-prospecting` | job-hunting-cold-prospecting | 22 | 36 | — |
| `10-approval-and-submit` | job-hunting-approval-submit | 14 | 42 | — |
| `06-cover-letter` | job-hunting-cover-letter | 15 | 37 | — |
| `19-career-path-planner` | job-hunting-career-path-planner | 26 | 25 | — |
| `00-orchestrator` | job-hunting-orchestrator | 26 | 24 | 30 7,10,13,16,19,22 * * 1-6 |
| `12-company-research` | job-hunting-company-research | 15 | 34 | — |
| `08-application-qa` | job-hunting-application-qa | 14 | 34 | — |
| `13-interview-prep` | job-hunting-interview-prep | 24 | 24 | 0 9,15 * * 1-6 |
| `21-output-templates` | job-hunting-output-templates | 21 | 22 | — |
| `03-resume-match` | job-hunting-resume-match | 17 | 22 | — |
| `02-jd-parser` | job-hunting-jd-parser | 10 | 28 | — |
| `22-contact-enrichment` | job-hunting-contact-enrichment | 17 | 21 | — |
| `20-interests-profile` | job-hunting-interests-profile | 17 | 20 | — |
| `23-portfolio-onepager` | job-hunting-portfolio-onepager | 22 | 6 | — |
| `18-skill-composer` | job-hunting-skill-composer | 18 | 8 | — |
| `04-keyword-analysis` | job-hunting-keyword-analysis | 8 | 11 | — |
| `24-linkedin-profile-optimizer` | job-hunting-linkedin-profile-optimizer | 16 | 2 | — |
| `onboarding` | job-hunting-onboarding | 12 | 1 | — |

## Shared surface — files depended on by the most components

Anything high in this table is a change-blast-radius risk and an addon-compatibility boundary.

| File | Depended on by |
|---|---|
| `shared/target-profile_yaml.template` | 53 |
| `07-context-architect/references/title-taxonomy.md` | 24 |
| `cron/cron-jobs.md` | 24 |
| `shared/dynamic-target-calibration_yaml.template` | 23 |
| `shared/pipeline-rules.md` | 22 |
| `templates/domain-knowledge.md` | 22 |
| `shared/applications_db_schema.sql` | 21 |
| `14-social-discovery-outreach/references/cold-dm-email-schema.md` | 19 |
| `shared/pitch-catalog_yaml.template` | 18 |
| `shared/site-access-model.md` | 18 |
| `14-social-discovery-outreach/references/platform-capability-matrix.md` | 17 |
| `shared/output-templates_yaml.template` | 17 |
| `onboarding/references/starting-out-track.md` | 15 |
| `security/security-setup.md` | 15 |
| `templates/star-story-bank.md` | 15 |
| `07-context-architect/references/voice-interview-mode.md` | 14 |
| `shared/enrichment-tier-usage_yaml.template` | 14 |
| `07-context-architect/references/gap-analysis-engine.md` | 13 |
| `shared/pipeline-rules-addendum.md` | 13 |
| `07-context-architect/references/content-model-overlap.md` | 12 |

## Database surface

40 tables and 6 views, defined across 21 SQL files.

| Table/view | Defined in | Written/read by |
|---|---|---|
| `below` | `applications_db_schema.sql` | 73 |
| `applications` | `applications_db_schema.sql` | 49 |
| `social_outreach` | `applications_db_schema_addendum.sql` | 17 |
| `career_journal` | `applications_db_schema_addendum.sql` | 13 |
| `career_path_plans` | `applications_db_schema_addendum_4.sql` | 12 |
| `open_gaps` | `applications_db_schema.sql` | 10 |
| `email_insights` | `applications_db_schema.sql` | 9 |
| `skill_self_edits` | `applications_db_schema.sql` | 8 |
| `profile_monitor_events` | `applications_db_schema_addendum.sql` | 6 |
| `career_path_plan_roadmap_items` | `applications_db_schema_addendum_4.sql` | 6 |
| `interview_debrief` | `applications_db_schema_addendum.sql` | 5 |
| `career_path_plan_progress` | `applications_db_schema_addendum_3.sql` | 5 |
| `career_path_plan_reevaluations` | `applications_db_schema_addendum_4.sql` | 5 |
| `posting_sources` | `applications_db_schema_addendum_8.sql` | 5 |
| `v_cost_per_outcome` | `applications_db_schema_addendum_10.sql` | 4 |
| `pipeline_pause` | `applications_db_schema_addendum_13.sql` | 4 |
| `seniority_floor` | `applications_db_schema_addendum_13.sql` | 4 |
| `portfolio_artifacts` | `applications_db_schema_addendum_18.sql` | 4 |
| `career_path_plan_stepping_stones` | `applications_db_schema_addendum_4.sql` | 4 |
| `career_path_plan_roadmap_item_history` | `applications_db_schema_addendum_4.sql` | 4 |
| `career_path_plan_paths` | `applications_db_schema_addendum_14.sql` | 3 |
| `career_path_plan_hop_gaps` | `applications_db_schema_addendum_14.sql` | 3 |
| `fact_influence` | `applications_db_schema_addendum_17.sql` | 3 |
| `cron_executions` | `applications_db_schema_addendum_20.sql` | 3 |
| `schema_version` | `applications_db_schema_addendum_7.sql` | 3 |

## Findings worth acting on

### 1. Twenty declared relations that appear nowhere in the skill body

`related_skills:` frontmatter that no prose in that file actually references. Either the relation is real and undocumented, or the metadata is stale. Each one needs a decision before the manifest is written, because addon compatibility will be computed from this metadata.

- `01-job-discovery` declares `14-social-discovery-outreach`
- `04-keyword-analysis` declares `02-jd-parser`
- `05-resume-customizer` declares `21-output-templates`
- `06-cover-letter` declares `08-application-qa`
- `10-approval-and-submit` declares `00-orchestrator`
- `11-analytics-and-learning` declares `00-orchestrator`, `16-career-pulse`
- `12-company-research` declares `01-job-discovery`, `17-cold-prospecting`
- `13-interview-prep` declares `11-analytics-and-learning`
- `14-social-discovery-outreach` declares `17-cold-prospecting`
- `16-career-pulse` declares `11-analytics-and-learning`, `20-interests-profile`
- `18-skill-composer` declares `00-orchestrator`, `onboarding`
- `24-linkedin-profile-optimizer` declares `21-output-templates`, `23-portfolio-onepager`
- `onboarding` declares `00-orchestrator`, `18-skill-composer`

### 2. The archive is genuinely dead

27 files under `_merge-history/` are referenced by nothing live. That confirms the ABSORBED-addendum problem: those addenda were folded into host files and their originals are now unreachable. Fine as history; fatal as a shipping mechanism. Exclude the whole directory from the built plugin.

### 3. `shared/` is the real coupling point, not the orchestrator

`shared/` is referenced by 105 distinct sources — more than every skill combined. `pipeline-rules.md`, `applications_db_schema.sql`, and `site-access-model.md` are the three highest-fan-in files in the package. Practical consequence for packaging: **`shared/` is core and can never live in an addon**, and any addon that needs new shared state must add its own namespaced file rather than editing one of these.

### 4. Twenty-one SQL files, one migration chain

`applications_db_schema.sql` plus 20 numbered addenda, tracked by a `schema_version` table. This already is a migration system — the manifest should formalise it rather than replace it, and every addon that adds tables gets the next number in the same chain.

### 5. Only four skills carry cron blueprints, but there are 22 cron jobs

`00-orchestrator`, `01-job-discovery`, `11-analytics-and-learning`, `13-interview-prep` ship blueprints; the other 18 jobs are hand-installed from `cron/cron-jobs.md`. That gap is an onboarding failure mode — a user who never reads that file silently gets a third of the automation.

## What this unlocks next

- **Gate registry** — every human-decision point, derived from the reference edges into `pipeline-rules.md`, `security/`, and `10-approval-and-submit`.
- **Settings registry** — `settings-catalog.md` cross-checked against the 12 config files and their actual readers, so no setting is documented-but-unwired or wired-but-undocumented.
- **Flow catalog** — canonical paths through the graph plus variation axes.
- **Context dimensions for the bandit** — the ten covariates, confirmed against what the schema actually stores.
