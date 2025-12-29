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

import ast
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

Literal = Tuple[int, int]
Clause = List[Literal]

UNASSIGNED = -1

def load_gcnf(path: str) -> List[Clause]:
    clauses: List[Clause] = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                clauses.append(ast.literal_eval(line))
    return clauses

def infer_dimensions(clauses: List[Clause]) -> Tuple[int, int]:
    n = max(x for c in clauses for (x, _) in c)
    b = max(v for c in clauses for (_, v) in c) + 1
    return n, b

def write_solution(path: str, sat: List[int]) -> None:
    seq = list(range(1, len(sat) + 1))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(repr(list(zip(seq, sat))) + '\n')

def _init_stats() -> Dict[str, float]:
    return {
        'decisions': 0,
        'propagations': 0,
        'conflicts': 0,
        'clauses': 0,
    }

def _normalize_clause(clause: Clause) -> Clause:
    seen = set()
    out: Clause = []
    for lit in clause:
        if lit not in seen:
            out.append(lit)
            seen.add(lit)
    return out


def solve_cdcl(
    clauses: List[Clause],
    n: int,
    b: int,
    root_assignments: Optional[Dict[int, int]] = None,
    preferred_values: Optional[List[int]] = None,
    *,
    stop_after_conflicts: int = 0,
) -> Tuple[str, Optional[List[int]], Dict[str, float]]:
    if stop_after_conflicts < 0:
        stop_after_conflicts = 0

    assign_val = [UNASSIGNED] * (n + 1)
    level = [UNASSIGNED] * (n + 1)
    reason = [UNASSIGNED] * (n + 1)
    trail: List[int] = []
    trail_lim: List[int] = []
    pending_conflict_cid = UNASSIGNED
    stats = _init_stats()
    stats['clauses'] = len(clauses)
    # Root assignments come from HESS (or external) and are treated as level-0 facts.
    root_assignments = dict(root_assignments or {})
    for var, val in root_assignments.items():
        if not (1 <= int(var) <= n):
            raise ValueError('root_assignments has invalid var index')
        if not (0 <= int(val) < b):
            raise ValueError('root_assignments has value outside domain')

    # Preferred values (warm-start) from HESS: used as deterministic value ordering for decisions.
    # preferred_values is indexed 1..n (preferred_values[0] unused). If None, default ordering 0..b-1.
    if preferred_values is not None:
        if len(preferred_values) != n + 1:
            raise ValueError('preferred_values must have length n+1 (index 1..n)')
        for i in range(1, n + 1):
            pv = int(preferred_values[i])
            if pv < 0 or pv >= b:
                raise ValueError('preferred_values has value outside domain')
  
    def current_level() -> int:
        return len(trail_lim)

    def enqueue(var: int, val: int, reason_cid: int) -> bool:
        if assign_val[var] != UNASSIGNED:
            return assign_val[var] == val
        assign_val[var] = val
        level[var] = current_level()
        reason[var] = reason_cid
        trail.append(var)
        return True

    def apply_root_assignments() -> Optional[int]:
        # Inject HESS-provided assignments as level-0 facts (never undone).
        if not root_assignments:
            return None
        # Ensure trail has the root vars first; if resuming, they should already be present.
        for var, val in sorted(root_assignments.items()):
            if assign_val[var] == UNASSIGNED:
                assign_val[var] = val
                level[var] = 0
                reason[var] = UNASSIGNED
                trail.append(var)
            elif assign_val[var] != val:
                return 0  # signal immediate contradiction at level 0
        return None

    def propagate() -> Optional[int]:
        while True:
            progressed = False
            for cid, clause in enumerate(clauses):
                satisfied = False
                unassigned = 0
                last_unassigned: Optional[Literal] = None
                for (x, v) in clause:
                    a = assign_val[x]
                    if a == UNASSIGNED:
                        unassigned += 1
                        if unassigned == 1:
                            last_unassigned = (x, v)
                    elif a == v:
                        satisfied = True
                        break
                if satisfied:
                    continue
                if unassigned == 0:
                    return cid
                if unassigned == 1 and last_unassigned is not None:
                    var, val = last_unassigned
                    if not enqueue(var, val, cid):
                        return cid
                    stats['propagations'] += 1
                    progressed = True
            if not progressed:
                return None

    def analyze(conflict_cid: int) -> Tuple[Clause, int]:
        nogood: Dict[int, int] = {}
        for (x, _) in clauses[conflict_cid]:
            val = assign_val[x]
            if val != UNASSIGNED:
                nogood[x] = val

        cur_level = current_level()
        while True:
            count = sum(1 for var in nogood if level[var] == cur_level)
            if count <= 1:
                break
            resolve_var = None
            for var in reversed(trail):
                if var in nogood and level[var] == cur_level:
                    resolve_var = var
                    break
            if resolve_var is None:
                break
            reason_cid = reason[resolve_var]
            if reason_cid == UNASSIGNED:
                break
            del nogood[resolve_var]
            for (y, _) in clauses[reason_cid]:
                if y == resolve_var:
                    continue
                val_y = assign_val[y]
                if val_y != UNASSIGNED:
                    nogood[y] = val_y

        learned: Clause = []
        for var in sorted(nogood):
            val = nogood[var]
            for v in range(b):
                if v != val:
                    learned.append((var, v))
        learned = _normalize_clause(learned)

        backjump = 0
        for var in nogood:
            lvl = level[var]
            if lvl != cur_level and lvl > backjump:
                backjump = lvl
        return learned, backjump

    def backtrack(to_level: int) -> None:
        if to_level <= 0:
            # Never undo root (level-0) assignments (e.g., from HESS).
            for var in reversed(trail):
                if level[var] != 0:
                    assign_val[var] = UNASSIGNED
                    level[var] = UNASSIGNED
                    reason[var] = UNASSIGNED
            trail[:] = [var for var in trail if level[var] == 0]
            trail_lim.clear()
            return
        target = trail_lim[to_level - 1]
        for i in range(len(trail) - 1, target - 1, -1):
            var = trail[i]
            assign_val[var] = UNASSIGNED
            level[var] = UNASSIGNED
            reason[var] = UNASSIGNED
        del trail[target:]
        del trail_lim[to_level:]

    def value_conflicts(var: int, val: int) -> bool:
        for clause in clauses:
            conflict = True
            for (x, v) in clause:
                a = assign_val[x]
                if x == var:
                    a = val
                if a == UNASSIGNED or a == v:
                    conflict = False
                    break
            if conflict:
                return True
        return False

    # Apply root assignments once before any propagation/decisions.
    ra_conflict = apply_root_assignments()
    if ra_conflict is not None:
        # Immediate contradiction among root facts.
        return 'UNSAT', None, stats

    if stop_after_conflicts > 0 and stats['conflicts'] >= stop_after_conflicts:
        return 'UNKNOWN', None, stats

    if n == 0:
        return 'SAT', [], stats

    while True:
        if pending_conflict_cid != UNASSIGNED:
            conflict_cid = pending_conflict_cid
            pending_conflict_cid = UNASSIGNED
        else:
            conflict_cid = propagate()
            if conflict_cid is not None:
                stats['conflicts'] += 1
                pending_conflict_cid = conflict_cid
                conflict_cid = pending_conflict_cid
                pending_conflict_cid = UNASSIGNED

        if conflict_cid is not None:
            if current_level() == 0:
                return 'UNSAT', None, stats
            learned, backjump = analyze(conflict_cid)
            if not learned:
                return 'UNSAT', None, stats
            clauses.append(learned)
            stats['clauses'] += 1
            backtrack(backjump)
            if stop_after_conflicts > 0 and stats['conflicts'] >= stop_after_conflicts:
                return 'UNKNOWN', None, stats
            continue

        if all(assign_val[i] != UNASSIGNED for i in range(1, n + 1)):
            sat = [assign_val[i] for i in range(1, n + 1)]
            return 'SAT', sat, stats

        var = next(i for i in range(1, n + 1) if assign_val[i] == UNASSIGNED)
        chosen_val = None
        if preferred_values is not None:
            pv = preferred_values[var]
            order = [pv] + [v for v in range(b) if v != pv]
        else:
            order = list(range(b))
        for v in order:
            if not value_conflicts(var, v):
                chosen_val = v
                break
        if chosen_val is None:
            chosen_val = 0
        trail_lim.append(len(trail))
        enqueue(var, chosen_val, UNASSIGNED)
        stats['decisions'] += 1


