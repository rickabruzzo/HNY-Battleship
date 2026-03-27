# renderer.py — all drawing code
# Badgeware builtins (screen, color, rom_font, Image) are globals — not imported.

# ── Honeycomb brand palette ───────────────────────────────────────────────────
BG_COLOR    = (1,   72,  123)   # Denim
HC_ORANGE   = (249, 110, 16)    # Tango  — hits / P1 accent
HC_GREEN    = (100, 186, 0)     # Lime   — confirmed ship placement
HC_BLUE     = (2,   120, 205)   # Cobalt — water / empty cells
HC_YELLOW   = (255, 176, 0)     # Honey  — cursor / P2 accent
HC_SHIP     = (89,  96,  109)    # gray700 #59606D — closest brand gray to ship hull
STATUS_BG   = (1,   50,  90)    # Denim darker (~70% Denim)

# Layout constants (integers only)
SCREEN_W    = 320
SCREEN_H    = 240
STATUS_H    = 18
GRID_TOP    = 28        # y-offset where grids start (below label row)
GRID_ROWS   = 10
GRID_COLS   = 10
CELL_SIZE   = 13        # pixels per cell
GRID_W      = GRID_COLS * CELL_SIZE   # 130
GRID_H      = GRID_ROWS * CELL_SIZE   # 130
# Left grid x start, right grid x start — centred with a gap
GRID_GAP    = 10
TOTAL_W     = GRID_W * 2 + GRID_GAP  # 270
GRID_LEFT_X = (SCREEN_W - TOTAL_W) // 2          # 25
GRID_RIGHT_X = GRID_LEFT_X + GRID_W + GRID_GAP   # 165

LOGO_MARK_SMALL = 24   # logomark size on game screens
LOGO_MARK_MENU  = 48

# ── Image references (set by __init__.py) ─────────────────────────────────────
img_logo      = None   # hc_logo_white.png  200×50
img_logomark  = None   # hc_logomark_white.png 48×48

def set_images(logo, logomark):
    global img_logo, img_logomark
    img_logo     = logo
    img_logomark = logomark

# ── Drawing primitives ────────────────────────────────────────────────────────

def _bg():
    screen.pen = BG_COLOR
    screen.rectangle(0, 0, SCREEN_W, SCREEN_H)

