"""채권명세 PBC CSV -> workpaper sheet.

Unlike every other detail sheet in this project, there's no blank row 1 here
-- the reference workpaper's '채권명세' sheet has its header directly on row
1 and data starting row 2. Verified directly against the real file; not
assumed by analogy with the other sheets.

No row filtering needed -- this fund holds exactly one bond
(국고채권01125-3909), matching the raw CSV's single row 1:1.
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "채권명세"
HEADER_ROW = 1
FIRST_DATA_ROW = 2


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
