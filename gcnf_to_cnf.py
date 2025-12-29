#!/usr/bin/env python3
'''
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

'''

"""
gcnf_to_cnf.py

Reduce GCNF (multivalued CNF with equality literals (x=v)) to boolean CNF in DIMACS.

GCNF input format (your project):
- Text file
- One clause per line
- Each line is a Python literal like: [(27, 4), (89, 4), (94, 1)]
  meaning (x=27, v=4) OR (x=89, v=4) OR (x=94, v=1)

Reduction (standard one-hot):
- Introduce boolean var p[x,v] meaning "x == v"
- Each GCNF clause becomes a CNF clause over p[x,v]
- Add exactly-one constraints for each x:
    (at least one)  p[x,0] v p[x,1] v ... v p[x,b-1]
    (at most one)   for all i<j:  ¬p[x,i] v ¬p[x,j]

Outputs:
- DIMACS CNF file
- Optional mapping file to decode solutions back to (x,v)

Usage:
  python3 gcnf_to_cnf.py input.gcnf output.cnf --map output.map

Notes:
- This is the "direct" reduction. It often blows up clauses by O(n*b^2),
  which is useful if you want to measure how much your GCNF "compresses".
"""

from __future__ import annotations
import ast
import argparse
from dataclasses import dataclass
from typing import List, Tuple, Dict, Iterable, Optional


Literal = Tuple[int, int]          # (var, val) with var>=1, val>=0
GCNFClause = List[Literal]         # OR of equality literals
CNFClause = List[int]              # DIMACS ints, negative for negated boolean var


@dataclass
class GCNFInstance:
    clauses: List[GCNFClause]
    n: int
    b: int


def parse_gcnf(path: str) -> GCNFInstance:
    clauses: List[GCNFClause] = []
    max_var = 0
    max_val = -1

    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = ast.literal_eval(s)  # SAFE parsing (no eval)
            except Exception as e:
                raise ValueError(f"Parse error at line {lineno}: {e}\nLine: {s}") from e

            if not isinstance(obj, list):
                raise ValueError(f"Line {lineno}: expected a list, got {type(obj)}")

            clause: GCNFClause = []
            for item in obj:
                if (
                    not isinstance(item, tuple)
                    or len(item) != 2
                    or not isinstance(item[0], int)
                    or not isinstance(item[1], int)
                ):
                    raise ValueError(f"Line {lineno}: bad literal {item!r}, expected (int,int)")
                var, val = item
                if var < 1:
                    raise ValueError(f"Line {lineno}: var must be >=1, got {var}")
                if val < 0:
                    raise ValueError(f"Line {lineno}: val must be >=0, got {val}")
                clause.append((var, val))
                max_var = max(max_var, var)
                max_val = max(max_val, val)

            # Optional: drop duplicates inside a clause (safe, doesn't change semantics)
            # but keep order stable
            if clause:
                seen = set()
                uniq: GCNFClause = []
                for lit in clause:
                    if lit not in seen:
                        uniq.append(lit)
                        seen.add(lit)
                clause = uniq

            clauses.append(clause)

    if max_var == 0:
        raise ValueError("No clauses/literals found; empty file?")

    n = max_var
    b = max_val + 1
    return GCNFInstance(clauses=clauses, n=n, b=b)


def bool_var_id(var: int, val: int, b: int) -> int:
    """Map (var in 1..n, val in 0..b-1) -> DIMACS variable id in 1..n*b"""
    return (var - 1) * b + val + 1


