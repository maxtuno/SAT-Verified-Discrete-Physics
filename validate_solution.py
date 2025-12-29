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
Valida soluciones para:
  - Instancias GCNF (igualdades multivaluadas) con asignaciones var=val.
  - Instancias CNF resultantes de gcnf_to_cnf, con modelo booleano y archivo de mapeo.

Formatos soportados:
1) Asignacion GCNF directa (--gcnf --assign):
   Archivo de asignacion con lineas "x=v" o "x v" (enteros).
2) Asignacion CNF booleano (--cnf --map --bool-model):
   - --cnf: archivo DIMACS
   - --map: archivo generado por gcnf_to_cnf (vid -> (var,val))
   - --bool-model: archivo con modelo SAT (lista de enteros como salida de minisat/cadical; se aceptan lineas que empiezan con 'v' o 's', termina en 0 opcional).

Ejemplos:
  python validate_solution.py --gcnf test.gcnf --assign model.txt
  python validate_solution.py --cnf out.cnf --map out.map --bool-model sat.sol --gcnf test.gcnf
"""

from __future__ import annotations
import argparse
import ast
import re
from typing import Dict, List, Tuple, Optional

Literal = Tuple[int, int]          # (var, val)
GCNFClause = List[Literal]


# ----------------- Parsing helpers -----------------
def parse_gcnf(path: str) -> Tuple[List[GCNFClause], int, int]:
    clauses: List[GCNFClause] = []
    max_var = 0
    max_val = -1
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = ast.literal_eval(s)
            except Exception as e:
                raise ValueError(f"GCNF parse error line {lineno}: {e}")
            if not isinstance(obj, list):
                raise ValueError(f"GCNF line {lineno}: expected list")
            clause: GCNFClause = []
            for item in obj:
                if not (isinstance(item, tuple) and len(item) == 2 and all(isinstance(x, int) for x in item)):
                    raise ValueError(f"GCNF line {lineno}: bad literal {item!r}")
                var, val = item
                if var < 1 or val < 0:
                    raise ValueError(f"GCNF line {lineno}: var>=1, val>=0 required, got {item}")
                clause.append((var, val))
                max_var = max(max_var, var)
                max_val = max(max_val, val)
            clauses.append(clause)
    if max_var == 0:
        raise ValueError("Empty GCNF instance")
    return clauses, max_var, max_val + 1


def parse_assignment(path: str) -> Dict[int, int]:
    """Parse file with lines 'x=v', 'x v', or a single line with many 'x=y' tokens into dict var->val."""
    assign: Dict[int, int] = {}
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            tokens = s.split()
            if len(tokens) == 1:
                tokens = [s]  # might be single x=v
            for tok in tokens:
                if "=" in tok:
                    parts = tok.split("=", 1)
                else:
                    parts = tok.split()
                if len(parts) != 2:
                    raise ValueError(f"Assign parse error line {lineno}: {s!r}")
                try:
                    var = int(parts[0])
                    val = int(parts[1])
                except Exception:
                    raise ValueError(f"Assign parse error line {lineno}: {s!r}")
                assign[var] = val
    return assign


def parse_tuple_solution(path: str) -> Dict[int, int]:
    """
    Parse file containing a Python literal list of (var, val), e.g.:
      [(1, 0), (2, 3), ...]
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        raise ValueError("Empty solution file")
    try:
        obj = ast.literal_eval(content)
    except Exception as e:
        raise ValueError(f"Solution parse error: {e}") from e
    if not isinstance(obj, list):
        raise ValueError("Solution must be a list of tuples")
    assign: Dict[int, int] = {}
    for item in obj:
        if not (isinstance(item, tuple) and len(item) == 2 and all(isinstance(x, int) for x in item)):
            raise ValueError(f"Bad item in solution: {item!r}, expected (int,int)")
        var, val = item
        assign[var] = val
    return assign


def parse_dimacs_cnf(path: str) -> Tuple[List[List[int]], int]:
    clauses: List[List[int]] = []
    num_vars = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("c"):
                continue
            if line.startswith("p"):
                parts = line.split()
                if len(parts) >= 4:
                    num_vars = int(parts[2])
                continue
            lits = [int(x) for x in line.split() if x != "0"]
            if lits:
                clauses.append(lits)
    return clauses, num_vars


