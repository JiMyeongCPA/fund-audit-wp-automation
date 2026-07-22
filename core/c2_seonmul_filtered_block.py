"""Generic "선물명세, filtered by 포지션" block builder for
C2_자산부채평가. Covers 선물미수입금 (포지션=="선물매수") and 선물미지급금
(포지션=="선물매도") -- same 7-column layout, different filter.

Column mapping into 선물명세 (verified against the real formulas): E=종목명,
F=포지션, G=계약수, H=정산가, I=평가금액, J=취득가액, L=미수입금/미지급금.
"""
from __future__ import annotations

from core.c2_blocks import write_block
from core.seonmul import FIRST_DATA_ROW as SEONMUL_FIRST_DATA_ROW
from core.seonmul import SHEET_NAME as SEONMUL_SHEET_NAME

COLUMN_HEADERS = ["종목명", "포지션", "계약수", "정산가", "평가금액", "취득가액", "미수(지급)금"]
POSITION_COL_IDX = 5  # 0-indexed: 포지션


def _make_row_writer(source_row: int, amount_col_letter: str):
    s = SEONMUL_SHEET_NAME

    def writer(ws, row: int) -> None:
        ws.cell(row, 3, f"={s}!E{source_row}")
        ws.cell(row, 4, f"={s}!F{source_row}")
        ws.cell(row, 5, f"={s}!G{source_row}")
        ws.cell(row, 6, f"={s}!H{source_row}")
        ws.cell(row, 7, f"={s}!I{source_row}")
        ws.cell(row, 8, f"={s}!J{source_row}")
        ws.cell(row, 9, f"={s}!{amount_col_letter}{source_row}")

    return writer


def build(
    ws,
    start_row: int,
    seonmul_df,
    header_text: str,
    position_value: str,
    amount_col_letter: str = "L",
    summary_row: int | None = None,
) -> dict:
    position_col = seonmul_df.columns[POSITION_COL_IDX]

    row_writers = []
    for i, position in enumerate(seonmul_df[position_col]):
        if str(position).strip() == position_value:
            source_row = SEONMUL_FIRST_DATA_ROW + i
            row_writers.append(_make_row_writer(source_row, amount_col_letter))

    return write_block(
        ws,
        start_row,
        header_text,
        COLUMN_HEADERS,
        row_writers,
        total_cols=["I"],
        hidden=not row_writers,
        summary_row=summary_row,
    )
