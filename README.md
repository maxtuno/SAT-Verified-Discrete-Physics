We present a **methods paper**: a small, auditable workflow that compiles **finite discrete physics constraints** into **SAT** instances with mechanically checkable witnesses. The goal is *not* a continuum unification claim, but a reproducible way to (i) **verify** the satisfiability of discrete model constraints, or (ii) **refute** them (UNSAT) within explicit finite regimes.

Two families of fully checkable examples are provided:

1. **Combinatorial 2D gravity (equilateral)**: we encode the *existence* of a closed simplicial 2‑complex via triangle‑incidence variables, enforce vertex valence constraints, and validate the discrete Gauss–Bonnet curvature sum. We include both SAT (octahedral sphere) and UNSAT (attempted “flat sphere”) instances.
2. **Boolean locality dynamics (finite‑speed influence)**: a discrete‑time influence propagation model on graphs that yields an exact light‑cone constraint (a Boolean analogue of Lieb–Robinson locality). We provide SAT/UNSAT reachability instances parameterized by graph size and time horizon.

We report clause/variable growth under a one‑hot reduction and include baseline solve times using a reference Python CDCL prototype, while emphasizing that the primary deliverable is the **auditable encoding + validator**, compatible with industrial SAT solvers.

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





