"""Prompt templates for the analyzer agent."""

from inference.utils.grid_utils import ARC_COLOR_LEGEND
TOOL_CALL_FORMAT_GUIDANCE = (
    "When calling `python`, emit exactly the tool-call format shown elsewhere in this prompt for this model. "
    "Use only that format; do not add markdown fences, prose wrappers, or alternate tool-call syntax. "
    "Do not quote or place tool-call markup inside explanatory text; when you decide to call the tool, emit the tool call itself."
)

CYBERNETIC_FLIPBOOK_ONTOLOGY = (
    "\n\nCybernetic flipbook ontology:\n"
    "- Treat the run as a flipbook of observed integer-grid states connected by opaque actions. "
    "Integers and action numbers have no supplied semantic meaning.\n"
    "- Probe to discover persistent bodies, direct control, terrain, counters, levers, environmental forces, "
    "driven objects, inert objects, and repeatable transformation laws. Keep competing models alive until evidence separates them.\n"
    "- A useful world model explains what changes, what stays invariant, under which action and conditions, "
    "and predicts a later observation. Names without mechanisms are not understanding.\n"
    "- A win is a platform-observed event. Never infer, predict, or declare that an unobserved state is a win. "
    "Explore novel counter-masked configurations only after the prerequisite mechanics are demonstrated.\n"
)

GAME_OVERVIEW_ADDENDUM = (
    "\n\nGame overview:\n"
    "- You are solving a multi-level grid puzzle game. \n"
    "- You are called repeatedly over the course of a run. Treat each turn as one observe-plan-act cycle: re-understand the current state from the newest frame, update your working world model in Python, choose the next best action or short sequence against the goal as currently understood, execute it, and expect to re-evaluate on the next turn from the updated state.\n"
    "- Your job is to solve the entire game by clearing every level, not just the current screen.\n"
    "- Levels often build on earlier mechanics, but layouts and interactions can still change between levels.\n"
    "- Optimize for as few in-game actions as possible while still being reliable.\n"
    "- In this environment, boards are presented as 64 x 64 color grids rendered with ARC color symbols.\n"
    f"- Color legend: {ARC_COLOR_LEGEND}.\n"
)

