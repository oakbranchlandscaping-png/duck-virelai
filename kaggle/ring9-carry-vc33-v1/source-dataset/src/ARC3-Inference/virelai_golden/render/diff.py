"""RENDER · the two-run comparison. Formats only.

Canon: 04 R-B — the win is a state and the routes are a set; two runs of one world are two
witnesses. Rung 0 has no roles to compare, so this diff compares what Rung 0 produces: the
distinct visual objects (LIST 1, by fingerprint) and the worldlines (LIST 2, by a label-free
signature). NEW here (labeled): v4 had no two-run instrument; WINLAB_NOTE_01 compared by hand.

A worldline's signature is (class field, activity) — the two header fields that do not scale
with the life's length (cell range, distinct objects and appearances all do). Equal signatures
across runs are a reading ("reproduced in kind"), never an identity claim. The full header is
printed for the unmatched so the reader sees what differed.
"""
from __future__ import annotations

from collections import Counter
from typing import List, Sequence, Tuple

from virelai_golden.render.roster import class_field, collapse
from virelai_golden.weave.worldline import Worldline

Signature = Tuple[str, str]


def signature(w: Worldline) -> Signature:
    entries = collapse(w.steps)
    return (class_field(sorted({e.value for e in entries})), "STATIC" if len(entries) == 1 else "ACTIVE")


def header(w: Worldline) -> str:
    entries = collapse(w.steps)
    ccs = sorted({len(e.cells) for e in entries})
    cc = f"{ccs[0]}" if len(ccs) == 1 else f"{ccs[0]}–{ccs[-1]}"
    return (f"###{w.id:03d} · {signature(w)[0]} · {cc} cells · {len(entries)} object(s) · "
            f"{sum(len(e.trail) for e in entries)} appearance(s) · {signature(w)[1]}")


def render_diff(label_a: str, wls_a: Sequence[Worldline], label_b: str, wls_b: Sequence[Worldline]) -> str:
    objs_a = {(e.value, e.cells) for e in collapse((n, r) for w in wls_a for n, r in w.steps)}
    objs_b = {(e.value, e.cells) for e in collapse((n, r) for w in wls_b for n, r in w.steps)}
    sig_a, sig_b = Counter(signature(w) for w in wls_a), Counter(signature(w) for w in wls_b)
    shared = sig_a & sig_b
    lines: List[str] = [
        f"########## DIFF · {label_a} vs {label_b} · last played life ##########",
        f"  LIST 1 · distinct objects: A={len(objs_a)} B={len(objs_b)} · common {len(objs_a & objs_b)} · "
        f"only A {len(objs_a - objs_b)} · only B {len(objs_b - objs_a)}",
        f"  LIST 2 · worldlines: A Y={len(wls_a)} B Y={len(wls_b)} · same signature {sum(shared.values())}",
    ]
    for title, wls, other in (("only A", wls_a, sig_b - shared), ("only B", wls_b, sig_a - shared)):
        unmatched = Counter(sig_a - shared if title == "only A" else sig_b - shared)
        for w in sorted(wls, key=lambda w: w.id):
            if unmatched[signature(w)] > 0:
                unmatched[signature(w)] -= 1
                lines.append(f"    {title}: {header(w)}")
    lines.append("########## END DIFF ##########")
    return "\n".join(lines)
