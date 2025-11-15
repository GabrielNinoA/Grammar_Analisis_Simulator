"""
Módulo: storage.py - Persistencia de gramáticas en JSON
========================================================
Guarda y carga objetos Grammar desde/hacia archivos JSON.
"""

import json
from typing import Dict
from .grammar import Grammar


def save_grammar(g: Grammar, path: str) -> None:
    """
    Guarda una gramática en un archivo JSON.
    Parámetros: g (objeto Grammar), path (ruta del archivo)
    """
    
    # Abrir archivo en modo escritura con codificación UTF-8
    # 'w': modo write (sobrescribe si existe)
    # encoding='utf-8': permite caracteres especiales (→, ε, acentos)
    with open(path, "w", encoding="utf-8") as f:
        # g.to_dict(): convertir Grammar a diccionario Python
        # json.dump(): serializar diccionario a JSON y escribir en f
        # indent=2: formato legible con 2 espacios de indentación
        # ensure_ascii=False: mantener caracteres Unicode sin escapar
        json.dump(g.to_dict(), f, indent=2, ensure_ascii=False)


def load_grammar(path: str) -> Grammar:
    """
    Carga una gramática desde un archivo JSON.
    Parámetros: path (ruta del archivo)
    Retorna: objeto Grammar reconstruido
    """
    
    # Abrir archivo en modo lectura con codificación UTF-8
    # 'r': modo read
    with open(path, "r", encoding="utf-8") as f:
        # Leer y parsear el archivo JSON completo
        # json.load(): convierte texto JSON a diccionario Python
        data = json.load(f)
    
    # Extraer componentes de la gramática del diccionario
    # data["N"]: lista de símbolos no terminales
    N = data["N"]
    
    # data["T"]: lista de símbolos terminales
    T = data["T"]
    
    # data["P"]: lista de producciones en formato texto
    P = data["P"]
    
    # Símbolo inicial: intentar "S0" primero, luego "S"
    # get("S0"): retorna valor si existe, None si no existe
    # or data.get("S"): usa "S" si "S0" era None
    S = data.get("S0") or data.get("S")
    
    # Tipo de gramática: usar "2" (CFG) como default
    # get("type", "2"): retorna data["type"] si existe, sino "2"
    gtype = data.get("type", "2")
    
    # Construir objeto Grammar desde los componentes
    # from_text(): método estático que parsea texto a Grammar
    return Grammar.from_text(N, T, P, S, gtype)
