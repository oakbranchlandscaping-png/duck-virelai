"""golden_log_adapter.py -- fills the card's dict from a golden-run log.

RING 6, VERIFICATION PATH ONLY. This is NOT the production route and must never
become it. Production reads the live weave objects; this reads the text those
objects printed, so that the card can be SEEN and graded before anyone spends a
week vendoring 200 files into a Kaggle bundle.

It parses the LAST occurrence of each block, because a multi-life run prints
each one per life and the handover card is the last one.

Every field it cannot find is left ABSENT rather than defaulted, so the card
renders a named absence instead of a confident wrong number. The one exception
is the grid shape, which the log does not print at all: it defaults to 64x64 and
says so below. The live path reads the real value from the node cut.
"""

from __future__ import annotations

import re
import sys

GRID_DEFAULT = (64, 64)          # the log does not print grid_shape; live path has it

_ROW = re.compile(
    r"^\s*(###\d+):\s+.*?:\s+(\d+)(?:[–—-](\d+))?\s+cells:\s+"
    r"NW\s+\((\d+),\s*(\d+)\):\s*(.*)$")
_L3 = re.compile(r"^\s*(###\d+)\s+·.*?B1\s+(\w+)\(cov\s+(\d+)(?:,\s*revisit\s+(\d+))?\)")
_MODEL = re.compile(r"(\d+)→\(([+-]?\d+),([+-]?\d+)\)×(\d+)")
_MODEL_ANY = re.compile(r"(\d+)→\(([+-]?\d+),([+-]?\d+)\)")
_FOOT = re.compile(r"footprint\s+(\d+)\s+cell")
_SEALED = re.compile(r"ego\s+sealed\s+((?:###\d+\s*)+)")
_HEAD = re.compile(r"Life\s+(\d+)\s*\|\s*Level\s+(\d+)\s*\|\s*Actions:\s*(\d+)"
                   r"\s*\|\s*World:\s*(\w+)")
_LIST1 = re.compile(r"LIST 1 · VISUAL OBJECTS \(X=(\d+)")
_TARGET = re.compile(r"^\s*#\d+\s+\((\d+),\s*(\d+)\)\s+class\s+\d+\s+(\d+)\s+cells\s+"
                     r"→\s+(.+?)\s*$")
_GROUND = re.compile(r"(###\d+)\s+typed GROUND\s+—\s+deformed on\s+(\d+)\s+nodes")
_COUNT = re.compile(r"^\s*(TOUCHED|NOT REACHED|NEVER ATTEMPTED|UNREACHABLE|queued)\s+(\d+)")

_COUNT_KEY = {"TOUCHED": "touched", "NOT REACHED": "not_reached",
              "NEVER ATTEMPTED": "never", "UNREACHABLE": "unreachable",
              "queued": "queued"}


def _tail(rest):
    """Role, seal and fields from a closing-summary row's tail."""
    out = {"role": None, "seal": None, "fields": (), "ticks": 0, "multi": 0}
    m = re.match(r"\s*(\S+)\s*\((FIRM|PROVISIONAL)\)", rest)
    if m:
        role = m.group(1)
        out["role"] = None if role == "∅" else role
        out["seal"] = m.group(2)
    fields = []
    if "+ GROUND" in rest:
        fields.append("GROUND")
    if "+ WALL" in rest:
        fields.append("WALL")
    out["fields"] = tuple(fields)
    t = re.search(r"TICKS\s+×(\d+)", rest)
    if t:
        out["ticks"] = int(t.group(1))
    mm = re.search(r"MULTI-MEMBER\s+\((\d+)\)", rest)
    if mm:
        out["multi"] = int(mm.group(1))
    return out