def _status_bar(text):
    screen.pen = STATUS_BG
    screen.rectangle(0, SCREEN_H - STATUS_H, SCREEN_W, STATUS_H)
    screen.pen = color.white
    screen.font = rom_font.bitmap8
    tw = len(text) * 8
    screen.text(text, (SCREEN_W - tw) // 2, SCREEN_H - STATUS_H + 5)

def _cell_color(state, is_cursor, placement_confirmed=False):
    """Return pen color for a cell during battle."""
    if is_cursor:
        return HC_YELLOW
    from game import EMPTY, SHIP, HIT, MISS
    if state == HIT:
        return HC_ORANGE
    if state == MISS:
        return color.white
    if state == SHIP:
        return HC_SHIP
    return HC_BLUE   # EMPTY / water

def _draw_grid(board, ox, oy, hide_ships, cursor_r, cursor_c, placement_phase=False):
    """
    Draw a 10×10 grid at pixel offset (ox, oy).
    hide_ships=True  → enemy grid (don't reveal SHIP cells)
    placement_phase  → SHIP cells draw HC_GREEN
    cursor_r/c       → highlighted cell (-1 to skip)
    """
    from game import EMPTY, SHIP, HIT, MISS
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            x = ox + c * CELL_SIZE
            y = oy + r * CELL_SIZE
            state = board[r * GRID_COLS + c]
            is_cur = (r == cursor_r and c == cursor_c)

            if is_cur:
                screen.pen = HC_YELLOW
            elif state == HIT:
                screen.pen = HC_ORANGE
            elif state == MISS:
                screen.pen = color.white
            elif state == SHIP:
                if hide_ships:
                    screen.pen = HC_BLUE
                elif placement_phase:
                    screen.pen = HC_GREEN
                else:
                    screen.pen = HC_SHIP
            else:
                screen.pen = HC_BLUE

            screen.rectangle(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)

def _draw_grid_border(ox, oy):
    screen.pen = (60, 60, 90)
    screen.rectangle(ox, oy, GRID_W, GRID_H)
    # Overdraw interior — just draw thin lines between cells
    screen.pen = BG_COLOR
    for i in range(1, GRID_ROWS):
        screen.rectangle(ox, oy + i * CELL_SIZE, GRID_W, 1)
    for i in range(1, GRID_COLS):
        screen.rectangle(ox + i * CELL_SIZE, oy, 1, GRID_H)

def _label(text, cx, y):
    screen.font = rom_font.bitmap8
    tw = len(text) * 8
    screen.pen = color.white
    screen.text(text, cx - tw // 2, y)

def _small_logomark(x, y):
    if img_logomark is not None:
        screen.scale_blit(img_logomark, x, y, LOGO_MARK_SMALL, LOGO_MARK_SMALL)

# ── Public draw functions ─────────────────────────────────────────────────────

def draw_menu(selected):
    """Main menu: logomark top-left, title centred, 3 options."""
    _bg()
    # Logomark
    if img_logomark is not None:
        screen.scale_blit(img_logomark, 4, 4, LOGO_MARK_MENU, LOGO_MARK_MENU)
    # Title
    screen.font = rom_font.bitmap14
    title = "BATTLESHIP"
    tw = len(title) * 14
    screen.pen = color.white
    screen.text(title, (SCREEN_W - tw) // 2, 20)

    # Subtitle
    screen.font = rom_font.bitmap8
    sub = "by honeycomb.io"
    sw = len(sub) * 8
    screen.pen = HC_ORANGE
    screen.text(sub, (SCREEN_W - sw) // 2, 40)

    options = ["1 Player (vs Computer)", "2 Players (pass-and-play)", "Instructions"]
    oy = 80
    for i, opt in enumerate(options):
        tw2 = len(opt) * 8
        rx = (SCREEN_W - tw2) // 2 - 6
        if i == selected:
            screen.pen = HC_ORANGE
            screen.rectangle(rx, oy - 2, tw2 + 12, 16)
            screen.pen = color.white
        else:
            screen.pen = color.white
        screen.font = rom_font.bitmap8
        screen.text(opt, (SCREEN_W - tw2) // 2, oy)
        oy += 30

def draw_instructions():
    """Static instructions screen."""
    _bg()
    # Header
    _small_logomark(4, 4)
    screen.font = rom_font.bitmap14
    screen.pen = color.white
    title = "BATTLESHIP"
    screen.text(title, (SCREEN_W - len(title) * 14) // 2, 6)
    screen.font = rom_font.bitmap8
    screen.pen = HC_ORANGE
    sub = "by honeycomb.io"
    screen.text(sub, (SCREEN_W - len(sub) * 8) // 2, 24)

    screen.pen = color.white
    lines = [
        ("GOAL", HC_YELLOW),
        ("Place your fleet. Sink the enemy's", color.white),
        ("before they sink yours.", color.white),
        ("", color.white),
        ("PLACEMENT", HC_YELLOW),
        ("UP/DOWN/A/B move cursor", color.white),
        ("C rotate  |  A twice = confirm", color.white),
        ("", color.white),
        ("BATTLE", HC_YELLOW),
        ("UP/DOWN/A/B move cursor  C fire", color.white),
        ("", color.white),
        ("FLEET", HC_YELLOW),
        ("Carrier 5  Battleship 4  Cruiser 3", color.white),
        ("Submarine 3  Destroyer 2", color.white),
        ("", color.white),
        ("B back to menu", (150, 150, 150)),
    ]
    y = 38
    for text, pen in lines:
        if text == "":
            y += 4
            continue
        screen.font = rom_font.bitmap8
        screen.pen = pen
        screen.text(text, 8, y)
        y += 12
        if y > SCREEN_H - 20:
            break

def draw_placement(board, ship_idx, cursor_r, cursor_c, orientation):
    """
    Ship placement screen.
    board       — current player's board
    ship_idx    — index into SHIP_SIZES (0-4)
    orientation — HORIZONTAL=0 / VERTICAL=1
    cursor_r/c  — current cursor cell
    """
    from game import SHIP_NAMES, SHIP_SIZES, HORIZONTAL
    _bg()
    _small_logomark(4, 4)

    screen.font = rom_font.bitmap8
    screen.pen = color.white
    placing = "Placing: " + SHIP_NAMES[ship_idx] + " (" + str(SHIP_SIZES[ship_idx]) + ")"
    screen.text(placing, 32, 8)
    orient_str = "HORIZ" if orientation == HORIZONTAL else "VERT"
    screen.pen = HC_YELLOW
    screen.text("C:rotate [" + orient_str + "]", SCREEN_W - 104, 8)

    # Draw grid centred
    gx = (SCREEN_W - GRID_W) // 2
    gy = 28
    _draw_grid_border(gx, gy)
    _draw_grid(board, gx, gy, False, cursor_r, cursor_c, placement_phase=True)

    _status_bar("A:preview/confirm  B:move left  UP/DOWN:move")

def draw_placement_error():
    """Flash the status bar red for one frame on bad placement."""
    screen.pen = (140, 0, 0)
    screen.rectangle(0, SCREEN_H - STATUS_H, SCREEN_W, STATUS_H)
    screen.pen = color.white
    screen.font = rom_font.bitmap8
    msg = "Can't place there!"
    screen.text(msg, (SCREEN_W - len(msg) * 8) // 2, SCREEN_H - STATUS_H + 5)

def draw_battle(own_board, target_board, cursor_r, cursor_c, player_name, status_msg=""):
    """
    Battle phase: two grids side by side.
    own_board    — own fleet + incoming shots
    target_board — enemy grid (only hits/misses shown)
    """
    _bg()
    _small_logomark(4, 4)

    # Grid labels
    screen.font = rom_font.bitmap8
    screen.pen = color.white
    label_l = "YOUR FLEET"
    label_r = "ENEMY WATERS"
    lx_l = GRID_LEFT_X  + (GRID_W - len(label_l) * 8) // 2
    lx_r = GRID_RIGHT_X + (GRID_W - len(label_r) * 8) // 2
    screen.text(label_l, lx_l, 16)
    screen.text(label_r, lx_r, 16)

    # Grids
    _draw_grid_border(GRID_LEFT_X,  GRID_TOP)
    _draw_grid_border(GRID_RIGHT_X, GRID_TOP)
    _draw_grid(own_board,    GRID_LEFT_X,  GRID_TOP, False, -1, -1)
    _draw_grid(target_board, GRID_RIGHT_X, GRID_TOP, True, cursor_r, cursor_c)

    # Status bar
    if status_msg:
        _status_bar(status_msg)
    else:
        _status_bar(player_name + " | C:fire  UP/DOWN/A/B:move")

def draw_pass_screen(message):
    """Pass-device splash between turns / players."""
    _bg()
    if img_logomark is not None:
        lx = (SCREEN_W - LOGO_MARK_MENU) // 2
        screen.scale_blit(img_logomark, lx, 40, LOGO_MARK_MENU, LOGO_MARK_MENU)

    screen.font = rom_font.bitmap14
    screen.pen = HC_ORANGE
    line1 = "PASS THE DEVICE"
    screen.text(line1, (SCREEN_W - len(line1) * 14) // 2, 110)

    screen.font = rom_font.bitmap8
    screen.pen = color.white
    # Split message into two lines if needed (max ~38 chars per line)
    if len(message) <= 38:
        screen.text(message, (SCREEN_W - len(message) * 8) // 2, 135)
    else:
        mid = len(message) // 2
        # Find nearest space
        while mid < len(message) and message[mid] != ' ':
            mid += 1
        l1 = message[:mid]
        l2 = message[mid+1:]
        screen.text(l1, (SCREEN_W - len(l1) * 8) // 2, 132)
        screen.text(l2, (SCREEN_W - len(l2) * 8) // 2, 146)

    screen.pen = (150, 150, 150)
    cont = "Press A when ready"
    screen.text(cont, (SCREEN_W - len(cont) * 8) // 2, 175)

def draw_victory(winner_name):
    """Victory screen."""
    _bg()
    # Full logo centred upper half
    if img_logo is not None:
        lx = (SCREEN_W - 200) // 2
        screen.scale_blit(img_logo, lx, 30, 200, 50)

    screen.font = rom_font.bitmap14
    screen.pen = HC_ORANGE
    wins = winner_name + " WINS!"
    screen.text(wins, (SCREEN_W - len(wins) * 14) // 2, 110)

    screen.font = rom_font.bitmap8
    screen.pen = color.white
    screen.text("Congratulations!", (SCREEN_W - 16 * 8) // 2, 138)

    screen.pen = (150, 150, 150)
    foot = "A - Play Again      B - Main Menu"
    screen.text(foot, (SCREEN_W - len(foot) * 8) // 2, 200)
