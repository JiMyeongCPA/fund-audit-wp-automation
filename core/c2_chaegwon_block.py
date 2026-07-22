""""N. 채권" block within C2_자산부채평가, built from 채권명세 (one row per
bond holding, no filtering).

Has its own 합계 row like every other block (H/I/J summed), for consistency
-- even though the summary table's rows (국채/특수채/통안채/회사채) don't
read it directly; they each do their own SUMIF over this block's raw row
range instead, grouping by 코스콤대분류 (column E here). Callers still get
`first_data_row`/`last_data_row` back to build that SUMIF range.

Column mapping into 채권명세 (verified against the real formulas): C=종목명,
F=종류, G=코스콤대분류, H=발행률(/100), N=액면, Q=만기일,
T=장부가평가액(종목통화), U=시가평가금액(종목통화), AA=기경과이자,
AE=미수이자.
"""
from __future__ import annotations

from core.c2_blocks import write_block
from core.chaegwon import FIRST_DATA_ROW as CHAEGWON_FIRST_DATA_ROW
from core.chaegwon import SHEET_NAME as CHAEGWON_SHEET_NAME

COLUMN_HEADERS = ["종목명", "종류", "코스콤대분류", "발행률", "만기일", "액면", "장부가액", "시가액"]


def _make_row_writer(source_row: int):
    s = CHAEGWON_SHEET_NAME

    def writer(ws, row: int) -> None:
        ws.cell(row, 3, f"={s}!C{source_row}")
        ws.cell(row, 4, f"={s}!F{source_row}")
        ws.cell(row, 5, f"={s}!G{source_row}")
        ws.cell(row, 6, f"={s}!H{source_row}/100")
        ws.cell(row, 7, f"={s}!Q{source_row}")
        ws.cell(row, 8, f"={s}!N{source_row}")
        ws.cell(row, 9, f"={s}!T{source_row}-{s}!AA{source_row}-{s}!AE{source_row}")
        ws.cell(row, 10, f"={s}!U{source_row}-{s}!AA{source_row}-{s}!AE{source_row}")

    return writer


def build(
    ws, start_row: int, chaegwon_df, section_number: int, summary_row: int | None = None
) -> dict:
    row_writers = [
        _make_row_writer(CHAEGWON_FIRST_DATA_ROW + i) for i in range(len(chaegwon_df))
    ]
    header_text = f"{section_number}. 채권"
    return write_block(
        ws,
        start_row,
        header_text,
        COLUMN_HEADERS,
        row_writers,
        total_cols=["H", "I", "J"],
        hidden=not row_writers,
        summary_row=summary_row,
    )
