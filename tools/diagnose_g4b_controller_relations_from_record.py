#!/usr/bin/env python3
"""Read-only diagnostic: what could the controller have known at G4-B, and what did Duck's card show?

Author: Claude (Alpha build seat), 2026-10-04. For RULING_G4_CONTROLLER_FIRST_v1 (Director-ruled, broad).

Drives a live record as live (the controller's own answers; Duck's recorded answers only where the gate
asks Duck; the harness RESET delivered as live), takes the G4-B lever regions at the transition before
G4-B's first probe, then labels every transition from LEVEL_START on: which lever was acted, what each
lever region did (UNCHANGED / STEPS / CHANGES, graded exactly as G4-B grades), whether anything changed
elsewhere, and each region's state label as the card shows it (``state_now``). It then scores simple
record-lookup predictors online on the G4-B and G4-C transitions (history = every earlier transition of
the level), with G4-B's own grading rule. It changes nothing.

Usage:
  PYTHONPATH=ARC3-Inference:tufa-arc-agi-framework/src python3 tools/diagnose_g4b_controller_relations_from_record.py RECORD.json.gz G4B_FIRST LEVEL_START
  (v7: G4B_FIRST=141 LEVEL_START=70)
"""
import collections
import json
import sys

from inference.framework.controller_executor import next_owned_step
from inference.framework.record_replay import (
    _answer_index, _replay_reset, ReplayResult, click_world_machine, decode_grid, load_record, lossless_outcome,
    merge_recorded_answer, record_like_live, record_protocol,
)

def drive(path, stop_before=None, on_step=None):
    record = load_record(path)
    grid = decode_grid(record["initial_grid"])
    machine = click_world_machine(grid, record["valid_actions"], **record_protocol(record))
    result = ReplayResult(machine=machine, grid=grid, steps_replayed=0, answers_used=0, measure=False)
    pending = {}
    for answer in record["answers"]:
        pending.setdefault(answer["gate_id"], []).append(answer)

    def answers():
        while True:
            owned = next_owned_step(machine)
            if owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
                machine.submit_answer(json.loads(json.dumps(owned.answer)))
                continue
            view = machine.gate_view()
            template, queue = view.get("answer_template") or {}, pending.get(machine.gate_id) or []
            due = view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"
            ready = template.get("entity_id") and any(item.get("entity_id") == template["entity_id"] for item in queue)
            if template and (ready or (due and owned.owner == "DUCK" and queue)):
                machine.submit_answer(merge_recorded_answer(template, queue.pop(_answer_index(queue, template))))
                continue
            return

    for step in record["steps"]:
        tid = step["transition_id"]
        if stop_before is not None and tid >= stop_before:
            break
        if step["action"].get("action") == "RESET" or step.get("kind") == "RESET":
            before = [row[:] for row in result.grid]
            _replay_reset(result, step)
            if on_step: on_step(machine, step, before, result.grid, None)
            continue
        answers()
        cap = machine.next_probe_capability()
        if cap is None:
            return machine, result, f"no capability at {machine.gate_id} before t{tid}", record
        probe = machine.validate_probe({"probe_token": cap["probe_token"]}, [step["action"]])
        before = [row[:] for row in result.grid]
        result.grid, outcome = lossless_outcome(result.grid, tid, step["action"], step["changed"], step.get("boundary"))
        record_like_live(machine, probe, outcome, record["valid_actions"])
        if on_step: on_step(machine, step, before, result.grid, probe)
    answers()
    return machine, result, "end", record


from inference.framework.g4_relations import masked_changes, masked_address, _met, CHANGES, NO_CHANGE

PATH = sys.argv[1]
G4B_FIRST, LEVEL_START = int(sys.argv[2]), int(sys.argv[3])
m, _, why, rec = drive(PATH, stop_before=G4B_FIRST)
g4b = m._adapters["G4-B-LEVER-RELATIONS"]
regions = g4b._regions or (g4b._seed() or g4b._regions)
print("G4-B regions at t140:", [(r.entity_id, len(r.cells), len(r.steps), r.click) for r in regions])
cell_owner = {cell: r.entity_id for r in regions for cell in r.cells}
click_of = {(int(r.click.get("row", -1)), int(r.click.get("col", -1))): r.entity_id for r in regions}

rows = []
def on_step(machine, step, before, after, probe):
    tid = step["transition_id"]
    if tid < LEVEL_START:
        return
    if probe is None:
        rows.append({"t": tid, "reset": True}); return
    law = machine.counter.mask_law
    ch = masked_changes(before, after, law)
    inside = {c for r in regions for c in r.cells}
    obs = tuple(r.observe(ch) for r in regions)
    elsewhere = CHANGES if any(c not in inside for c in ch) else NO_CHANGE
    a = step["action"]; site = (a.get("row"), a.get("col"))
    lever = click_of.get(site) or cell_owner.get(site)
    states = tuple(r.state_label(before) for r in regions)
    contents = tuple(tuple(before[rr][cc] for rr, cc in r.cells) for r in regions)
    b = step.get("boundary") or {}
    rows.append({"t": tid, "gate": probe.gate_id, "action": (site), "lever": lever, "obs": obs, "else": elsewhere,
                 "states": states, "contents": contents, "addr": masked_address(before, law), "terminal": b.get("state") in ("GAME_OVER", "WIN"),
                 "n": len(ch)})

drive(PATH, on_step=on_step)
names = [r.entity_id for r in regions]
def fmt(o, e): return " ".join(f"{n[-2:]}:{x[0]}" for n, x in zip(names, o)) + f" | else:{e[0]}"

def match(pred, row):
    po, pe = pred
    return all(_met(p, o) for p, o in zip(po, row["obs"])) and pe == row["else"]

models = {
    "M1 same action, same masked board": lambda r: ("A", r["action"], r["addr"]),
    "M2 same lever, same state of every lever": lambda r: ("B", r["lever"], r["states"]),
    "M4 same lever, same contents of every lever region": lambda r: ("D", r["lever"], r["contents"]),
    "M5 same lever, same contents of its own region": lambda r: ("E", r["lever"], r["contents"][names.index(r["lever"])] if r["lever"] in names else None),
    "M3 same lever, same own state": lambda r: ("C", r["lever"], r["states"][names.index(r["lever"])] if r["lever"] in names else None),
}
print("\nLevel transitions:")
for r in rows:
    if r.get("reset"): print(f"t{r['t']} RESET"); continue
    print(f"t{r['t']:3d} {r['gate'][:14]:14s} {str(r['lever']):6s} states={','.join(s.replace('UNRECORDED','U') for s in r['states'])} n={r['n']:3d}  {fmt(r['obs'], r['else'])}{'  TERMINAL' if r['terminal'] else ''}")

print(f"\nOnline prediction from t{G4B_FIRST} (history = every earlier transition of the level):")
for name, key in models.items():
    hist = collections.defaultdict(list); covered = right = total = 0; detail = []
    for r in rows:
        if r.get("reset") or r["terminal"]:
            continue
        if r["t"] >= G4B_FIRST:
            total += 1
            k = key(r)
            if hist.get(k):
                covered += 1
                pred = collections.Counter(hist[k]).most_common(1)[0][0]
                ok = match(pred, r); right += ok; detail.append((r["t"], ok))
            else:
                detail.append((r["t"], None))
        hist[key(r)].append((r["obs"], r["else"]))
    print(f"  {name}: predicted {covered}/{total}, correct {right}/{total}; {detail}")

labels = collections.Counter(s for r in rows if not r.get("reset") for s in r["states"])
print("\nstate_now labels across the level (what the card shows Duck):", dict(labels))
