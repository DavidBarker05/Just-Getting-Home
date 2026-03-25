# Refinements & Changes Log

## Day 1 decisions
- Target Python `3.13` to match your jam build preference.
- Use `pygame` for the 2D platformer foundation (`pygame==2.6.1` as the initial pinned version).
- Use `PyInstaller` to satisfy the “build/executable” requirement for the jam (Windows-friendly).
- Day 1 scope is intentionally scaffold-only: no gameplay systems, no level logic, no asset pipeline yet.

## Running notes (updates later)
- Level content will be drafted first (text-only), then implemented on Day 2 as real tilemaps/logic.
- Asset generation (pixel art) will happen later using ChatGPT/DALL-E outputs where appropriate.
- Packaging will be validated after Day 2 code exists, so Day 3 can bundle assets reliably.

## Open questions
- Exact tile size / resolution for the pixel art (tentative: 16x16 or 24x24 tiles).
- Whether to hardcode levels as simple ASCII maps first, or use a tiny JSON tilemap format.

