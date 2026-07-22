"""Tracks C2_자산부채평가's running top-level section number.

Verified against the real file: the section captions use a conditional
numbering scheme (`=IF(prev_total=0, keep_prev_number, prev_number+1)`) so a
run of zero-balance categories (콜론/REPO매수/매입어음/전자단기사채, all
zero this period) all display the same number, and the number only advances
once a category with real data is reached. This replicates that as plain
Python state instead of a live formula chain -- we already know at build
time whether each block is empty, so there's no need to encode the check as
a formula.
"""
from __future__ import annotations


class SectionNumberer:
    def __init__(self, start: int = 1):
        self.current = start

    def use(self) -> int:
        return self.current

    def advance(self, is_empty: bool) -> None:
        if not is_empty:
            self.current += 1
