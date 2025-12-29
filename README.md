# Abstract

We present a **methods paper**: a small, auditable workflow that compiles **finite discrete physics constraints** into **SAT** instances with mechanically checkable witnesses. The goal is *not* a continuum unification claim, but a reproducible way to (i) **verify** the satisfiability of discrete model constraints, or (ii) **refute** them (UNSAT) within explicit finite regimes.

Two families of fully checkable examples are provided:

1. **Combinatorial 2D gravity (equilateral)**: we encode the *existence* of a closed simplicial 2‑complex via triangle‑incidence variables, enforce vertex valence constraints, and validate the discrete Gauss–Bonnet curvature sum. We include both SAT (octahedral sphere) and UNSAT (attempted “flat sphere”) instances.
2. **Boolean locality dynamics (finite‑speed influence)**: a discrete‑time influence propagation model on graphs that yields an exact light‑cone constraint (a Boolean analogue of Lieb–Robinson locality). We provide SAT/UNSAT reachability instances parameterized by graph size and time horizon.

We report clause/variable growth under a one‑hot reduction and include baseline solve times using a reference Python CDCL prototype, while emphasizing that the primary deliverable is the **auditable encoding + validator**, compatible with industrial SAT solvers.

---

# Contributions

This paper contributes a reproducible SAT-based verification workflow for small but exact instances of discrete physics models. Concretely:

Method: SAT/MaxSAT as bounded verification for discrete physics.
We formalize “existence / non-existence” questions for finite discrete models as SAT/MaxSAT problems, so that claims of the form “there exists a configuration satisfying constraints X” become SAT with an auditable witness, and “no such configuration exists” becomes UNSAT.

A minimal intermediate specification format (GCNF) and an auditable toolchain.
We introduce and use a compact “generalized CNF” representation to express arithmetic/equality constraints over finite domains, together with a toolchain that cleanly separates:
(i) human-readable constraint specification,
(ii) mechanical compilation to CNF, and
(iii) independent witness validation.
This structure improves reproducibility and reduces ambiguity in discrete-model experiments.

Encoding patterns for geometric and operational constraints.
We provide explicit constraint templates for (a) combinatorial/Regge-inspired discrete curvature constraints and (b) locality / finite-horizon constraints inspired by Lieb–Robinson-type reasoning. The goal is not a new physical theory, but a reusable encoding methodology.

Non-trivial toy instances including both SAT and UNSAT cases.
Beyond trivial satisfiable examples, we include deliberately inconsistent constraint sets that produce UNSAT certificates, demonstrating how the workflow can refute discrete hypotheses in bounded regimes, not merely find solutions.

Explicit cost model and evaluation metrics.
We analyze the growth of variables/clauses induced by standard finite-domain encodings (e.g., one-hot/pairwise) and propose simple, measurable metrics (instance size, palette size, clause counts, solve time, and invariant error where applicable) to support objective comparisons across instance families and encodings.

---

# Polímata Research Project

## Project Nature

This project is distributed under a **dual licensing model** designed to
balance:

- Open research and collaboration.
- Author protection.
- Explicit and controlled commercial use.

---

## Licensing Model

You may use this **Research Document** under **ONE** of the following options:

### 🔓 Option A — Open License (Non-Commercial)

- License: **AGPL-3.0**
- Permitted use:
  - Personal, educational, academic, and research purposes.
- Obligations:
  - Publish any modifications or derivatives.
  - Maintain the same license.
  - Share the full modified Research Document,
    including when used in hosted or online platforms.
- ❌ Commercial use is not permitted.

### 💼 Option B — Commercial License

- Required for any for-profit or monetized use.
- Permits:
  - Proprietary or confidential use.
  - Commercial platforms and services.
  - Internal corporate or institutional deployment.
- Requires an explicit agreement with the author.

See full details in:
- `LICENSE`
- `COMMERCIAL.md`

---

## Scope and Control

This project is **NOT public domain**.
The author retains all rights not explicitly granted.

Any violation of the license terms automatically terminates usage rights.

---

## Author

Oscar Riveros  
Polímata  
Chile  

---

## Legal Notice

This README is informational only.
Legally binding terms are defined exclusively in the `LICENSE` file.

---

For commercial licensing, see `COMMERCIAL.md`.






