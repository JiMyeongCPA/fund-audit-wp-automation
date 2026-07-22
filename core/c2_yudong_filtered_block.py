"""Generic "국내유동명세, filtered by 유동종류" block builder for
C2_자산부채평가.

Covers 예금, 콜론, REPO(매수), 매입어음, 전자단기사채, REPO(매도) -- all
built the exact same way, just with a different 유동종류 filter value and
header text. Column mapping into 국내유동명세 (verified against the real
formulas): E=발행률, K=수량, Q=취득원가, R=장부가평가액, S=시가평가금액.
"""
from __future__ import annotations

from core.c2_blocks import write_block
from core.gungnaeyudong import FIRST_DATA_ROW as YUDONG_FIRST_DATA_ROW
from core.gungnaeyudong import SHEET_NAME as YUDONG_SHEET_NAME

COLUMN_HEADERS = ["종목명", "발행률", "수량", "취득원가", "장부가평가액", "시가평가금액"]
KIND_COL_IDX = 3  # 0-indexed: 유동종류
NAME_COL_IDX = 2  # 0-indexed: 종목명


def _make_row_writer(name: str, source_row: int):
    s = YUDONG_SHEET_NAME

    def writer(ws, row: int) -> None:
        ws.cell(row, 3, name)
        ws.cell(row, 4, f"={s}!E{source_row}")
        ws.cell(row, 5, f"=SUMIF({s}!$C:$C,C{row},{s}!$K:$K)")
        ws.cell(row, 6, f"=SUMIF({s}!$C:$C,C{row},{s}!$Q:$Q)")
        ws.cell(row, 7, f"=SUMIF({s}!$C:$C,C{row},{s}!$R:$R)")
        ws.cell(row, 8, f"=SUMIF({s}!$C:$C,C{row},{s}!$S:$S)")

    return writer


def build(
    ws,
    start_row: int,
    gungnaeyudong_df,
    header_text: str,
    kind_value: str,
    summary_row: int | None = None,
) -> dict:
    kind_col = gungnaeyudong_df.columns[KIND_COL_IDX]
    name_col = gungnaeyudong_df.columns[NAME_COL_IDX]

    row_writers = []
    for i, kind in enumerate(gungnaeyudong_df[kind_col]):
        if str(kind).strip() == kind_value:
            source_row = YUDONG_FIRST_DATA_ROW + i
            row_writers.append(_make_row_writer(gungnaeyudong_df.iloc[i][name_col], source_row))

    return write_block(
        ws,
        start_row,
        header_text,
        COLUMN_HEADERS,
        row_writers,
        total_cols=["F", "G", "H"],
        hidden=not row_writers,
        summary_row=summary_row,
    )
