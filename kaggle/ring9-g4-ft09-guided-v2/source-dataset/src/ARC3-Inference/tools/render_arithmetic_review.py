"""Render a compact human review packet from Ring 8 arithmetic/weave artifacts."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _region(item: dict[str, Any] | None) -> str:
    if not item:
        return "none"
    return (
        f"node {item['node_index']} component {item['component_id']} · "
        f"integer {item['class_id']} · {item['cell_count']} cells · "
        f"bbox {item['bbox']}"
    )


def _signed(values: list[list[int]]) -> str:
    return ", ".join(f"{class_id}:{delta:+d}" for class_id, delta in values) or "none"


def render(game_root: Path) -> str:
    summary = _json(game_root / "continuity_summary.json")
    pixels = _jsonl(game_root / "pixel_arithmetic.jsonl")
    canonical = _jsonl(game_root / "weave_edges.jsonl")
    golden = _jsonl(game_root / "golden_weave_edges.jsonl")
    experimental_path = game_root / "experimental_partition_edges.jsonl"
    experimental = _jsonl(experimental_path) if experimental_path.exists() else []
    tracks = _json(game_root / "continuity_tracks.json")
    by_pair = {(row["from_node"], row["to_node"]): row for row in pixels}
    total_sites = sum(int(row["site_count"] or 0) for row in pixels)
    held = sum(int(row["held_cells"] or 0) for row in pixels)
    changed = sum(int(row["changed_cells"] or 0) for row in pixels)
    geometry = sum(bool(row["geometry_changed"]) for row in pixels)
    conservation_failures = sum(row["conservation_closes"] is False for row in pixels)
    verbs = Counter(row["verb"] for row in canonical)
    golden_verbs = Counter(row["verb"] for row in golden)
    lines = [
        f"# Arithmetic and correspondence review — {game_root.name}",
        "",
        "This packet separates literal grid facts from proposed object continuity.",
        "A site is never empty: every footprint-membership change retains its exact integer rewrite.",
        "",
        "## Record coverage",
        "",
        f"- Frames: {summary['compiled_through_node'] + 1}; observed edges: {len(pixels)}.",
        f"- Site observations: {total_sites:,} = {held:,} HELD + {changed:,} CHANGED.",
        f"- Geometry-change edges: {geometry}; conservation failures: {conservation_failures}.",
        f"- INTERIM_O9 worldlines: {summary['tracks']}; stitches: {summary['stitches']}.",
        f"- Anchor-first verbs: {dict(sorted(verbs.items()))}.",
        f"- Anchor-first golden verbs: {dict(sorted(golden_verbs.items()))}.",
        "",
        "## Largest literal changes",
        "",
        "These are observations, not object or causal claims.",
        "",
    ]
    peaks = sorted(
        (row for row in pixels if row["changed_cells"] is not None),
        key=lambda row: (-int(row["changed_cells"]), int(row["to_node"])),
    )[:12]
    for row in peaks:
        lines.append(
            f"- {row['from_node']}→{row['to_node']} · action {row['action_id']} · "
            f"{row['changed_cells']} cells changed · signed integer counts: "
            f"{_signed(row['signed_class_delta'])}."
        )

    lines.extend(["", "## Level-boundary edges", ""])
    boundaries = [row for row in pixels if row["level_after"] != row["level_before"]]
    if not boundaries:
        lines.append("- None observed in this recording.")
    for row in boundaries:
        lines.append(
            f"- {row['from_node']}→{row['to_node']} · level {row['level_before']}→"
            f"{row['level_after']} · action {row['action_id']} · "
            f"{row['changed_cells']} changed cells · {_signed(row['signed_class_delta'])}."
        )

    lines.extend([
        "",
        "## Experimental split/merge cases",
        "",
        "These come from the partition-fenced hypothesis, not settled ontology. For each case,",
        "judge the correspondence: CONTINUE, SPLIT, MERGE, UNRELATED, or UNCLEAR.",
        "",
    ])
    branches = [row for row in experimental if row["verb"] in {"SPLIT", "MERGE"}]
    if not branches:
        lines.append("- None proposed.")
    for index, row in enumerate(branches[:20], start=1):
        pixel = by_pair.get((row["from_node"], row["to_node"]), {})
        lines.extend([
            f"### Case B{index} · proposed {row['verb']} · {row['from_node']}→{row['to_node']}",
            "",
            f"- Action: {pixel.get('action_id')}; whole-grid changed cells: {pixel.get('changed_cells')}.",
            f"- Subject: {_region(row['before'] or row['after'])}.",
            "- Related sightings:",
        ])
        for related in row.get("related_branch_sightings") or []:
            lines.append(f"  - {_region(related)}.")
        lines.extend([
            "- Judgment: `_____`",
            "- Reason from the observed frames: `_____`",
            "",
        ])
    if len(branches) > 20:
        lines.append(f"_Showing 20 of {len(branches)} branch proposals._")

    lines.extend(["", "## Residual correspondence cases", ""])
    residuals = [row for row in canonical if row["verb"] in {"AMBIGUOUS", "DEFORM"}]
    lines.append(f"Total residuals: {len(residuals)}. Representative cases:")
    lines.append("")
    for row in residuals[:12]:
        pixel = by_pair.get((row["from_node"], row["to_node"]), {})
        lines.append(
            f"- {row['verb']} at {row['from_node']}→{row['to_node']} · action "
            f"{pixel.get('action_id')} · {_region(row['before'])}."
        )

    lines.extend([
        "",
        "## Most active INTERIM_O9 worldlines",
        "",
        "These are compact histories for judging whether the weave tracks coherent things.",
        "",
    ])
    active = []
    for track in tracks:
        nonstill = [stitch for stitch in track["stitches"] if stitch["verb"] != "STILL"]
        if nonstill:
            active.append((len(nonstill), len(track["stitches"]), track, nonstill))
    active.sort(key=lambda item: (-item[0], -item[1], item[2]["track_id"]))
    for _, _, track, nonstill in active[:15]:
        first, last = track["observations"][0], track["observations"][-1]
        stream = Counter(stitch["verb"] for stitch in track["stitches"])
        examples = ", ".join(
            f"{item['from_node']}→{item['to_node']} {item['verb']}"
            for item in nonstill[:5]
        )
        lines.extend([
            f"### {track['display_id']}",
            "",
            f"- Span: nodes {track['born_node']}→{track['last_seen_node']}; "
            f"integer {first['class_id']}→{last['class_id']}; "
            f"cells {first['cell_count']}→{last['cell_count']}.",
            f"- Verb counts: {dict(sorted(stream.items()))}.",
            f"- First non-STILL examples: {examples}.",
            "- Coherent persistent object? `YES / NO / UNCLEAR`",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    body = render(args.game_root.resolve())
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
