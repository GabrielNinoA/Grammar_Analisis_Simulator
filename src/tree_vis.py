"""
Módulo: tree_vis.py - Visualización de árboles de derivación
=============================================================
Convierte árboles en formato tupla a representación textual con indentación.
"""

from typing import Tuple, Any


def render_tree_text(node: Tuple[Any, ...], indent: int = 0) -> str:
    """
    Renderiza un árbol de parsing en formato texto con indentación jerárquica.
    Parámetros: node (nodo del árbol), indent (nivel de indentación)
    Retorna: string con el árbol formateado
    """
    
    # Calcular indentación: 2 espacios por cada nivel
    # Ejemplo: indent=0 → "", indent=1 → "  ", indent=2 → "    "
    pad = "  " * indent
    
    # =======================================================================
    # CASO 1: Nodo hoja (terminal)
    # =======================================================================
    # Formato: (símbolo_no_terminal, 'terminal')
    # Ejemplo: ('A', 'a') representa A -> a
    
    # Verificar: longitud 2 Y segundo elemento es string
    if len(node) == 2 and isinstance(node[1], str):
        # node[0]: símbolo no terminal (ej: 'A')
        # node[1]: símbolo terminal (ej: 'a')
        # Formato salida: "  A -> a\n"
        return f"{pad}{node[0]} -> {node[1]}\n"
    
    # =======================================================================
    # CASO 2: Nodo sin hijos (producción vacía o epsilon)
    # =======================================================================
    # Formato: (símbolo,)
    # Ejemplo: ('S',) 
    
    elif len(node) == 1:
        # Solo mostrar el símbolo
        # Formato salida: "  S\n"
        return f"{pad}{node[0]}\n"
    
    # =======================================================================
    # CASO 3: Nodo interno con hijos (producción binaria o múltiple)
    # =======================================================================
    # Formato: (símbolo, hijo1, hijo2, ...)
    # Ejemplo: ('S', ('A', 'a'), ('B', 'b'))
    
    else:
        # Imprimir símbolo actual con indentación
        # node[0]: símbolo del nodo actual (ej: 'S')
        out = f"{pad}{node[0]}\n"
        
        # Recursivamente renderizar cada hijo con mayor indentación
        # node[1:]: todos los elementos después del primero (los hijos)
        # Ejemplo: si node = ('S', hijo1, hijo2), entonces node[1:] = (hijo1, hijo2)
        for child in node[1:]:
            # Llamada recursiva: aumentar indentación en 1
            out += render_tree_text(child, indent + 1)
        
        # Retornar string completo
        return out
