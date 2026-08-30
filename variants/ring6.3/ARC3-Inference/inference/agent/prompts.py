"""Prompt templates for the analyzer agent."""

from inference.utils.grid_utils import ARC_COLOR_LEGEND

TOOL_CALL_FORMAT_GUIDANCE = (
    "When calling `python`, emit exactly the tool-call format shown elsewhere in this prompt for this model. "
    "Use only that format; do not add markdown fences, prose wrappers, or alternate tool-call syntax. "
    "Do not quote or place tool-call markup inside explanatory text; when you decide to call the tool, emit the tool call itself."
)

GAME_OVERVIEW_ADDENDUM = (
    "\n\nGame overview:\n"
    "- You are solving a multi-level grid puzzle game. \n"
    "- You are called repeatedly over the course of a run. Treat each turn as one observe-learn-act cycle: re-read the current state from the newest frame and the [MAP], update your working world model in Python, act per the strategy below, and re-evaluate next turn from the updated state.\n"
    "- Your job is to solve the entire game by clearing every level, not just the current screen.\n"
    "- Levels often build on earlier mechanics, but layouts and interactions can still change between levels.\n"
    "- Optimize for as few in-game actions as possible while still being reliable.\n"
    "- In this environment, boards are presented as 64 x 64 color grids rendered with ARC color symbols.\n"
    f"- Color legend: {ARC_COLOR_LEGEND}.\n"
)

# Ring 6 — the ARC Grid Multiverse Ontology.
#
# This is domain knowledge, not a game-specific strategy.  It tells the model
# what kind of evidence an ARC world can provide.  The Captain report in the
# first user turn supplies the particular facts earned in this world.
VIRELAI_WORLD_ADDENDUM = (
    "\n\nARC Grid Multiverse Ontology:\n"
    "- You encounter the world as successive finite grids plus the legal actions currently declared by the environment. A grid is an observation of state, not necessarily the whole state; identical visible grids do not prove identical hidden state.\n"
    "- Knowledge is grounded in observed transitions. An action connects a before-grid to an after-grid. A visual resemblance, position, color, or shape alone does not establish an object's function.\n"
    "- Cells are the observed substrate. Objects, persistence, motion, counters, levers, obstacles, and goals are compact explanations of spatial and temporal cell relationships. Treat those explanations as falsifiable models, not literal facts supplied by the pixels.\n"
    "- Controlled action-dependent change can reveal an embodied ego. Repeated change that is independent of which target or action was chosen is evidence for a counter or other autonomous process. These are hypotheses until their transition records distinguish them.\n"
    "- Causal roles are relational. A lever is established by an attributed intervention and its repeatable effects elsewhere, after ego motion and counter-like change are excluded from that attribution.\n"
    "- Hidden state is evidenced when the same visible situation and action produce different transitions under different histories. Preserve such divergences instead of forcing them into one rule.\n"
    "- A win is never inferred from appearance. It is first known when the environment reports a level or game transition. Before that observation, every still-playing state already visited is evidence of a non-win, and unexplored transitions remain possible locations of the win.\n"
    "- A proposed rule must predict an observable transition and name what future observation would falsify it. A rule that won one level is evidence for the next level, not a universal guarantee.\n"
    "\nWhat you are handed:\n"
    "- THE CAPTAIN REPORT appears in the first user turn. It is the bounded probe phase's world-specific evidence: observations, earned roles, causal findings, coverage, and explicit gaps. Read it before acting.\n"
    "- `virelai_card()` is a separate live Duck ledger view that continues updating after handoff; do not confuse it with the fixed Captain report.\n"
    "- THE MENU -- actions proven no-ops at the current state are removed from the valid-actions list. This advises; you may override it when your goal-model says otherwise.\n"
    # WO-RING6-01 Phase C.2 -- LOCKSTEP DELETION. The "How to play" discovery
    # strategy (OPEN GENERATIVELY / EGO FIRST / COUNTER SECOND / THE LEVER HUNT
    # / THE WIN FALLS OUT) told the model to find these facts itself, by
    # experiment. Ring 6's captain now runs that experiment before turn 1 and
    # hands the model the result as the field card (solver.py _virelai_opening
    # -> tool_agent.py _build_user_prompt, action_num == 0 only). Deleted here,
    # not softened -- a prompt that still teaches the hunt while the card
    # answers it has replaced nothing.
    "\nHandoff: begin from the current live frame and the Captain report. Continue investigating its named gaps when needed. If the report contains an observed winning transition, treat that transition as a tested example whose explanation still must survive the current level.\n"
)

