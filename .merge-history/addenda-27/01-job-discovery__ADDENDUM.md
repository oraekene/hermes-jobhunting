<!-- STATUS: ABSORBED. This file is preserved as a record, not as instructions.
Content lives in 01-job-discovery/SKILL.md (calibration inheritance at the filter step).
Do not follow it as a procedure; the host file named above is authoritative. -->

# 01-job-discovery — Addendum: calibration is inherited, not read directly

Short on purpose. `01-job-discovery` does not read `shared/dynamic-
target-calibration.yaml` itself, and doesn't need to: it already reads
`target-profile.yaml`'s `title_variants` for what titles to search for,
and `07-context-architect`'s Phase 1.5 (see that skill's own addendum)
is what keeps `title_variants` in sync with calibration state — wider
during an auto-relax period, unchanged otherwise. `01-job-discovery`
inherits the effect automatically the next time it reads a field it was
already reading.

Filed as its own addendum anyway, rather than left unstated, because
Kene specifically asked whether calibration was actually wired into
"all relevant files" — this is the honest answer for this one: it's
relevant, but indirectly, and that's a real architectural choice (one
re-run point for the net-widening logic, not three places that all need
to agree with each other) rather than an oversight being described as
one.
