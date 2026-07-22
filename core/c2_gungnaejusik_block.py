""""(1) 거래소주식" block within C2_자산부채평가, built from 국내주식명세
(one row per real holding -- 국내주식명세.parse() already drops 수량==0 rows).

Column mapping (verified against the real formulas): B=종목명, D=수량,
E=취득가액, G=평가금액.
"""
from __future__ import annotations

from core.c2_blocks import write_block
from core.gungnaejusik import FIRST_DATA_ROW as JUSIK_FIRST_DATA_ROW
from core.gungnaejusik import SHEET_NAME as JUSIK_SHEET_NAME

COLUMN_HEADERS = ["종목명", "수량", "결산전장부가액", "결산후장부가액"]


def _make_row_writer(source_row: int):
    s = JUSIK_SHEET_NAME

    def writer(ws, row: int) -> None:
        ws.cell(row, 3, f"={s}!B{source_row}")
        ws.cell(row, 4, f"={s}!D{source_row}")
        ws.cell(row, 5, f"={s}!E{source_row}")
        ws.cell(row, 6, f"={s}!G{source_row}")

    return writer


def build(
    ws, start_row: int, gungnaejusik_df, section_header: str, summary_row: int | None = None
) -> dict:
    row_writers = [
        _make_row_writer(JUSIK_FIRST_DATA_ROW + i) for i in range(len(gungnaejusik_df))
    ]
    return write_block(
        ws,
        start_row,
        section_header,
        COLUMN_HEADERS,
        row_writers,
        total_cols=["F"],
        hidden=not row_writers,
        summary_row=summary_row,
    )
