"""Run the full tightening-cycle timing study end to end.

Usage:  python run_all.py        (set FORCE_REFRESH=1 to bypass the cache)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from data import load_all, verify_series          # noqa: E402
from events import CYCLES, verify_events          # noqa: E402
import analysis                                   # noqa: E402


def main():
    print("=== 1/3 data ===")
    series = load_all()
    data_problems = verify_series(series)

    print("=== 2/3 event verification ===")
    flags = verify_events(series)
    for f in flags:
        print("  FLAG:", f)
    if not flags:
        print("  no inconsistencies")

    print("=== 3/3 detection + analysis ===")
    master, stats, orders, dd, robust = analysis.run(series, flags, data_problems)

    print(f"\n{len(CYCLES)} cycles, {len(master)} master rows.")
    print("Outputs in output/: SUMMARY.md, master_timeline.csv, "
          "interval_stats.csv, orderings.csv, drawdowns.csv, robustness.csv, "
          "timeline_<cycle>.png, timelines_all.png")


if __name__ == "__main__":
    main()
