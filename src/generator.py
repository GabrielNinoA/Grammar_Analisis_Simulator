# contenido completo del módulo generator.py
from typing import List, Tuple, Set, Dict
from .grammar import Grammar
from collections import deque

# Generador por búsqueda en anchura de derivaciones para encontrar las N cadenas más cortas

def generate_shortest(grammar: Grammar, limit: int = 10, max_steps: int = 100000) -> List[str]:
    # representamos derivación como list of symbols (terminal or nonterminal)
    start = (grammar.S,)
    queue = deque()
    queue.append(start)
    results: List[str] = []
    seen: Set[Tuple[str, ...]] = set()
    steps = 0

    while queue and len(results) < limit and steps < max_steps:
        cur = queue.popleft()
        steps += 1
        # si todos son terminales
        if all(sym not in grammar.N for sym in cur):
            s = "".join(cur)
            if s not in results:
                results.append(s)
            continue
        # expandir la primera no-terminal (izquierda) para BFS en orden creciente de longitud
        for i, sym in enumerate(cur):
            if sym in grammar.N:
                A = sym
                prefix = cur[:i]
                suffix = cur[i + 1:]
                for rhs in grammar.P.get(A, []):
                    new_seq = tuple(prefix + rhs + suffix)
                    if new_seq not in seen:
                        seen.add(new_seq)
                        queue.append(new_seq)
                break

    return results
