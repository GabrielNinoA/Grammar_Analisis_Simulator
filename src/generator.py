"""
Módulo: generator.py - Generador de cadenas usando BFS
=======================================================
Genera las N cadenas más cortas del lenguaje L(G) usando búsqueda en anchura.
El BFS garantiza que las cadenas se generen en orden de longitud creciente.
"""

from typing import List, Tuple, Set, Dict
from .grammar import Grammar
from collections import deque


def generate_shortest(grammar: Grammar, limit: int = 10, max_steps: int = 100000) -> List[str]:
    """
    Genera las N cadenas más cortas del lenguaje usando BFS.
    Parámetros: grammar (gramática), limit (cantidad), max_steps (límite de iteraciones)
    Retorna: lista de cadenas generadas
    """
    
    # =======================================================================
    # INICIALIZACIÓN
    # =======================================================================
    
    # Forma sentencial inicial: solo el símbolo inicial
    # Una forma sentencial es una secuencia de terminales y no terminales
    # Ejemplo: si S es inicial, start = ('S',)
    start = (grammar.S,)
    
    # Cola FIFO para BFS: procesa formas sentenciales en orden
    queue = deque()
    queue.append(start)  # Agregar forma sentencial inicial
    
    # Lista de resultados: cadenas terminales generadas
    results: List[str] = []
    
    # Conjunto para evitar procesar la misma forma sentencial múltiples veces
    # Evita ciclos infinitos y reduce trabajo redundante
    seen: Set[Tuple[str, ...]] = set()
    
    # Contador de pasos para evitar bucles infinitos
    steps = 0

    # =======================================================================
    # BUCLE PRINCIPAL: Búsqueda en Anchura (BFS)
    # =======================================================================
    # Condiciones de terminación:
    # 1. Cola vacía (no quedan formas sentenciales por explorar)
    # 2. Ya generamos 'limit' cadenas
    # 3. Alcanzamos max_steps iteraciones
    
    while queue and len(results) < limit and steps < max_steps:
        # Extraer siguiente forma sentencial de la cola (orden FIFO = BFS)
        # FIFO: First In First Out - garantiza orden por longitud
        cur = queue.popleft()
        
        # Incrementar contador de pasos
        steps += 1
        
        # -------------------------------------------------------------------
        # CASO BASE: Verificar si es una cadena terminal
        # -------------------------------------------------------------------
        # Una forma sentencial es terminal si todos sus símbolos son terminales
        # Ejemplo: ('a', 'b', 'a') es terminal, ('a', 'S', 'b') no lo es
        
        # all(): retorna True si TODOS los elementos cumplen la condición
        # sym not in grammar.N: el símbolo NO es no terminal (es terminal)
        if all(sym not in grammar.N for sym in cur):
            # Todos son terminales, convertir tupla a string
            # "".join: concatena símbolos sin separadores
            # ('a', 'b', 'a') → "aba"
            s = "".join(cur)
            
            # Agregar a resultados si no está duplicada
            if s not in results:
                results.append(s)
            
            # No expandir más esta forma sentencial (ya es terminal)
            continue
        
        # -------------------------------------------------------------------
        # CASO RECURSIVO: Expandir el primer no terminal
        # -------------------------------------------------------------------
        # Estrategia: expandir el no terminal más a la izquierda
        # Esto garantiza exploración sistemática (leftmost derivation)
        
        # Buscar el primer no terminal en la forma sentencial
        for i, sym in enumerate(cur):
            # Verificar si el símbolo es no terminal
            if sym in grammar.N:
                A = sym  # A es el no terminal a expandir
                
                # Separar la forma sentencial en tres partes:
                # prefix: símbolos ANTES del no terminal
                # A: el no terminal a expandir
                # suffix: símbolos DESPUÉS del no terminal
                # Ejemplo: cur=('a', 'S', 'b') con i=1 → prefix=('a',), A='S', suffix=('b',)
                prefix = cur[:i]  # Subcadena [0, i)
                suffix = cur[i + 1:]  # Subcadena [i+1, fin]
                
                # Aplicar cada producción de A
                # grammar.P.get(A, []): obtener producciones de A, [] si no existe
                for rhs in grammar.P.get(A, []):
                    # rhs: lado derecho de una producción A -> α
                    # Ejemplo: si A -> aSb entonces rhs = ('a', 'S', 'b')
                    
                    # Crear nueva forma sentencial: prefix + rhs + suffix
                    # Ejemplo: ('a',) + ('a', 'S', 'b') + ('b',) = ('a', 'a', 'S', 'b', 'b')
                    new_seq = tuple(prefix + rhs + suffix)
                    
                    # Solo agregar a la cola si no la hemos visto antes
                    # Esto evita procesar la misma derivación múltiples veces
                    if new_seq not in seen:
                        seen.add(new_seq)  # Marcar como vista
                        queue.append(new_seq)  # Agregar a cola para procesar
                
                # Solo expandimos el primer no terminal (leftmost), salir del bucle
                break

    # Retornar lista de cadenas generadas
    return results
