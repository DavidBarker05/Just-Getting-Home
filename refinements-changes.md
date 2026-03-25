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

## Running notes (updates later)
- Level content will be drafted first (text-only), then implemented on Day 2 as real tilemaps/logic.
- Asset generation (pixel art) will happen later using ChatGPT/DALL-E outputs where appropriate.
- Packaging will be validated after Day 2 code exists, so Day 3 can bundle assets reliably.

## Open questions
- Exact tile size / resolution for the pixel art (tentative: 16x16 or 24x24 tiles).
- Whether to hardcode levels as simple ASCII maps first, or use a tiny JSON tilemap format.

