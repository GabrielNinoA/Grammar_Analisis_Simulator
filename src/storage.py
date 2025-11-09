# contenido completo del módulo storage.py
import json
from typing import Dict
from .grammar import Grammar

def save_grammar(g: Grammar, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(g.to_dict(), f, indent=2, ensure_ascii=False)

def load_grammar(path: str) -> Grammar:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    N = data["N"]
    T = data["T"]
    P = data["P"]
    S = data.get("S0") or data.get("S")
    gtype = data.get("type", "2")
    return Grammar.from_text(N, T, P, S, gtype)
