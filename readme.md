# SAT/MaxSAT Encoding for the Multiple Depot Vehicle Scheduling Problem (MDVSP)

> **Status: negative result.**
> The approach is theoretically sound but **does not scale** to large instances, because the number of variables and clauses grows too quickly. This repository is made public so that others can use it as a reference, avoid repeating this direction, and possibly build on it.

## Table of Contents

1. [Problem](#1-problem)
2. [Approach](#2-approach)
3. [Directory Structure](#3-directory-structure)
4. [Installation and Usage](#4-installation-and-usage)
5. [Results and Why It Does Not Scale](#5-results-and-why-it-does-not-scale)
6. [Future Work](#6-future-work)
7. [Contributions](#7-contributions)
8. [Citation](#8-citation)
9. [License](#9-license)

## 1. Problem

The **Multiple Depot Vehicle Scheduling Problem (MDVSP)** with a single homogeneous vehicle type: assign trips with fixed timetables to vehicles stationed at multiple depots such that:

- Each trip is served exactly once.
- Each vehicle departs from a depot and **must return to that same depot**.
- The number of vehicles departing from depot `d` does not exceed `r_d`.
- Two consecutive trips on the same vehicle must be compatible in terms of time and travel.
- The total cost of waiting and deadheading (including pull-out, pull-in, and trip-connection costs) is **minimized**.

Main references:

- Kulkarni, Krishnamoorthy, Ranade, Ernst, Patil (2018). *A new formulation and a column generation-based heuristic for the multiple depot vehicle scheduling problem.* Transportation Research Part B, 118, 457–487.
- Laurent, B. & Hao, J.-K. (2009). *Iterated local search for the multiple depot vehicle scheduling problem.* Computers & Industrial Engineering, 57, 277–286.

## 2. Approach

Instead of using LP/MIP or column generation as in the papers above, this project attempts to **encode the problem as MaxSAT** and solve it with a **CEGAR** (Counter-Example Guided Abstraction Refinement) loop.

### SAT Model

Boolean variables (defined over the graph of valid arcs):

| Variable | Meaning |
|---|---|
| `s_{i,j}` | Trip `j` is run immediately after trip `i` on the same vehicle |
| `Pout_{d,j}` | A vehicle leaves depot `d` to run trip `j` as its first trip |
| `Pin_{i,d}` | A vehicle ends at trip `i` and then returns to depot `d` |

Hard clauses:

- **Inflow conservation:** each trip `j` has exactly one incoming arc (from another trip or from a depot).
- **Outflow conservation:** each trip `i` has exactly one outgoing arc (to another trip or back to a depot).
- **Depot capacity:** the number of `Pout` arcs (and `Pin` arcs) of each depot does not exceed `r_d`.

Soft clauses: each selected arc is penalized by exactly its cost, so MaxSAT minimizes the total cost.

### CEGAR Loop

The base model does **not** enforce the condition "a vehicle returns to its depot of origin". This condition is added incrementally:

1. Solve the current MaxSAT model.
2. **Validate the solution** (`kiem_dinh.py`): trace each vehicle route, and find routes with `d_start != d_end` as well as subtours.
3. If there are no violations: the solution is globally optimal; stop.
4. Otherwise: generate **refinement clauses** (`tinh_chinh.py`) that exclude the violating paths (prefix/suffix pruning, forbidding entire paths, breaking subtours), add them to the solver, and return to step 1.

**Preprocessing** (`tien_xu_ly.py`): BFS is used to compute two tables, `reach_from[d]` and `reach_to[d]`, to eliminate early any arcs that cannot belong to a closed tour through some depot.

## 3. Directory Structure

```
.
├── chay_chinh.py            # Entry point: read data -> preprocess -> build model -> CEGAR
├── requirements.txt
├── ma_nguon/
│   ├── __init__.py
│   ├── doc_du_lieu.py       # Reads instance files (.inp)
│   ├── tien_xu_ly.py        # Graph preprocessing, reach_from / reach_to tables
│   ├── xay_dung_mo_hinh.py  # Builds the base MaxSAT model
│   ├── kiem_dinh.py         # Decodes solutions, traces routes, finds counterexamples
│   ├── tinh_chinh.py        # Generates refinement clauses
│   └── giai_mo_hinh.py      # Standalone trial solving code with timeout (not used in chay_chinh.py)
└── du_lieu/                 # (not included in the repo) create it yourself and place .inp instance files here
```

> `chay_chinh.py` adds the `ma_nguon/` directory to `sys.path` and reads data from `du_lieu/du_lieu_mau.inp`. Create the `du_lieu/` directory yourself, place an instance file in it and rename it to `du_lieu_mau.inp`, or modify the path in `main()`.

## 4. Installation and Usage

Requirements: Python 3.9+.

Libraries used:

- [**Hermax**](https://hermax.readthedocs.io): a Python library for MaxSAT, using the `EvalMaxSAT` solver via `hermax.incremental` (which supports adding clauses incrementally within the CEGAR loop).
- [**PySAT**](https://pysathq.github.io): `IDPool` is used for variable management and `CardEnc` for encoding cardinality constraints.

```bash
pip install -r requirements.txt
```

Run:

```bash
python chay_chinh.py
```

Default parameters in `chay_chinh.py`: a maximum of **100 CEGAR iterations** and a **3600-second** time limit.

### Input File Format (`.inp`)

The file consists of whitespace-separated numbers:

1. `m` (number of depots), `n` (number of trips).
2. `m` numbers: the number of vehicles `r_d` for each depot.
3. A cost matrix of size `(m + n) x (m + n)`, read row by row. Indices `0..m-1` are depots and `m..m+n-1` are trips. A value of `-1` means there is no arc.

### Data

The test datasets are **not included in the repo**. The standard MDVSP instances used in Pepin et al. (2008) and Laurent & Hao (2009) can be downloaded at <http://people.few.eur.nl/huisman/instances.htm>.

## 5. Results and Why It Does Not Scale

- **Small graphs:** for instances with few depots and few trips, the numbers of arcs, variables, and clauses remain small, so the MaxSAT solver can handle them, the CEGAR loop converges, and optimal solutions are obtained.
- **Larger graphs:** the numbers of variables and clauses **explode**; the solver cannot find a solution within the allotted time (or the model is too large to build or solve). The method produces no results for large instances.

Main causes:

- The number of trip-connection arcs `E_compat` grows nearly quadratically with the number of trips `n`, which causes the number of `s_{i,j}` variables and the number of clauses encoding cardinality constraints (sequential counter) to grow very quickly.
- The CEGAR loop needs many refinement iterations because the "return to the same depot" constraint is absent from the base model; each iteration calls the MaxSAT solver again on an already very large model.
- The problem has a network-flow structure with an arithmetic objective, so LP/MIP combined with column generation (Kulkarni et al., 2018) is generally more effective than pure SAT at large scale.

## 6. Future Work

- Reduce the number of variables: stronger arc filtering, symmetry breaking, and a more compact time-space model (see the inventory formulation of Kulkarni et al.).
- More compact encodings for cardinality constraints.
- Combine SAT with LP: use SAT to initialize columns for column generation, or use Logic-based Benders Decomposition.
- Use heuristic solutions (e.g., ILS) as an initial upper bound for MaxSAT.

## 7. Contributions

- **SAT model and method idea:** Nguyễn Kim Trung Đức.
- **Code implementation and experiments:** Bùi Thế Dũng.

## 8. Citation

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

## 9. License

Copyright 2026 Bùi Thế Dũng. This project is released under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
