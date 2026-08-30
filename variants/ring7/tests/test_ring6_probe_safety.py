"""WO-RING6-01 -- regression tests for two defects found on the first two live
Kaggle runs, both in solver.py's _virelai_opening (the captain driver) and its
helpers.

Defect 1 (root cause of `ModuleNotFoundError: No module named 'virelai_v4'`,
all 25 games crashed=0 score, 2026-08-29 run): the vendored package was nested
under `inference/`, while its production modules use the package's canonical
absolute imports (`from virelai_v4...`).  The Kaggle notebook adds the
ARC3-Inference repository root to ``sys.path``.  The package therefore belongs
at ``ARC3-Inference/virelai_v4/``, as a sibling of ``inference/``.  The solver
must use that same canonical import path; no path alias or 123-file rewrite is
allowed to hide a wrong package topology.

Defect 2 (a second, independent problem found while diagnosing the first):
_virelai_opening's own `from virelai_v4... import Virelai` and
`captain = Virelai(...)` were top-level statements in the function, executed
BEFORE its only try/except -- so any exception there (an import failure,
this one included) propagated out of _virelai_opening entirely and crashed
the whole game, contradicting the function's own documented guarantee ("a
captain fault costs only the card; it never costs the game"). Fixed by
moving the import and construction inside the existing try block, with
`captain` pre-initialized to None so the already-defensive
_card_dict_from_captain(captain) call (its own try/except already falls back
to an empty dict on any exception, NameError included) produces the correct
v3.5 fallback-sentence card when the captain never gets constructed at all."""
import ast
import os

_SOLVER = os.path.join(
    os.path.dirname(__file__), "..", "ARC3-Inference",
    "inference", "framework", "solver.py",
)


def _read_solver() -> str:
    with open(_SOLVER, "r", encoding="utf-8") as f:
        return f.read()


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise AssertionError(f"function {name!r} not found")


def _all_virelai_v4_imports(tree: ast.AST) -> list[ast.ImportFrom]:
    return [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.module and "virelai_v4" in n.module
    ]


def test_every_solver_import_uses_the_canonical_top_level_package():
    """The solver and the vendored package must agree on ``virelai_v4``.

    Rewriting only solver.py to ``inference.virelai_v4`` leaves the package's
    own absolute imports broken one line later.  The topology, not an alias, is
    the invariant.
    """
    tree = ast.parse(_read_solver(), filename=_SOLVER)
    imports = _all_virelai_v4_imports(tree)
    assert imports, "no virelai_v4 imports found at all -- has the captain driver moved?"
    bad = [n.module for n in imports if not n.module.startswith("virelai_v4")]
    assert not bad, (
        f"found non-canonical Virelai import(s): {bad}; the Kaggle package "
        "must live at ARC3-Inference/virelai_v4 and import as virelai_v4"
    )


def test_vendored_package_is_a_sibling_of_inference():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ARC3-Inference"))
    assert os.path.isfile(os.path.join(root, "virelai_v4", "virelai.py"))
    assert not os.path.exists(os.path.join(root, "inference", "virelai_v4"))


def test_probe_setup_is_exception_guarded():
    """Defect 2. The captain-construction import must be a statement INSIDE
    _virelai_opening's try block, not a direct top-level statement of the
    function body executed before any try/except -- otherwise a setup
    failure (an import error, e.g. defect 1 before it was fixed) propagates
    out of _virelai_opening and crashes the whole game, contradicting the
    function's own documented 'captain fault costs only the card' guarantee."""
    tree = ast.parse(_read_solver(), filename=_SOLVER)
    func = _find_function(tree, "_virelai_opening")

    top_level_imports = [
        n for n in func.body
        if isinstance(n, ast.ImportFrom) and n.module and "virelai_v4" in n.module
    ]
    assert not top_level_imports, (
        "the virelai_v4 import is a direct top-level statement of "
        "_virelai_opening, outside any try/except -- an import failure here "
        "crashes the whole game, not just the card."
    )

    try_nodes = [n for n in func.body if isinstance(n, ast.Try)]
    assert try_nodes, "_virelai_opening no longer has any try block at all"
    first_try = try_nodes[0]

    guarded_imports = [
        n for n in ast.walk(first_try)
        if isinstance(n, ast.ImportFrom) and n.module and "virelai_v4" in n.module
    ]
    assert guarded_imports, (
        "the virelai_v4 import is not found inside _virelai_opening's first "
        "try block -- it must be guarded there for the captain-fault-only "
        "guarantee to hold."
    )

    # The captain construction call (`Virelai(...)`) must also be inside that
    # same try -- guarding only the import while leaving construction
    # unguarded reopens the identical hole one line later.
    construction_inside = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Virelai"
        for n in ast.walk(first_try)
    )
    assert construction_inside, (
        "Virelai(...) construction is not inside _virelai_opening's first "
        "try block -- a construction failure would still crash the game."
    )
    construction_outside = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Virelai"
        for stmt in func.body if stmt is not first_try
        for n in ast.walk(stmt)
    )
    assert not construction_outside, (
        "Virelai(...) construction also appears as a top-level statement of "
        "_virelai_opening outside the try block."
    )


def test_render_field_card_still_reachable_if_captain_never_builds():
    """Sanity check on the fix's fallback path (not solver.py's own code --
    this exercises the real renderer, matching test_ring6_card_guards.py):
    _card_dict_from_captain(None) is expected to raise (captain has no
    attributes), which the existing outer try/except in _virelai_opening
    already catches and turns into card_dict = {} -- confirm that empty
    dict still renders a complete, honest, all-fallback card end to end,
    exactly as it must when the captain never gets constructed at all."""
    import sys
    _card_dir = os.path.join(os.path.dirname(__file__), "..", "ARC3-Inference", "inference", "framework")
    sys.path.insert(0, _card_dir)
    from virelai_field_card_v6 import render_field_card  # noqa: E402

    card = render_field_card({}, game_id="TEST")
    text = str(card)
    for header in (
        "§1 — What Am I?", "§2 — What Do I See?",
        "§3 — What Can I Do?", "§4 — What Changes When I Act?",
        "§5 — What Don't I Know?", "§6 — How Much Time Do I Have?",
        "§7 — What Have I Tried?",
    ):
        assert header in text
