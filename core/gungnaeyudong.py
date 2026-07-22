"""국내유동명세 PBC CSV -> workpaper sheet.

Unlike 기준가격대장, this raw PBC file has no placeholder row and no column
reordering quirk -- its own header row is row 1, and every column lines up
1:1 with what 'C2_자산부채평가' expects. Column letters carry the header's
trailing whitespace exactly as the source file has it; that's harmless since
'C2_자산부채평가' references data by column letter (e.g. SUMIF against $C:$C,
$K:$K), never by header text.

Data must start at row 3 (header on row 2, row 1 left blank) -- this is
load-bearing: 'C2_자산부채평가' (copied verbatim from the reference
workpaper) has formulas hardcoded to this sheet's specific rows (e.g.
`=국내유동명세!E3`, `=국내유동명세!AG4`, `=국내유동명세!C5`), matching the
reference file's own layout.
"""
from __future__ import annotations

import pandas as pd

SHEET_NAME = "국내유동명세"
HEADER_ROW = 2
FIRST_DATA_ROW = 3


def parse(path: str, encoding: str = "cp949") -> pd.DataFrame:
    return pd.read_csv(path, encoding=encoding)


def create_sheet(wb, df: pd.DataFrame):
    """Create a fresh '국내유동명세' sheet in `wb` and fill it with `df`.
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
