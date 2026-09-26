from types import SimpleNamespace

import numpy as np

from inference.framework.virelai_semantic.joint_transform import compile_joint_transformation


def _record(*grids):
    return SimpleNamespace(nodes=[SimpleNamespace(settled=np.array(grid)) for grid in grids])


def _press(left, right, cells):
    return SimpleNamespace(
        left=left, right=right, action=6, attributed=(7,), residue=frozenset(cells)
    )


def test_joint_pixel_arithmetic_recognizes_repeated_permutation():
    record = _record([[1, 2]], [[2, 1]], [[1, 2]], [[2, 1]], [[1, 2]])
    presses = [_press(i, i + 1, {(0, 0), (0, 1)}) for i in range(4)]
    result = compile_joint_transformation(record, presses, 7, component_boxes=((0, 0, 0, 1),))
    assert result["kind"] == "COORDINATED_CLASS_PERMUTATION"
    assert result["class_multiset_conserved_each_press"] is True
    assert result["period"] == 2
    assert result["witness_steps"] == [1, 2, 3, 4]


def test_joint_pixel_arithmetic_keeps_nonconserved_rewrite_distinct():
    record = _record([[1, 1]], [[2, 2]], [[3, 3]])
    presses = [_press(0, 1, {(0, 0), (0, 1)}), _press(1, 2, {(0, 0), (0, 1)})]
    result = compile_joint_transformation(record, presses, 7)
    assert result["kind"] == "COORDINATED_CLASS_REWRITE"
    assert result["class_multiset_conserved_each_press"] is False
    assert result["period"] is None


def test_repeated_relation_is_not_called_a_substitution_when_one_class_has_two_outputs():
    record = _record([[1, 1]], [[2, 3]], [[4, 4]])
    # Repeat the same 1->{2,3} relation on two independent transitions.
    record = _record([[1, 1]], [[2, 3]], [[1, 1]], [[2, 3]])
    presses = [_press(0, 1, {(0, 0), (0, 1)}), _press(2, 3, {(0, 0), (0, 1)})]
    result = compile_joint_transformation(record, presses, 7)
    assert result["kind"] == "COORDINATED_REPEATED_CLASS_REWRITE"
    assert result["rewrite_is_functional_substitution"] is False
