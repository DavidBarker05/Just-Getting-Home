# Just Getting Home

## Overview
Game jam project for the theme **"You are not the main character"**.

You play as an ordinary peasant trying to get home while the hero fights enemies in front of you and leaves destruction behind.

Core loop:
1. Player spawns and sees the hero/enemy fight sequence.
2. The fight creates hazards and changes traversal.
3. The hero leaves the area.
4. The player crosses the damaged route and reaches the exit.

## Installation / Run Instructions

### Requirements
- Python `3.10+` (recommended: `3.13`, which was used for development and testing)
- Windows target for executable packaging (PyInstaller)

### Setup
1) Create a virtual environment (PowerShell):
```powershell
python -m venv .venv
```

2) Activate it:
```powershell
.venv\Scripts\Activate.ps1
```

3) Install dependencies:
```powershell
pip install -r requirements.txt
```

### Run from source
```powershell
python main.py
```

Optional smoke test:
```powershell
python main.py --smoke-test
```

Optional level select:
```powershell
python main.py --level market
```
Supported level names are listed via:
```powershell
python main.py --help
```

### Build instructions (PyInstaller)
Build using the project spec:
```powershell
python -m PyInstaller --clean -y JustGettingHome.spec
```

Why the spec file matters:
- It ensures the required asset folders are bundled (`assets/levels`, `assets/sprites`, `assets/story`).
- Keep `JustGettingHome.spec` in GitHub so builds are reproducible.

Build outputs:
- Local build output: `dist/JustGettingHome.exe`
- Packaged deliverables are also kept in the `deliverables/` folder.
- Builds are available under the GitHub Releases section.

## Credits
- Me: `ST10438528 - David Barker`
- Library: `pygame`
- Packaging tool: `PyInstaller`

Personal project refinements are logged in `refinements-changes.md`.

## AI Tools Used
- Sonnet (Anthropic): initial idea generation that was then refined further.
- Cursor: primary coding assistant during implementation and iteration.
- Gemini: final image generation used for assets.
- ChatGPT/DALL-E: initially planned in `plan.md`, but not used in the final project deliverables.