def parse(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    lines = text.splitlines()
    d = {"grid": GRID_DEFAULT, "hud": None, "win_seen": False}

    for m in _HEAD.finditer(text):                       # last header wins
        d["lives"] = int(m.group(1))
        d["level"] = int(m.group(2))
        d["actions"] = int(m.group(3))
        d["world_type"] = m.group(4)
    m = re.search(r"Game:\s*(\S+)", text)
    if m:
        d["game_id"] = m.group(1)
    for m in re.finditer(r"Ego:\s*(\w+)\s*\(", text):     # EMBODIED / GOD_MODE
        d["ego_mode"] = m.group(1)

    m = None
    for m in _LIST1.finditer(text):
        pass
    if m:
        d["visual_objects"] = int(m.group(1))

    # -- worldlines: the LAST closing-summary block ---------------------------
    starts = [i for i, l in enumerate(lines) if "CLOSING SUMMARY" in l]
    rows = {}
    if starts:
        for line in lines[starts[-1] + 1:]:
            m = _ROW.match(line)
            if not m:
                if line.strip().startswith("──") and rows:
                    break
                continue
            lo = int(m.group(2))
            hi = int(m.group(3)) if m.group(3) else lo
            w = {"id": m.group(1), "cells": (lo, hi),
                 "anchor": (int(m.group(4)), int(m.group(5))),
                 "cov": 0, "revisit": None}
            w.update(_tail(m.group(6)))
            rows[w["id"]] = w

    for line in lines:                                   # LIST 3 supplies coverage
        m = _L3.match(line)
        if m and m.group(1) in rows:
            rows[m.group(1)]["cov"] = int(m.group(3))
            if m.group(4):
                rows[m.group(1)]["revisit"] = int(m.group(4))
    d["worldlines"] = [rows[k] for k in sorted(rows)]

    # -- the ego --------------------------------------------------------------
    ego = {}
    for m in _SEALED.finditer(text):
        ego["sealed"] = m.group(1).split()
    for m in _FOOT.finditer(text):
        ego["footprint"] = int(m.group(1))
    # The map line carries TWO sets and they answer different questions
    # (WO-OBSERVED-RENDER-01). Left of the bar: every press of this button
    # agreed -- the AGREED set, carrying a count. Right of it, "planned from":
    # this button has EVER gone that way -- the OBSERVED set, which by design
    # carries no count. An action present on the right and absent on the left
    # has moved you and disagreed with itself; that is not the same fact as an
    # action that never moved anything, and the card must not merge them.
    model, observed = {}, set()
    for line in lines:
        if line.strip().startswith("model"):
            left, _bar, right = line.partition("‖")
            model = {int(a): (int(dr), int(dc)) for a, dr, dc, _ in _MODEL.findall(left)}
            observed = {int(a) for a, _dr, _dc in _MODEL_ANY.findall(right)}
    if model or observed:
        ego["model"] = model
        ego["observed"] = sorted(observed)
        d["roster"] = sorted(set(model) | observed)
    if ego.get("sealed"):
        first = rows.get(ego["sealed"][0])
        if first:
            ego["anchor"] = first["anchor"]
            d["ego_seal"] = first.get("seal")
    d["ego"] = ego

    for m in _GROUND.finditer(text):
        d["ground_note"] = m.group(2)

    # -- the frontier: the LAST coverage roster -------------------------------
    starts = [i for i, l in enumerate(lines) if "COVERAGE ROSTER" in l and "END" not in l]
    if starts:
        f, targets = {}, []
        for line in lines[starts[-1]:]:
            if "END COVERAGE ROSTER" in line:
                break
            m = _COUNT.match(line)
            if m:
                f[_COUNT_KEY[m.group(1)]] = int(m.group(2))
                continue
            m = _TARGET.match(line)
            if m:
                targets.append({"anchor": (int(m.group(1)), int(m.group(2))),
                                "cells": int(m.group(3)), "state": m.group(4)})
        f["targets"] = targets
        d["frontier"] = f
    return d


if __name__ == "__main__":
    from virelai_field_card_v6 import render_card
    data = parse(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ring6.log")
    card = render_card(data)
    print(card)
    print("\n---- %d chars | %d words | %d worldlines parsed | %d targets ----"
          % (len(card), len(card.split()), len(data.get("worldlines") or ()),
             len((data.get("frontier") or {}).get("targets") or ())))
