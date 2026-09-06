"""Reserved CLI for future analysis orchestration."""

import argparse


def main() -> None:
    """Report pending work without running an unfinished pipeline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    parser.exit(
        2,
        "Not implemented: analysis orchestration. "
        "The project is in Phase 1.\n",
    )


if __name__ == "__main__":
    main()
