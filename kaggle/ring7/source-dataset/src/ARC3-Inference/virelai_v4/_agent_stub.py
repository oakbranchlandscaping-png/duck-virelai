"""Ring 6. Replaces agents.agent.Agent for the hybrid.

virelai.py reads exactly three attributes off its base class -- game_id,
action_counter and recorder -- and guards recorder with hasattr for "unit
tests, custom harnesses". This provides the first two and deliberately not
the third. It replaces the whole arc_agi / pydantic / Recorder / tracing
chain, none of which the hybrid has or needs.

If a fourth attribute is ever required, that is a HALT: it means virelai.py
changed and the stub was built against a stale reading.
"""


class Agent:
    def __init__(self, game_id: str = "", **kwargs):
        self.game_id = game_id
        self.action_counter = 0
