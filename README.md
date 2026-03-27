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

## AI Reflections
### Where did AI excel, and where did it mislead or limit me?
I would say that the AI excelled extremely well when it came to producing content fast. It was also very good at being able to understand a lot of bugs and able to fix them relatively easily.

I would say that Cursor’s biggest limitation was more quality. I found the best way to make sure errors get fixed faster is to understand where/how an error occurs. I spent a lot of day two making it fix bugs or add ways for me to debug or even add stuff to the game myself. One time I saw a bug and figured out why it happened and what Cursor did that caused this, and when I told it the bug, it told me that it wasn’t a bug, I then had to explain the whole reason for it to fix it. It also was not very good at generating levels, so I ended up having to write the JSON files for each level.

Nano Banana 2 had similar benefits and problems. It produced lots of pictures relatively fast, but they also weren’t the best quality. I had to spend a lot of time in Photoshop making fixed and changes so that the images were good for the game which limited the actual speed of image creating by a lot.

### How did AI alter my creative or technical process?
I would say the biggest change to my process was the fact that I wasn’t able to code. Having to let an AI do all the code writing for me felt extremely weird. Also, it programs much more differently to me so I had to understand how it writes code to be able to work with it. The fact that it put a lot of the code into game_app.py feels very weird to me.

I also had to try and keep changes small so that the AI would be less likely to be confused or start making lots of changes that break the game which I’ve learned from past uses of AI. Normally I like to make lots of similar changes at once, but for the AI I had to try and split up each of those changes into their own prompt.

Spending most of my time thinking what I want the AI to fix and how I want to tell the AI what to fix felt weird to me. Normally I have to think how to make the fixes myself, but here it feels like I’m managing someone and telling them to fix the changes for me.

### What would I change about my collaboration with AI next time?
If I were to do something similar to this again with AI, I would probably make the AI do the initial setup and creating the base for the game. I would then take that and refine the game myself and create a more polished game closer to how I like. In a similar way to how I was working with Nano Banana 2 where I took its images into Photoshop to refine and polish them for the game.

As I explained before that I often had to figure out where and why the bugs happened to explain them to Cursor for it to fix them. I often felt like I could probably just fix these bugs myself, but I’m not that experienced with Python and it would be against the spirit of this assignment. But, in the future, if there were bugs that I had trouble fixing or understanding then I could try and work with Cursor to help me fix them. It would feel like I have a second person helping me.

I’d also probably try to work in a language I have a better understanding of like C# or C++ because trying to work in a language I don’t understand well is hard.

### Ethical considerations: Did my use of AI respect originality, transparency, and fair use?
Coding-wise I’d say that my use of AI respected originality, transparency, and fair use. I think the biggest offender to those was Gemini/Nano Banana 2. I feel like because I told it that I wanted a pixelated art style that it started using very generic and derived art. A lot of the earlier art that it generated for me felt very much like Minecraft’s art. The grass, fire and stone textures are good examples of this. All the tile textures even had a border around them that felt like a hotbar slot from Minecraft.

After it generated the tile for the market then it looked a lot less like Minecraft and closer to its own style, but it still felt unoriginal. I think the reason that this happened is because I said fantasy village for the market tile so after that the sprites all felt more fantasy styled which can be seen in the wood for the bridge and trees. The characters it generated also seem very unoriginal, I feel like I could see them in a free fantasy asset pack on an online marketplace. However, they were still relatively unique enough that I feel they respect fair use, even though they feel derivative.

### Were there moments where relying on AI felt ethically questionable?
As stated int the previous section the use of Nano Banana 2 did feel very derivative of existing work. That to me felt ethically questionable, because it feels like I’m using the art of other people without giving them proper credit, even though the art isn’t exactly the same.

Also just going into personal beliefs relying on AI feels ethically or morally questionable. Personally, I try to avoid relying on AI as much as possible because I feel like it makes me unlearn all the stuff I used to know. So, using AI as much as I did in this project felt extremely wrong to me, and it felt like it went against everything that I stand for or believe in when it comes to AI.

Another ethical issue I have with AI is with it replacing jobs/people. So, using AI to generate all of my assets felt ethically questionable, because I could have rather used assets created by people online.

Also, in general, relying on AI for this entire project feels ethically questionable to me, because it doesn’t feel like I should be able to call this game “my game”. Even though I came up with the idea, it doesn’t feel like I did anything.

### Did I credit AI-generated assets properly?
I have properly credited all AI-generated assets and uses. All references can be found in [ST10438528 GADS7331 POE Part 1 References](/ST10438528%20GADS7331%20POE%20Part%201%20References.pdf)

I credited my use of Sonnet for helping me to come up with the original idea that I then designed and based my game off of. It has also been included in the AI usage statement in [ST10438528 GADS7331 POE Part 1 References](/ST10438528%20GADS7331%20POE%20Part%201%20References.pdf)

The code for this project was generated by Cursor which has been properly credited. The whole conversation with cursor can be found in [its respective markdown file](CursorConversation/cursor_game_development_plan_for_just_getting_home.md). It has also been included in the AI usage statement in [ST10438528 GADS7331 POE Part 1 References](/ST10438528%20GADS7331%20POE%20Part%201%20References.pdf)

The images used in this project were generated by Nano Banana 2 and have been properly credited. The edits that I made in Photoshop were properly credited as well. Nowhere did I explicitly claim they were my images; they all state that they used the generated images as a base. They also state what changes I made to the images in photoshop. [ST10438528 GADS7331 POE Part 1 References](/ST10438528%20GADS7331%20POE%20Part%201%20References.pdf) also contains a list of figures for every image. The use of Nano Banana 2 has been in included in the AI usage statement in [ST10438528 GADS7331 POE Part 1 References](/ST10438528%20GADS7331%20POE%20Part%201%20References.pdf)

### How can I ensure my future work with AI remains responsible and authentic?
For future work I can make sure that my work with AI remains responsible and authentic by using AI as a tool rather than relying on it to do everything. I can use AI as a way to teach me things that I don’t understand, I could use it to help me find bugs in code, or I could use it to show me the steps to finding the answer instead of it just giving me the answer. I can do most of the work myself and AI can just be there to fill in the gaps that I leave behind as if it were helping me, not as if I was managing it and hoping it does everything right. I would try to use it more responsibly and not rely on it.

For image generation I could use AI to generate concept art for the game, which I could then use as a basis for my own art. Although I am not the best artist, I can still draw create assets to a basic level. This would also help me feel better about my project and make it feel more authentic to not just others but myself.

## AI Ethics Statement
This project complies with originality and fair use. It doesn't use any person's assets without giving them permission.

All use of AI withing this project falls under the specifications that were given for the assignment.

No work was directly copied from any source. AI art is different any some way from any possible assets that I know of which makes it fall under fair user.
