# ai.py — hunt/target AI for the CPU player
# Relies on game constants imported below.
from game import BOARD_SIZE, HIT, MISS, EMPTY, SHIP, already_fired

# AI modes
_HUNT   = 0
_TARGET = 1

# Internal state — pre-allocated, no dicts
_mode        = [_HUNT]          # current mode
_last_hit_r  = [-1]             # row of first hit in target chain
_last_hit_c  = [-1]             # col of first hit in target chain
_axis        = [-1]             # 0=row, 1=col locked axis; -1=unknown
_axis_dir    = [0]              # +1 or -1 along axis
_probe_r     = [-1]             # current probe position row
_probe_c     = [-1]             # current probe position col
_probing     = [False]          # True while we are advancing along axis

# Target stack: up to 4 candidate cells stored as flat [r0,c0,r1,c1,...] pairs
_STACK_MAX = 8
_tgt_stack = [-1] * (_STACK_MAX * 2)
_tgt_top   = [0]

def _push(r, c):
    t = _tgt_top[0]
    if t < _STACK_MAX:
        _tgt_stack[t * 2]     = r
        _tgt_stack[t * 2 + 1] = c
        _tgt_top[0] = t + 1

def _pop():
    t = _tgt_top[0]
    if t == 0:
        return -1, -1
    t -= 1
    _tgt_top[0] = t
    return _tgt_stack[t * 2], _tgt_stack[t * 2 + 1]

def _clear_stack():
    _tgt_top[0] = 0

def _reset():
    _mode[0]       = _HUNT
    _last_hit_r[0] = -1
    _last_hit_c[0] = -1
    _axis[0]       = -1
    _axis_dir[0]   = 0
    _probing[0]    = False
    _clear_stack()

def _push_adjacent(board, r, c, shots):
    """Push all unfired orthogonal neighbours onto the target stack."""
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if not already_fired(board, nr, nc) and not _in_shots(shots, nr, nc):
                _push(nr, nc)

def _in_shots(shots, r, c):
    # shots is a flat list of (r,c) pairs
    i = 0
    while i < len(shots) - 1:
        if shots[i] == r and shots[i + 1] == c:
            return True
        i += 2
    return False

# Hunt: checkerboard — only fire at cells where (r+c) % 2 == 0
# We iterate through a pre-built candidate list derived on demand.

def _hunt_shot(board):
    """Pick a random-ish untried hunt cell using checkerboard parity."""
    # Find first unchecked checkerboard cell (deterministic scan is fine for
    # embedded; the board state already provides enough variety).
    # To add pseudo-randomness we start from a varying offset.
    best_r, best_c = -1, -1
    count = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r + c) % 2 == 0 and not already_fired(board, r, c):
                count += 1
    if count == 0:
        # Fall back: any unfired cell
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if not already_fired(board, r, c):
                    return r, c
        return 0, 0

    # Pick pseudo-random index among candidates
    from game import _lcg
    target_idx = _lcg() % count
    i = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if (r + c) % 2 == 0 and not already_fired(board, r, c):
                if i == target_idx:
                    return r, c
                i += 1
    return 0, 0

def _ship_sunk_at(board, r, c):
    """
    Heuristic: a ship is considered sunk when the cell that was just hit
    has no adjacent SHIP cell remaining.  Full sunk-tracking would need the
    original ship list; this approximation is sufficient for resetting the AI.
    """
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            if board[nr * BOARD_SIZE + nc] == SHIP:
                return False
    return True

# ── Public API ─────────────────────────────────────────────────────────────────

def ai_reset():
    """Call this before starting a new game."""
    _reset()

def ai_take_shot(board, shots_taken):
    """
    Decide where the AI fires next.
    board       — flat 100-element list (game.BOARD_SIZE²) with cell states
    shots_taken — flat list [r0,c0,r1,c1,...] of all previous AI shots
    Returns (row, col).
    After calling, the caller must fire at that cell and then call
    ai_notify_result(board, row, col, result) to update AI state.
    """
    if _mode[0] == _HUNT:
        return _hunt_shot(board)

    # TARGET mode: pop from stack
    while _tgt_top[0] > 0:
        r, c = _pop()
        if not already_fired(board, r, c):
            return r, c
    # Stack exhausted without sinking — back to hunt
    _reset()
    return _hunt_shot(board)

def ai_notify_result(board, r, c, result):
    """
    Inform the AI of the outcome of a shot.
    result: 1=miss, 2=hit  (same as game.fire() return values)
    """
    if result == 1:  # miss
        if _mode[0] == _TARGET and _probing[0]:
            # Reverse direction along current axis
            _probing[0] = False
            _axis_dir[0] = -_axis_dir[0]
            # Push cells in the new direction from the first hit
            lr = _last_hit_r[0]
            lc = _last_hit_c[0]
            for step in range(1, BOARD_SIZE):
                if _axis[0] == 0:
                    nr, nc = lr + _axis_dir[0] * step, lc
                else:
                    nr, nc = lr, lc + _axis_dir[0] * step
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if not already_fired(board, nr, nc):
                        _push(nr, nc)
                    else:
                        break
                else:
                    break
        return

    # Hit
    if _mode[0] == _HUNT:
        _mode[0]       = _TARGET
        _last_hit_r[0] = r
        _last_hit_c[0] = c
        _axis[0]       = -1
        _clear_stack()
        _push_adjacent(board, r, c, [])
    else:
        # Second+ hit in TARGET mode — lock axis
        if _axis[0] == -1:
            lr = _last_hit_r[0]
            lc = _last_hit_c[0]
            if r == lr:
                _axis[0] = 1       # column axis
                _axis_dir[0] = 1 if c > lc else -1
            else:
                _axis[0] = 0       # row axis
                _axis_dir[0] = 1 if r > lr else -1
            _probing[0] = True
            _clear_stack()
            # Push continuation from this hit in same direction
            for step in range(1, BOARD_SIZE):
                if _axis[0] == 0:
                    nr, nc = r + _axis_dir[0] * step, c
                else:
                    nr, nc = r, c + _axis_dir[0] * step
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                    if not already_fired(board, nr, nc):
                        _push(nr, nc)
                    else:
                        break
                else:
                    break

    # Check if ship sunk
    if _ship_sunk_at(board, r, c):
        _reset()
