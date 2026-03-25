# Just Getting Home

2D platformer game jam project (theme: **You are not the main character**).

## What’s the game about?
You are an ordinary peasant trying to get home. You cross paths with the hero, who fights enemies. During those fights, the hero’s actions destroy the surroundings, turning your route into a dangerous obstacle course.

## Core gameplay loop (high level)
1. You spawn in a level and observe the hero fighting.
2. The fight creates hazards/obstacles in the environment.
3. The hero goes off-screen after winning.
4. You navigate through the newly-dangerous area to the level exit.

## Requirements
- Python `3.13`
- Windows is the current target (game jam submission + PyInstaller)

## Setup

### 1) Create a virtual environment
PowerShell (recommended):
```powershell
python -m venv .venv
```

### 2) Activate it
```powershell
.venv\\Scripts\\Activate.ps1
```

### 3) Install dependencies
```powershell
pip install -r requirements.txt
```

## Run (scaffold)
```powershell
python main.py
```

### Quick smoke test
Runs briefly and exits:
```powershell
python main.py --smoke-test
```

## Build (later, Day 2/Day 3)
This project uses PyInstaller (per `requirements.txt`) to produce an executable.

Once gameplay + assets exist, the build step will likely move to a `.spec` file and proper asset bundling.

## AI tools used / planned
- Sonnet (Anthropic) to help pick a baseline game idea (and iterate on mechanics).
- Cursor to generate code and build level layouts/tilemaps from drafts.
- ChatGPT (and DALL-E) planned/used to generate pixel-art style assets.

