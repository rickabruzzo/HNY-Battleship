# __init__.py — Honeycomb Battleship for Tufty 2350 / Badgeware (BadgeOS)
import sys, os
sys.path.insert(0, "/system/apps/battleship")
os.chdir("/system/apps/battleship")

badge.mode(HIRES)

import game
import ai
import renderer

# ── Load PNG assets once ───────────────────────────────────────────────────────
_img_logo     = Image.load("assets/hc_logo_white.png")
_img_logomark = Image.load("assets/hc_logomark_white.png")
renderer.set_images(_img_logo, _img_logomark)

# ── Game-phase constants ───────────────────────────────────────────────────────
PHASE_MENU        = 0
PHASE_INSTRUCTIONS= 1
PHASE_PLACE_P1    = 2
PHASE_PLACE_P2    = 3
PHASE_PASS_PLACE  = 4   # pass device before P2 placement
PHASE_BATTLE      = 5
PHASE_PASS_BATTLE = 6   # pass device between battle turns
PHASE_VICTORY     = 7

# ── Persistent game state (no dicts, no dynamic alloc in update) ───────────────
_phase          = [PHASE_MENU]
_mode_1p        = [True]       # True = 1-player, False = 2-player
_menu_sel       = [0]

# Boards: pre-allocated flat 100-element lists
_board_p1  = game.make_board()   # P1 fleet / incoming shots
_board_p2  = game.make_board()   # P2 (or CPU) fleet / incoming shots
_tgt_p1    = game.make_board()   # P1's targeting view of P2's board
_tgt_p2    = game.make_board()   # P2's targeting view of P1's board (2p only)

# Placement state
_place_ship_idx  = [0]     # which ship we are placing (0-4)
_place_cursor_r  = [4]
_place_cursor_c  = [4]
_place_orient    = [game.HORIZONTAL]
_place_preview_r = [-1]    # cell where A was first pressed
_place_preview_c = [-1]
_place_error     = [0]     # frames remaining to show error flash
_placing_p1_done = [False]

# Battle state
_battle_cursor_r = [4]
_battle_cursor_c = [4]
_current_player  = [1]     # 1 or 2
_warn_ticks      = [0]     # badge.ticks when "already fired" warning started
_show_warn       = [False]
_winner          = [""]

# Pass screen
_pass_msg        = [""]
_pass_next_phase = [PHASE_BATTLE]

# ── Helper: reset everything for a new game ───────────────────────────────────

def _reset_boards():
    for i in range(100):
        _board_p1[i] = game.EMPTY
        _board_p2[i] = game.EMPTY
        _tgt_p1[i]   = game.EMPTY
        _tgt_p2[i]   = game.EMPTY

def _reset_placement():
    _place_ship_idx[0]  = 0
    _place_cursor_r[0]  = 4
    _place_cursor_c[0]  = 4
    _place_orient[0]    = game.HORIZONTAL
    _place_preview_r[0] = -1
    _place_preview_c[0] = -1
    _place_error[0]     = 0
    _placing_p1_done[0] = False

def _reset_battle():
    _battle_cursor_r[0] = 4
    _battle_cursor_c[0] = 4
    _current_player[0]  = 1
    _show_warn[0]       = False
    ai.ai_reset()

def _seed_rng():
    # Seed with low bits of badge.ticks for variety
    game.seed_rng(badge.ticks & 0xFFFF)

# ── Cursor movement helper ────────────────────────────────────────────────────

def _move_cursor(r_ref, c_ref, up, down, left, right, size=10):
    moved = False
    if up:
        if r_ref[0] > 0:
            r_ref[0] -= 1
            moved = True
    if down:
        if r_ref[0] < size - 1:
            r_ref[0] += 1
            moved = True
    if left:
        if c_ref[0] > 0:
            c_ref[0] -= 1
            moved = True
    if right:
        if c_ref[0] < size - 1:
            c_ref[0] += 1
            moved = True
    return moved

# ── Phase handlers ────────────────────────────────────────────────────────────

