# renderer.py — all drawing code
# Badgeware builtins (screen, color, rom_font, image) are globals — not imported.

# ── Honeycomb brand palette ───────────────────────────────────────────────────
# Defined as color.rgb() values — color is a Badgeware builtin global
BG_COLOR    = color.rgb(1,   72,  123)   # Denim
HC_ORANGE   = color.rgb(249, 110, 16)    # Tango  — hits / P1 accent
HC_GREEN    = color.rgb(100, 186, 0)     # Lime   — confirmed ship placement
HC_BLUE     = color.rgb(2,   120, 205)   # Cobalt — water / empty cells
HC_YELLOW   = color.rgb(255, 176, 0)     # Honey  — cursor / P2 accent
HC_SHIP     = color.rgb(89,  96,  109)   # gray700 — ship hull
STATUS_BG   = color.rgb(1,   50,  90)    # Denim darker
WHITE       = color.rgb(255, 255, 255)
GRAY        = color.rgb(150, 150, 150)
DARK_RED    = color.rgb(140, 0,   0)
GRID_LINE   = color.rgb(60,  60,  90)

# ── Layout constants (integers only) ─────────────────────────────────────────
SCREEN_W = screen.width
SCREEN_H = screen.height
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

# ── Game module imports ───────────────────────────────────────────────────────
from game import EMPTY, SHIP, HIT, MISS, SHIP_NAMES, SHIP_SIZES, HORIZONTAL, VERTICAL, ship_cells, can_place

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
    screen.rectangle(0, 0, screen.width, screen.height)

