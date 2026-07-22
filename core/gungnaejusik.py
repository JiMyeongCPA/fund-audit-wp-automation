"""국내주식명세 PBC CSV -> workpaper sheet.

The raw PBC file includes rows for stocks the fund no longer holds any
shares of (수량 == 0, a fully liquidated position lingering in the export).
The reference workpaper's own '국내주식명세' sheet drops exactly these rows
-- verified against the real file: of 206 raw rows, the 2 with 수량 == 0
('현대건설우[유상]', 'KR700072100A' and another) are absent from the sheet,
while the remaining 204 appear in the same order. So this parser filters
them out too; not just for tidiness, but because 'C2_자산부채평가' (copied
verbatim from the reference workpaper) references this sheet by direct row
position, not by lookup (e.g. `=국내주식명세!B3`, `=국내주식명세!D3` for its
own row 101) -- keeping a zero-quantity row would shift every row after it
out of alignment with those hardcoded references.

Data must start at row 3 (header on row 2, row 1 left blank), matching
C2's hardcoded row offset (국내주식명세 row N -> C2 row N+98).
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "국내주식명세"
HEADER_ROW = 2
FIRST_DATA_ROW = 3
QUANTITY_COL = 3  # 0-indexed position of 수량 in the raw CSV


def parse(path: str, encoding: str = "cp949") -> pd.DataFrame:
    df = pd.read_csv(path, encoding=encoding)
    quantity_col = df.columns[QUANTITY_COL]
    return df[df[quantity_col] != 0].reset_index(drop=True)


def create_sheet(wb, df: pd.DataFrame):
    """Create a fresh '국내주식명세' sheet in `wb` and fill it with `df`.
    Row 1 is intentionally left blank; the header goes on row 2 and data
    starts on row 3, matching 'C2_자산부채평가'의 하드코딩된 행 참조."""
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
