# contenido completo del módulo grammar.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set, List, Dict, Tuple
import re


@dataclass
class Grammar:
    N: Set[str]
    T: Set[str]
    P: Dict[str, List[Tuple[str, ...]]]
    S: str
    gtype: str = "2"  # '2' para CFG, '3' para regulares

    @staticmethod
    def parse_production_line(line: str) -> Tuple[str, Tuple[str, ...]]:
        # ejemplo: "E -> E + T" o "A -> a"
        left, right = line.split("->") if "->" in line else line.split("→")
        left = left.strip()
        right = right.strip()
        # separar por espacios, pero mantener terminales compuestos entre '' si el usuario las pone
        symbols = tuple(sym for sym in re.split(r"\s+", right) if sym != "")
        return left, symbols

    @classmethod
    def from_text(cls, N: List[str], T: List[str], productions: List[str], S: str, gtype: str = "2") -> "Grammar":
        P: Dict[str, List[Tuple[str, ...]]] = {}
        for line in productions:
            left, rhs = cls.parse_production_line(line)
            P.setdefault(left, []).append(rhs)
        return cls(set(N), set(T), P, S, gtype)

    def to_dict(self) -> Dict:
        return {
            "N": sorted(list(self.N)),
            "T": sorted(list(self.T)),
            "P": [f"{A} -> {' '.join(rhs)}" for A, rhss in self.P.items() for rhs in rhss],
            "S0": self.S,
            "type": self.gtype
        }

    def __str__(self) -> str:
        parts = [f"N = {{{', '.join(sorted(self.N))}}}", f"T = {{{', '.join(sorted(self.T))}}}", f"S = {self.S}"]
        parts.append("P:")
        for A, rhss in self.P.items():
            for rhs in rhss:
                parts.append(f"  {A} -> {' '.join(rhs)}")
        return "\n".join(parts)