def _handle_menu():
    if badge.pressed(BUTTON_UP):
        _menu_sel[0] = (_menu_sel[0] - 1) % 3
    if badge.pressed(BUTTON_DOWN):
        _menu_sel[0] = (_menu_sel[0] + 1) % 3
    if badge.pressed(BUTTON_A):
        sel = _menu_sel[0]
        if sel == 0:   # 1 player
            _mode_1p[0] = True
            _seed_rng()
            _reset_boards()
            _reset_placement()
            _phase[0] = PHASE_PLACE_P1
        elif sel == 1: # 2 players
            _mode_1p[0] = False
            _seed_rng()
            _reset_boards()
            _reset_placement()
            _phase[0] = PHASE_PLACE_P1
        else:          # instructions
            _phase[0] = PHASE_INSTRUCTIONS
    renderer.draw_menu(_menu_sel[0])

def _handle_instructions():
    if badge.pressed(BUTTON_B):
        _phase[0] = PHASE_MENU
    renderer.draw_instructions()

def _handle_placement(board, player_num):
    """Shared placement handler for P1 and P2."""
    r = _place_cursor_r
    c = _place_cursor_c

    up    = badge.pressed(BUTTON_UP)
    down  = badge.pressed(BUTTON_DOWN)
    left  = badge.pressed(BUTTON_A)    # A = left
    right = badge.pressed(BUTTON_B)    # B = right (during placement only)
    rot   = badge.pressed(BUTTON_C)
    fire  = badge.pressed(BUTTON_A)    # also A — dual role handled below

    # Rotation
    if rot:
        _place_orient[0] ^= 1
        _place_preview_r[0] = -1  # cancel preview on rotate
        _place_preview_c[0] = -1

    # Movement (A doubles as left AND confirm; if moved, cancel confirm logic)
    moved = _move_cursor(r, c, up, down, left, right)
    if moved:
        _place_preview_r[0] = -1
        _place_preview_c[0] = -1

    # Placement confirm via A (only if not moved this frame)
    if fire and not moved:
        cr, cc = r[0], c[0]
        idx  = _place_ship_idx[0]
        size = game.SHIP_SIZES[idx]
        orient = _place_orient[0]

        if _place_preview_r[0] == cr and _place_preview_c[0] == cc:
            # Second press on same cell — confirm
            if game.can_place(board, cr, cc, size, orient):
                game.place_ship(board, cr, cc, size, orient)
                _place_ship_idx[0] += 1
                _place_preview_r[0] = -1
                _place_preview_c[0] = -1
                if _place_ship_idx[0] >= len(game.SHIP_SIZES):
                    # All ships placed
                    _placement_done(player_num)
                    return
            else:
                _place_error[0] = 3
        else:
            # First press — preview (validate visually)
            if game.can_place(board, cr, cc, size, orient):
                _place_preview_r[0] = cr
                _place_preview_c[0] = cc
            else:
                _place_error[0] = 3

    # Draw
    if _place_error[0] > 0:
        _place_error[0] -= 1
        renderer.draw_placement_error()
    else:
        renderer.draw_placement(board, _place_ship_idx[0], r[0], c[0], _place_orient[0])

def _placement_done(player_num):
    if player_num == 1:
        if _mode_1p[0]:
            # CPU places automatically
            game.cpu_place_ships(_board_p2)
            _reset_battle()
            _current_player[0] = 1
            _phase[0] = PHASE_BATTLE
        else:
            # 2-player: pass to P2
            _place_ship_idx[0]  = 0
            _place_cursor_r[0]  = 4
            _place_cursor_c[0]  = 4
            _place_orient[0]    = game.HORIZONTAL
            _place_preview_r[0] = -1
            _place_preview_c[0] = -1
            _pass_msg[0]       = "PLAYER 2 - look away"
            _pass_next_phase[0] = PHASE_PLACE_P2
            _phase[0]           = PHASE_PASS_PLACE
    else:
        # P2 done placing
        _reset_battle()
        _current_player[0] = 1
        _pass_msg[0]       = "PLAYER 1 - your turn"
        _pass_next_phase[0] = PHASE_BATTLE
        _phase[0]           = PHASE_PASS_BATTLE

def _handle_pass():
    renderer.draw_pass_screen(_pass_msg[0])
    if badge.pressed(BUTTON_A):
        _phase[0] = _pass_next_phase[0]

