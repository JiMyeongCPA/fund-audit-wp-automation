"""수익증권명세 PBC CSV -> workpaper sheet.

Same layout as 국내유동명세/국내주식명세/펀드별명세: row 1 blank, header row 2,
data from row 3. No row filtering needed -- this fund holds exactly one
수익증권 (종목ETF001), matching the raw CSV's single row 1:1.

Note: 'C2_자산부채평가'의 "(2) 코스닥주식" 섹션도 이 시트의 훨씬 아래쪽
(rows 38-80)을 참조하지만, 이 펀드는 그 범위에 해당하는 데이터가 없어서
원본 파일에서도 이미 전부 0으로 나온다 -- 이 시트를 원본 그대로(구조 그대로)
재현하면 그 부분도 자동으로 똑같이 재현된다."""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "수익증권명세"
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