# --- HESS glue (minimal) ---

db = set()

def oracle(seq, sat, clauses):
    '''Cuenta cuantas clausulas NO se satisfacen con la asignacion (seq, sat).'''
    assignment = dict(zip(seq, sat))
    unsat = 0
    for clause in clauses:
        for (x, y) in clause:
            if assignment.get(x) == y:
                break
        else:
            unsat += 1
    return unsat


def step(i, j, k, b, seq, sat):
    seq[i], seq[j] = seq[j], seq[i]
    sat[k] = (sat[k] + 1) % b # deterministic
    

def next_orbit(b: int, seq: List[int], sat: List[int]) -> bool:
    global db
    for i in range(len(seq)):
        for j in range(len(seq)):
            for k in range(len(seq)):
                key = tuple(zip(seq, sat))
                if key not in db:
                    db.add(key)
                    return True
                step(i, j, k, b, seq, sat)
    return False



def hess_cdcl(clauses: List[Clause], n: int, b: int, *,stop_after_conflicts: int = 0) -> Tuple[str, Optional[List[int]]]:
    seq = list(range(1, n + 1))
    sat = n * [0]
    cur = math.inf
    while next_orbit(b, seq, sat):
        for i in range(n):
            for j in range(n):                 
                glb = math.inf
                for k in range(n):
                    old_seq_i = seq[i]
                    old_seq_j = seq[j]
                    old_sat_k = sat[k]
                    step(i, j, k, b, seq, sat)

                    status, assignment, stats = solve_cdcl(
                        clauses,
                        n,
                        b,
                        root_assignments=None,
                        preferred_values=[0] + list(sat),
                        stop_after_conflicts=stop_after_conflicts,
                    )
                    if status == 'SAT' or status == 'UNSAT':
                        print(stats)
                        return status, assignment

                    loc = oracle(seq, sat, clauses) / math.log(stats['propagations'])
                                        
                    if loc < glb:
                        glb = loc
                        if glb < cur:
                            cur = glb
                            print(cur)
                            if cur == 0:
                                return 'SAT', list(sorted(zip(seq, sat)))[1]
                    elif loc > glb:
                        seq[i] = old_seq_i
                        seq[j] = old_seq_j
                        sat[k] = old_sat_k                

    return []


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--gcnf', required=True)
    ap.add_argument('--sol', default=None)
    ap.add_argument('--stop-after-conflicts', type=int, default=1)
    args = ap.parse_args()

    clauses = load_gcnf(args.gcnf)
    n, b = infer_dimensions(clauses)
    status, sat = hess_cdcl(clauses, n, b, stop_after_conflicts=args.stop_after_conflicts)

    print(status)
    
    if status == 'SAT' and sat is not None:
        out = args.sol or str(Path(args.gcnf).with_suffix('.sol'))
        write_solution(out, sat)

if __name__ == '__main__':
    main()
