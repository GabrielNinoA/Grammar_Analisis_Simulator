# contenido completo del módulo cnf.py
from __future__ import annotations
from typing import Dict, List, Tuple, Set
from .grammar import Grammar
import itertools

# Conversión básica a CNF. No es la implementación más optimizada, pero funcional para gramáticas de tarea.

def to_cnf(grammar: Grammar) -> Grammar:
    # pasos resumidos:
    # 1. Eliminar reglas epsilon (no implementado exhaustivamente; asumimos pocas epsilon)
    # 2. Eliminar producciones unitarias
    # 3. Reemplazar terminales en reglas largas por variables nuevas
    # 4. Romper reglas más largas en binarias

    N = set(grammar.N)
    T = set(grammar.T)
    P = {A: [tuple(rhs) for rhs in rhss] for A, rhss in grammar.P.items()}
    S0 = grammar.S

    # 0. asegurarnos de que el símbolo inicial no aparece en RHS producciones que generen S0 -> ...
    new_start = S0
    if any(S0 in rhs for rhss in P.values() for rhs in rhss):
        new_start = S0 + "0"
        N.add(new_start)
        P.setdefault(new_start, []).append((S0,))

    # 1. eliminar epsilon (simplificado)
    # recolectar nullable
    nullable = set()
    changed = True
    while changed:
        changed = False
        for A, rhss in P.items():
            for rhs in rhss:
                if len(rhs) == 0 or all((sym in nullable) for sym in rhs):
                    if A not in nullable:
                        nullable.add(A)
                        changed = True

    # expandir producciones removiendo nullable en RHS
    newP: Dict[str, List[Tuple[str, ...]]] = {}
    for A, rhss in P.items():
        new_rhs_set = set()
        for rhs in rhss:
            positions = [i for i, sym in enumerate(rhs) if sym in nullable]
            # generar combinaciones de eliminación
            for mask in range(1 << len(positions)):
                rhs_list = list(rhs)
                # eliminar marcados
                to_remove_indices = {positions[i] for i in range(len(positions)) if (mask >> i) & 1}
                new_rhs = tuple(sym for idx, sym in enumerate(rhs_list) if idx not in to_remove_indices)
                new_rhs_set.add(new_rhs)
        # eliminar epsilon vacío si A es el símbolo inicial nuevo
        final_rhs = [rhs for rhs in new_rhs_set if not (len(rhs) == 0 and A != new_start)]
        newP[A] = final_rhs

    P = newP

    # 2. eliminar unit productions A -> B
    def remove_unit_productions(P: Dict[str, List[Tuple[str, ...]]]) -> Dict[str, List[Tuple[str, ...]]]:
        unit_pairs = set()
        for A in list(P.keys()):
            for rhs in P[A]:
                if len(rhs) == 1 and rhs[0] in N:
                    unit_pairs.add((A, rhs[0]))
        # cierre transitiva
        while True:
            added = False
            for (A, B) in list(unit_pairs):
                for (C, D) in list(unit_pairs):
                    if B == C and (A, D) not in unit_pairs:
                        unit_pairs.add((A, D))
                        added = True
            if not added:
                break
        # construir nuevas producciones sin unitarias
        newP = {A: [] for A in N}
        for A in N:
            for rhs in P.get(A, []):
                if not (len(rhs) == 1 and rhs[0] in N):
                    newP[A].append(rhs)
            # agregar producciones de las variables unitarias
            for (X, Y) in unit_pairs:
                if X == A:
                    for rhs in P.get(Y, []):
                        if not (len(rhs) == 1 and rhs[0] in N):
                            if rhs not in newP[A]:
                                newP[A].append(rhs)
        return newP

    P = remove_unit_productions(P)

    # 3. Reemplazar terminales en reglas largas
    term_map: Dict[str, str] = {}
    counter = 0
    for A in list(P.keys()):
        newlist = []
        for rhs in P[A]:
            if len(rhs) >= 2:
                new_rhs = list(rhs)
                for i, sym in enumerate(rhs):
                    if sym in T:
                        if sym in term_map:
                            var = term_map[sym]
                        else:
                            var = f"T_{counter}"
                            counter += 1
                            while var in N:
                                var = f"T_{counter}"
                                counter += 1
                            N.add(var)
                            P.setdefault(var, []).append((sym,))
                            term_map[sym] = var
                        new_rhs[i] = var
                newlist.append(tuple(new_rhs))
            else:
                newlist.append(rhs)
        P[A] = newlist

    # 4. Romper reglas con longitud > 2 en binarias
    # Enfoque iterativo: despliegue de cadenas largas reemplazando por variables intermedias
    while True:
        changed = False
        for A in list(P.keys()):
            new_rhss = []
            for rhs in P[A]:
                if len(rhs) > 2:
                    changed = True
                    symbols = list(rhs)
                    # crear cadena A -> symbols[0] X1 ; X1 -> symbols[1] X2 ; ... ; Xk -> sym[-2] sym[-1]
                    cur_left = A
                    for i in range(len(symbols) - 2):
                        first = symbols[i]
                        new_var = f"X_{len(N)}_{i}"
                        while new_var in N:
                            new_var = f"X_{len(N)}_{i}_{i}"
                        N.add(new_var)
                        # agregar cur_left -> first new_var
                        P.setdefault(cur_left, [])
                        P[cur_left].append((first, new_var))
                        cur_left = new_var
                    # terminar con cur_left -> penultimo ultimo
                    last_two = (symbols[-2], symbols[-1])
                    P.setdefault(cur_left, [])
                    P[cur_left].append(last_two)
                else:
                    new_rhss.append(rhs)
            P[A] = new_rhss
        if not changed:
            break

    # rebuild Grammar: eliminar duplicados
    for A in list(P.keys()):
        seen = []
        for rhs in P[A]:
            if rhs not in seen:
                seen.append(rhs)
        P[A] = seen

    return Grammar(N, T, P, new_start, grammar.gtype)
