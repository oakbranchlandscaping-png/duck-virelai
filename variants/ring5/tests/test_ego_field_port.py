"""Ring 5 battery. ego_field's conjuncts + the Director's direct-control ruling.
Fixtures are derived from anchor arithmetic, not written by eye: _anchor is
(min row, min col) -- a bounding-box corner, NOT a cell. A ground that keeps any
cell in row 0 and any cell in col 0 holds its anchor however much it churns."""
import sys, os, importlib.util
_R = os.path.join(os.path.dirname(__file__), '..', 'ARC3-Inference')
_s = importlib.util.spec_from_file_location(
    'vw', os.path.join(_R, 'inference/framework/virelai_weave.py'))
vw = importlib.util.module_from_spec(_s); sys.modules['vw'] = vw; _s.loader.exec_module(vw)

def build(lb, spec):
    w = vw.Weave(); w.edge_label = dict(lb)
    for wid, at in spec.items():
        wl = vw.Worldline(wid, 1, frozenset(at[max(at)]))
        wl.at = {k: frozenset(v) for k, v in at.items()}
        w.worldlines[wid] = wl
    return w

A = {0:{(2,0)}, 1:{(1,0)}, 2:{(1,1)}}
G = {0:{(0,0),(1,0),(1,1),(3,0)}, 1:{(0,0),(2,0),(1,1),(3,0)}, 2:{(0,0),(2,0),(1,0),(3,0)}}

def test_figure_seals_and_ground_does_not():
    w = build({0:'S',1:'UP',2:'RIGHT'}, {1:A, 2:G})
    assert w.field_seal(1) is not None
    assert w.field_seal(2) is None
    assert [x.wid for x in w.egos()] == [1]

def test_announcement_is_observed_not_concluded():
    w = build({0:'S',1:'UP',2:'RIGHT'}, {1:A, 2:G}); w.settle()
    n = " ".join(w.notes)
    assert "exchanged ground" in n and "falsified" in n
    assert "is YOU" not in n and "not doubt" not in n.lower()

def test_single_action_refuses():
    w = build({0:'S',1:'UP'}, {1:{0:{(2,0)},1:{(1,0)}},
                               2:{0:{(0,0),(1,0)},1:{(0,0),(2,0)}}})
    assert w.field_seal(1) is None

def test_both_displaced_both_refuse():
    Gd = dict(G); Gd[3] = {(1,0),(3,0),(2,0),(4,0)}          # wholesale translation
    w = build({0:'S',1:'UP',2:'RIGHT',3:'DOWN'}, {1:A, 2:Gd})
    _, disp = w._field()
    assert disp[1] and disp[2], "fixture must genuinely displace BOTH"
    assert w.field_seal(1) is None and w.field_seal(2) is None

def test_stationary_refuses():
    w = build({0:'S',1:'UP',2:'RIGHT'}, {1:{0:{(5,5)},1:{(5,5)},2:{(5,5)}}, 2:G})
    assert w.field_seal(1) is None

def test_gains_from_nowhere_refuse():
    w = build({0:'S',1:'UP',2:'RIGHT'}, {1:{0:{(2,0)},1:{(9,9)},2:{(8,8)}}, 2:G})
    assert w.field_seal(1) is None

def test_driven_object_refuses_and_its_driver_seals():
    E  = {0:{(4,0)},1:{(3,0)},2:{(2,0)},3:{(2,1)}}
    B  = {0:{(1,0)},1:{(1,0)},2:{(1,0)},3:{(1,1)}}
    GG = {0:{(0,0),(3,0),(2,0),(2,1),(1,1)}, 1:{(0,0),(4,0),(2,0),(2,1),(1,1)},
          2:{(0,0),(4,0),(3,0),(2,1),(1,1)}, 3:{(0,0),(4,0),(3,0),(2,0),(1,0)}}
    w = build({0:'S',1:'UP',2:'UP',3:'RIGHT'}, {1:E, 2:B, 3:GG})
    assert w.field_seal(2) is None, "a lever is something the ego moves"
    assert w.field_seal(1) is not None

def test_two_tones_of_one_body_both_seal():
    t1 = {0:{(2,0)},1:{(1,0)},2:{(1,1)}}
    t2 = {0:{(2,5)},1:{(1,5)},2:{(1,6)}}
    G2 = {0:{(0,0),(1,0),(1,1),(1,5),(1,6)}, 1:{(0,0),(2,0),(1,1),(2,5),(1,6)},
          2:{(0,0),(2,0),(1,0),(2,5),(1,5)}}
    w = build({0:'S',1:'UP',2:'RIGHT'}, {1:t1, 2:t2, 3:G2})
    assert w.field_seal(1) is not None and w.field_seal(2) is not None

def test_wide_set_is_not_the_verdict_set():
    w = build({0:'S',1:'UP',2:'RIGHT'}, {1:{0:{(5,5)},1:{(5,5)},2:{(5,5)}}, 2:G})
    w.worldlines[1].ego = True
    assert [x.wid for x in w.ego_candidates()] == [1]
    assert [x.wid for x in w.egos()] == []

def test_anchor_is_a_corner_not_a_cell():
    assert vw._anchor(frozenset()) == (-1, -1)
    assert vw._anchor({(3,7),(1,9),(5,2)}) == (1, 2)
