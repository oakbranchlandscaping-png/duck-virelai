from argparse import Namespace

import pytest

from inference.framework.run import _online_arcade_spec
from taaf.game_api import arc_agi


def test_online_arcade_builds_explicit_network_spec_without_offline_files():
    spec = _online_arcade_spec(Namespace(
        online_arcade=True,
        simulate_competition_arcade=False,
    ))
    assert spec is not None
    assert spec.operation_mode is arc_agi.OperationMode.ONLINE
    assert spec.environments_dir == ""
    assert spec.arc_base_url == "https://three.arcprize.org"


def test_online_and_local_competition_modes_are_mutually_exclusive():
    with pytest.raises(ValueError, match="mutually exclusive"):
        _online_arcade_spec(Namespace(
            online_arcade=True,
            simulate_competition_arcade=True,
        ))
