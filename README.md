# Understanding GPU Energy Dynamics in HPC Applications

Poster presented at the **Smoky Mountains Computational Sciences and Engineering Conference
([SMC 2025](https://events.ornl.gov/events/smc2025/))**, The Westin Chattanooga, Tennessee,
31 August – 5 September 2025.

**[Read the poster page](https://ethan-puyaubreau.github.io/smc2025-gpu-energy-poster/)** ·
**[Download the PDF](https://ethan-puyaubreau.github.io/smc2025-gpu-energy-poster/smc2025-poster.pdf)**

**Authors** — Ethan Puyaubreau (Université Paris-Saclay, France); Daniel Arndt, Jakob Bludau,
Damien Lebrun-Grandié (Oak Ridge National Laboratory, Computational Science and Engineering Division)

## Abstract

Energy efficiency is becoming as decisive as raw performance in high-performance computing, yet
existing profiling tools struggle to attribute power draw to fine-grained computational events:
hardware counters sample coarsely, and software instrumentation adds significant overhead.

This work extends the [Kokkos Tools](https://github.com/kokkos/kokkos-tools) framework with a
Variorum/NVML connector that samples GPU power from a background daemon and aligns user-defined
region timestamps with the power trace in a postprocessing step. Kokkos applications need no code changes; other codes only have to
annotate the regions of interest.

The poster characterizes the resolution limits of that approach. NVML exposes instantaneous power
only every 100 ms, and the value reported covers just the last 25 ms of each interval, so the
sub-10 ms kernels typical of HPC codes cannot be profiled individually. Larger user-defined regions,
however, remain reliably measurable. A power heatmap across compute- and memory-bound workloads on
an NVIDIA H100 NVL shows that steady-state power depends strongly on workload type, and an ArborX
DBSCAN case study compares two implementations, `fdbscan` and `fdbscan-dense`, which have the same runtime
and return the same result but consume 925.1 J and 784.8 J respectively.

**Minimal runtime does not imply energy efficiency.** GPU power dynamics mandate per-algorithm,
per-hardware measurements, and current tools lack the resolution required to provide them.

## Re-analysis, September 2026

The abstract above is the one presented in 2025. Going back to the raw power traces and region
timestamps of the 64 runs of each implementation, the two DBSCAN implementations do not take the
same time. Over the DBSCANCalculation region, the medians are 2.69 s and 777 J for `fdbscan`, and
2.19 s and 580 J for `fdbscan-dense`: 19% less time and 25% less energy, because the dense variant
also draws 9% less power (262 W against 288 W). The poster's energy boxes (772.8 J and 615.6 J) sum
every kernel region of one run, and its totals (925.1 J and 784.8 J) include the time outside any
region.

The conclusion holds in a narrower form: a time profile reports the 19%, and the remaining six
points only appear when energy is measured. The poster itself is left as presented. Details in
[the write-up](https://ethan-puyaubreau.github.io/blog/kokkos-gpu-energy).

## Data and reproduction

`data/fdbscan/` and `data/fdbscan-dense/` hold the 64 runs of each ArborX DBSCAN implementation
on one NVIDIA H100 NVL, three CSV files per run:

| File | Columns |
| --- | --- |
| `<run>-nvml-power.csv` | `time_epoch_ns`, `power_w`: GPU power read through NVML about every 20 ms |
| `<run>-nvml-regions.csv` | `name`, `type`, `start_time_epoch_ns`, `end_time_epoch_ns`, `duration_ns`: Kokkos user regions |
| `<run>-nvml-kernels.csv` | same columns, for Kokkos kernels |

Recompute every figure on this page (Python 3, standard library only):

```bash
python analysis/dbscan_medians.py
```

The output must match [`analysis/expected_output.txt`](analysis/expected_output.txt); the
[Reproduce workflow](.github/workflows/reproduce.yml) checks it on every push. The poster's own
boxes and totals came from its 2025 plotting script and are not recomputed here.

To attribute the energy of a run to every region and kernel, convert it to the trace format of
[energy-dashboard-for-kokkos](https://github.com/ethan-puyaubreau/energy-dashboard-for-kokkos) and analyze it:

```bash
python analysis/to_trace_v1.py data/fdbscan/illyad-2778967 trace/
energy-dashboard-for-kokkos analyze trace/
```

The tool interpolates power at region boundaries, so it reads about 2 J more than the script for
the same region (771.8 J against 769.3 J for this run).

## External reference

Cited in the U.S. Department of Energy technical report *S4PST 2024–2025 Project Report*
(**ORNL/SPR-2026/4406**, January 2026), [available on OSTI.GOV](https://www.osti.gov/servlets/purl/3016977):

> Ethan Puyaubreau, an undergraduate ORNL summer 2025 intern from Paris-Saclay University, France,
> worked on Kokkos' performance tool capabilities to analyze energy usage of HPC applications. The
> results were presented at the Smoky Mountains Computational Sciences and Engineering Conference.

Reference [63] of the same report: *"Ethan Puyaubreau. Understanding GPU energy dynamics in HPC
applications. Poster presented at the Smoky Mountains Computational Sciences and Engineering
Conference, 2025."*

My appointment title was Graduate Research Fellow (GRO program); I was then in the master's-level
engineering cycle at Polytech Paris-Saclay.

## Associated code

Contributed upstream (status as of September 2026) to [kokkos/kokkos-tools](https://github.com/kokkos/kokkos-tools):

| PR | Status | Title |
| --- | --- | --- |
| [#300](https://github.com/kokkos/kokkos-tools/pull/300) | merged | Energy profiling tools: Add Daemon class for periodic task execution |
| [#299](https://github.com/kokkos/kokkos-tools/pull/299) | open | Energy profiling tools: Core infrastructure with timing tool and export capabilities |
| [#301](https://github.com/kokkos/kokkos-tools/pull/301) | open | Energy profiling tools: NVML-based measurement tool |
| [#302](https://github.com/kokkos/kokkos-tools/pull/302) | draft | Energy profiling tools: Variorum-based measurement tool |
| [#296](https://github.com/kokkos/kokkos-tools/pull/296) | draft | Combining multiple Kokkos Tools using a common interface (PoC) |
| [#293](https://github.com/kokkos/kokkos-tools/pull/293) | merged | Update Makefiles to nvtx3 |

## Cite

```bibtex
@misc{puyaubreau2025gpuenergy,
  author       = {Puyaubreau, Ethan and Arndt, Daniel and Bludau, Jakob
                  and Lebrun-Grandi{\'e}, Damien},
  title        = {Understanding {GPU} Energy Dynamics in {HPC} Applications},
  howpublished = {Poster presented at the Smoky Mountains Computational
                  Sciences and Engineering Conference (SMC 2025),
                  Chattanooga, TN, USA},
  year         = {2025},
  month        = sep,
  url          = {https://ethan-puyaubreau.github.io/smc2025-gpu-energy-poster/}
}
```

## Acknowledgments

This material is based upon work supported by the U.S. Department of Energy, Office of Science,
Office of Advanced Scientific Computing Research (ASCR) as part of the Next Generation of Scientific
Software Technologies program, Stewardship of Programming Systems and Tools (S4PST) project. This
research used resources on the Frank cluster at the University of Oregon.

---

The LaTeX sources of the poster are kept in a separate private repository.
