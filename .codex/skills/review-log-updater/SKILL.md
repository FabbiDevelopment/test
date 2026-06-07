---
name: review-log-updater
description: Append-only project review documentation workflow. Use when an agent finds, confirms, reviews, or reports a functional bug, security issue, regression, missing test, or implementation risk; and use when an agent fixes, mitigates, verifies, or summarizes a bug fix. Findings must be appended to docs/code-review-findings.md and fixes must be appended to docs/fix-summary.md without rewriting existing content.
---

# Review Log Updater

## Purpose

Keep the project review docs current without losing history. Every new finding or fix gets appended as a new entry; existing entries stay intact.

## Required Files

- Findings log: `docs/code-review-findings.md`
- Fix summary: `docs/fix-summary.md`

If either file or the `docs/` folder is missing, create only the missing path/file, then append the new entry.

## Finding Workflow

When an agent finds or confirms a bug, append one entry to `docs/code-review-findings.md`.

Use this format:

```markdown

## Finding - YYYY-MM-DD - Short Title

Severity: Critical | High | Medium | Low
Area: Backend | Frontend | Full-stack | Docs | Infrastructure
Status: Open | Fixed in <commit/branch if known>

Bug: One concise paragraph describing the broken behavior.

Evidence: File paths, routes, commands, test names, or reproduction notes that support the finding.

Impact: User-visible, security, data integrity, reliability, or developer workflow consequence.

Recommended fix: One concise paragraph describing the solution direction.
```

Rules:
- Append at the end of the file.
- Do not rewrite, reorder, deduplicate, or reformat older findings.
- Record only meaningful functional bugs or risks, not style-only issues.
- If evidence is uncertain, mark `Status: Needs confirmation` and explain the uncertainty.

## Fix Workflow

When an agent fixes or mitigates a bug, append one entry to `docs/fix-summary.md`.

Use this format:

```markdown

## Fix - YYYY-MM-DD - Short Title

Area: Backend | Frontend | Full-stack | Docs | Infrastructure
Related finding: Short title, finding heading, issue ID, or `Unknown`

Bug: One concise paragraph describing what was wrong.

Solution: One concise paragraph describing how it was fixed. Do not include code snippets.

Verification: Commands run and observed results, or `Not run` with the reason.

Residual notes: Remaining warning, limitation, migration note, or `None`.
```

Rules:
- Append at the end of the file.
- Do not rewrite, reorder, deduplicate, or reformat older fixes.
- Do not include code blocks unless the user explicitly asks for command output.
- Prefer behavior-level summaries over file-by-file implementation details.

## Practical Notes

- Use the current date in `YYYY-MM-DD` format.
- Preserve Markdown exactly outside the appended section.
- If multiple bugs are found or fixed, append separate entries unless they are one inseparable root cause.
- If docs are ignored by Git, still update them locally when requested; mention that they may not be committed unless force-added or unignored.
