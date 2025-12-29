Supplementary SAT instances for 'SAT-Verified Discrete Physics'.

Files:
- lr_L8_T3_unsat.*        Boolean locality on path: UNSAT (outside light cone)
- lr_L8_T7_sat.*          Boolean locality on path: SAT (on/inside light cone)
- tri_N6_deg4_sat.*       Triangulation synthesis (N=6, deg=4): SAT (octahedron)
- tri_N6_deg6_unsat.*     Triangulation synthesis (N=6, deg=6): UNSAT
- tri_N7_deg_pattern_unknown.*  Triangulation synthesis (N=7, 5,5,4,4,4,4,4): SAT
- tri_N8_deg_pattern.*    Larger triangulation synthesis (N=8 pattern): solver may timeout on prototype

Each instance includes:
- .gcnf  original equality-CNF
- .cnf   one-hot reduced DIMACS CNF
- .map   mapping between domains and CNF indicators
- .sol   decoded assignment (when available)
