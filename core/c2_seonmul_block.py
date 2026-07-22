""""N. 선물미수입금" block within C2_자산부채평가 -- a thin wrapper around
c2_seonmul_filtered_block for 포지션=="선물매수", kept as its own module
since it was built and tested first."""
from __future__ import annotations

from core import c2_seonmul_filtered_block

POSITION_VALUE = "선물매수"


def build(ws, start_row: int, seonmul_df, section_number: int) -> dict:
    header_text = f"{section_number}. 선물미수입금"
    return c2_seonmul_filtered_block.build(ws, start_row, seonmul_df, header_text, POSITION_VALUE)