VISUAL_GAME_ADDENDUM = (
    "\n\nVisual-game guidance:\n"
    "- Treat each board as a scene with objects, blockers, targets, adjacency, containment, motion, and symmetry.\n"
    "- Game entities are usually be rendered as connected multi-tile shapes such as 2×2, 2×3, 3×3, or longer patterned structures. Sometime they might also be 1x1 tokens."

    "- When the [MAP] announces a [COUNTER], that region is excluded from state identity and `world_changed` tells you whether a press changed anything beyond it. A changing region without a seal remains an unresolved candidate, not a known counter.\n"
    "- Use coordinates only to target actions or describe local evidence. Do not frame the objective as reaching a specific absolute row or column.\n"
    "- Re-ground on the newest frame after any score increase or abrupt scene change; the returned board may already be the next level.\n"
    "- `WIN` means the whole game is solved. Mid-run level completion is more likely to appear as a score increase while play continues.\n"
    "- Strategies may transfer loosely across levels, but layouts and mechanics can change. Re-check the new board before repeating a plan.\n"
    "- For `MOUSE`, pass `row` and `col` integer arguments. `row` is vertical position, `col` is horizontal position.\n"
)

STRUCTURED_RUNTIME_STATE_ADDENDUM = (
    "\n\nRuntime variables inside every `python` tool call:\n"
    "- `current_frame` is a lightweight frame view for the latest environment state.\n"
    "- `current_frame` exposes only `.ascii`, `.step`, `.level`, `.shape`, and `.segmentation`.\n"
    "- `current_frame.ascii` is a single newline-delimited string containing the latest board rendered with the letter-coded ARC color symbols.\n"
    "- `current_frame.segmentation` parses the board into objects. It returns `{'nodes': [...], 'adjacency_list': [...]}`.\n"
    "- Each node in `segmentation['nodes']` is one 4-connected same-color object with: `id` (index, ordered top-most-left-most), `color` (ARC color character), `hash` (a signature of the object's color and shape that ignores its position -- equal hashes mean the same object regardless of where it is, so use it to track an object across frames or to spot multiple identical objects in one frame), `pixels` (cell count), `boundary` (clockwise outer-perimeter corner points as `[row, col]`), and `children` (ids of objects fully enclosed by this one).\n"
    "- `segmentation['adjacency_list']` is a list of `[i, j]` node-id pairs whose objects share an edge.\n"
    
    "- `current_frame.step` is the current environment step count.\n"
    "- `current_frame.level` is the current level number.\n"
    "- `current_frame.shape` is a `(rows, cols)` tuple.\n"
    "- The raw numeric grid is intentionally not exposed. Use `current_frame.segmentation` as your primary view of the board -- objects, colors, shapes, containment, adjacency, and cross-frame object hashes. Use `current_frame.ascii` only to read a small, specific region; do not scan the whole board with it.\n"

    "- `history` is a chronological list of action/frame snapshots.\n"
    "- `history` is a Python list of objects, not a dict.\n"
    "- Each history entry exposes only `.action` and `.frame`; entries are not subscriptable like `entry['action']`.\n"
    "- Each `history[i].frame` is the frame after `history[i].action`; each frame exposes only `.ascii`, `.step`, `.level`, `.shape`, and `.segmentation`.\n"
    "- Important history semantics: when `history` is non-empty, `history[-1].frame` is the same latest/post-action board as `current_frame`. It is not the previous board. To inspect the state before the latest action, use `previous_frame` or `history[-2].frame` when available.\n"
    "- `previous_frame` is the frame before the most recent real environment action, or `None` if no previous frame is available.\n"
    "- `last_action` is the most recent real environment action name/display, or `None` before any real action.\n"
    "- `last_action_frame` is the post-action frame for `last_action`; it matches `current_frame` after a real action.\n"
    "- `transitions` is a chronological list of actual action transitions, excluding the initial seeded frame. Each transition exposes `.action`, `.before_frame`, `.after_frame`, `.frame` (alias of `.after_frame`), and `.result`.\n"
    "- `last_transition` is `transitions[-1]` or `None`. Its `.result` mirrors `last_action_result`; older transitions may have an empty `.result`. For before/after diffs, compare `last_transition.before_frame` to `last_transition.after_frame`; do not compare `current_frame` to `history[-1].frame`.\n"
    "- `last_action_result` is the persisted result dict from the most recent `action(...)` call. It remains available across later Python inspection calls that do not call `action(...)`, and is `{}` before any action result exists. Read transition metadata from fields/keys such as `last_action_result['board_changed']`, `last_action_result['world_changed']` (changed beyond any sealed counter), `last_action_result['done']`, `last_action_result['level_completed']`, `last_action_result['game_over']`, `last_action_result['run_complete']`, `last_action_result['reward']`, and `last_action_result['valid_actions']`.\n"
    "- `valid_actions` is the current list of valid action names (actions proven no-ops at the current state are already removed -- see the world layer).\n"
    "- `virelai_card()` renders the whole library as a readable dossier -- sections for SITUATION, OBJECTS (each sealed read with the observation that earned it and what would falsify it), ACTIONS AT THIS STATE, EXPLORATION, CAUSAL MAP, and GAPS. Prefer it over traversing the raw dict.\n"
    "- `virelai` is the full walked-state map as a dict: `{'root', 'states', 'moves', 'resets', 'counter', 'world_type', 'roster', 'ego', 'worldlines', 'drains', 'levers', 'nodes': {state_key: {'arrivals', 'actions': {name: {'tries', 'changes', 'outcomes'}}}}}`. State keys are counter-masked (a sealed counter's ticks do not mint new states), `changes` counts WORLD changes (outside any sealed counter), and `counter` lists sealed counter regions (bbox, cells, cells_per_press) or is null. `world_type` is NAV/CLICK/HYBRID from the action roster; `ego` lists sealed ego shapes (bbox, class, cells, observed per-action bearings) or is null. It is the complete ground-truth record of everywhere you have been; query it instead of re-deriving state history. `None` only before the first action.\n"
    "- Call `action(actions)` to execute one or more real environment actions from Python.\n"
    "- Pass `action(actions)` a list like `['LEFT']` or `[{'action': 'MOUSE', 'row': 4, 'col': 7}]`.\n"
    "- One action usually returns one frame, but a single action can result in a short multi-frame animation.\n"
    "- After `action(actions)` returns, `current_frame`, `previous_frame`, `history`, `transitions`, `valid_actions`, and `last_action_result` are refreshed.\n"
)

