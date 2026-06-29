#!/usr/bin/env bash
# check-build-guide-faithfulness.sh — anti-drift gate for build-guide.md
#
# Verifies that every "claimed verbatim" reference code block in build-guide.md is
# byte-identical to its real source-of-truth file under the module-*/ directories,
# AFTER stripping the single per-module "Frozen snapshot from Module N output …"
# provenance line. See docs/adr/0001-build-guide-mirrors-module-dirs.md.
#
# Covers the 8 claimed-verbatim blocks:
#   bq-cost-guard.sh, dbt-auto-test.sh, full stop-summary.sh, full settings.json,
#   and analyze.md / check-cost.md / validate-models.md / generate-report.md.
#
# Exit 0  = all blocks faithful.
# Exit !=0 = drift (or a missing/ambiguous block) — suitable as a CI gate.
#
# Usage (from anywhere): scripts/check-build-guide-faithfulness.sh
set -euo pipefail

# Resolve repo root relative to this script so it runs from any CWD.
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

python3 - <<'PY'
import difflib
import re
import sys

BUILD_GUIDE = "build-guide.md"

with open(BUILD_GUIDE, encoding="utf-8") as fh:
    bg = fh.read()


def strip_provenance(text):
    """Drop the per-module 'Frozen snapshot from Module N output …' provenance line."""
    kept = [ln for ln in text.splitlines() if "Frozen snapshot from Module" not in ln]
    return "\n".join(kept).rstrip("\n")


# label, real source file, heredoc target path, heredoc delimiter, disambiguating substring (or None)
CHECKS = [
    ("bq-cost-guard.sh",
     "module-1-hooks/.claude/hooks/bq-cost-guard.sh",
     ".claude/hooks/bq-cost-guard.sh", "HOOKEOF", None),
    ("dbt-auto-test.sh",
     "module-1-hooks/.claude/hooks/dbt-auto-test.sh",
     ".claude/hooks/dbt-auto-test.sh", "HOOKEOF", None),
    ("stop-summary.sh (full)",
     "module-1-hooks/.claude/hooks/stop-summary.sh",
     ".claude/hooks/stop-summary.sh", "HOOKEOF", None),
    ("settings.json (full)",
     "module-1-hooks/.claude/settings.json",
     ".claude/settings.json", "EOF", "Bash(dbt run:*)"),
    ("analyze.md",
     "module-3-orchestration/.claude/commands/analyze.md",
     ".claude/commands/analyze.md", "EOF", None),
    ("check-cost.md",
     "module-3-orchestration/.claude/commands/check-cost.md",
     ".claude/commands/check-cost.md", "EOF", None),
    ("validate-models.md",
     "module-3-orchestration/.claude/commands/validate-models.md",
     ".claude/commands/validate-models.md", "EOF", None),
    ("generate-report.md",
     "module-3-orchestration/.claude/commands/generate-report.md",
     ".claude/commands/generate-report.md", "EOF", None),
]

failures = []
passed = 0

for label, real_path, target, delim, contains in CHECKS:
    pattern = re.compile(
        r"cat > " + re.escape(target) + r" << '" + re.escape(delim) + r"'\n"
        r"(.*?)\n" + re.escape(delim) + r"(?:\n|$)",
        re.DOTALL,
    )
    blocks = [m.group(1) for m in pattern.finditer(bg)]
    if contains is not None:
        # Disambiguate when several heredocs share a target (e.g. the empty
        # settings.json skeleton vs the full file): keep only the real one.
        blocks = [b for b in blocks if contains in b]

    if not blocks:
        failures.append(f"[{label}] no reference block found "
                        f"(looked for: cat > {target} << '{delim}')")
        continue
    if len(blocks) > 1:
        failures.append(f"[{label}] ambiguous: expected exactly 1 reference block, "
                        f"found {len(blocks)}")
        continue

    try:
        with open(real_path, encoding="utf-8") as fh:
            real = strip_provenance(fh.read())
    except FileNotFoundError:
        failures.append(f"[{label}] source-of-truth file missing: {real_path}")
        continue

    if blocks[0] == real:
        passed += 1
        continue

    diff = difflib.unified_diff(
        real.splitlines(),
        blocks[0].splitlines(),
        fromfile=f"{real_path} (source of truth, provenance line stripped)",
        tofile=f"build-guide.md :: {label}",
        lineterm="",
    )
    snippet = "\n".join(list(diff)[:30])
    failures.append(f"[{label}] DRIFT vs {real_path}:\n{snippet}")

if failures:
    print(f"✗ build-guide.md faithfulness check FAILED "
          f"({len(failures)} of {len(CHECKS)} block(s) drifted/missing):\n", file=sys.stderr)
    for msg in failures:
        print("  " + msg.replace("\n", "\n  "), file=sys.stderr)
    print("\nThe module-*/ files are the single source of truth "
          "(see docs/adr/0001-build-guide-mirrors-module-dirs.md).", file=sys.stderr)
    print("Fix: re-copy the real file into the build-guide.md block verbatim, "
          "minus the 'Frozen snapshot from Module N output …' line.", file=sys.stderr)
    sys.exit(1)

print(f"✓ build-guide.md faithfulness check PASSED — all {passed} claimed-verbatim "
      f"reference blocks are byte-identical to their module-*/ sources "
      f"(provenance line excluded).")
sys.exit(0)
PY