def _status_bar(text):
    screen.pen = STATUS_BG
    screen.rectangle(0, screen.height - STATUS_H, screen.width, STATUS_H)
    screen.pen = WHITE
    screen.font = rom_font.nope
    tw, _ = screen.measure_text(text)
    screen.text(text, (screen.width - tw) // 2, screen.height - STATUS_H + 5)

def _draw_grid(board, ox, oy, hide_ships, cursor_r, cursor_c, placement_phase=False):
    """
    Draw a 10×10 grid at pixel offset (ox, oy).
    hide_ships=True  → enemy grid (don't reveal SHIP cells)
    placement_phase  → SHIP cells draw HC_GREEN
    cursor_r/c       → highlighted cell (-1 to skip)
    """
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
                screen.pen = WHITE
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
    screen.pen = GRID_LINE
    screen.rectangle(ox, oy, GRID_W, GRID_H)
    # Overdraw interior — draw thin lines between cells
    screen.pen = BG_COLOR
    for i in range(1, GRID_ROWS):
        screen.rectangle(ox, oy + i * CELL_SIZE, GRID_W, 1)
    for i in range(1, GRID_COLS):
        screen.rectangle(ox + i * CELL_SIZE, oy, 1, GRID_H)

def _label(text, cx, y):
    screen.font = rom_font.nope
    tw, _ = screen.measure_text(text)
    screen.pen = WHITE
    screen.text(text, cx - tw // 2, y)

def _small_logomark(x, y):
    if img_logomark is not None:
        screen.blit(img_logomark, rect(x, y, LOGO_MARK_SMALL, LOGO_MARK_SMALL))

# ── Public draw functions ─────────────────────────────────────────────────────

def _draw_menu_ship(ox, oy):
    """
    Pixel-art battleship drawn at ~45° angle, bow upper-left to stern lower-right.
    ox, oy = top-left origin of the drawing area (~60×60px used).
    Each 'cell' is 4×2px to give a compressed perspective feel.
    """
    # Hull — diagonal stepped rectangles from stern (lower-right) to bow (upper-left)
    hull = [
        (40, 44, 16, 5),   # stern (lower-right)
        (28, 38, 16, 5),
        (16, 32, 16, 5),
        (4,  26, 16, 5),
        (0,  22, 10, 4),   # bow taper (upper-left)
    ]
    screen.pen = HC_SHIP
    for (x, y, w, h) in hull:
        screen.rectangle(ox + x, oy + y, w, h)

    # Waterline — slightly lighter strip along bottom of each hull segment
    screen.pen = color.rgb(100, 110, 125)
    for (x, y, w, h) in hull:
        screen.rectangle(ox + x, oy + y + h - 1, w, 1)

    # Deck — thin strip along top of hull segments
    screen.pen = color.rgb(75, 85, 100)
    for (x, y, w, h) in hull:
        screen.rectangle(ox + x, oy + y, w, 1)

    # Superstructure — two stepped blocks mid-ship
    screen.pen = color.rgb(80, 90, 108)
    screen.rectangle(ox + 22, oy + 30, 10, 7)   # rear structure
    screen.rectangle(ox + 30, oy + 25, 8,  6)    # forward structure

    # Gun turret — small dark rectangle on forward structure
    screen.pen = color.rgb(55, 62, 75)
    screen.rectangle(ox + 31, oy + 22, 6, 4)

    # Gun barrel — thin line jutting upper-left from turret
    screen.pen = color.rgb(40, 45, 55)
    screen.rectangle(ox + 25, oy + 18, 7, 2)

    # Wake — small bright dots below stern
    screen.pen = color.rgb(150, 190, 220)
    screen.rectangle(ox + 48, oy + 48, 3, 1)
    screen.rectangle(ox + 52, oy + 50, 2, 1)
    screen.rectangle(ox + 44, oy + 50, 2, 1)

    # HC brand hex dots — small cluster above the ship
    _dot_colors = [HC_ORANGE, HC_GREEN, HC_BLUE, HC_YELLOW]
    dot_pos = [(0, 6), (5, 2), (10, 6), (5, 10)]
    for i, (dx, dy) in enumerate(dot_pos):
        screen.pen = _dot_colors[i]
        screen.rectangle(ox + dx, oy + dy, 4, 4)


def draw_menu(selected):
    _bg()

    # Logomark top-left
    if img_logomark is not None:
        screen.blit(img_logomark, rect(4, 4, LOGO_MARK_MENU, LOGO_MARK_MENU))

    # Title
    screen.font = rom_font.yesterday
    title = "BATTLESHIP"
    tw, _ = screen.measure_text(title)
    screen.pen = WHITE
    screen.text(title, (screen.width - tw) // 2, 10)

    # Subtitle
    screen.font = rom_font.nope
    sub = "by honeycomb.io"
    sw, _ = screen.measure_text(sub)
    screen.pen = HC_ORANGE
    screen.text(sub, (screen.width - sw) // 2, 28)

    # START button — large centered button
    BW = 200
    BH = 36
    bx = (screen.width  - BW) // 2
    by = (screen.height - BH) // 2 + 20

    # Button shadow
    screen.pen = color.rgb(0, 0, 0)
    screen.rectangle(bx + 3, by + 3, BW, BH)

    # Button fill
    screen.pen = HC_ORANGE
    screen.rectangle(bx, by, BW, BH)

    # Button top highlight
    screen.pen = color.rgb(255, 210, 120)
    screen.rectangle(bx, by, BW, 2)

    # Button text
    screen.font = rom_font.yesterday
    screen.pen = WHITE
    btn_text = "START GAME"
    btw, _ = screen.measure_text(btn_text)
    screen.text(btn_text, (screen.width - btw) // 2, by + 12)

    # Prompt below button
    screen.font = rom_font.nope
    screen.pen = HC_YELLOW
    prompt = "Press B to play"
    pw, _ = screen.measure_text(prompt)
    screen.text(prompt, (screen.width - pw) // 2, by + BH + 10)

def draw_instructions():
    """Static instructions screen."""
    _bg()
    # Header
    if img_logomark is not None:
        screen.blit(img_logomark, rect(4, 4, 24, 24))
    screen.font = rom_font.yesterday
    screen.pen = WHITE
    title = "BATTLESHIP"
    tw, _ = screen.measure_text(title)
    screen.text(title, (screen.width - tw) // 2, 6)
    screen.font = rom_font.nope
    screen.pen = HC_ORANGE
    sub = "by honeycomb.io"
    sw, _ = screen.measure_text(sub)
    screen.text(sub, (screen.width - sw) // 2, 24)

    lines = [
        ("GOAL", HC_YELLOW),
        ("Place your fleet. Sink the enemy's", WHITE),
        ("before they sink yours.", WHITE),
        ("", WHITE),
        ("PLACEMENT", HC_YELLOW),
        ("UP/DOWN/A/B move cursor", WHITE),
        ("C rotate  |  A twice = confirm", WHITE),
        ("", WHITE),
        ("BATTLE", HC_YELLOW),
        ("UP/DOWN/A/B move cursor  C fire", WHITE),
        ("", WHITE),
        ("FLEET", HC_YELLOW),
        ("Carrier 5  Battleship 4  Cruiser 3", WHITE),
        ("Submarine 3  Destroyer 2", WHITE),
        ("", WHITE),
        ("B back to menu", GRAY),
    ]
    y = 38
    for text, pen in lines:
        if text == "":
            y += 4
            continue
        screen.font = rom_font.nope
        screen.pen = pen
        screen.text(text, 8, y)
        y += 12
        if y > screen.height - 20:
            break

def draw_placement_intro():
    """Splash screen shown before placement begins."""
    _bg()
    _small_logomark(4, 4)

    screen.font = rom_font.nope
    screen.pen = WHITE
    tw, _ = screen.measure_text("PLACE YOUR FLEET")
    screen.text("PLACE YOUR FLEET", (screen.width - tw) // 2, 8)

    ships = [
        ("Carrier",    5),
        ("Battleship", 4),
        ("Cruiser",    3),
        ("Submarine",  3),
        ("Destroyer",  2),
    ]

    BW = 12
    BH = 8
    start_y = 36

    for i, (name, size) in enumerate(ships):
        y = start_y + i * 24
        # Name left-aligned
        screen.pen = WHITE
        screen.font = rom_font.nope
        screen.text(name, 8, y + 2)
        # Size label
        tw_name, _ = screen.measure_text(name)
        screen.pen = HC_YELLOW
        screen.text("x" + str(size), 8 + tw_name + 4, y + 2)
        # Silhouette right-aligned
        ship_w = size * BW
        sx = screen.width - ship_w - 8
        screen.pen = HC_SHIP
        screen.rectangle(sx, y + BH // 3, ship_w, BH - BH // 3)
        screen.pen = color.rgb(120, 130, 145)
        screen.rectangle(sx, y + BH // 3, ship_w, 2)
        screen.pen = color.rgb(90, 100, 115)
        screen.rectangle(sx + BW, y, BW - 2, BH // 3 + 2)

    # Controls block
    y_ctrl = start_y + 5 * 24 + 6
    screen.font = rom_font.nope
    screen.pen = HC_YELLOW
    screen.text("UP/DN/A/C: move cursor", 8, y_ctrl)
    screen.pen = WHITE
    screen.text("B: rotate ship", 8, y_ctrl + 13)
    screen.pen = WHITE
    screen.text("A + C together: confirm placement", 8, y_ctrl + 26)

    screen.pen = HC_ORANGE
    tw3, _ = screen.measure_text("Press B to begin")
    screen.text("Press B to begin", (screen.width - tw3) // 2, screen.height - 14)

def draw_placement(board, ship_idx, cursor_r, cursor_c, orientation):
    _bg()
    _small_logomark(4, 4)

    screen.font = rom_font.nope
    screen.pen = color.rgb(255, 255, 255)
    placing = "Placing: " + SHIP_NAMES[ship_idx] + " (" + str(SHIP_SIZES[ship_idx]) + ")"
    screen.text(placing, 32, 8)

    orient_str = "HORIZ" if orientation == HORIZONTAL else "VERT"
    ow, _ = screen.measure_text("B:rotate [" + orient_str + "]")
    screen.pen = HC_YELLOW
    screen.text("B:rotate [" + orient_str + "]", screen.width - ow - 4, 8)

    # Draw grid centred
    gx = (screen.width - GRID_W) // 2
    gy = 28
    _draw_grid_border(gx, gy)

    # Draw existing placed ships
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = gx + col * CELL_SIZE
            y = gy + row * CELL_SIZE
            state = board[row * GRID_COLS + col]
            if state == SHIP:
                screen.pen = HC_GREEN
                screen.rectangle(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)
            else:
                screen.pen = HC_BLUE
                screen.rectangle(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)

    # Draw ghost preview of ship being placed
    size = SHIP_SIZES[ship_idx]

    # Build ghost cells manually — never returns empty for off-grid ships
    ghost_cells = []
    for i in range(size):
        if orientation == HORIZONTAL:
            ghost_cells.append((cursor_r, cursor_c + i))
        else:
            ghost_cells.append((cursor_r + i, cursor_c))

    valid = can_place(board, cursor_r, cursor_c, size, orientation)
    ghost_color = HC_GREEN if valid else color.rgb(200, 50, 50)

    for (gr, gc) in ghost_cells:
        if 0 <= gr < GRID_ROWS and 0 <= gc < GRID_COLS:
            x = gx + gc * CELL_SIZE
            y = gy + gr * CELL_SIZE
            screen.pen = ghost_color
            screen.rectangle(x + 1, y + 1, CELL_SIZE - 2, CELL_SIZE - 2)

    # Draw cursor cell outline (highlight the anchor cell)
    ax = gx + cursor_c * CELL_SIZE
    ay = gy + cursor_r * CELL_SIZE
    screen.pen = HC_YELLOW
    screen.rectangle(ax, ay, CELL_SIZE, 1)
    screen.rectangle(ax, ay + CELL_SIZE - 1, CELL_SIZE, 1)
    screen.rectangle(ax, ay, 1, CELL_SIZE)
    screen.rectangle(ax + CELL_SIZE - 1, ay, 1, CELL_SIZE)

    _status_bar("UP/DN/A/C:move  B:rotate  A+C:place")

def draw_placement_error():
    """Flash the status bar red for one frame on bad placement."""
    screen.pen = DARK_RED
    screen.rectangle(0, screen.height - STATUS_H, screen.width, STATUS_H)
    screen.pen = WHITE
    screen.font = rom_font.nope
    msg = "Can't place there!"
    mw, _ = screen.measure_text(msg)
    screen.text(msg, (screen.width - mw) // 2, screen.height - STATUS_H + 5)

def draw_place_confirm(ship_name):
    """Brief confirmation popup after a ship is placed."""
    PW = 220
    PH = 36
    px = (screen.width  - PW) // 2
    py = (screen.height - PH) // 2
    screen.pen = color.rgb(10, 40, 10)
    screen.rectangle(px, py, PW, PH)
    screen.pen = HC_GREEN
    screen.rectangle(px, py, PW, 2)
    screen.rectangle(px, py + PH - 2, PW, 2)
    screen.pen = WHITE
    screen.font = rom_font.nope
    msg = ship_name + " in position"
    tw, _ = screen.measure_text(msg)
    screen.text(msg, (screen.width - tw) // 2, py + 12)

def draw_battle(own_board, target_board, cursor_r, cursor_c, player_name, status_msg=""):
    """
    Battle phase: two grids side by side.
    own_board    — own fleet + incoming shots
    target_board — enemy grid (only hits/misses shown)
    """
    _bg()
    _small_logomark(4, 4)

    # Grid labels
    screen.font = rom_font.nope
    screen.pen = WHITE
    label_l = "YOUR FLEET"
    label_r = "ENEMY WATERS"
    lw_l, _ = screen.measure_text(label_l)
    lw_r, _ = screen.measure_text(label_r)
    lx_l = GRID_LEFT_X  + (GRID_W - lw_l) // 2
    lx_r = GRID_RIGHT_X + (GRID_W - lw_r) // 2
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
        _status_bar(player_name + " | B:fire  UP/DN/A/C:move")


def draw_ship_silhouette(size, x, y, cw, ch):
    """Draw a horizontal ship silhouette. Uses HC_SHIP palette."""
    ship_w = size * cw
    screen.pen = HC_SHIP
    screen.rectangle(x, y + ch // 3, ship_w, ch - ch // 3)
    screen.pen = color.rgb(120, 130, 145)
    screen.rectangle(x, y + ch // 3, ship_w, 3)
    screen.pen = color.rgb(90, 100, 115)
    screen.rectangle(x + cw, y, cw - 2, ch // 3 + 2)


def draw_turn_result(is_hit, sunk_name, sunk_size, cells_left, attacker, elapsed_ms):
    """Small popup overlay — draw on top of whatever is already on screen."""
    PW = 260
    PH = 80 if not sunk_name else 108
    px = (screen.width  - PW) // 2
    py = (screen.height - PH) // 2

    # Popup background color: green=P1 hit, red=CPU hit, yellow=miss
    if not is_hit:
        bg = color.rgb(40, 40, 20)
        border = HC_YELLOW
    elif attacker == "P1":
        bg = color.rgb(10, 50, 10)
        border = HC_GREEN
    else:
        bg = color.rgb(50, 10, 10)
        border = color.rgb(200, 50, 50)

    # Shadow
    screen.pen = color.rgb(0, 0, 0)
    screen.rectangle(px + 3, py + 3, PW, PH)
    # Body
    screen.pen = bg
    screen.rectangle(px, py, PW, PH)
    # Border
    screen.pen = border
    screen.rectangle(px,          py,          PW, 2)
    screen.rectangle(px,          py + PH - 2, PW, 2)
    screen.rectangle(px,          py,          2,  PH)
    screen.rectangle(px + PW - 2, py,          2,  PH)

    # Expanding box animation for hits
    if is_hit:
        ring = (elapsed_ms // 35) % 24 + 4
        screen.pen = border
        rx = px + PW // 2
        ry = py + PH // 2
        screen.rectangle(rx - ring, ry - ring, ring * 2, 2)
        screen.rectangle(rx - ring, ry + ring, ring * 2, 2)
        screen.rectangle(rx - ring, ry - ring, 2, ring * 2)
        screen.rectangle(rx + ring, ry - ring, 2, ring * 2)

    # Result text
    screen.font = rom_font.yesterday
    if is_hit:
        screen.pen = border
        result_text = "HIT!" if not sunk_name else "SUNK!"
    else:
        screen.pen = HC_YELLOW
        result_text = "MISS"
    tw, _ = screen.measure_text(result_text)
    screen.text(result_text, (screen.width - tw) // 2, py + 8)

    # Attacker label
    screen.font = rom_font.nope
    screen.pen = GRAY
    who = "Your shot" if attacker == "P1" else "CPU fires"
    tw2, _ = screen.measure_text(who)
    screen.text(who, (screen.width - tw2) // 2, py + 26)

    if sunk_name and sunk_size > 0:
        screen.pen = WHITE
        screen.font = rom_font.nope
        if attacker == "P1":
            msg = "You sunk their " + sunk_name + "!"
        else:
            msg = "CPU sunk your " + sunk_name + "!"
        tw3, _ = screen.measure_text(msg)
        screen.text(msg, (screen.width - tw3) // 2, py + 42)
        sil_cw = 14
        sil_w  = sunk_size * sil_cw
        draw_ship_silhouette(sunk_size, (screen.width - sil_w) // 2, py + 58, sil_cw, 9)
        screen.pen = GRAY
        rem = str(cells_left) + " enemy cells remain"
        tw4, _ = screen.measure_text(rem)
        screen.text(rem, (screen.width - tw4) // 2, py + 78)
    else:
        screen.pen = GRAY
        rem = str(cells_left) + " enemy cells remain"
        tw4, _ = screen.measure_text(rem)
        screen.text(rem, (screen.width - tw4) // 2, py + 42)


def draw_victory(winner_name):
    """Victory screen."""
    _bg()
    # Full logo centred upper half
    if img_logo is not None:
        lx = (screen.width - 200) // 2
        screen.blit(img_logo, rect(lx, 30, 200, 50))

    screen.font = rom_font.yesterday
    screen.pen = HC_ORANGE
    wins = winner_name + " WINS!"
    ww, _ = screen.measure_text(wins)
    screen.text(wins, (screen.width - ww) // 2, 110)

    screen.font = rom_font.nope
    screen.pen = WHITE
    congrats = "Congratulations!"
    cw, _ = screen.measure_text(congrats)
    screen.text(congrats, (screen.width - cw) // 2, 138)

    screen.pen = GRAY
    foot = "A - Play Again      B - Main Menu"
    fw, _ = screen.measure_text(foot)
    screen.text(foot, (screen.width - fw) // 2, 200)
