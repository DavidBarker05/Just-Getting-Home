import argparse
import os
import sys
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Just Getting Home (prototype scaffold)")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run briefly and exit (useful for CI/sanity checks).",
    )
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    return parser.parse_args()


def run(smoke_test: bool, width: int, height: int) -> int:
    # Import pygame only after we potentially set SDL_VIDEODRIVER.
    if smoke_test:
        # Helps the smoke test avoid needing a real display.
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    import pygame  # noqa: WPS433 (runtime import is intentional)

    pygame.init()
    try:
        pygame.display.set_caption("Just Getting Home")
        screen = pygame.display.set_mode((width, height))
        clock = pygame.time.Clock()
        font = pygame.font.SysFont(None, 28)

        start = time.time()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            if smoke_test and (time.time() - start) >= 1.5:
                running = False

            screen.fill((30, 25, 20))
            title = font.render("Prototype scaffold (Day 2 gameplay later)", True, (235, 220, 190))
            help_text = font.render("Press Esc to quit.", True, (200, 200, 200))
            screen.blit(title, (30, 30))
            screen.blit(help_text, (30, 65))
            pygame.display.flip()

            clock.tick(60)
    finally:
        pygame.quit()

    return 0


def main() -> int:
    args = parse_args()
    return run(smoke_test=args.smoke_test, width=args.width, height=args.height)


if __name__ == "__main__":
    raise SystemExit(main())

