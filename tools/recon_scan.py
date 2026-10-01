"""Recon scanner: first-pass inventory of a third-party ARC-AGI-3 solution tree.

Author: Claude (Alpha build seat), 2026-09-29. Read-only: it never executes, imports or
modifies the scanned tree. Output is a JSON report on stdout.

It answers the recon plan's first questions mechanically:
  - what is in the tree (files and lines by extension);
  - which models and serving stacks it names;
  - whether it names specific games (a sign of game-specific content, which is recorded
    and never ported: see RECON_PLAN_MILESTONE_2 section 4);
  - where prompts live.

Usage: python3 tools/recon_scan.py <path-to-cloned-solution>
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

GAME_ID = re.compile(r"\b([a-z]{2}\d{2})(?:-[0-9a-f]{8})?\b")
KNOWN_PREFIXES = {
    "ar25", "bp35", "cd82", "cn04", "dc22", "ft09", "ka59", "lf52", "lp85", "ls20", "re86",
    "sb26", "sc25", "sk48", "sp80", "su15", "tn36", "tr87", "tu93", "vc33", "wa30",
}
MODEL = re.compile(
    r"(?<![A-Za-z0-9+/])(qwen[\w.\-/]*|gemma[\w.\-/]*|llama[\w.\-/]*|mistral[\w.\-/]*|deepseek[\w.\-/]*|"
    r"gpt-[\w.\-]+|claude[\w.\-]*|gemini[\w.\-]*|phi-[\w.\-]+|glm-[\w.\-]+)(?![A-Za-z0-9+/=]{12})",
    re.IGNORECASE,
)
STACK = re.compile(r"\b(vllm|sglang|llama\.cpp|transformers|torch|jax|lora|peft|trl|unsloth)\b", re.I)
PROMPT_HINT = re.compile(r"(system_prompt|SYSTEM_PROMPT|prompt\s*=|\.prompt|prompts?/)")
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".ipynb_checkpoints"}
TEXT_EXT = {".py", ".ipynb", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".cfg", ".j2", ".jinja"}


def _classify_game_mentions(game_hits: dict[str, list[str]]) -> dict:
    """Split files that list many games (rosters, loaders) from files that single out a few.

    A roster naming 10+ games is infrastructure. A file naming 1-3 games is a lead for
    hand inspection: it may special-case a world. Neither is a verdict.
    """
    ids_per_file: dict[str, set[str]] = defaultdict(set)
    for prefix, files in game_hits.items():
        for rel in files:
            ids_per_file[rel].add(prefix)
    roster = {f: len(ids) for f, ids in ids_per_file.items() if len(ids) >= 10}
    targeted = {f: sorted(ids) for f, ids in ids_per_file.items() if len(ids) <= 3}
    middle = {f: sorted(ids) for f, ids in ids_per_file.items() if 3 < len(ids) < 10}
    return {
        "game_roster_files": dict(sorted(roster.items())),
        "game_targeted_files_INSPECT": dict(sorted(targeted.items())),
        "game_partial_list_files_INSPECT": dict(sorted(middle.items())),
    }


def scan(root: Path) -> dict:
    lines_by_ext: Counter = Counter()
    files_by_ext: Counter = Counter()
    game_hits: dict[str, list[str]] = defaultdict(list)
    models: Counter = Counter()
    stacks: Counter = Counter()
    prompt_files: list[str] = []
    big_files: list[tuple[str, int]] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
            continue
        ext = path.suffix.lower()
        files_by_ext[ext or "<none>"] += 1
        size = path.stat().st_size
        if size > 5_000_000:
            big_files.append((str(path.relative_to(root)), size))
            continue
        if ext not in TEXT_EXT:
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(root))
        lines_by_ext[ext] += text.count("\n") + 1
        for match in GAME_ID.finditer(text):
            prefix = match.group(1)
            if prefix in KNOWN_PREFIXES and len(game_hits[prefix]) < 20:
                game_hits[prefix].append(rel)
        models.update(m.lower() for m in MODEL.findall(text))
        stacks.update(s.lower() for s in STACK.findall(text))
        if PROMPT_HINT.search(text) or "prompt" in rel.lower():
            prompt_files.append(rel)
    return {
        "root": str(root),
        "files_by_ext": dict(files_by_ext.most_common()),
        "lines_by_ext": dict(lines_by_ext.most_common()),
        "large_files_unscanned": big_files[:50],
        **_classify_game_mentions(game_hits),
        "models_named": dict(models.most_common(20)),
        "stack_named": dict(stacks.most_common()),
        "prompt_files": sorted(set(prompt_files))[:100],
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: recon_scan.py <path>")
    print(json.dumps(scan(Path(sys.argv[1])), indent=1))