GATED_GAME_OVERVIEW_ADDENDUM = (
    "\n\n# Campaign context\n"
    "- You are investigating a deterministic multi-level interactive grid world.\n"
    "- You are called repeatedly. Each turn extends one continuous evidence record.\n"
    "- The current gate, rather than an inferred winning objective, determines the immediate task.\n"
    "- Levels may preserve earlier physics while adding, removing, or rearranging mechanisms. "
    "Treat prior laws as testable evidence.\n"
    "- Boards are 64 x 64 grids rendered with ARC color symbols.\n"
    f"- Color legend: {ARC_COLOR_LEGEND}.\n"
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

GATED_VISUAL_GAME_ADDENDUM = (
    "\n\n# Visual evidence guidance\n"
    "- Treat each frame as integer-grid evidence. Connected regions, repeated shapes, adjacency, "
    "containment, and persistence are candidate structure, not supplied function.\n"
    "- A persistent body, pointer locus, object, counter, lever, obstacle, or target is an "
    "interpretation that must satisfy the active gate's evidence standard.\n"
    "- Use coordinates only for authorized actions or local evidence. Absolute coordinates are "
    "addresses, not goals.\n"
    "- Re-ground after any reported level transition or abrupt scene change.\n"
    "- `WIN` means the whole game is solved; a level transition is evidence to preserve, not a "
    "license to assume every earlier law transfers unchanged.\n"
    "- For `ACTION6`, pass integer `row` and `col` arguments.\n"
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
    "- `valid_actions` is the current list of valid action names.\n"
    "- Call `action(actions)` to execute one or more real environment actions from Python.\n"
    "- Pass `action(actions)` a list like `['LEFT']` or `[{'action': 'MOUSE', 'row': 4, 'col': 7}]`.\n"
    "- One action usually returns one frame, but a single action can result in a short multi-frame animation.\n"
    "- After `action(actions)` returns, `current_frame`, `previous_frame`, `history`, `transitions`, `valid_actions`, and `last_action_result` are refreshed.\n"
)

VIRELAI_TOOL_ADDENDUM = (
    "\n\nVirelai evidence tool:\n"
    "- `virelai(operation, **parameters)` provides observation queries and a separate intent operation that records a proposed experiment. Neither consumes a game action.\n"
    "- It preserves raw evidence across Python calls: observed states, action transitions, changed cells, level wins, and capture gaps.\n"
    "- The persistent world-model operations are `world`, `diff`, `object`, `mechanic`, and `model_evidence`. Raw-record operations remain available; call `virelai('help')` for details.\n"
    "- Useful examples: `virelai('overview')`, `virelai('recent', limit=5)`, `virelai('transition', step='last')`, and `virelai('wins')`.\n"
    "- Query it when past evidence can answer a concrete question or prevent repeating work. Ask for the smallest relevant record.\n"
    "- Virelai reports observations; it does not choose actions or replace your judgment.\n"
    "- Use `world` for the compact accumulated model, `diff` after a level change, and a focused object, mechanic, or evidence lookup only when it answers the current question.\n"
    "- Repeated structural types across levels are correspondences, not proof of the same role. Reconfirm behavior in the new level.\n"
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
    "- Maintain a compact working world model: what entities or regions exist, what actions seem to do, what the goal likely is, what remains uncertain, and what plan best fits the evidence so far.\n"
    "- IMPORTANT: Especially when the game is about making an agent navigate to a target, it is usually safer to write an explicit search algorithm such as BFS. More generally, when the objective is understood but the best action order is unclear, pathfinding, flood fill, BFS, DFS, beam search, shortest-path search, limited action-sequence search, or custom heuristics are all valid.\n"
    "- Optimize for the shortest reliable sequence that advances the current goal as described by your world model. If confidence is low, program a discriminating probe and revise the world model from the result.\n"
    "- Once the important state variables and action effects are sufficiently understood, stop probing and search in the inferred state space.\n"
    "- Inspect current and history frames from Python instead of describing frames freehand.\n"
    "- Never print or echo full board frames. Return only compact derived summaries such as object lists, diffs, coordinates, counts, or tiny local crops.\n"
    "- Keep tool-output context size minimal and decision-oriented so you can quickly compare before/after state. It's fine to write a lot of python code, just make the output short and interpretable\n"
    "- A strong default loop is: summarize the board, infer the desired environment change, write a small scorer or search over candidate sequences, execute the best probe or plan with `action(...)`, then inspect again until you understand exactly what changed.\n"
    "- For object tracking, match objects by color, overlap, bounding box proximity, area change, and edge contact rather than by exact coordinates alone.\n"
    "- For frame diffs, summarize changed cells, color transitions, appearing/disappearing components, movement candidates, and small local row slices around the changed region.\n"
    "- After every action, verify whether gameplay objects changed or whether only a timer, progress bar, or remaining-step bar moved. Do not treat HUD-only changes as evidence that the move worked.\n"
    "- Use `print(...)` for compact summaries, or assign a final compact object to `result`.\n"
    "- Call `action(...)` inside Python rather than returning action text in the chat.\n"
    "- `action(...)` accepts an ordered list of one or more actions. Once your code has selected a reliable sequence, it is often useful to batch it.\n"
    "- You can also call `action(...)` multiple times in one Python snippet, including inside loops. Each call updates the preloaded variables before execution continues.\n"
    "- If an action result reports `game_over`, `run_complete`, `level_completed`, or `done`, stop acting immediately and re-ground on the next turn.\n"
)

GATED_PYTHON_ADDENDUM = PYTHON_ADDENDUM.replace(
    "- Maintain a compact working world model: what entities or regions exist, what actions seem to do, what the goal likely is, what remains uncertain, and what plan best fits the evidence so far.\n",
    "- Maintain a compact evidence model for the current gate: live alternatives, observations, candidate mechanism, remaining uncertainty, and the next authorized discriminating test.\n",
).replace(
    "- Optimize for the shortest reliable sequence that advances the current goal as described by your world model. If confidence is low, program a discriminating probe and revise the world model from the result.\n",
    "- Optimize for the smallest authorized experiment that answers the current gate. If evidence is insufficient, preserve the alternatives and execute the gate's next discriminating probe.\n",
).replace(
    "- Once the important state variables and action effects are sufficiently understood, stop probing and search in the inferred state space.\n",
    "- Do not self-advance to a later target. The gate controller closes the current target when its explanation and evidence contract are satisfied.\n",
).replace(
    "- A strong default loop is: summarize the board, infer the desired environment change, write a small scorer or search over candidate sequences, execute the best probe or plan with `action(...)`, then inspect again until you understand exactly what changed.\n",
    "- The gated loop is: read the gate, inspect the relevant evidence, state the live alternatives, obtain the next authorized probe, execute it exactly, and update the candidate law from the result.\n",
).replace(
    "- After every action, verify whether gameplay objects changed or whether only a timer, progress bar, or remaining-step bar moved. Do not treat HUD-only changes as evidence that the move worked.\n",
    "- After every action, compare raw changes with the active gate's declared scope. Do not assign a changed region a gameplay or bookkeeping role before the relevant gate establishes it.\n",
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