def gcnf_to_cnf(inst: GCNFInstance) -> List[CNFClause]:
    n, b = inst.n, inst.b
    cnf: List[CNFClause] = []

    # 1) Convert each GCNF clause directly:
    #    [(x,v),(y,w),...]  ->  [p(x,v), p(y,w), ...]
    for clause in inst.clauses:
        cnf_clause: CNFClause = []
        for (var, val) in clause:
            if val >= b:
                raise ValueError(f"Value {val} out of inferred domain 0..{b-1}")
            cnf_clause.append(bool_var_id(var, val, b))
        cnf.append(cnf_clause)

    # 2) Exactly-one constraints per variable x:
    for var in range(1, n + 1):
        # at least one
        cnf.append([bool_var_id(var, val, b) for val in range(b)])

        # at most one (pairwise)
        # ¬p[var,i] v ¬p[var,j] for i<j
        for i in range(b):
            vi = bool_var_id(var, i, b)
            for j in range(i + 1, b):
                vj = bool_var_id(var, j, b)
                cnf.append([-vi, -vj])

    return cnf


def write_dimacs_cnf(path: str, cnf: List[CNFClause], num_vars: int) -> None:
    num_clauses = len(cnf)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"p cnf {num_vars} {num_clauses}\n")
        for cl in cnf:
            # DIMACS: literals + trailing 0
            f.write(" ".join(str(l) for l in cl) + " 0\n")


def write_mapping(path: str, n: int, b: int) -> None:
    """
    Writes a simple mapping file:
      dimacs_var_id -> (var,val)
    Useful to decode SAT solver outputs.
    """
    with open(path, "w", encoding="utf-8") as f:
        for var in range(1, n + 1):
            for val in range(b):
                vid = bool_var_id(var, val, b)
                f.write(f"{vid}\t({var},{val})\n")


def stats(inst: GCNFInstance, cnf: List[CNFClause]) -> Dict[str, int]:
    n, b = inst.n, inst.b
    gcnf_clauses = len(inst.clauses)
    gcnf_lits = sum(len(c) for c in inst.clauses)

    cnf_clauses = len(cnf)
    cnf_lits = sum(len(c) for c in cnf)

    # Breakdown for exactly-one:
    # at-least-one: n clauses of size b
    # at-most-one pairwise: n * C(b,2) clauses of size 2
    at_least = n
    at_most = n * (b * (b - 1) // 2)

    return {
        "n": n,
        "b": b,
        "gcnf_clauses": gcnf_clauses,
        "gcnf_literals_total": gcnf_lits,
        "cnf_vars": n * b,
        "cnf_clauses_total": cnf_clauses,
        "cnf_literals_total": cnf_lits,
        "exactly_one_at_least_clauses": at_least,
        "exactly_one_at_most_pairwise_clauses": at_most,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Reduce GCNF (multivalued equality-CNF) to boolean DIMACS CNF")
    ap.add_argument("input_gcnf", help="Input .gcnf path")
    ap.add_argument("output_cnf", help="Output DIMACS .cnf path")
    ap.add_argument("--map", dest="map_path", default=None, help="Optional mapping output path")
    args = ap.parse_args()

    inst = parse_gcnf(args.input_gcnf)
    cnf = gcnf_to_cnf(inst)

    num_vars = inst.n * inst.b
    write_dimacs_cnf(args.output_cnf, cnf, num_vars)

    if args.map_path:
        write_mapping(args.map_path, inst.n, inst.b)

    s = stats(inst, cnf)
    print("=== GCNF -> CNF stats ===")
    for k in [
        "n", "b",
        "gcnf_clauses", "gcnf_literals_total",
        "cnf_vars",
        "cnf_clauses_total", "cnf_literals_total",
        "exactly_one_at_least_clauses", "exactly_one_at_most_pairwise_clauses",
    ]:
        print(f"{k}: {s[k]}")

    # Simple "compression" indicators (higher means GCNF is more compact than CNF)
    # Note: these are crude, but useful for your purpose.
    g_size = s["gcnf_clauses"] + s["gcnf_literals_total"]
    c_size = s["cnf_clauses_total"] + s["cnf_literals_total"]
    print(f"rough_size_gcnf (clauses+lits): {g_size}")
    print(f"rough_size_cnf  (clauses+lits): {c_size}")
    if g_size > 0:
        print(f"blowup_factor (cnf/gcnf): {c_size / g_size:.3f}")


if __name__ == "__main__":
    main()
