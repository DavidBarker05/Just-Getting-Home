# Refinements & Changes Log

## Day 1 decisions
- Target Python `3.13` to match your jam build preference.
- Use `pygame` for the 2D platformer foundation (`pygame==2.6.1` as the initial pinned version).
- Use `PyInstaller` to satisfy the “build/executable” requirement for the jam (Windows-friendly).
- Replaced `high-concept.md` with the provided `ST10438528 GADS7331 POE Part 1 High Concept.pdf` as the project’s high concept source doc.
- Day 1 scope is intentionally scaffold-only: no gameplay systems, no level logic, no asset pipeline yet.

## Day 2 decisions (prototype implementation begins)
- Implemented a minimal 2D tile-based platformer core (movement, jump, gravity, collision).
- Added a text-based level loader using ASCII maps for `market` and `bridge`.
- Implemented the “hero fight phase” as a timed sequence:
  - hero attacks enemy until the enemy “dies”
  - the fight breaks destructible floor tiles (`X`)
  - broken areas spawn temporary hazard patches (fire)
  - after the hero retreats off-screen, the exit becomes reachable
- Added missing Day 2 draft ASCII layout sketches for `ForestChokePoint` and `BurningHearthRun` in `plan.md` (text-only, before full implementation).
- Added `forestchokepoint` and `burninghearthrun` level ASCII maps to `src/levels.py` (prototype implementation).
- Updated prototype progression: reaching the exit advances to the next level; only the final level shows the “You made it home!” message.
- Refactored level data to load from external JSON files (`assets/levels/*.json`) instead of hard-coded ASCII maps, and updated the tilemap loader accordingly.
- Refined the JSON level schema: `x`/`y` for floors, spawns, and hazards are now tile coordinates (not pixel coordinates) to make level editing simpler and consistent with fixed tile size.
- Refined the JSON level coordinate system again: levels now use a bottom-left origin for `x`/`y` (so `y=0` is the bottom row).
- Fixed level JSON floor placement after the origin change: floor/breakable floor now uses `y=0` (bottom row) so the world renders at the bottom of the screen.
- Fixed fire hazards not spawning reliably when the enemy dies slightly before `DESTROY_AT`; hazards now trigger based on time alone.
- Updated gameplay rules: player movement is locked at the start (until the hero is off-screen) and fire hazards are now permanent (no expiration).
- Big gameplay refactor: hero/enemy now follow a per-level `route`, destroying `breakable_floor` tiles and spawning permanent fire tile-by-tile after the hero leaves each tile; levels were redesigned to create vertical traversal.
- Fixed progression edge case: after the enemy is defeated, the hero now properly walks off-screen (so the player unlocks) instead of being re-snapped to the route end tile.
- Refined hazard semantics (reverted): `fire_spawn` markers place fire on the tile above the floor tile the hero leaves (matching the earlier “floating fire over the tile” behavior before the refactor).
- Refined level design: levels now go up then back down (exit on the same vertical level as the player), platforms are wider (avoid single-tile landings), and fire is placed only on non-`breakable_floor` tiles.
- Updated route traversal: enemy now leads and hero follows; exit is placed at the far right of each level. Enemy stops 1 tile left of the exit tile, and the hero stops 2 tiles left.
- Fixed exit placement: exit rect now aligns with the floor tile (no longer spawns partially inside the ground).
- Fix: player jumping is now consistent via jump buffering and coyote time (tolerates slightly early/late jump presses on landing).
- Fixed route visuals: hero/enemy now use the route tile’s actual `y` position when being placed (no -1 tile offset).
- Added a Python-only debug mode (disabled in the executable): F1 toggle; F2 FPS-in-title; F3 level name overlay; F4 god mode; F5 restart level; F6 restart game; F7 pause; and step-time controls (`,`/`.`/`/`) with configurable step sizes.
- Fixed debug pause/restart timing bug by using one simulation clock for route timing and debug stepping, preventing paused restart desync and route index errors.
- Fixed route/fire alignment: route points are treated as actor-step cells (one above floor), so break/fire logic now offsets to the actual floor tile when applying destruction/spawn.
- Cleanup: removed unused `enemy_gap_steps` (hero follow gap is fixed at 1 step now).

## Day 3 decisions
- Clamp player to screen left/right bounds (no off-screen drift).
- Add per-object `sprite` support to level JSONs (defaults to shapes when `sprite` is empty) and bundle `assets/sprites/`.

## Personal Human-Made Refinements
### Day 1
- None
### Day 2
- Designed the levels myself so that they had more fine-tuning compared to what the AI could output

## Running notes (updates later)
- Level content will be drafted first (text-only), then implemented on Day 2 as real tilemaps/logic.
- Asset generation (pixel art) will happen later using ChatGPT/DALL-E outputs where appropriate.
- Packaging will be validated after Day 2 code exists, so Day 3 can bundle assets reliably.

## Open questions
- Exact tile size / resolution for the pixel art (tentative: 16x16 or 24x24 tiles).
- Whether to hardcode levels as simple ASCII maps first, or use a tiny JSON tilemap format.

