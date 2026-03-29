# HNY Battleship

A single-player Battleship game for the **Pimoroni Tufty 2350** badge, built with the Badgeware (BadgeOS) firmware and the Honeycomb.io brand palette.

Place your fleet, hunt the CPU's ships, and sink them before they sink you.

Built by [Honeycomb.io](https://honeycomb.io)

---

## Platform

| Item | Detail |
|---|---|
| Hardware | Pimoroni Tufty 2350 |
| Firmware | Badgeware (BadgeOS) |
| Resolution | 320×240 (HIRES mode) |
| Buttons | A · B · C (top row) · UP · DOWN (right side) |

Firmware repo: [github.com/pimoroni/tufty2350](https://github.com/pimoroni/tufty2350)

> The game targets Badgeware's injected global API (`screen`, `color`, `rom_font`, `image`, `io`, `rect`, `mode`). It will not run under plain MicroPython or the older PicoGraphics / Tufty2040 firmware.

---

## File Structure

```
/system/apps/battleship/
├── __init__.py        # App entry point — phase state machine, input handling
├── game.py            # Pure game logic — board, placement, fire, sunk detection
├── ai.py              # CPU AI — hunt/target algorithm, checkerboard pattern
├── renderer.py        # All drawing code — menus, grids, overlays, popups
├── icon.png           # 24×24 RGBA launcher icon
└── assets/
    ├── hc_logo_white.png       # Full wordmark   — 200×50 px, white on transparent
    └── hc_logomark_white.png   # Hex logomark    —  48×48 px, white on transparent
```

---

## Installation

1. Hold **BOOT** and tap **RESET** on the Tufty 2350 — a `Tufty2350` USB drive mounts on your computer.
2. Copy the entire `battleship/` folder into `/system/apps/` on that drive:
   ```
   /system/apps/battleship/__init__.py   ← must exist at this path
   ```
3. Safely eject the drive and reboot. The app appears in the BadgeOS launcher.

---

## Asset Requirements

| File | Dimensions | Format | Notes |
|---|---|---|---|
| `icon.png` | 24×24 px | RGBA PNG | BadgeOS launcher icon — HC_ORANGE flat-top hexagon with battleship silhouette |
| `assets/hc_logo_white.png` | 200×50 px | RGBA PNG | Full wordmark, white on transparent |
| `assets/hc_logomark_white.png` | 48×48 px | RGBA PNG | Hex logomark, white on transparent |

Logo draws are guarded with `if img is not None` — missing assets do not crash the app.

---

## Controls

### Menu

| Button | Action |
|---|---|
| B | Start game |

### Ship Placement

| Button | Action |
|---|---|
| UP / DOWN | Move cursor up / down |
| A | Move cursor left |
| C | Move cursor right |
| B | Rotate ship (horizontal ↔ vertical) |
| A + C held together | Confirm placement |

Ghost preview shows the ship in **green** when placement is valid, **red** when invalid. A brief "in position" popup confirms each placement and the cursor nudges to the next row automatically.

### Battle

| Button | Action |
|---|---|
| UP / DOWN | Move targeting cursor up / down |
| A | Move targeting cursor left |
| C | Move targeting cursor right |
| B | Fire at cursor cell |

A turn-result popup appears after every shot. It auto-dismisses after 2.2 seconds and the CPU fires automatically.

---

## Fleet Reference

| Ship | Size |
|---|---|
| Carrier | 5 |
| Battleship | 4 |
| Cruiser | 3 |
| Submarine | 3 |
| Destroyer | 2 |

Total: **17 cells**. First player to have all 17 cells hit loses.

---

## Brand Palette

All colors are `color.rgb()` values — raw tuples are rejected by the Badgeware runtime.

| Token | Role | R | G | B | Hex |
|---|---|---|---|---|---|
| `BG_COLOR` | Screen background (Denim) | 1 | 72 | 123 | `#01487B` |
| `HC_ORANGE` | Hits / P1 accent (Tango) | 249 | 110 | 16 | `#F96E10` |
| `HC_GREEN` | Valid placement / player hit (Lime) | 100 | 186 | 0 | `#64BA00` |
| `HC_BLUE` | Water / empty cells (Cobalt) | 2 | 120 | 205 | `#0278CD` |
| `HC_YELLOW` | Cursor / UI accent (Honey) | 255 | 176 | 0 | `#FFB000` |
| `HC_SHIP` | Ship hull (gray700) | 89 | 96 | 109 | `#59606D` |
| `STATUS_BG` | Status bar (Denim dark) | 1 | 50 | 90 | `#01325A` |
| `WHITE` | Body text | 255 | 255 | 255 | `#FFFFFF` |
| `GRAY` | Dim / hint text | 150 | 150 | 150 | `#969696` |
| `DARK_RED` | Invalid placement flash | 140 | 0 | 0 | `#8C0000` |

---

## Known Limitations

- **Single-player only.** Pass-and-play 2-player mode was removed; Bluetooth badge-vs-badge is on the roadmap.
- **No save state.** Rebooting mid-game loses all progress.
- **No sound.** Buzzer support is not implemented.
- **Fixed fonts.** Only `rom_font.nope` (8 px) and `rom_font.yesterday` (10 px) are available under Badgeware.

---

## Roadmap

- [ ] **Bluetooth 2-player** — badge-vs-badge over BLE; each badge hosts one fleet, turns alternate wirelessly. Deferred pending Badgeware BLE API stabilization.
- [ ] Difficulty levels (easy / normal / hard CPU)
- [ ] High-score persistence via badge filesystem

---

## Credits

Built by [Honeycomb.io](https://honeycomb.io) — Internal tool. Not for redistribution.
