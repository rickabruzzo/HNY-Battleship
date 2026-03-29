# __init__.py — Honeycomb Battleship for Tufty 2350 / Badgeware (BadgeOS)
import sys, os
sys.path.insert(0, "/system/apps/battleship")
os.chdir("/system/apps/battleship")

mode(HIRES)

import time
import game
import ai
import renderer

# ── Load PNG assets once (image is a Badgeware builtin global) ─────────────────
_img_logo     = image.load("assets/hc_logo_white.png")
_img_logomark = image.load("assets/hc_logomark_white.png")
renderer.set_images(_img_logo, _img_logomark)

# ── Game-phase constants ───────────────────────────────────────────────────────
PHASE_MENU        = 0
PHASE_INSTRUCTIONS= 1
PHASE_PLACE_P1    = 2
PHASE_BATTLE      = 3
PHASE_VICTORY     = 4
PHASE_PLACE_INTRO   = 8
PHASE_TURN_RESULT   = 9
PHASE_PLACE_CONFIRM = 10

# ── Persistent game state (no dicts, no dynamic alloc in update) ───────────────
_phase          = [PHASE_MENU]
_mode_1p        = [True]       # True = 1-player, False = 2-player

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
_place_error     = [0]     # frames remaining to show error flash
_confirm_ship_name = [""]
_confirm_ticks     = [0]
_last_placed_r     = [4]   # row of last confirmed placement anchor

# Battle state
_battle_cursor_r = [4]
_battle_cursor_c = [4]
_current_player  = [1]     # 1 or 2
_warn_ticks      = [0]     # time.ticks_ms() when "already fired" warning started
_show_warn       = [False]
_winner          = [""]

# Turn result state
_result_ticks      = [0]
_result_is_hit     = [False]
_result_sunk_name  = [""]
_result_sunk_size  = [0]
_result_cells_left = [0]
_result_attacker   = ["P1"]

# ── Helper: reset everything for a new game ───────────────────────────────────

def _reset_boards():
    for i in range(100):
        _board_p1[i] = game.EMPTY
        _board_p2[i] = game.EMPTY
        _tgt_p1[i]   = game.EMPTY
        _tgt_p2[i]   = game.EMPTY

def _reset_placement():
    _place_ship_idx[0] = 0
    _place_cursor_r[0] = 4
    _place_cursor_c[0] = 4
    _place_orient[0]   = game.HORIZONTAL
    _place_error[0]    = 0
    _last_placed_r[0]  = 4

def _reset_battle():
    _battle_cursor_r[0] = 4
    _battle_cursor_c[0] = 4
    _current_player[0]  = 1
    _show_warn[0]       = False
    ai.ai_reset()

def _seed_rng():
    game.seed_rng(time.ticks_ms() & 0xFFFF)

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
    if io.BUTTON_B in io.pressed:
        _mode_1p[0] = True
        _seed_rng()
        _reset_boards()
        _reset_placement()
        _phase[0] = PHASE_PLACE_INTRO
    renderer.draw_menu(0)

def _handle_instructions():
    if io.BUTTON_B in io.pressed:
        _phase[0] = PHASE_MENU
    renderer.draw_instructions()

def _handle_placement(board, player_num):
    r = _place_cursor_r
    c = _place_cursor_c

    up      = io.BUTTON_UP   in io.pressed
    down    = io.BUTTON_DOWN in io.pressed
    left    = io.BUTTON_A    in io.pressed
    right   = io.BUTTON_C    in io.pressed
    b       = io.BUTTON_B    in io.pressed
    confirm = (io.BUTTON_A in io.held) and (io.BUTTON_C in io.held)

    if not confirm:
        if up    and r[0] > 0:  r[0] -= 1
        if down  and r[0] < 9:  r[0] += 1
        if left  and c[0] > 0:  c[0] -= 1
        if right and c[0] < 9:  c[0] += 1

    if b and not confirm:
        _place_orient[0] ^= 1

    if confirm:
        idx  = _place_ship_idx[0]
        size = game.SHIP_SIZES[idx]
        if game.can_place(board, r[0], c[0], size, _place_orient[0]):
            game.place_ship(board, r[0], c[0], size, _place_orient[0])
            _last_placed_r[0] = r[0]
            _place_ship_idx[0] += 1
            if _place_ship_idx[0] >= len(game.SHIP_SIZES):
                _placement_done(player_num)
                return
            # Smart cursor: one row below last anchor, or one above if at bottom
            if r[0] < 9:
                r[0] += 1
            else:
                r[0] -= 1
            # Show confirm popup
            _confirm_ship_name[0] = game.SHIP_NAMES[idx]
            _confirm_ticks[0]     = io.ticks
            _phase[0]             = PHASE_PLACE_CONFIRM
        else:
            _place_error[0] = 4

    if _place_error[0] > 0:
        _place_error[0] -= 1
        renderer.draw_placement_error()
    else:
        renderer.draw_placement(board, _place_ship_idx[0], r[0], c[0], _place_orient[0])

def _handle_place_confirm():
    renderer.draw_placement(
        _board_p1,
        _place_ship_idx[0],
        _place_cursor_r[0],
        _place_cursor_c[0],
        _place_orient[0]
    )
    renderer.draw_place_confirm(_confirm_ship_name[0])
    if io.ticks - _confirm_ticks[0] > 1200:
        _phase[0] = PHASE_PLACE_P1

