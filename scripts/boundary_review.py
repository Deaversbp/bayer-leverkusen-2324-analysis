"""Build the bounded Phase 3A-2A human review pack from pinned sources."""

from pathlib import Path
import argparse

from leverkusen.sequences.boundary_review import STATUS, run_review_pack
from leverkusen.visualization.boundary_review import (
    load_review_tables,
    write_review_visuals,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Reuse existing derived review CSVs offline",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tables = (
        load_review_tables(root)
        if args.render_only
        else run_review_pack(root, progress=lambda text: print(text, flush=True))
    )
    traces, triptychs = write_review_visuals(tables, root)
    print(tables["category_coverage"].to_string(index=False))
    print(f"Wrote {traces} traces and {triptychs} snapshot triptychs. {STATUS}")


if __name__ == "__main__":
    main()
