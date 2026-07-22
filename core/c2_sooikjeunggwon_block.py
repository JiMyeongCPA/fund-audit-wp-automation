""""N. 모펀드수익증권, 상장펀드" block within C2_자산부채평가, built from
수익증권명세 (one row per holding, no filtering -- this fund holds exactly
one: 종목ETF001).

Column mapping (verified against the real formulas): C=종목명, G=좌수,
K=취득가액, J=평가금액. 평가손익 (column G here) is computed within C2 itself
(결산후 - 결산전), not pulled from the source.
"""
from __future__ import annotations

from core.c2_blocks import write_block
from core.sooikjeunggwon import FIRST_DATA_ROW as SOOIK_FIRST_DATA_ROW
from core.sooikjeunggwon import SHEET_NAME as SOOIK_SHEET_NAME

COLUMN_HEADERS = ["종목명", "수량", "결산전장부가액", "결산후장부가액", "평가손익"]


def _make_row_writer(source_row: int):
    s = SOOIK_SHEET_NAME

    def writer(ws, row: int) -> None:
        ws.cell(row, 3, f"={s}!C{source_row}")
        ws.cell(row, 4, f"={s}!G{source_row}")
        ws.cell(row, 5, f"={s}!K{source_row}")
        ws.cell(row, 6, f"={s}!J{source_row}")
        ws.cell(row, 7, f"=F{row}-E{row}")

    return writer


def build(
    ws, start_row: int, sooikjeunggwon_df, section_number: int, summary_row: int | None = None
) -> dict:
    row_writers = [
        _make_row_writer(SOOIK_FIRST_DATA_ROW + i) for i in range(len(sooikjeunggwon_df))
    ]
    header_text = f"{section_number}. 모펀드수익증권, 상장펀드"
    return write_block(
        ws,
        start_row,
        header_text,
        COLUMN_HEADERS,
        row_writers,
        total_cols=["F"],
        hidden=not row_writers,
        summary_row=summary_row,
    )
