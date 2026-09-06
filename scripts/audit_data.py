"""Reserved CLI for future observability audit."""

import argparse


def main() -> None:
    """Report pending work without running an unfinished pipeline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    parser.exit(
        2,
        "Not implemented: observability audit. "
        "Start with notebooks/00_data_observability_audit.ipynb.\n",
    )


if __name__ == "__main__":
    main()
