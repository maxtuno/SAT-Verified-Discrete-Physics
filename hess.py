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

import argparse
import ast
import hashlib
import math
import random
import time
import tracemalloc
from pathlib import Path

db = {}


def oracle(sat, clauses):
    '''Cuenta cuantas clausulas NO se satisfacen con la asignacion sat.'''
    unsat = 0
    for clause in clauses:
        for (x, y) in clause:
            if sat[x - 1] == y:
                break
        else:
            unsat += 1
    return unsat


def next_orbit(sat):
    global db
    for k in range(len(sat)):
        key = hashlib.sha1(''.join(list(map(str, sat))).encode())
        if key not in db:
            db[key] = True
            return True
        step(k, sat)
    return False


def step(k, sat):
    sat[k] = (sat[k] + 1) % b

def hess(clauses):
    sat = n * [0]
    cur = math.inf
    while next_orbit(sat):
        glb = math.inf
        for k in range(n):
            old_sat_k = sat[k]
            step(k, sat)
            loc = oracle(sat, clauses)
            if loc < glb:
                glb = loc
                if glb < cur:
                    cur = glb
                    print(cur)
                    if cur == 0:
                        return list(range(1, len(sat) + 1)), sat
            elif loc > glb:
                sat[k] = old_sat_k
    return []


def load_gcnf(path):
    clauses = []
    with open(path) as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            clauses.append(ast.literal_eval(line))
    return clauses


def infer_dimensions(clauses):
    max_var = max(x for clause in clauses for (x, _) in clause)
    max_val = max(v for clause in clauses for (_, v) in clause)
    return max_var, max_val + 1


def run_hess_benchmark(clauses, seed=1234):
    global n, b, db
    n, b = infer_dimensions(clauses)
    db = {}
    if seed is not None:
        random.seed(seed)
    tracemalloc.start()
    start = time.perf_counter()
    res = hess(clauses)
    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    score = None
    if res:
        seq, sat = res
        score = oracle(sat, clauses)
    stats = {
        'elapsed_sec': elapsed,
        'mem_current': current,
        'mem_peak': peak,
        'score': score,
        'n': n,
        'b': b,
        'clauses': len(clauses),
    }
    return res, stats


def generate_instance(n, b, m, k, seed=None):
    if seed is not None:
        random.seed(seed)
    clauses = []
    for _ in range(m):
        clause = []
        while True:
            item = random.randint(1, n)
            if item not in clause:
                clause.append((item, random.randrange(0, b)))
            if len(clause) >= random.randint(1, k):
                break
        clauses.append(clause)
    return clauses

def write_solution(path, seq, sat):
    solution = list(zip(seq, sat))
    with open(path, 'w') as file:
        file.write(repr(solution) + '\n')

def main():
    parser = argparse.ArgumentParser(description='HESS para GSP: generador y benchmark simple.')
    parser.add_argument('--input', type=str, default='test.gcnf', help='Ruta del archivo GCNF de entrada.')
    parser.add_argument('--generate', action='store_true', help='Genera instancia aleatoria en vez de leer --input.')
    parser.add_argument('--output', type=str, default='test.gcnf', help='Ruta para escribir la instancia generada.')
    parser.add_argument('--n', type=int, default=100, help='Numero de variables para generar.')
    parser.add_argument('--b', type=int, default=5, help='Valores por variable para generar.')
    parser.add_argument('--m', type=int, default=100, help='Numero de clausulas para generar.')
    parser.add_argument('--k', type=int, default=10, help='Maximo largo de clausula al generar.')
    parser.add_argument('--seed', type=int, default=1234, help='Semilla para reproducibilidad.')
    parser.add_argument('--sol-output', type=str, default=None, help='Ruta para escribir la solucion (lista de tuplas). Por defecto usa el nombre de entrada/salida con extension .sol.')
    args = parser.parse_args()

    if args.generate:
        clauses = generate_instance(args.n, args.b, args.m, args.k, seed=args.seed)
        if args.output:
            with open(args.output, 'w') as file:
                for clause in clauses:
                    print(clause, file=file)
    else:
        clauses = load_gcnf(args.input)

    res, stats = run_hess_benchmark(clauses, seed=args.seed)
    print(stats)
    if res:
        seq, sat = res
        solution = list(zip(seq, sat))
        print(solution)
        base = Path(args.output if args.generate else args.input)
        if args.sol_output:
            sol_path = Path(args.sol_output)
        else:
            sol_path = base.with_suffix('.sol') if base.suffix else Path(str(base) + '.sol')
        write_solution(sol_path, seq, sat)
        print(f'Solucion guardada en {sol_path}')


if __name__ == '__main__':
    main()
