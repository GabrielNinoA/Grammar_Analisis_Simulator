"""
Módulo: cyk_parser.py - Algoritmo CYK (Cocke-Younger-Kasami)
=============================================================
Algoritmo de parsing para gramáticas en CNF usando programación dinámica.
Complejidad: O(n³ · |G|) donde n = longitud de la cadena
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Set, Optional
from .grammar import Grammar
from .cnf import to_cnf


class CYKResult:
    """Resultado del parsing CYK"""
    def __init__(self, accepted: bool, parse_tree: Optional[Tuple] = None):
        self.accepted = accepted  # True si la cadena pertenece al lenguaje
        self.parse_tree = parse_tree  # Árbol de derivación (None si rechazada)


def cyk_parse(grammar: Grammar, w: List[str]) -> CYKResult:
    """
    Ejecuta algoritmo CYK para determinar si w ∈ L(G)
    Parámetros: grammar (gramática CFG), w (cadena como lista de símbolos)
    Retorna: CYKResult con accepted y parse_tree
    """
    
    # Convertir gramática a CNF (requisito del algoritmo CYK)
    cnf = to_cnf(grammar)
    
    # Extraer componentes de la gramática
    N = list(cnf.N)  # Lista de no terminales
    P = cnf.P  # Diccionario de producciones
    n = len(w)  # Longitud de la cadena a analizar
    
    # =======================================================================
    # CASO ESPECIAL: Cadena vacía (epsilon)
    # =======================================================================
    if n == 0:
        # Verificar si existe producción S -> ε
        for rhs in P.get(cnf.S, []):
            if len(rhs) == 0:  # Producción epsilon
                # Cadena vacía es aceptada
                return CYKResult(True, (cnf.S, []))
        # No hay producción epsilon, rechazar
        return CYKResult(False, None)

    # =======================================================================
    # ESTRUCTURA DE DATOS: Tabla CYK
    # =======================================================================
    # table[i][j] = diccionario {no_terminal: [lista_de_derivaciones]}
    # i: posición inicial en la cadena (0 a n-1)
    # j: longitud - 1 de la subcadena (0 a n-i-1)
    # 
    # Ejemplo para cadena "ab" (n=2):
    # table[0][0]: símbolos que derivan w[0] = 'a'
    # table[1][0]: símbolos que derivan w[1] = 'b'
    # table[0][1]: símbolos que derivan w[0:2] = 'ab'
    
    # Crear tabla inicializada con diccionarios vacíos
    table: List[List[Dict[str, List]]] = [[{} for _ in range(n - i)] for i in range(n)]

    # =======================================================================
    # FASE 1: Llenar celdas base (subcadenas de longitud 1)
    # =======================================================================
    # Para cada símbolo de la cadena, encontrar qué no terminales lo derivan
    
    for i in range(n):  # i va de 0 a n-1
        sym = w[i]  # Símbolo terminal en posición i
        
        # Buscar producciones que derivan este terminal
        for A, rhss in P.items():  # A: no terminal, rhss: sus producciones
            for rhs in rhss:  # rhs: una producción específica
                # Verificar si es producción A -> terminal
                if len(rhs) == 1 and rhs[0] == sym:
                    # Encontramos A -> sym
                    # Agregar A a la celda table[i][0]
                    # setdefault: si A no existe, crear lista []
                    table[i][0].setdefault(A, []).append((sym,))
                    # (sym,) es tupla que guarda info de derivación

    # =======================================================================
    # FASE 2: Llenar tabla bottom-up (subcadenas de longitud 2 a n)
    # =======================================================================
    # Usar programación dinámica para construir derivaciones largas
    # a partir de derivaciones cortas ya calculadas
    
    for l in range(2, n + 1):  # l: longitud de subcadena (2, 3, ..., n)
        for i in range(0, n - l + 1):  # i: posición inicial
            # Subcadena actual: w[i:i+l]
            
            # Probar todas las formas de partir la subcadena en dos
            for s in range(1, l):  # s: tamaño de la parte izquierda
                # Dividir en: parte_izq (tamaño s) + parte_der (tamaño l-s)
                # Parte izquierda: w[i:i+s]
                # Parte derecha: w[i+s:i+l]
                
                # Obtener celdas correspondientes de la tabla
                left_cell = table[i][s - 1]  # Celda de parte izquierda
                right_cell = table[i + s][l - s - 1]  # Celda de parte derecha
                
                # Si alguna celda está vacía, no podemos formar derivaciones
                if not left_cell or not right_cell:
                    continue  # Probar siguiente partición
                
                # Buscar producciones binarias A -> BC que combinen las partes
                for A, rhss in P.items():
                    for rhs in rhss:
                        # Verificar si es producción binaria
                        if len(rhs) == 2:
                            B, C = rhs  # Extraer los dos no terminales
                            
                            # Verificar si B deriva parte izquierda y C parte derecha
                            if B in left_cell and C in right_cell:
                                # ¡Encontramos derivación válida!
                                # A -> BC donde:
                                #   B =>* subcadena_izquierda
                                #   C =>* subcadena_derecha
                                
                                # Guardar todas las combinaciones de árboles
                                for left_tree in left_cell[B]:
                                    for right_tree in right_cell[C]:
                                        # Crear tupla de derivación
                                        # Formato: (B, árbol_izq, C, árbol_der)
                                        derivation = (B, left_tree, C, right_tree)
                                        
                                        # Agregar a tabla
                                        table[i][l - 1].setdefault(A, []).append(derivation)

    # =======================================================================
    # FASE 3: Verificar aceptación y reconstruir árbol
    # =======================================================================
    
    start = cnf.S  # Símbolo inicial de la gramática
    
    # La cadena es aceptada si S puede derivar toda la cadena w
    # Esto se verifica en la celda superior: table[0][n-1]
    accepted = start in table[0][n - 1]
    
    parse_tree = None  # Inicializar árbol como None
    
    if accepted:
        # La cadena fue aceptada, reconstruir árbol de parsing
        
        def rebuild_from_cell(symbol: str, entry) -> Tuple:
            """Reconstruye recursivamente el árbol de derivación"""
            
            # CASO BASE: Llegamos a un terminal (hoja del árbol)
            if len(entry) == 1 and isinstance(entry[0], str):
                # entry = ('a',) → nodo hoja
                return (symbol, entry[0])  # (A, 'a')
            
            # CASO RECURSIVO: Producción binaria A -> BC
            else:
                # entry = (B, left_entry, C, right_entry)
                B, left_e, C, right_e = entry
                
                # Reconstruir subárbol izquierdo recursivamente
                left_node = rebuild_from_cell(B, left_e)
                
                # Reconstruir subárbol derecho recursivamente
                right_node = rebuild_from_cell(C, right_e)
                
                # Retornar nodo interno: (A, hijo_izq, hijo_der)
                return (symbol, left_node, right_node)
        
        # Tomar primera derivación encontrada (índice [0])
        # Puede haber múltiples si la gramática es ambigua
        parse_tree = rebuild_from_cell(start, table[0][n - 1][start][0])
    
    # Retornar resultado del parsing
    return CYKResult(accepted, parse_tree)
