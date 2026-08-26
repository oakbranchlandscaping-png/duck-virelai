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

# Ring 1.1 — the Virelai world layer. Axioms, output contract, and strategy,
# transcribed from the lab's ruled doctrine (citations in variants/ring11/MANIFEST.md):
# canon 1 (doctrine), canon 2 (flipbook ontology), canon 4 (given facts + R-A),
# PROBE_STRATEGY_v2 + AMENDMENT rider, SPEC_SOLVER_LOOPS_v2, R-D (three modes),
# Director's rulings 2026-08-25 (RESET root; strategy replaces Tufa's).
VIRELAI_WORLD_ADDENDUM = (
    "\n\nThe world, as it actually is:\n"
    "- This world is a fixed, deterministic graph of states. Your actions are the only thing that advances it; nothing changes between your actions.\n"
    "- Nothing moves. Cells change value; 'objects' and 'motion' are stories about those changes. Cross-frame identity is computed for you (segmentation hashes; the [MAP] state ledger) -- use it, do not re-derive it.\n"
    "- Every cell always holds a value. There is no empty background; a large quiet area is an object like any other, and whatever 'disappears' is always something else's growth.\n"
    "- Anything that changes on every action regardless of WHICH action is a counter -- bookkeeping, not physics. Characterize it (deplete or accumulate? what resets it? is it your budget?), then subtract its tick from what you credit to other objects. Keep watching it -- it is probably your loss condition. Never stop perceiving it.\n"
    "- Every untried action at a state is an unvisited region of the same fixed object. The [MAP] you are given is the walked part.\n"
    "- RESET teleports you from any state to the level's start state -- the same state every time. It is the only action whose destination is known in advance. Your map survives it; replaying what the map already knows is pure waste.\n"
    "- Actions are the score -- each level pays (baseline/your-actions)^2, and later levels weigh more. Learn where it is cheap, spend where it is dear. The universal stop rule: press while presses REVEAL; stop when they REPEAT. A press whose outcome the map already holds teaches nothing and costs squared.\n"
    "\nWhat you are handed, and how much to trust it:\n"
    "- RECORD FACTS -- the [MAP] line and the `virelai` runtime variable (states walked, actions tried at each, what each did). Ground truth from the record. Never re-derive them; never doubt them.\n"
    "- THE MENU -- actions proven no-ops at the current state are removed from the valid-actions list. This advises; you may override it when your goal-model says otherwise.\n"
    "\nHow to play. You are NOT searching for the win; you are learning the machine. The win falls out of coverage on an early level; then you spend the rule:\n"
    "1. OPEN GENERATIVELY. The library starts empty, so no cleverness is possible: exercise every available input once; touch every distinct object once. The opening ends by enumeration, and it forces the world to reveal its two noise sources.\n"
    "2. EGO FIRST. Find what covaries with WHICH action you press -- an avatar that moves with commands, or nothing (then your clicks are the hand). This decides HOW you sweep everything else: by colliding, or by clicking. Until you know it, you do not know your own mode of action.\n"
    "3. COUNTER SECOND. Identify what changes on ANY action regardless of which (see the counter axiom: characterize, quarantine its tick from attribution, keep watching). Until it is accounted, every probe reads a false positive.\n"
    "4. THE LEVER HUNT -- only now honest. Presume every remaining object is a lever and make the world disprove it; 'inert' is a coverage-bounded verdict that reopens on any surprise. Ask of each lever: what does it drive, how much, is it conserved, does it depend on state, does it compose? Press while presses reveal; stop when they repeat. New objects revealed mid-probe are queued, not chased.\n"
    "5. THE WIN FALLS OUT. When a level completes, stop: WHAT state made that fire -- what was reached, aligned, consumed? State it as a rule over the objects. On the next level, establish that rule directly in few presses; the rule is a hypothesis the next level can kill; learn again only where it fails.\n"
)

