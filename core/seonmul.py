"""선물명세 PBC CSV -> workpaper sheet.

Same layout as 국내유동명세/국내주식명세/펀드별명세: row 1 blank, header row 2,
data from row 3. No row filtering needed -- all 5 raw rows (5 counterparties
each holding the same futures contract) match the reference sheet 1:1.

The first column's raw values carry a literal leading tab character (e.g.
'\\t000012') -- that's what keeps pandas from reading 매매처 codes as numbers
and stripping their leading zeros; it needs no special handling here since
it's just part of the string value itself.
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "선물명세"
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
