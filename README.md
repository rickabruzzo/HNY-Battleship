# Battleship — Honeycomb.io Edition

A branded Battleship game for the **Pimoroni Tufty 2350** badge running **Badgeware (BadgeOS)** firmware.

Built with the Honeycomb.io brand palette and assets.

---

## Hardware Requirements

| Item | Detail |
|---|---|
| Device | Pimoroni Tufty 2350 |
| Firmware | Badgeware / BadgeOS |
| Display | 320 × 240 px (HIRES mode) |
| Buttons | A · B · C (top row) · UP · DOWN (right side) |

Firmware source: [github.com/pimoroni/tufty2350](https://github.com/pimoroni/tufty2350)

---

## Project Structure

```
battleship/
├── __init__.py          # App entry point — game loop & state machine
├── game.py              # Pure logic — board, placement, firing, win check
├── ai.py                # Hunt/target AI (checkerboard hunt + axis-lock targeting)
├── renderer.py          # All drawing — menus, grids, status bar, overlays
├── icon.png             # 24×24 launcher icon (HC_ORANGE hexagon)
└── assets/
    ├── hc_logo_white.png        # 200×50 full horizontal logo (white)
    └── hc_logomark_white.png    # 48×48 hexagon logomark (white)
```

---

## Deployment

### 1 — Prepare assets on your computer

Resize PNGs to the exact dimensions before copying:

| File | Required size |
|---|---|
| `assets/hc_logo_white.png` | 200 × 50 px |
| `assets/hc_logomark_white.png` | 48 × 48 px |
| `icon.png` | 24 × 24 px |

### 2 — Copy to badge via USB mass storage

1. Hold **BOOT**, tap **RESET** on the Tufty 2350 — a `Tufty2350` drive mounts on your computer.
2. Copy the entire `battleship/` folder into `/system/apps/` on that drive:
   ```
   /system/apps/battleship/
   ```
3. Safely eject the drive.
4. The app will appear in the **BadgeOS launcher** on next boot.

---

## Controls

### Menu
| Button | Action |
|---|---|
| UP / DOWN | Navigate options |
| A | Confirm selection |

### Ship Placement
| Button | Action |
|---|---|
| UP / DOWN / A / B | Move cursor (up / down / left / right) |
| C | Rotate ship (horizontal ↔ vertical) |
| A (twice, same cell) | Confirm placement |

### Battle Phase
| Button | Action |
|---|---|
| UP / DOWN / A / B | Move targeting cursor |
| C | Fire at selected cell |

### General
| Button | Action |
|---|---|
| B | Back / return to menu |

---

## Game Modes

### 1 Player — vs Computer
- Human places ships, then battles the CPU.
- CPU uses a **hunt/target algorithm**: checkerboard-pattern hunt, axis-locked targeting on hits.

### 2 Players — Pass-and-Play
- Both players place ships on the same device — a "look away" splash screen separates each player's turns.
- Pass the device between battle turns.

---

## Fleet

| Ship | Size |
|---|---|
| Carrier | 5 cells |
| Battleship | 4 cells |
| Cruiser | 3 cells |
| Submarine | 3 cells |
| Destroyer | 2 cells |

Total: **17 cells**. First player to have all 17 cells hit loses.

---

## Color Palette

| Role | Name | Hex | RGB |
|---|---|---|---|
| Water / empty | Cobalt | `#0278CD` | (2, 120, 205) |
| Hit / P1 accent | Tango | `#F96E10` | (249, 110, 16) |
| Ship confirmed | Lime | `#64BA00` | (100, 186, 0) |
| Cursor / P2 accent | Honey | `#FFB000` | (255, 176, 0) |
| Background | Denim | `#01487B` | (1, 72, 123) |
| Status bar | Denim darker | `#01325A` | (1, 50, 90) |
| Ship hull | gray700 | `#59606D` | (89, 96, 109) |

---

## Module Reference

### `game.py`
Pure logic — no display calls.

```python
init_board(board)                          # fill 100-cell list with EMPTY
place_ship(board, r, c, length, horiz)     # returns True on success
can_place(board, r, c, length, horiz)      # bounds + overlap check
fire(board, r, c)                          # returns HIT or MISS
check_win(board)                           # True when all SHIP cells are HIT
cpu_place_all(board)                       # random valid placement for CPU

# Cell state constants
EMPTY = 0 | SHIP = 1 | HIT = 2 | MISS = 3
```

### `ai.py`
```python
ai_reset()                                 # reset AI state for new game
ai_take_shot(board, shots_taken)           # returns (row, col)
```

- **HUNT mode**: fires on checkerboard pattern for maximum coverage.
- **TARGET mode**: probes the four cardinal neighbours of a hit, locks onto the correct axis after the second hit, and walks the axis until the ship sinks.
- On ship sunk: clears the target stack and returns to HUNT.

### `renderer.py`
```python
set_images(logo, logomark)                 # call once at startup with loaded Images

draw_menu(selected)                        # main menu (0/1/2)
draw_instructions()                        # static instructions screen
draw_placement(board, ship_idx, r, c, orientation)
draw_battle(own_board, target_board, r, c, player_name)
draw_pass_screen(message)                  # full-screen pass-device splash
draw_victory(winner_name)                  # win screen with logo
```

---

## License

Internal tool — Honeycomb.io. Not for redistribution.
