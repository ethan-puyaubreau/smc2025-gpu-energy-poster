"""Duration, energy and mean power of ArborX's DBSCANCalculation region.

Reads the NVML power traces and Kokkos region timestamps in data/<variant>/,
integrates power with the trapezoid rule over the samples that fall inside each
run's DBSCANCalculation region, and prints the medians over all runs, then the
single run of each variant drawn in the poster and on the portfolio home page.
Standard library only:

    python analysis/dbscan_medians.py

The partial sampling intervals at the two edges of a region (at most one 20 ms
step each) are left out, which lowers each energy by about 2 J; the percentages
do not move.
"""
import csv
import statistics
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
REGION = "DBSCANCalculation"
PLOTTED = {"fdbscan": "illyad-2778967", "fdbscan-dense": "illyad-2039758"}


def read_power(path):
    with open(path, newline="") as f:
        return sorted((int(r["time_epoch_ns"]), float(r["power_w"])) for r in csv.DictReader(f))


def region_bounds(path):
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            if r["name"].endswith(REGION):
                return int(r["start_time_epoch_ns"]), int(r["end_time_epoch_ns"])
    raise ValueError(f"no {REGION} region in {path}")


def measure(regions_csv):
    """Return (seconds, joules, watts) for one run."""
    start, end = region_bounds(regions_csv)
    power = read_power(regions_csv.with_name(regions_csv.name.replace("-regions", "-power")))
    pts = [(t, p) for t, p in power if start <= t <= end]
    joules = sum((t1 - t0) * (p0 + p1) / 2 for (t0, p0), (t1, p1) in zip(pts, pts[1:])) / 1e9
    seconds = (end - start) / 1e9
    return seconds, joules, joules / seconds


def main():
    medians = {}
    for variant in ("fdbscan", "fdbscan-dense"):
        runs = [measure(p) for p in sorted((DATA / variant).glob("*-nvml-regions.csv"))]
        s, j, w = (statistics.median(col) for col in zip(*runs))
        medians[variant] = (s, j, w)
        print(f"{variant:14s} median of {len(runs)} runs: {s:.2f} s  {j:.1f} J  {w:.1f} W")
    (s0, j0, w0), (s1, j1, w1) = medians["fdbscan"], medians["fdbscan-dense"]
    print(f"fdbscan-dense vs fdbscan: {1 - s1 / s0:.0%} less time, {1 - j1 / j0:.0%} less energy, "
          f"{1 - w1 / w0:.0%} less mean power")
    for variant, run in PLOTTED.items():
        s, j, _ = measure(DATA / variant / f"{run}-nvml-regions.csv")
        print(f"plotted run {run} ({variant}): {s:.3f} s  {j:.1f} J")
    return 0


if __name__ == "__main__":
    sys.exit(main())