def _handle_battle():
    cp = _current_player[0]
    # In 1p mode, CPU turn is handled automatically after human fires
    if _mode_1p[0] and cp == 2:
        _cpu_turn()
        return

    own_board = _board_p1 if cp == 1 else _board_p2
    tgt_board = _tgt_p1   if cp == 1 else _tgt_p2
    enemy_board = _board_p2 if cp == 1 else _board_p1
    player_name = "P1" if cp == 1 else "P2"

    # Cursor movement
    _move_cursor(_battle_cursor_r, _battle_cursor_c,
                 badge.pressed(BUTTON_UP),   badge.pressed(BUTTON_DOWN),
                 badge.pressed(BUTTON_A),    badge.pressed(BUTTON_B))

    status_msg = ""
    # Warning timer
    if _show_warn[0]:
        if badge.ticks - _warn_ticks[0] > 2000:
            _show_warn[0] = False
        else:
            status_msg = "Already fired there!"

    # Fire
    if badge.pressed(BUTTON_C):
        cr, cc = _battle_cursor_r[0], _battle_cursor_c[0]
        if game.already_fired(enemy_board, cr, cc):
            _show_warn[0]  = True
            _warn_ticks[0] = badge.ticks
        else:
            result = game.fire(enemy_board, cr, cc)
            # Mirror result to targeting board
            from game import HIT, MISS
            if result == 2:
                tgt_board[cr * 10 + cc] = HIT
                if _mode_1p[0]:
                    ai.ai_notify_result(enemy_board, cr, cc, result)
            elif result == 1:
                tgt_board[cr * 10 + cc] = MISS
                if _mode_1p[0]:
                    ai.ai_notify_result(enemy_board, cr, cc, result)

            # Check win
            if game.is_defeated(enemy_board):
                _winner[0] = player_name
                _phase[0]  = PHASE_VICTORY
                return

            # Switch turns
            if _mode_1p[0]:
                _current_player[0] = 2   # CPU will fire next frame
            else:
                next_p = 2 if cp == 1 else 1
                _current_player[0] = next_p
                _pass_msg[0] = "PLAYER " + str(next_p) + " - your turn"
                _pass_next_phase[0] = PHASE_BATTLE
                _phase[0] = PHASE_PASS_BATTLE

    renderer.draw_battle(own_board, tgt_board,
                         _battle_cursor_r[0], _battle_cursor_c[0],
                         player_name, status_msg)

def _cpu_turn():
    """Execute one CPU shot."""
    shots = []  # build flat shots list from board
    for r in range(10):
        for c in range(10):
            from game import HIT, MISS
            s = _board_p1[r * 10 + c]
            if s == HIT or s == MISS:
                shots.append(r)
                shots.append(c)

    row, col = ai.ai_take_shot(_board_p1, shots)
    result = game.fire(_board_p1, row, col)
    from game import HIT, MISS
    if result == 2:
        _tgt_p2[row * 10 + col] = HIT
    else:
        _tgt_p2[row * 10 + col] = MISS
    ai.ai_notify_result(_board_p1, row, col, result)

    if game.is_defeated(_board_p1):
        _winner[0] = "CPU"
        _phase[0]  = PHASE_VICTORY
        return

    _current_player[0] = 1

    # Show the battle screen immediately after CPU moves
    renderer.draw_battle(_board_p1, _tgt_p1,
                         _battle_cursor_r[0], _battle_cursor_c[0],
                         "P1")

def _handle_victory():
    renderer.draw_victory(_winner[0])
    if badge.pressed(BUTTON_A):
        # Play again — same mode
        _reset_boards()
        _reset_placement()
        _phase[0] = PHASE_PLACE_P1
        if _mode_1p[0]:
            game.seed_rng(badge.ticks & 0xFFFF)
    if badge.pressed(BUTTON_B):
        _menu_sel[0] = 0
        _phase[0] = PHASE_MENU

# ── Main update loop ──────────────────────────────────────────────────────────

def update():
    p = _phase[0]
    if p == PHASE_MENU:
        _handle_menu()
    elif p == PHASE_INSTRUCTIONS:
        _handle_instructions()
    elif p == PHASE_PLACE_P1:
        _handle_placement(_board_p1, 1)
    elif p == PHASE_PLACE_P2:
        _handle_placement(_board_p2, 2)
    elif p == PHASE_PASS_PLACE or p == PHASE_PASS_BATTLE:
        _handle_pass()
    elif p == PHASE_BATTLE:
        _handle_battle()
    elif p == PHASE_VICTORY:
        _handle_victory()

run(update)
