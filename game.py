# game.py — pure logic, no screen calls
# Cell states
EMPTY = 0
SHIP  = 1
HIT   = 2
MISS  = 3

# Ship sizes: Carrier, Battleship, Cruiser, Submarine, Destroyer
SHIP_SIZES  = [5, 4, 3, 3, 2]
SHIP_NAMES  = ["Carrier", "Battleship", "Cruiser", "Submarine", "Destroyer"]
TOTAL_CELLS = 17  # 5+4+3+3+2

BOARD_SIZE = 10

# Orientation constants
HORIZONTAL = 0
VERTICAL   = 1

# ── Board helpers ──────────────────────────────────────────────────────────────

def make_board():
    """Return a flat 100-element list of EMPTY cells."""
    return [EMPTY] * (BOARD_SIZE * BOARD_SIZE)

def _idx(r, c):
    return r * BOARD_SIZE + c

def get_cell(board, r, c):
    return board[_idx(r, c)]

def set_cell(board, r, c, val):
    board[_idx(r, c)] = val

# ── Placement ─────────────────────────────────────────────────────────────────

def ship_cells(r, c, size, orientation):
    """Return list of (r,c) tuples for a ship, or [] if out of bounds."""
    cells = []
    for i in range(size):
        if orientation == HORIZONTAL:
            nc = c + i
            nr = r
        else:
            nc = c
            nr = r + i
        if nr < 0 or nr >= BOARD_SIZE or nc < 0 or nc >= BOARD_SIZE:
            return []
        cells.append((nr, nc))
    return cells

def can_place(board, r, c, size, orientation):
    """True if placement is in bounds and no overlap."""
    cells = ship_cells(r, c, size, orientation)
    if not cells:
        return False
    for (nr, nc) in cells:
        if board[_idx(nr, nc)] != EMPTY:
            return False
    return True

def place_ship(board, r, c, size, orientation):
    """Place ship cells (SHIP) on board. Returns True on success."""
    if not can_place(board, r, c, size, orientation):
        return False
    for (nr, nc) in ship_cells(r, c, size, orientation):
        board[_idx(nr, nc)] = SHIP
    return True

# ── Firing ────────────────────────────────────────────────────────────────────

def fire(board, r, c):
    """
    Fire at (r,c).
    Returns:
      0 — already fired (HIT or MISS)
      1 — miss
      2 — hit
    """
    state = board[_idx(r, c)]
    if state == HIT or state == MISS:
        return 0
    if state == SHIP:
        board[_idx(r, c)] = HIT
        return 2
    # EMPTY
    board[_idx(r, c)] = MISS
    return 1

def already_fired(board, r, c):
    s = board[_idx(r, c)]
    return s == HIT or s == MISS

# ── Win condition ─────────────────────────────────────────────────────────────

def count_hits(board):
    h = 0
    for v in board:
        if v == HIT:
            h += 1
    return h

def is_defeated(board):
    """True when all TOTAL_CELLS ship cells have been hit."""
    return count_hits(board) >= TOTAL_CELLS

# ── CPU random placement ──────────────────────────────────────────────────────
# Uses a simple LCG so we avoid importing random (saves heap).

_lcg_state = [12345]

def _lcg():
    _lcg_state[0] = (_lcg_state[0] * 1664525 + 1013904223) & 0xFFFFFFFF
    return _lcg_state[0]

def seed_rng(val):
    _lcg_state[0] = val & 0xFFFFFFFF

def cpu_place_ships(board):
    """Fill board with all 5 ships at random valid positions."""
    for size in SHIP_SIZES:
        placed = False
        attempts = 0
        while not placed and attempts < 1000:
            r = _lcg() % BOARD_SIZE
            c = _lcg() % BOARD_SIZE
            o = _lcg() % 2
            placed = place_ship(board, r, c, size, o)
            attempts += 1

def cells_remaining(board):
    """Count unhit SHIP cells still on the board."""
    return sum(1 for v in board if v == SHIP)

def check_sunk(board, r, c):
    """
    After a hit at (r,c), check if a complete ship was just sunk.
    Scans horizontal then vertical runs of HITs from (r,c).
    Returns (size, name) if sunk, or (0, "") if not.
    """
    for horiz in (True, False):
        run_len = 1
        # extend in negative direction
        i = 1
        end_neg_ok = True
        while True:
            nr = r if horiz else r - i
            nc = c - i if horiz else c
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr * BOARD_SIZE + nc] == HIT:
                    run_len += 1
                    i += 1
                    continue
                elif board[nr * BOARD_SIZE + nc] == SHIP:
                    end_neg_ok = False  # ship continues — not sunk
            break
        if not end_neg_ok:
            continue
        # extend in positive direction
        i = 1
        end_pos_ok = True
        while True:
            nr = r if horiz else r + i
            nc = c + i if horiz else c
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                if board[nr * BOARD_SIZE + nc] == HIT:
                    run_len += 1
                    i += 1
                    continue
                elif board[nr * BOARD_SIZE + nc] == SHIP:
                    end_pos_ok = False
            break
        if not end_pos_ok:
            continue
        if run_len > 1:
            # Match run length to a ship name
            for idx in range(len(SHIP_SIZES)):
                if SHIP_SIZES[idx] == run_len:
                    return run_len, SHIP_NAMES[idx]
    return 0, ""
