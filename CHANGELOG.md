# Changelog

All notable changes to HNY Battleship are documented here.
Format follows [Conventional Commits](https://www.conventionalcommits.org/).

---

## [v1.0.0] — 2026-03-28

### feat: initial architecture

- Five-file project structure: `__init__.py` (state machine), `game.py` (pure logic), `ai.py` (CPU), `renderer.py` (drawing), with PNG assets loaded at startup
- Targeted Badgeware (BadgeOS) firmware on Pimoroni Tufty 2350; all builtins (`screen`, `color`, `rom_font`, `image`, `io`, `rect`, `mode`) treated as injected globals — not imported
- Flat 100-element lists for board state; no dicts or dynamic allocation inside `update()`
- Phase state machine with single-element list refs (`_phase = [PHASE_MENU]`) for MicroPython closure compatibility

### fix: Badgeware API corrections

- Removed all `import badge` / `badge.mode()` / `badge.pressed()` calls — `badge` object does not exist in Badgeware
- Replaced `run(update)` module-level call; Badgeware calls `update()` directly via its own runtime loop
- Replaced `Image` class references with `image.load()` (lowercase builtin global)
- Replaced all `badge.pressed(BUTTON_X)` with `io.BUTTON_X in io.pressed`
- Replaced all `badge.ticks` with `io.ticks` (placement timing) and `time.ticks_ms()` (battle warning timer)
- Added `mode(HIRES)` call at module level before renderer import so `screen.width` returns 320 when renderer constants are evaluated

### fix: font system

- Replaced PicoGraphics font names `rom_font.bitmap8` and `rom_font.bitmap14` with Badgeware equivalents: `rom_font.nope` (8 px body) and `rom_font.yesterday` (10 px title)
- Switched all text centering from `len(text) * N` pixel estimates to `screen.measure_text(str)` returning `(width, height)`

### fix: color system

- Corrected Honeycomb.io brand palette from badge screenshots; final values: Denim `(1,72,123)`, Tango `(249,110,16)`, Lime `(100,186,0)`, Cobalt `(2,120,205)`, Honey `(255,176,0)`, gray700 `(89,96,109)`
- Replaced all raw RGB tuples with `color.rgb(r,g,b)` — the Badgeware runtime rejects tuples with `TypeError: value must be of type brush or color`

### fix: screen resolution

- Replaced hardcoded `SCREEN_W = 320` / `SCREEN_H = 240` constants with `screen.width` / `screen.height` dynamic reads, resolved text clipping at 160 px (low-res default)
- Confirmed `screen.blit(img, rect(x,y,w,h))` as correct blit API; removed references to nonexistent `screen.scale_blit()`

### refactor: remove 2-player mode

- Stripped pass-and-play 2-player mode entirely: removed `PHASE_PLACE_P2`, `PHASE_PASS_PLACE`, `PHASE_PASS_BATTLE`, `_handle_pass()`, and `draw_pass_screen()`
- Simplified `_placement_done()` — always places CPU ships and transitions directly to `PHASE_BATTLE`
- Removed `_placing_p1_done` flag and all P2 board placement state

### feat: placement controls

- Iterated through multiple placement schemes: A-twice-on-same-cell, double-tap B within 350 ms timing window, final: UP/DOWN/A/C to move cursor, B to rotate, A+C held simultaneously to confirm
- Movement suppressed while confirm chord is held to prevent accidental cursor drift
- `io.held` used for confirm detection; `io.pressed` used for discrete button events

### feat: placement UX

- Ghost preview renders full ship length at cursor in HC_GREEN (valid) or `rgb(200,50,50)` (invalid); built with manual cell list to avoid empty returns for partially off-grid positions
- Cursor nudges one row below anchor after each confirmed placement (or one row up if at bottom row)
- Brief "in position" confirmation popup (`draw_place_confirm`) displayed for 1.2 s after each ship placed; draws placement grid underneath with popup overlay on top
- Removed dirty-flag optimization (`_placement_dirty`) in favor of always-redraw each frame — eliminates one-frame gap when transitioning back from `PHASE_PLACE_CONFIRM`
- `PHASE_PLACE_CONFIRM = 10` added to phase constants

### feat: placement intro screen

- `draw_placement_intro()` added: full-screen splash before placement begins showing all five ship silhouettes with hull, deck strip, and conning tower pixel art
- Each ship row: name + size label left-aligned, silhouette right-aligned with `BW=12` cell width
- Controls reference block lists move, rotate, and confirm inputs
- "Press B to begin" prompt centered at bottom; B press transitions to `PHASE_PLACE_P1`
- `PHASE_PLACE_INTRO = 8` added to phase constants

### feat: battle controls

- Battle cursor movement: UP/DOWN/A/C (left=A, right=C, mirroring placement)
- Fire button: B
- `draw_battle()` status bar updated to `"B:fire  UP/DN/A/C:move"`

### feat: turn result popup

- `draw_turn_result()` renders a centered `260×80` (or `260×108` when a ship sank) popup overlay drawn on top of the existing battle screen — no full-screen repaint
- Border and background color varies by outcome: HC_GREEN border = player hit, `rgb(200,50,50)` border = CPU hit, HC_YELLOW border = miss
- Expanding box animation on hits: ring radius cycles via `elapsed_ms // 35 % 24 + 4`
- Sunk path: sunk ship name + `draw_ship_silhouette()` centered + enemy cells remaining count
- Auto-dismisses after 2.2 s; CPU fires automatically after player's result screen clears
- `PHASE_TURN_RESULT = 9` added to phase constants

### feat(game): sunk detection and cells remaining

- `check_sunk(board, r, c)` added: after a hit, scans horizontal then vertical HIT runs from `(r,c)`; confirms sunk when both ends of the run border non-SHIP cells; matches run length against `SHIP_SIZES`; returns `(size, name)` or `(0, "")`
- `cells_remaining(board)` added: counts unhit SHIP cells via generator sum; used for cells-remaining display in turn result popup

### feat: CPU AI

- Hunt/target algorithm in `ai.py`: checkerboard-pattern hunt for maximum coverage, switches to TARGET mode on first hit
- Target mode probes four cardinal neighbours; locks to correct axis after second consecutive hit on same ship; walks axis until ship sinks
- On ship sunk: clears target stack and returns to HUNT mode
- `ai_reset()`, `ai_take_shot(board, shots)`, `ai_notify_result(board, r, c, result)` public API

### feat: menu redesign

- Single large START GAME button (`200×36`, HC_ORANGE fill, highlight strip, shadow) replaces two-item navigable list
- Logomark PNG restored via `screen.blit()` top-left; `_draw_menu_ship()` pixel-art helper removed
- `_menu_sel` state variable removed; UP/DOWN navigation and instructions branch removed from `_handle_menu`
- B press on menu immediately seeds RNG, resets boards, and transitions to `PHASE_PLACE_INTRO`
- `renderer.draw_menu()` still accepts `selected` parameter for call-site compatibility (unused)

### feat: app icon

- 24×24 RGBA PNG generated via Pillow: HC_ORANGE flat-top hexagon background, diagonal battleship silhouette (dark gray hull + deck strip), small bow explosion spark in white/yellow
- Placed at `/system/apps/battleship/icon.png` for BadgeOS launcher display

### docs: roadmap

- Bluetooth badge-vs-badge 2-player mode pinned as next major feature; deferred pending Badgeware BLE API stabilization
