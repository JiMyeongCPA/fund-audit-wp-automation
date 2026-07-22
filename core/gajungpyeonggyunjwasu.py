"""가중평균좌수 PBC CSV -> workpaper sheet.

The raw PBC file (샘플펀드_일별좌수순자산현황) is a daily 기준일/좌수/순자산/
과세순자산 series for the whole year -- verified to match the reference
workpaper's '가중평균좌수' sheet exactly (365 rows, same values).

Unlike every other detail sheet in this project, column A is left entirely
blank and data starts at column B -- verified directly against the real
file, not assumed.

Data must start at row 3 (header on row 2, row 1 left blank): 'C1_정산표'
(copied verbatim from the reference workpaper) sums this sheet's 좌수 column
over `가중평균좌수!C3:C368` to compute "1좌당 당기순이익(손실)" (row 121),
so both the starting row and the column offset are load-bearing.
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "가중평균좌수"
HEADER_ROW = 2
FIRST_DATA_ROW = 3
FIRST_COL = 2  # column A intentionally left blank


def parse(path: str, encoding: str = "cp949") -> pd.DataFrame:
    return pd.read_csv(path, encoding=encoding)


def create_sheet(wb, df: pd.DataFrame):
    ws = wb.create_sheet(SHEET_NAME)
    for i, col_name in enumerate(df.columns):
        ws.cell(HEADER_ROW, FIRST_COL + i, col_name)
    for i, record in enumerate(df.itertuples(index=False)):
        row = FIRST_DATA_ROW + i
        for j, value in enumerate(record):
            if pd.isna(value):
                continue
            ws.cell(row, FIRST_COL + j, value)
    return ws
