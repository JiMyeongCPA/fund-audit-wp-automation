"""펀드별명세 PBC CSV -> workpaper sheet.

Unlike 국내주식명세, no rows need filtering here -- the raw CSV's 213 rows
line up 1:1, in order, with the reference workpaper's '펀드별명세' sheet.
'C2_자산부채평가' references this sheet at rows 360-389, well past this
fund's real data (which ends at row 215); those cells are already blank/0 in
the original file, so they don't need anything special here either.

Data must start at row 3 (header on row 2, row 1 left blank), matching the
reference layout other sheets in this project already follow.
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "펀드별명세"
HEADER_ROW = 2
FIRST_DATA_ROW = 3


def parse(path: str, encoding: str = "cp949") -> pd.DataFrame:
    return pd.read_csv(path, encoding=encoding)


def create_sheet(wb, df: pd.DataFrame):
    """Create a fresh '펀드별명세' sheet in `wb` and fill it with `df`.
    Row 1 is intentionally left blank; the header goes on row 2 and data
    starts on row 3."""
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
