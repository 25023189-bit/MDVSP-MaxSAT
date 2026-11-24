<div align="center">

# SAT/MaxSAT Encoding for the Multiple Depot Vehicle Scheduling Problem

**A MaxSAT model solved with a counterexample-guided refinement (CEGAR) loop, published as a documented negative result.**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![MaxSAT](https://img.shields.io/badge/MaxSAT-EvalMaxSAT%20via%20Hermax-purple)
![PySAT](https://img.shields.io/badge/PySAT-IDPool%20%2B%20CardEnc-orange)
![Status](https://img.shields.io/badge/Status-negative%20result-lightgrey)
![License](https://img.shields.io/badge/License-Apache%202.0-blue)

</div>

---

> **Status: negative result.**
> The approach is theoretically sound but **does not scale** to large instances, because the number of variables and clauses grows too quickly. The repository is public so that others can use it as a reference, avoid repeating this direction, and possibly build on it.

## Table of Contents

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [Method](#method)
   - [Variables](#variables)
   - [Constraints](#constraints)
   - [CEGAR Loop](#cegar-loop)
   - [Preprocessing](#preprocessing)
4. [Repository Structure](#repository-structure)
5. [Installation](#installation)
6. [Usage](#usage)
7. [Input & Data](#input--data)
8. [Results and Why It Does Not Scale](#results-and-why-it-does-not-scale)
9. [Future Work](#future-work)
10. [Authors](#authors)
11. [Citation](#citation)
12. [License](#license)

---

## Overview

This project tries to solve the **Multiple Depot Vehicle Scheduling Problem (MDVSP)** with a purely logical approach instead of the usual LP/MIP or column-generation methods:

| Component | File | Role |
|---|---|---|
| **Base MaxSAT model** | `xay_dung_mo_hinh.py` | Hard clauses for flow conservation and depot capacity, soft clauses for arc costs. |
| **Counterexample detection** | `kiem_dinh.py` | Decodes a solution, traces vehicle routes and finds routes that do not return to their depot, as well as subtours. |
| **Refinement** | `tinh_chinh.py` | Generates clauses that exclude the violating paths. |
| **Preprocessing** | `tien_xu_ly.py` | BFS reachability tables that remove arcs that cannot lie on a closed tour through any depot. |

The "return to the depot of origin" condition is deliberately **left out of the base model** and added lazily, which keeps the first model smaller but, as the results show, is not enough for large instances.

## The Problem

MDVSP with a single homogeneous vehicle type: trips with fixed timetables are assigned to vehicles stationed at several depots such that

- each trip is served exactly once;
- each vehicle leaves a depot and **must return to that same depot**;
- the number of vehicles leaving depot `d` does not exceed its capacity `r_d`;
- two consecutive trips of one vehicle are compatible in time and travel;
- the total cost of waiting and deadheading (pull-out, pull-in and trip-connection costs) is **minimised**.

Main references:

- Kulkarni, Krishnamoorthy, Ranade, Ernst, Patil (2018). *A new formulation and a column generation-based heuristic for the multiple depot vehicle scheduling problem.* Transportation Research Part B, 118, 457–487.
- Laurent, B. & Hao, J.-K. (2009). *Iterated local search for the multiple depot vehicle scheduling problem.* Computers & Industrial Engineering, 57, 277–286.

## Method

### Variables

Boolean variables are defined over the graph of valid arcs:

| Variable | Meaning |
|---|---|
| `s[i,j]` | trip `j` is run immediately after trip `i` on the same vehicle |
| `Pout[d,j]` | a vehicle leaves depot `d` to run trip `j` as its first trip |
| `Pin[i,d]` | a vehicle ends at trip `i` and then returns to depot `d` |

### Constraints

| Type | Constraint |
|---|---|
| **Hard** | **Inflow conservation:** each trip `j` has exactly one incoming arc (from another trip or from a depot). |
| **Hard** | **Outflow conservation:** each trip `i` has exactly one outgoing arc (to another trip or back to a depot). |
| **Hard** | **Depot capacity:** the number of `Pout` arcs, and of `Pin` arcs, of each depot is at most `r_d`. |
| **Soft** | Every selected arc is penalised by exactly its cost, so MaxSAT minimises the total cost. |

### CEGAR Loop

The base model does **not** enforce that a vehicle returns to its depot of origin. This condition is added incrementally:

```text
repeat (at most 100 iterations, 3600 s in total):
    solve the current MaxSAT model
    validate the solution                      # kiem_dinh.py
        trace every vehicle route
        look for routes with start depot ≠ end depot, and for subtours
    if no violation:                           # the solution is globally optimal
        stop
    else:
        add refinement clauses                 # tinh_chinh.py
            prefix / suffix pruning
            forbidding entire violating paths
            breaking subtours
```

The solver is kept alive between iterations (`hermax.incremental`, EvalMaxSAT), so clauses are added without rebuilding the model.

### Preprocessing

`tien_xu_ly.py` runs BFS to compute two tables, `reach_from[d]` and `reach_to[d]`. An arc that cannot belong to a closed tour through some depot is removed before the model is built.

## Repository Structure

```text
.
├── chay_chinh.py            # Entry point: read data → preprocess → build model → CEGAR
├── requirements.txt
├── ma_nguon/
│   ├── __init__.py
│   ├── doc_du_lieu.py       # Reads instance files (.inp)
│   ├── tien_xu_ly.py        # Graph preprocessing, reach_from / reach_to tables
│   ├── xay_dung_mo_hinh.py  # Builds the base MaxSAT model
│   ├── kiem_dinh.py         # Decodes solutions, traces routes, finds counterexamples
│   ├── tinh_chinh.py        # Generates refinement clauses
│   └── giai_mo_hinh.py      # Standalone trial solving code with timeout (not used by chay_chinh.py)
└── du_lieu/                 # Not included: create it and place the .inp instances here
```

> `chay_chinh.py` adds `ma_nguon/` to `sys.path` and reads `du_lieu/du_lieu_mau.inp`. Create the `du_lieu/` folder, put an instance in it and rename it to `du_lieu_mau.inp`, or change the path in `main()`.

## Installation

Requires **Python 3.9+**.

Libraries:

- [**Hermax**](https://hermax.readthedocs.io) — Python MaxSAT library; the `EvalMaxSAT` solver is used through `hermax.incremental`, which supports adding clauses inside the CEGAR loop.
- [**PySAT**](https://pysathq.github.io) — `IDPool` for variable management and `CardEnc` for cardinality constraints.

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Usage

```bash
python chay_chinh.py
```

Default parameters in `chay_chinh.py`:

| Parameter | Default |
|---|---|
| Maximum CEGAR iterations | 100 |
| Time limit | 3600 s |
| Instance | `du_lieu/du_lieu_mau.inp` |

## Input & Data

### Instance format (`.inp`)

Whitespace-separated numbers:

1. `m` (number of depots) and `n` (number of trips);
2. `m` numbers: the capacity `r_d` of each depot;
3. a cost matrix of size `(m + n) × (m + n)`, row by row. Indices `0 … m−1` are depots and `m … m+n−1` are trips. The value `-1` means there is no arc.

### Benchmark data

The test instances are **not included** in this repository. The standard MDVSP instances used by Pepin et al. (2008) and Laurent & Hao (2009) can be downloaded from <http://people.few.eur.nl/huisman/instances.htm>. Please check the terms of use on that page before redistributing them.

## Results and Why It Does Not Scale

| Instance size | Behaviour |
|---|---|
| **Small** (few depots, few trips) | Numbers of arcs, variables and clauses stay small; the MaxSAT solver copes, the CEGAR loop converges and optimal solutions are obtained. |
| **Large** | Numbers of variables and clauses **explode**; the solver finds no solution within the time limit, or the model is too large to build or solve. No results are produced. |

No benchmark table is reported here because the method yields no results on the large standard instances.

Main causes:

- **Quadratic arc growth.** The number of trip-connection arcs `E_compat` grows almost quadratically in the number of trips `n`. This inflates both the `s[i,j]` variables and the clauses of the cardinality encoding (sequential counter).
- **Many refinement rounds.** The "return to the same depot" condition is missing from the base model, so the CEGAR loop needs many iterations, and each iteration calls the MaxSAT solver again on an already very large model.
- **Problem structure.** MDVSP has a network-flow structure with an arithmetic objective, so LP/MIP combined with column generation (Kulkarni et al., 2018) is generally more effective than pure SAT at large scale.

## Future Work

- Fewer variables: stronger arc filtering, symmetry breaking, and a more compact time-space model (see the inventory formulation of Kulkarni et al.).
- More compact encodings of the cardinality constraints.
- Combining SAT with LP: use SAT to initialise columns for column generation, or use Logic-Based Benders Decomposition.
- Use heuristic solutions (for example iterated local search) as an initial upper bound for MaxSAT.

## Authors

| Contributor | Role |
|---|---|
| **Nguyễn Kim Trung Đức** | SAT model and method idea |
| **Bùi Thế Dũng** | Code implementation and experiments |

## Citation

If you reuse this work, please cite Hermax:

```bibtex
@InProceedings{salviahornos_et_al:LIPIcs.SAT.2026.41,
  author    = {Salvia Hornos, Josep Maria and Fern\'{a}ndez Cam\'{o}n, C\`{e}sar and Mateu Pi\~{n}ol, Carles},
  title     = {{Hermax: A Unified MaxSAT Library}},
  booktitle = {29th International Conference on Theory and Applications of Satisfiability Testing (SAT 2026)},
  year      = {2026},
  doi       = {10.4230/LIPIcs.SAT.2026.41}
}
```

Please also cite the paper of the backend solver you use (see the Hermax documentation).

## License

Copyright 2026 Bùi Thế Dũng. Released under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

The benchmark instances are not part of this repository and remain subject to their original terms.
