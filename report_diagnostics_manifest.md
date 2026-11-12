# Spectral Core — Protected Source and Change Guard

**Status:** active repository integrity protocol  
**Repository:** `concreteballs/-Ifyouhhjjg2`  
**Protected baseline:** `.guard/manifest.json`  
**Validator:** `tools/verify_guard.py`  
**CI gate:** `.github/workflows/spectral-core-tests.yml`

## 1. Purpose

This file is the owner-facing control manifest for preserving working Spectral
Core code against accidental degradation and uncontrolled edits.

The guard is deliberately adapted to this repository. It does not refer to
YJ-64, Android APKs, Buildozer, participant chats, or files that do not exist
in Spectral Core.

The machine-readable baseline records the Git blob SHA-1 of every tracked
repository file except the baseline file itself. It also records the exact
tracked-file inventory. Therefore:
- changed protected files fail validation;
- missing or renamed protected files fail validation;
- newly tracked files fail until explicitly registered;
- changes to tests, documentation, and CI are also visible to the guard.

This first version protects complete tracked files rather than selected line
ranges. That is intentionally conservative: a line-range baseline can miss
damage elsewhere in the same module. Future versions may add separately
identified protected fragments where finer-grained change permissions are
needed.

## 2. Mandatory change procedure

1. Identify the exact files and functional areas involved.
2. Inspect the current source from the working branch; never reconstruct an
   original fragment from memory or an old conversation.
3. Describe the proposed change, its purpose, dependencies, and tests.
4. Obtain explicit owner approval before changing protected working code.
5. Copy the exact current source fragment to the patch workspace.
6. Record the target file, original fragment, replacement fragment, and a
   unique PATCH-ID.
7. Verify that the original fragment occurs exactly once. If it does not,
   stop and re-audit; do not widen or guess the replacement.
8. Apply only the approved replacement. Verify the new fragment and inspect
   the complete diff to ensure no unrelated changes occurred.
9. Run the guard, compilation checks, focused tests, and the complete test
   suite.
10. Only after the implementation and tests pass, update the approved baseline
    with the exact Git blob IDs of the resulting tracked files.
11. Review the baseline diff together with the source diff. Never refresh the
    baseline automatically to make a failing guard pass.
12. Commit the source, tests, documentation, and baseline update as one
    coherent approved change. Record the result below.

A task appearing in a roadmap or queue is not permission to implement it.

## 3. Validation commands and required order

From the repository root:

```bash
python tools/verify_guard.py
python -m compileall -q spectral_core spectral_monitor tests tools
python -m unittest discover -s tests -v
```

The GitHub Actions workflow runs these checks in this order. A guard failure
stops the job before compilation and tests. There is no Android build in this
repository, so no Android-build gate is claimed here.

A passing test suite does not replace Guard Validation. A passing guard does
not prove that code is correct; it proves only that the tracked files match
the explicitly approved baseline.

## 4. Protected baseline rules

- Canonical machine baseline: `.guard/manifest.json`.
- Hash algorithm: Git blob SHA-1, matching the repository's Git object IDs.
- Inventory source: `git ls-files`.
- All tracked files are protected except `.guard/manifest.json`, which
  cannot contain its own hash.
- No automatic baseline update command exists.
- Symbolic links in protected paths are rejected.
- The validator rejects unsafe paths, invalid digests, unregistered files,
  missing files, and content changes.
- New files must be reviewed and registered in the same approved change.
- A deliberate change to an existing file requires an explicit baseline
  update after tests pass.

The manifest itself is the trust root for this lightweight guard and cannot
self-hash. Its changes therefore require human review with the source diff.
The guard is not a digital signature, access-control boundary, malicious
maintainer defense, or substitute for protected branches and review.

## 5. Patch workspace

**Status: CLEAN — no active patch.**

For each future patch, keep only the currently approved work item in the
workspace. Use this record:

- PATCH-ID:
- Owner approval:
- Target files:
- Original fragments copied from:
- Intended replacement:
- Focused tests:
- Full test result:
- Guard result:
- Baseline update reviewed:
- Commit:

After completion, move the implementation record to the history section and
clear the active patch workspace. Do not leave abandoned or unapproved
fragments presented as active work.

## 6. Implementation history

### PATCH-SPECTRAL-GUARD-001

- Purpose: adapt the former generic/YJ-64 protected-line concept to Spectral
  Core and make it executable in CI.
- Scope: repository-wide tracked-file baseline, validator, regression tests,
  architecture research principles, README integration, and CI consolidation.
- Acceptance: Guard PASS, Python compilation PASS, complete unit-test suite
  PASS, and no unrelated source changes.
- Baseline updates are reviewed as part of this patch; the manifest is not
  self-authenticating.

## 7. Active task queue

No active code patch is authorized by this manifest.

Future work must be proposed and approved package by package. The next
architectural work is Package 4: temporal and epistemic foundations. Its
schema must not be written until the claim model, applicability conditions,
event history, evidence provenance, and local event-density model have been
specified and reviewed.

## 8. Architecture principles

The owner-approved research principles are recorded in
`docs/ARCHITECTURE_RESEARCH_PRINCIPLES.md`. They include historical
applicability, local knowledge dynamics, independent knowledge regions,
gradient-weighted typed relations, innovation hypotheses, incremental
checkpoints, and revisable assumptions about time and uncertainty.
