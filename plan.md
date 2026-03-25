# Day Plan: Development Milestones (Day 1 Scaffold + Future Work)

This file tracks milestones and the “when to do what” schedule for the jam.

## Day 1 (current)

### Milestones
1. Scaffold a minimal Python + Pygame project that runs.
2. Create required documentation:
   - `high-concept.md`
   - `plan.md`
   - `README.md`
   - `refinements-changes.md`
3. Add level set drafts (text-only) for implementation on Day 2.
4. Initialize git and push the Day 1 scaffold to GitHub.

### AI tools planned (Day 1)
- Sonnet for early ideation/constraints.
- Cursor for project scaffolding and later code generation.
- ChatGPT/DALL-E for art assets (later).

## Day 2 (later)

### Milestones
1. Implement core platformer movement and collisions.
2. Implement the “hero fight phase” (a timed event that spawns hazards).
3. Implement a level loader and level layout format.
4. Create a playable prototype build/executable via PyInstaller.

## Day 3 (later)

### Milestones
1. Polish gamefeel (controls, feedback, hazards readability).
2. Finalize level content.
3. Generate/insert pixel art assets.
4. Ensure PyInstaller packaging works reliably with assets.
5. Produce final playable build/executable and tidy the submission.

## Level Set Drafts (text-only)

The goal is to describe visuals, spawn markers, exit markers, and “hero fight hazards” so Day 2 implementation can translate drafts into tilemaps.

### Shared visual language (tentative)
- Tile size: `16x16` (placeholder assumption).
- Colors: stone/wood neutrals for environment; warm orange for hazards; moss/leaf greens for forest.
- Markers (placeholders later):
  - Start marker: a small signpost or lantern sprite.
  - End marker: a banner/door/bridge-end icon.

### Market Level: `Market`
Theme: daytime market chaos; hero battle knocks debris into the walking route.

Visual style
- Ground: packed dirt with stone slabs between stalls.
- Stalls: simple wood posts with cloth awnings.
- Background: town wall outline and trees beyond.

Spawn marker concept
- A “Peasant Notice Board” (small sign + paper) near the market entrance.

Exit marker concept
- A bright town-gate arch (banner on top) at the far end.

Hero fight hazard concept (created during the fight)
- Dropping crates from toppled stalls (temporary platforms that become hazards).
- Flying broken pottery (short-lived ground fire patches / burn stains).
- Collapsed canopy beams that become impassable rubble blocks.

Draft layout idea (single-screen-ish ASCII sketch)
Legend: `#` solid ground, `.` empty, `S` start, `E` exit, `B` stall post, `H` hazard spawn area
```
................................................................
..................................................B.............
....B..........B.................B...............................
....#..........#.................#..............H...............
....#.....B....#......H.............B...........................
....#..........##.........#...................########...........
....#.....#######.........#..............##........##............
....#....#.....#.........#..............#..........#............
....#....#.....#.........#..............#...H......#............
....S....#.....#........E#.............#..........#.............
....######.....############.............##########....B..........
................................................................
```

### Bridge Level: `Bridge`
Theme: the hero battle changes a critical crossing.

Visual style
- Ground: stone bridge floor tiles.
- Sides: wooden railings with occasional broken planks.
- Background: river with light shimmer; trees along banks.

Spawn marker concept
- A “Bridge Toll Board” sign (peasant avoids the gate; heads for the crossing).

Exit marker concept
- A “Road Continue” marker (banner/marker stone) on the far bank.

Hero fight hazard concept
- Bridge planks break in the hero’s struggle (gaps appear).
- Debris piles up where the player must walk (temporary blockade).
- Rope or chain (if any) can swing hazards across the route.

Draft layout idea
Legend: `#` solid, `.` empty, `S` start, `E` exit, `G` gap, `H` hazard zone, `R` railing
```
................................................................
......R###############################R..........................
......R#.................H...........#R........................
......R#.......................G.......#R.......................
......R#......#######................#R........................
......R#.....#.....#...........H.....#R........................
......R#.....#..S..#.................#R........................
......R#.....#.....#...........#######R.......................
......R#.................G.......E.....R.......................
......R###############################R..........................
................................................................
```

### Forest Level: `ForestChokePoint`
Additional level idea (beyond Market + Bridge).

Visual style
- Ground: roots + packed dirt.
- Platforms: fallen logs and stump tops.
- Background: layered trees; light fog feel.

Spawn marker concept
- A mossy signpost with an arrow pointing toward the “homeward path”.

Exit marker concept
- A stone cairn (stacked rocks) at a narrow trail exit.

Hero fight hazard concept
- Fallen logs shift and fall as the hero battles (introduce moving hazard blocks).
- Debris cascades down slopes (short-term hazard trails).

Hazard theme
- “Choke points become collapsing routes.”

### Homecoming Level: `BurningHearthRun`
Additional level idea (beyond Market + Bridge).

Visual style
- Ground: charred wood planks and cracked stone.
- Lighting: darker palette, embers (orange glow) around hazards.
- Background: broken fence silhouette; smoke plume outline.

Spawn marker concept
- A broken hearthstone with cracks and soot.

Exit marker concept
- The home gate/doorway frame (still standing enough to aim for).

Hero fight hazard concept
- Collapsing timbers (large rubble blocks appear).
- Fire patches spread across “safe” ground after the hero battle.

Hazard theme
- “Home becomes the danger zone.”