def _handle_placement_intro():
    renderer.draw_placement_intro()
    if io.BUTTON_B in io.pressed:
        _phase[0] = PHASE_PLACE_P1

def _placement_done(player_num):
    game.cpu_place_ships(_board_p2)
    _reset_battle()
    _current_player[0] = 1
    _phase[0] = PHASE_BATTLE


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
                 io.BUTTON_UP   in io.pressed,
                 io.BUTTON_DOWN in io.pressed,
                 io.BUTTON_A    in io.pressed,
                 io.BUTTON_C    in io.pressed)

    status_msg = ""
    # Warning timer
    if _show_warn[0]:
        if time.ticks_ms() - _warn_ticks[0] > 2000:
            _show_warn[0] = False
        else:
            status_msg = "Already fired there!"

    # Fire
    if io.BUTTON_B in io.pressed:
        cr, cc = _battle_cursor_r[0], _battle_cursor_c[0]
        if game.already_fired(enemy_board, cr, cc):
            _show_warn[0]  = True
            _warn_ticks[0] = time.ticks_ms()
        else:
            result = game.fire(enemy_board, cr, cc)
            is_hit = (result == game.HIT)

            if is_hit:
                tgt_board[cr * 10 + cc] = game.HIT
                sunk_size, sunk_name = game.check_sunk(enemy_board, cr, cc)
                if _mode_1p[0]:
                    ai.ai_notify_result(enemy_board, cr, cc, result)
            else:
                tgt_board[cr * 10 + cc] = game.MISS
                sunk_size, sunk_name = 0, ""
                if _mode_1p[0]:
                    ai.ai_notify_result(enemy_board, cr, cc, result)

            cells_left = game.cells_remaining(enemy_board)

            # Check win before showing result screen
            if game.is_defeated(enemy_board):
                _winner[0] = player_name
                _phase[0]  = PHASE_VICTORY
                return

            # Transition to result screen
            _result_ticks[0]      = io.ticks
            _result_is_hit[0]     = is_hit
            _result_sunk_name[0]  = sunk_name
            _result_sunk_size[0]  = sunk_size
            _result_cells_left[0] = cells_left
            _result_attacker[0]   = player_name

            # Set next player for when result screen dismisses
            if _mode_1p[0]:
                _current_player[0] = 2   # CPU fires after result
            _phase[0] = PHASE_TURN_RESULT

    renderer.draw_battle(own_board, tgt_board,
                         _battle_cursor_r[0], _battle_cursor_c[0],
                         player_name, status_msg)

def _cpu_turn():
    """Execute one CPU shot."""
    shots = []  # build flat shots list from board
    for r in range(10):
        for c in range(10):
            s = _board_p1[r * 10 + c]
            if s == game.HIT or s == game.MISS:
                shots.append(r)
                shots.append(c)

    row, col = ai.ai_take_shot(_board_p1, shots)
    result = game.fire(_board_p1, row, col)
    if result == game.HIT:
        _tgt_p2[row * 10 + col] = game.HIT
        sunk_size, sunk_name = game.check_sunk(_board_p1, row, col)
    else:
        _tgt_p2[row * 10 + col] = game.MISS
        sunk_size, sunk_name = 0, ""
    ai.ai_notify_result(_board_p1, row, col, result)

    cells_left = game.cells_remaining(_board_p1)

    if game.is_defeated(_board_p1):
        _winner[0] = "CPU"
        _phase[0]  = PHASE_VICTORY
        return

    _current_player[0] = 1
    _result_ticks[0]      = io.ticks
    _result_is_hit[0]     = (result == game.HIT)
    _result_sunk_name[0]  = sunk_name
    _result_sunk_size[0]  = sunk_size
    _result_cells_left[0] = cells_left
    _result_attacker[0]   = "CPU"
    _phase[0] = PHASE_TURN_RESULT

def _handle_turn_result():
    elapsed = io.ticks - _result_ticks[0]
    renderer.draw_turn_result(
        _result_is_hit[0],
        _result_sunk_name[0],
        _result_sunk_size[0],
        _result_cells_left[0],
        _result_attacker[0],
        elapsed
    )
    if elapsed > 2200:
        if _mode_1p[0] and _current_player[0] == 2:
            _cpu_turn()
        else:
            _phase[0] = PHASE_BATTLE

def _handle_victory():
    renderer.draw_victory(_winner[0])
    if io.BUTTON_A in io.pressed:
        # Play again — same mode
        _reset_boards()
        _reset_placement()
        _phase[0] = PHASE_PLACE_P1
        if _mode_1p[0]:
            game.seed_rng(time.ticks_ms() & 0xFFFF)
    if io.BUTTON_B in io.pressed:
        _phase[0] = PHASE_MENU

# ── Main update loop ──────────────────────────────────────────────────────────

def update():
    p = _phase[0]
    if p == PHASE_MENU:
        _handle_menu()
    elif p == PHASE_INSTRUCTIONS:
        _handle_instructions()
    elif p == PHASE_PLACE_INTRO:
        _handle_placement_intro()
    elif p == PHASE_PLACE_CONFIRM:
        _handle_place_confirm()
    elif p == PHASE_PLACE_P1:
        _handle_placement(_board_p1, 1)
    elif p == PHASE_BATTLE:
        _handle_battle()
    elif p == PHASE_TURN_RESULT:
        _handle_turn_result()
    elif p == PHASE_VICTORY:
        _handle_victory()