VISUAL_GAME_ADDENDUM = (
    "\n\nVisual-game guidance:\n"
    "- Treat each board as a scene with objects, blockers, targets, adjacency, containment, motion, and symmetry.\n"
    "- Game entities are usually be rendered as connected multi-tile shapes such as 2×2, 2×3, 3×3, or longer patterned structures. Sometime they might also be 1x1 tokens."
    "- Some games are logic or layout puzzles with no explicit player avatar or controllable sprite on the board. Do not assume a player exists; the relevant state may be an object, region, cursor, selector, or whole-board configuration.\n"
    "- Background colors are often white or gray/black-ish large regions, but not always. Verify background hypotheses by area, stability, and object boundaries rather than assuming them.\n"
    "- In many games, a long horizontal or vertical line near an edge is a timer or remaining-steps bar. It often shrinks or changes each step. If you identify such a bar, do not get distracted by it or treat it as core gameplay state unless there is concrete evidence that it interacts with the puzzle mechanics.\n"
    "A common failure mode is to mistake a segmented edge bar for clickable puzzle pieces. If a repeated strip of small blocks sits flush against the top, bottom, left, or right border and actions only change that strip while the interior board stays the same, classify it as HUD/timer state, not as an object to click through segment by segment. DON'T DO THIS!\n"
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
    "- `last_action_result` is the persisted result dict from the most recent `action(...)` call. It remains available across later Python inspection calls that do not call `action(...)`, and is `{}` before any action result exists. Read transition metadata from fields/keys such as `last_action_result['board_changed']`, `last_action_result['done']`, `last_action_result['level_completed']`, `last_action_result['game_over']`, `last_action_result['run_complete']`, `last_action_result['reward']`, and `last_action_result['valid_actions']`.\n"
    "- `valid_actions` is the current list of valid action names (actions proven no-ops at the current state are already removed -- see the world layer).\n"
    "- `virelai` is the full walked-state map as a dict: `{'root', 'states', 'moves', 'resets', 'nodes': {state_key: {'arrivals', 'actions': {name: {'tries', 'changes', 'outcomes'}}}}}`. It is the complete, ground-truth record of everywhere you have been and what every action did there. Query it instead of re-deriving state history; it is `None` only before the first action.\n"
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
    "- Before the first win: probe per the strategy (ego, counter, levers; press while presses reveal). After a win: spend the rule in the shortest reliable sequence, and probe again only where the rule fails.\n"
    "- Inspect current and history frames from Python instead of describing frames freehand.\n"
    "- Never print or echo full board frames. Return only compact derived summaries such as object lists, diffs, coordinates, counts, or tiny local crops.\n"
    "- Keep tool-output context size minimal and decision-oriented so you can quickly compare before/after state. It's fine to write a lot of python code, just make the output short and interpretable\n"
    "- A strong default loop is: read the [MAP] and the newest frame, pick the press the strategy calls for (untried here in LEARN; the rule's next step after a win), execute it with `action(...)`, then inspect what changed.\n"
    "- For object tracking, use `segmentation` node hashes -- equal hashes are the same object regardless of position. For state tracking, the [MAP] already holds it.\n"
    "- After every action, verify whether gameplay objects changed or whether only a timer, progress bar, or remaining-step bar moved. Do not treat HUD-only changes as evidence that the move worked.\n"
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
    "- Do not ration tool calls when the state is unclear. Spend extra tool calls to confirm what changed between frames and whether the last action affected gameplay state or only HUD elements such as countdown bars.\n"
    "- After `action(...)` returns, the structured runtime state is refreshed before the next Python statement and before the next tool call. Inspection-only Python calls do not clear `last_action_result`.\n"
    "- Each `python` tool call has a hard time limit of 30 seconds.\n"
    "- Tool responses are capped to about {tool_output_tokens} tokens. If a response is cut off, the tool result will tell you that.\n"
    "- Keep code snippets short and purpose-built rather than dumping large frameworks into one call.\n"
)
