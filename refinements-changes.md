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
- Enemy disappears visually when defeated.
- Proper fight feedback: enemy flashes (instead of hero) during end-of-route combat.
- Final level: added a house prop that swaps to a destroyed sprite after the hero/enemy fight.
- Adjusted final-level house placement so its bottom-left aligns with the end platform (not buried in ground).
- Added a start screen with buttons for Start Game, Controls, and Quit (plus a controls screen/back flow).
- Controls screen now shows debug controls only in Python runs (hidden in packaged build).
- Added story text screens before each level, after pressing Start, and at game end (with wrapped text + configurable copy in `assets/story/story.json`).
- Fixed story-screen timing: gameplay simulation now stays paused until the player clicks Begin/Continue.
- Build packaging updated: include `assets/story/story.json` in the PyInstaller bundle.
- Updated CLI help text for `--level` to list all supported levels.
- Removed old placeholder sections (`Running notes` and `Open questions`) now that Day 3 decisions are finalized.
- Updated `plan.md` to remove non-required level draft placeholders and add a concrete Day 1/2/3 task list.
- Refined `plan.md` task list again to align with originally planned assignment tasks (removed later-added scope items like debug/menu/story from planned tasks).
- Clarified `plan.md` Day 1 git milestone rationale: repository setup/push happened early to allow safe rollback from the start.
- Restructured `plan.md` for clarity: moved AI tools to a project-wide section and nested each day's task list under that day's milestones.
- Restructured `README.md` to match assignment requirements explicitly (Overview, Installation/Run instructions, Credits, AI tools used) and clarified Python `3.10+` with `3.13` recommended.
- Updated `README.md` wording to state builds are in GitHub Releases and explicitly note ChatGPT/DALL-E were not used in final deliverables.
- Refined `README.md` AI note to clarify ChatGPT/DALL-E were planned in `plan.md` but not used in final deliverables.
- Updated `.gitignore` to stop ignoring `.spec` files so `JustGettingHome.spec` can be tracked for reproducible builds.

## Personal Human-Made Refinements
### Day 1
- None
### Day 2
- Designed the levels myself so that they had more fine-tuning compared to what the AI could output
### Day 3
- Using Gemini to generate images now because ran out of image prompts for ChatGPT after 5 images that I didn't like
- Added in sprites generated by AI to levels
- Updated bridge level ground so that there is variation in texture
- Made fire height 24 pixels so the tetxure wouldn't be squashed
- Added in sprites for player, hero and enemy
- Added in sprites for house and destroyed house
- Adjusted house position, exit position, and where the hero and enemy stop on the burninghearthrun level
- Changed the story messages to my own story messages to better match my original idea
- Fixed spelling and grammar in the story
- Added references pdf
- Added AI disclosure to references


