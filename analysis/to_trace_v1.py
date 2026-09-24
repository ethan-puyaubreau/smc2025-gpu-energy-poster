"""Convert one run of data/ into the trace format of energy-dashboard-for-kokkos.

The 2025 connector wrote three CSV files per run (power, regions, kernels).
energy-dashboard-for-kokkos reads a directory with events.csv and
power_samples.csv (trace format v1, see its DATA_SPEC.md). This script writes
that directory, nesting each event under the smallest event that contains it.
Standard library only:

    python analysis/to_trace_v1.py data/fdbscan/illyad-2778967 trace/
    energy-dashboard-for-kokkos analyze trace/
"""
import csv
import sys
from pathlib import Path

CATEGORY = {
    "user_region": "USER_REGION",
    "parallel_for": "PARALLEL_FOR",
    "parallel_reduce": "PARALLEL_REDUCE",
    "parallel_scan": "PARALLEL_SCAN",
    "deep_copy": "DEEP_COPY",
}


def read_events(prefix):
    events = []
    for kind in ("regions", "kernels"):
        with open(f"{prefix}-nvml-{kind}.csv", newline="") as f:
            for r in csv.DictReader(f):
                start, end = int(r["start_time_epoch_ns"]), int(r["end_time_epoch_ns"])
                events.append((start, end, r["name"], CATEGORY[r["type"]]))
    # Parents first: earlier start, then longer event.
    events.sort(key=lambda e: (e[0], -e[1]))
    return events


def convert(prefix, out):
    out.mkdir(parents=True, exist_ok=True)
    stack = []  # (id, end) of the enclosing events
    with open(out / "events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "parent_id", "name", "category", "start_ns", "end_ns"])
        for i, (start, end, name, category) in enumerate(read_events(prefix), start=1):
            while stack and stack[-1][1] < end:
                stack.pop()
            w.writerow([i, stack[-1][0] if stack else 0, name, category, start, end])
            stack.append((i, end))
    with open(f"{prefix}-nvml-power.csv", newline="") as src, \
            open(out / "power_samples.csv", "w", newline="") as dst:
        w = csv.writer(dst)
        w.writerow(["timestamp_ns", "domain", "device_id", "power_watts", "energy_joules"])
        for r in csv.DictReader(src):
            w.writerow([r["time_epoch_ns"], "GPU", 0, r["power_w"], ""])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: to_trace_v1.py data/<variant>/<run> <output directory>")
    convert(sys.argv[1], Path(sys.argv[2]))
