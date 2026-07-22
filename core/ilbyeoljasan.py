"""일별자산내역 PBC CSV -> workpaper sheet.

Header directly on row 1, data starts row 2 (no blank row 1) -- verified
against the real file. This is the daily asset-balance series that C3_수익's
평균잔액 (average balance) calculations average over the whole year.
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "일별자산내역"
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
