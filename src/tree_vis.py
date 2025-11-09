# contenido completo del módulo tree_vis.py
from typing import Tuple, Any

def render_tree_text(node: Tuple[Any, ...], indent: int = 0) -> str:
    # node: (Symbol, ...) where leaves are (Symbol, terminal)
    pad = "  " * indent
    if len(node) == 2 and isinstance(node[1], str):
        return f"{pad}{node[0]} -> {node[1]}\n"
    elif len(node) == 1:
        return f"{pad}{node[0]}\n"
    else:
        out = f"{pad}{node[0]}\n"
        for child in node[1:]:
            out += render_tree_text(child, indent + 1)
        return out
