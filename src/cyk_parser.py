# contenido completo del módulo cyk_parser.py
from __future__ import annotations
from typing import Dict, List, Tuple, Set, Optional
from .grammar import Grammar
from .cnf import to_cnf

# Implementación del algoritmo CYK con reconstrucción del árbol de derivación.

class CYKResult:
    def __init__(self, accepted: bool, parse_tree: Optional[Tuple] = None):
        self.accepted = accepted
        self.parse_tree = parse_tree

def cyk_parse(grammar: Grammar, w: List[str]) -> CYKResult:
    # convertimos a CNF
    cnf = to_cnf(grammar)
    N = list(cnf.N)
    P = cnf.P
    n = len(w)
    if n == 0:
        # aceptar epsilon si S -> epsilon
        for rhs in P.get(cnf.S, []):
            if len(rhs) == 0:
                return CYKResult(True, (cnf.S, []))
        return CYKResult(False, None)

    # table[i][j] contiene dict variable -> list of derivation tuples
    # i: posición inicial (0..n-1), j: longitud (1..n-i)
    table: List[List[Dict[str, List]]] = [[{} for _ in range(n - i)] for i in range(n)]

    # rellenar para longitud 1
    for i in range(n):
        sym = w[i]
        for A, rhss in P.items():
            for rhs in rhss:
                if len(rhs) == 1 and rhs[0] == sym:
                    table[i][0].setdefault(A, []).append((sym,))

    # llenar para longitudes mayores
    for l in range(2, n + 1):  # longitud de la subcadena
        for i in range(0, n - l + 1):  # inicio
            for s in range(1, l):  # partición
                left_cell = table[i][s - 1]
                right_cell = table[i + s][l - s - 1]
                if not left_cell or not right_cell:
                    continue
                for A, rhss in P.items():
                    for rhs in rhss:
                        if len(rhs) == 2:
                            B, C = rhs
                            if B in left_cell and C in right_cell:
                                # podemos derivar A -> B C
                                # guardar las posibles combinaciones
                                for left_tree in left_cell[B]:
                                    for right_tree in right_cell[C]:
                                        table[i][l - 1].setdefault(A, []).append((B, left_tree, C, right_tree))

    # verificar si S está en la celda (0, n)
    start = cnf.S
    accepted = start in table[0][n - 1]
    parse_tree = None
    if accepted:
        # reconstruir una derivación (la primera)
        def rebuild_from_cell(symbol: str, entry) -> Tuple:
            # entry could be ('a',) or (B, left_entry, C, right_entry)
            if len(entry) == 1 and isinstance(entry[0], str):
                return (symbol, entry[0])
            else:
                B, left_e, C, right_e = entry
                left_node = rebuild_from_cell(B, left_e)
                right_node = rebuild_from_cell(C, right_e)
                return (symbol, left_node, right_node)

        parse_tree = rebuild_from_cell(start, table[0][n - 1][start][0])
    return CYKResult(accepted, parse_tree)
