import argparse
import os

from src.game_app import GameApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Just Getting Home (prototype scaffold)")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run briefly and exit (useful for CI/sanity checks).",
    )
    parser.add_argument("--level", type=str, default="market", help="Level name: market or bridge.")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=544)
    return parser.parse_args()


def run(smoke_test: bool, width: int, height: int, level: str) -> int:
    # Import pygame only after we potentially set SDL_VIDEODRIVER.
    if smoke_test:
        # Helps the smoke test avoid needing a real display.
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    app = GameApp(width=width, height=height, level_name=level, smoke_test=smoke_test)
    return app.run()


def main() -> int:
    args = parse_args()
    return run(smoke_test=args.smoke_test, width=args.width, height=args.height, level=args.level)


if __name__ == "__main__":
    raise SystemExit(main())