def parse_map(path: str) -> Dict[int, Tuple[int, int]]:
    """Parse mapping file produced by gcnf_to_cnf: vid\t(var,val)"""
    mp: Dict[int, Tuple[int, int]] = {}
    pat = re.compile(r"\((\d+),\s*(\d+)\)")
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            try:
                vid = int(parts[0])
            except Exception:
                raise ValueError(f"Map parse error line {lineno}: {line!r}")
            m = pat.search(line)
            if not m:
                raise ValueError(f"Map parse error line {lineno}: {line!r}")
            var = int(m.group(1))
            val = int(m.group(2))
            mp[vid] = (var, val)
    return mp


def parse_bool_model(path: str) -> Dict[int, bool]:
    """Parse solver model: integers separated by spaces/newlines; ignore c/s/v prefixes; stop at 0 if present."""
    model: Dict[int, bool] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(("c", "s")):
                continue
            if line.startswith("v"):
                line = line[1:].strip()
            for tok in line.split():
                if tok == "0":
                    break
                lit = int(tok)
                var = abs(lit)
                model[var] = lit > 0
    return model


# ----------------- Checkers -----------------
def check_gcnf(clauses: List[GCNFClause], assign: Dict[int, int]) -> Tuple[bool, List[int]]:
    """Return (ok, unsat_clause_indices)."""
    unsat = []
    for idx, clause in enumerate(clauses):
        sat = False
        for var, val in clause:
            a = assign.get(var, None)
            if a is None:
                continue
            if a == val:
                sat = True
                break
        if not sat:
            unsat.append(idx)
    return len(unsat) == 0, unsat


def check_cnf(cnf: List[List[int]], model: Dict[int, bool]) -> Tuple[bool, List[int]]:
    unsat = []
    for idx, clause in enumerate(cnf):
        sat = False
        for lit in clause:
            val = model.get(abs(lit), False)
            if (lit > 0 and val) or (lit < 0 and not val):
                sat = True
                break
        if not sat:
            unsat.append(idx)
    return len(unsat) == 0, unsat


def decode_model_to_assign(model: Dict[int, bool], mapping: Dict[int, Tuple[int, int]]) -> Dict[int, int]:
    """Given boolean model and mapping vid->(var,val), return assign[var]=val (last true wins)."""
    assign: Dict[int, int] = {}
    for vid, (var, val) in mapping.items():
        if model.get(vid, False):
            assign[var] = val
    return assign


def main() -> None:
    ap = argparse.ArgumentParser(description="Valida soluciones para GCNF o CNF (reducido).")
    ap.add_argument("--gcnf", help="Archivo .gcnf para validar directamente o como referencia del CNF.")
    ap.add_argument("--assign", help="Archivo de asignacion var=val para validar GCNF.")
    ap.add_argument("--sol", help="Archivo con lista de tuplas [(var,val), ...] como salida de hess_gsp.")
    ap.add_argument("--cnf", help="Archivo DIMACS CNF (salida de gcnf_to_cnf).")
    ap.add_argument("--map", dest="map_path", help="Archivo de mapeo vid->(var,val).")
    ap.add_argument("--bool-model", help="Modelo booleano (salida SAT solver).")
    args = ap.parse_args()

    if args.gcnf and (args.assign or args.sol):
        gclauses, n, b = parse_gcnf(args.gcnf)
        if args.assign:
            assign = parse_assignment(args.assign)
        else:
            assign = parse_tuple_solution(args.sol)
        ok, bad = check_gcnf(gclauses, assign)
        if ok:
            print("GCNF: SAT con asignacion dada")
        else:
            print(f"GCNF: NO satisface; clausulas insatisfechas: {bad}")
        return

    if args.bool_model and args.cnf and args.map_path:
        cnf, _ = parse_dimacs_cnf(args.cnf)
        model = parse_bool_model(args.bool_model)
        ok_cnf, bad_cnf = check_cnf(cnf, model)
        mapping = parse_map(args.map_path)
        assign = decode_model_to_assign(model, mapping)
        print(f"CNF: {'SAT' if ok_cnf else 'NO SAT'}, clausulas malas: {bad_cnf}")
        if args.gcnf:
            gclauses, n, b = parse_gcnf(args.gcnf)
            ok_g, bad_g = check_gcnf(gclauses, assign)
            print(f"GCNF (decodificado): {'SAT' if ok_g else 'NO SAT'}, clausulas malas: {bad_g}")
        else:
            print("Asignacion decodificada (var=val):")
            for var in sorted(assign):
                print(f"{var}={assign[var]}")
        return

    ap.error("Usa --gcnf --assign o --gcnf --sol para validar GCNF, o --cnf --map --bool-model (y opcional --gcnf) para validar CNF.")


if __name__ == "__main__":
    main()
