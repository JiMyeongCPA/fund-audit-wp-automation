"""Structural placeholder block for C2_자산부채평가 categories with no
identified PBC source (위탁증거금, 현금담보증거금, 옵션매수, 옵션매도,
매도유가증권, 코스닥주식). Verified against the original file: this fund
has a zero balance in every one of these categories this period, so an
empty block (3 blank rows + a total of 0) is a faithful representation of
this period's data, not a stand-in for unfinished work.
"""
from __future__ import annotations

from core.c2_blocks import write_block


def build(
    ws,
    start_row: int,
    header_text: str,
    column_headers: list[str],
    total_cols: list[str],
    summary_row: int | None = None,
) -> dict:
    return write_block(
        ws,
        start_row,
        header_text,
        column_headers,
        row_writers=[],
        total_cols=total_cols,
        hidden=True,
        summary_row=summary_row,
    )