MULTIMODAL_CONTEXT_ADDENDUM = (
    "\n\nMultimodal context:\n"
    "- User turns include an attached image of the current ARC grid.\n"
    "- The image and `current_frame.ascii` are two representations of the same current frame.\n"
    "- You can use images and other tools to understand the game state and guide your strategy, each may be useful depending on the current uncertainty.\n"
)

PYTHON_ADDENDUM = (
    "\n\nPython tool guidance:\n"
    "- Use `current_frame.segmentation` as your primary view of the board -- objects, colors, containment, adjacency, and cross-frame object hashes.\n"
    "- Use `current_frame.ascii` only to read a small, specific region of the board when `segmentation` is not enough; never use it to scan or summarize the whole board.\n"
    "- Every `python` tool call starts fresh. Re-import modules or re-define any custom utility logic you need.\n"
    "- The only importable standard-library modules are: bisect, collections, copy, fractions, functools, heapq, itertools, json, math, operator, random, re, statistics, string.\n"
    "- The only tool is `python`; call it with one ephemeral `code` string.\n"
    "- Always inspect `current_frame`, `history`, and `valid_actions` from Python instead of reasoning from the raw board by eye.\n"
    "- For the most recent change, compare `previous_frame` to `current_frame`, or `last_transition.before_frame` to `last_transition.after_frame`. `history[-1].frame` is the current frame, so comparing it to `current_frame` only compares the board to itself.\n"
    "- Maintain a compact working world model: what the goal likely is (only once a win has shown you), what remains uncertain, what rule won the last level, and what plan best fits the evidence so far. Structural facts (what states exist, what actions did where) live in the [MAP] and `virelai` -- do not restate them.\n"
    "- IMPORTANT: Especially when the game is about making an agent navigate to a target, it is usually safer to write an explicit search algorithm such as BFS. More generally, once a rule is in hand and the action order is unclear, pathfinding, flood fill, BFS, DFS, beam search, shortest-path search, limited action-sequence search, or custom heuristics are all valid tools.\n"
    "- Before the first observed win, use the Captain report's gaps and the live map to choose informative unexplored transitions. After an observed win, prefer its shortest reliable reproduction and reopen inquiry where that prediction fails.\n"
    "- Inspect current and history frames from Python instead of describing frames freehand.\n"
    "- Never print or echo full board frames. Return only compact derived summaries such as object lists, diffs, coordinates, counts, or tiny local crops.\n"
    "- Keep tool-output context size minimal and decision-oriented so you can quickly compare before/after state. It's fine to write a lot of python code, just make the output short and interpretable\n"
    "- A strong default loop is: read the [MAP] and the newest frame, pick the press the strategy calls for (untried here in LEARN; the rule's next step after a win), execute it with `action(...)`, then inspect what changed.\n"
    "- For object tracking, use `segmentation` node hashes -- equal hashes are the same object regardless of position. For state tracking, the [MAP] already holds it.\n"
    "- `last_action_result['world_changed']` already answers whether the last press changed anything beyond a sealed counter; a press with `world_changed` False did not work, whatever the counter did.\n"
    "- Use `print(...)` for compact summaries, or assign a final compact object to `result`.\n"
    "- Call `action(...)` inside Python rather than returning action text in the chat.\n"
    "- `action(...)` accepts an ordered list of one or more actions. Once your code has selected a reliable sequence, it is often useful to batch it.\n"
    "- You can also call `action(...)` multiple times in one Python snippet, including inside loops. Each call updates the preloaded variables before execution continues.\n"
    "- If an action result reports `game_over`, `run_complete`, `level_completed`, or `done`, stop acting immediately and re-ground on the next turn.\n"
)

COMPACT_TOOL_SESSION_ADDENDUM = (
    "\n\nTool session rules:\n"
    "- You have exactly one tool: `python`.\n"
    f"- {TOOL_CALL_FORMAT_GUIDANCE}\n"
    "- The `python` tool code is not saved between calls, so rewrite any custom utility logic you still need.\n"
    "- You can call the `python` tool as many times as you want per step. Investigate until your code has a clear probe or plan.\n"
    "- Do not ration tool calls when the state is unclear. Spend extra tool calls to confirm what changed between frames.\n"
    "- After `action(...)` returns, the structured runtime state is refreshed before the next Python statement and before the next tool call. Inspection-only Python calls do not clear `last_action_result`.\n"
    "- Each `python` tool call has a hard time limit of 30 seconds.\n"
    "- Tool responses are capped to about {tool_output_tokens} tokens. If a response is cut off, the tool result will tell you that.\n"
    "- Keep code snippets short and purpose-built rather than dumping large frameworks into one call.\n"
)
