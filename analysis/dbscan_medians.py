"""Duration, energy and mean power of ArborX's DBSCANCalculation region.

Reads the NVML power traces and Kokkos region timestamps in data/<variant>/,
integrates power with the trapezoid rule over the samples that fall inside each
run's DBSCANCalculation region, and prints the medians and quartiles over all
runs, a bootstrap 95% interval for the relative differences, the slow runs and
the comparison without them, then the single run of each variant drawn in the
poster and on the portfolio home page.
Standard library only:

    python analysis/dbscan_medians.py

The partial sampling intervals at the two edges of a region (at most one 20 ms
step each) are left out, which lowers each energy by about 2 J; the percentages
do not move.
"""
import csv
import random
import statistics
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
REGION = "DBSCANCalculation"
PLOTTED = {"fdbscan": "illyad-2778967", "fdbscan-dense": "illyad-2039758"}
BOOTSTRAP = 10_000  # resamples; the seed is fixed so the output is reproducible


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


def reduction(a, b, k):
    """Relative reduction of the median of column k from runs a to runs b."""
    return 1 - statistics.median(r[k] for r in b) / statistics.median(r[k] for r in a)


def main():
    runs, medians = {}, {}
    for variant in ("fdbscan", "fdbscan-dense"):
        runs[variant] = [measure(p) for p in sorted((DATA / variant).glob("*-nvml-regions.csv"))]
        s, j, w = (statistics.median(col) for col in zip(*runs[variant]))
        medians[variant] = (s, j, w)
        print(f"{variant:14s} median of {len(runs[variant])} runs: {s:.2f} s  {j:.1f} J  {w:.1f} W")
    for variant in ("fdbscan", "fdbscan-dense"):
        (qs1, _, qs3), (qj1, _, qj3) = (statistics.quantiles([r[k] for r in runs[variant]], n=4)
                                        for k in (0, 1))
        print(f"{variant:14s} quartiles: {qs1:.2f} to {qs3:.2f} s  {qj1:.1f} to {qj3:.1f} J")
    (s0, j0, w0), (s1, j1, w1) = medians["fdbscan"], medians["fdbscan-dense"]
    print(f"fdbscan-dense vs fdbscan: {1 - s1 / s0:.0%} less time, {1 - j1 / j0:.0%} less energy, "
          f"{1 - w1 / w0:.0%} less mean power")
    rng = random.Random(2025)
    a, b = runs["fdbscan"], runs["fdbscan-dense"]
    for k, what in ((0, "time"), (1, "energy")):
        boot = sorted(reduction(rng.choices(a, k=len(a)), rng.choices(b, k=len(b)), k)
                      for _ in range(BOOTSTRAP))
        lo, hi = boot[int(0.025 * BOOTSTRAP)], boot[int(0.975 * BOOTSTRAP) - 1]
        print(f"bootstrap 95% interval, reduction in {what}: {lo:.1%} to {hi:.1%}")
    # Runs far slower than their variant's median, in job order (file names sort by job id).
    for variant in ("fdbscan", "fdbscan-dense"):
        med = medians[variant][0]
        slow = [i for i, r in enumerate(runs[variant], start=1) if r[0] > 1.3 * med]
        if not slow:
            print(f"{variant:14s} no run is more than 30% slower than the median")
            continue
        sr = [runs[variant][i - 1] for i in slow]
        print(f"{variant:14s} {len(slow)} slow runs, numbers {slow[0]} to {slow[-1]} in job order: "
              f"{min(r[0] for r in sr):.2f} to {max(r[0] for r in sr):.2f} s, "
              f"mean power {statistics.mean(r[2] for r in sr):.0f} W")
        rest = [r for i, r in enumerate(runs[variant], start=1) if i not in slow]
        other = runs["fdbscan" if variant == "fdbscan-dense" else "fdbscan-dense"]
        a, b = (other, rest) if variant == "fdbscan-dense" else (rest, other)
        print(f"without them, fdbscan-dense vs fdbscan: {reduction(a, b, 0):.0%} less time, "
              f"{reduction(a, b, 1):.0%} less energy")
    for variant in ("fdbscan", "fdbscan-dense"):
        s_, j_, _ = (statistics.mean(col) for col in zip(*runs[variant]))
        print(f"{variant:14s} mean of all runs: {s_:.2f} s  {j_:.1f} J")
    for variant, run in PLOTTED.items():
        s, j, _ = measure(DATA / variant / f"{run}-nvml-regions.csv")
        print(f"plotted run {run} ({variant}): {s:.3f} s  {j:.1f} J")
    return 0


if __name__ == "__main__":
    sys.exit(main())
