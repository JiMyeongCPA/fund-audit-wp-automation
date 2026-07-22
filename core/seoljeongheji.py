"""설정해지내역 PBC CSV -> workpaper sheet.

Row 1 blank, header row 2, data starts row 3 -- same layout as
국내유동명세/국내주식명세/펀드별명세 etc. This is the 자펀드 (sub-fund)
area's underlying daily 설정/해지 series; still only a raw dump here (no
computed sheet consumes it yet -- the multi-sub-fund C1_정산표 formulas
that reference it were already deferred earlier for lack of real
multi-sub-fund example data).
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "설정해지내역"
HEADER_ROW = 2
FIRST_DATA_ROW = 3


def parse(path: str, encoding: str = "cp949") -> pd.DataFrame:
    return pd.read_csv(path, encoding=encoding)


def create_sheet(wb, df: pd.DataFrame):
    ws = wb.create_sheet(SHEET_NAME)
    for col_idx, col_name in enumerate(df.columns, start=1):
        ws.cell(HEADER_ROW, col_idx, col_name)
    for i, record in enumerate(df.itertuples(index=False)):
        row = FIRST_DATA_ROW + i
        for col_idx, value in enumerate(record, start=1):
            if pd.isna(value):
                continue
            ws.cell(row, col_idx, value)
    return ws
