"""
Módulo: grammar.py
==================
Define la estructura de datos para Gramáticas Libres de Contexto (CFG).
Una gramática G = (N, T, P, S) donde:
- N: No terminales, T: Terminales, P: Producciones, S: Símbolo inicial
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, List, Dict, Tuple
import re


@dataclass
class Grammar:
    """Representa una Gramática Formal G = (N, T, P, S)"""
    # N: Conjunto de símbolos No Terminales (variables como S, A, B)
    N: Set[str]
    
    # T: Conjunto de símbolos Terminales (alfabeto como a, b, +, *)
    T: Set[str]
    
    # P: Diccionario de Producciones. Mapea cada no terminal a sus derivaciones
    # Ejemplo: {'S': [('a', 'S', 'b'), ('a', 'b')]} representa S -> aSb | ab
    P: Dict[str, List[Tuple[str, ...]]]
    
    # S: Símbolo Inicial desde donde comienzan las derivaciones
    S: str
    
    # gtype: Tipo de gramática ('2' = CFG, '3' = Regular)
    gtype: str = "2"

    @staticmethod
    def parse_production_line(line: str) -> Tuple[str, Tuple[str, ...]]:
        """
        Convierte texto "A -> B C" a tupla ('A', ('B', 'C'))
        Ejemplo: "S -> a S b" se convierte en ('S', ('a', 'S', 'b'))
        """
        # Dividir por la flecha (soporta -> o →)
        # Ejemplo: "S -> a b" se divide en left="S" y right="a b"
        if "->" in line:
            left, right = line.split("->")
        else:
            left, right = line.split("→")
        
        # Eliminar espacios en blanco al inicio y final
        left = left.strip()    # "S  " → "S"
        right = right.strip()  # "  a b  " → "a b"
        
        # Separar los símbolos del lado derecho usando espacios
        # re.split(r"\s+", "a b") → ["a", "b"]
        # Filtramos strings vacíos con if sym != ""
        symbols = tuple(sym for sym in re.split(r"\s+", right) if sym != "")
        
        # Retornar: lado izquierdo y tupla de símbolos derechos
        return left, symbols

    @classmethod
    def from_text(cls, N: List[str], T: List[str], productions: List[str], S: str, gtype: str = "2") -> "Grammar":
        """Construye una gramática desde listas de texto"""
        # Crear diccionario vacío para almacenar las producciones
        # Ejemplo: P = {} → luego será {'S': [('a',), ('b',)], 'A': [...]}
        P: Dict[str, List[Tuple[str, ...]]] = {}
        
        # Iterar sobre cada línea de producción en formato texto
        # Ejemplo: ["S -> a", "S -> b", "A -> c"]
        for line in productions:
            # Parsear la línea: "S -> a b" → left='S', rhs=('a', 'b')
            left, rhs = cls.parse_production_line(line)
            
            # Agregar la producción al diccionario
            # setdefault: si 'left' no existe, crea lista vacía []
            # append: agrega la nueva derivación 'rhs' a la lista
            # Ejemplo: P['S'] = [] luego P['S'].append(('a',)) → P['S'] = [('a',)]
            P.setdefault(left, []).append(rhs)
        
        # Crear instancia de Grammar convirtiendo listas a conjuntos (Set)
        # set(N): convierte ['S', 'A'] → {'S', 'A'} (elimina duplicados)
        return cls(set(N), set(T), P, S, gtype)

    def to_dict(self) -> Dict:
        """Convierte la gramática a diccionario para guardar en JSON"""
        return {
            # Convertir conjuntos a listas ordenadas para JSON
            # sorted: ordena alfabéticamente, list: convierte set a lista
            "N": sorted(list(self.N)),  # {'S', 'A'} → ['A', 'S']
            "T": sorted(list(self.T)),  # {'a', 'b'} → ['a', 'b']
            
            # Expandir todas las producciones a formato texto
            # List comprehension anidado: recorre cada no terminal A, cada derivación rhs
            # ' '.join(rhs): une símbolos con espacios ('a', 'S', 'b') → "a S b"
            # f-string: formatea como "A -> a S b"
            "P": [f"{A} -> {' '.join(rhs)}" for A, rhss in self.P.items() for rhs in rhss],
            
            # Símbolo inicial (usamos "S0" por compatibilidad con formato JSON estándar)
            "S0": self.S,
            
            # Tipo de gramática
            "type": self.gtype
        }

    def __str__(self) -> str:
        """Genera representación en texto legible para mostrar al usuario"""
        # Crear lista de strings para cada componente
        parts = [
            # Mostrar N: {A, B, S}
            f"N = {{{', '.join(sorted(self.N))}}}",
            # Mostrar T: {a, b}
            f"T = {{{', '.join(sorted(self.T))}}}",
            # Mostrar símbolo inicial
            f"S = {self.S}"
        ]
        
        # Agregar encabezado de producciones
        parts.append("P:")
        
        # Agregar cada producción con indentación
        # Recorrer cada no terminal A y sus derivaciones rhss
        for A, rhss in self.P.items():
            for rhs in rhss:
                # ' '.join(rhs): convierte ('a', 'S') → "a S"
                # Agregar con indentación "  S -> a S"
                parts.append(f"  {A} -> {' '.join(rhs)}")
        
        # Unir todas las partes con saltos de línea
        return "\n".join(parts)
