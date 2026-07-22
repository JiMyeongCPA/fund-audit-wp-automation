""""N. 예금" block within C2_자산부채평가 -- a thin wrapper around
c2_yudong_filtered_block for the "예금" 유동종류, kept as its own module
since it was built and tested first."""
from __future__ import annotations

from core import c2_yudong_filtered_block

KIND_VALUE = "예금"


def build(ws, start_row: int, gungnaeyudong_df, section_number: int) -> dict:
    header_text = f"{section_number}. 예금"
    return c2_yudong_filtered_block.build(ws, start_row, gungnaeyudong_df, header_text, KIND_VALUE)
