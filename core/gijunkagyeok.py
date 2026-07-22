"""기준가격대장(결산후) PBC CSV -> workpaper sheet.

The raw PBC file has a placeholder row, then its own header row, then data.
Column order in the raw file (전기말잔액, 당기증감액, 당기말잔액, 코드, 계정명,
전기말잔액, 당기증감액, 당기말잔액) does not match its own header text once
pasted into the sheet -- the sheet's 코드/당일잔액/... labels are just the
same 8 columns, position for position; only the header text differs.

계정코드 must be written as a number, not text: '통합기준가격대장(결산후)'
VLOOKUPs this column against its own numeric account-code list, and
VLOOKUP's exact-match mode treats "100000" and 100000 as unequal, silently
falling back to its IFERROR default of 0.
"""
from __future__ import annotations

import csv

import pandas as pd

COLUMNS = [
    "코드",
    "당일잔액_차변",
    "당일증감액_차변",
    "전일잔액_차변",
    "계정명",
    "전일잔액_대변",
    "당일증감액_대변",
    "당일잔액_대변",
]


def _read_raw_rows(path: str, encoding: str = "cp949") -> list[list[str]]:
    with open(path, "r", encoding=encoding, newline="") as f:
        return list(csv.reader(f))


def _find_header_row(
    rows: list[list[str]],
    required: tuple[str, ...] = ("코드", "계정명"),
    search_limit: int = 10,
) -> int:
    for i, row in enumerate(rows[:search_limit]):
        cells = [c.strip() for c in row]
        if all(any(req in c for c in cells) for req in required):
            return i
    raise ValueError(
        f"Header row containing all of {required} not found in the first {search_limit} rows"
    )


def _to_number(text: str) -> float:
    text = text.strip()
    return float(text) if text else 0.0


def parse(path: str, encoding: str = "cp949") -> pd.DataFrame:
    """Parse a 기준가격대장(결산전/후) PBC CSV into the 8-column layout the
    '기준가격대장(결산후)' sheet expects, one row per account code."""
    rows = _read_raw_rows(path, encoding)
    header_idx = _find_header_row(rows)
    data_rows = [r for r in rows[header_idx + 1 :] if any(cell.strip() for cell in r)]

    records = []
    for row in data_rows:
        if len(row) < 8:
            continue
        col1, col2, col3, code, name, col6, col7, col8 = row[:8]
        records.append(
            {
                "코드": int(code.strip()),
                "당일잔액_차변": _to_number(col1),
                "당일증감액_차변": _to_number(col2),
                "전일잔액_차변": _to_number(col3),
                "계정명": name.strip(),
                "전일잔액_대변": _to_number(col6),
                "당일증감액_대변": _to_number(col7),
                "당일잔액_대변": _to_number(col8),
            }
        )
    return pd.DataFrame.from_records(records, columns=COLUMNS)


SHEET_NAME = "기준가격대장(결산후)"
FIRST_DATA_ROW = 4

_HEADER_LABELS = ["코드", "당일잔액", "당일증감액", "전일잔액", "계정명", "전일잔액", "당일증감액", "당일잔액"]


def create_sheet(wb, df: pd.DataFrame):
    """Create a fresh '기준가격대장(결산후)' sheet in `wb` and fill it with
    `df`. Data starts at row `FIRST_DATA_ROW` (row 4) -- this is load-bearing:
    '통합기준가격대장(결산후)' (copied verbatim from the reference workpaper)
    has VLOOKUP formulas hardcoded to read this sheet's $A$4:$H$500, so the
    header layout above row 4 can be whatever's clearest, but the data itself
    must start on row 4.
    """
    ws = wb.create_sheet(SHEET_NAME)
    ws["C2"] = "차변"
    ws["G2"] = "대변"
    for col_idx, label in enumerate(_HEADER_LABELS, start=1):
        ws.cell(3, col_idx, label)
    for i, record in enumerate(df.itertuples(index=False)):
        row = FIRST_DATA_ROW + i
        for col_idx, value in enumerate(record, start=1):
            ws.cell(row, col_idx, value)
    return ws


def write_to_workbook(wb, df: pd.DataFrame) -> None:
    """Write parsed 기준가격대장(결산후) rows into `wb`'s sheet, replacing
    whatever was there before (blanking any leftover rows if the new data is
    shorter than the old)."""
    ws = wb[SHEET_NAME]

    last_existing = FIRST_DATA_ROW - 1
    r = FIRST_DATA_ROW
    while ws.cell(r, 1).value not in (None, "") or ws.cell(r, 5).value not in (None, ""):
        last_existing = r
        r += 1

    clear_through = max(last_existing, FIRST_DATA_ROW + len(df) - 1)
    for row in range(FIRST_DATA_ROW, clear_through + 1):
        for col in range(1, len(COLUMNS) + 1):
            ws.cell(row, col).value = None

    for i, record in enumerate(df.itertuples(index=False)):
        target_row = FIRST_DATA_ROW + i
        for col_idx, value in enumerate(record, start=1):
            ws.cell(target_row, col_idx).value = value


MASTER_SHEET_NAME = "통합기준가격대장(결산후)"
MASTER_CODE_COL = 5  # E열
MASTER_FIRST_ROW = 6


def find_missing_account_codes(wb, df: pd.DataFrame) -> list[dict]:
    """Compare the account codes just parsed from PBC against
    '통합기준가격대장(결산후)'의 E열 계정코드 목록. Returns one entry per
    code that exists in the new PBC data but not in that master list --
    those accounts won't be picked up anywhere downstream (their VLOOKUP
    falls through to 0), so they need a person to add a row for them.
    This is deliberately detection-only: where in the master list's
    sectioned layout a new row belongs, and which section-total range needs
    extending, is a judgment call this doesn't attempt to make.
    """
    ws = wb[MASTER_SHEET_NAME]
    known_codes = set()
    r = MASTER_FIRST_ROW
    while ws.cell(r, MASTER_CODE_COL).value not in (None, ""):
        known_codes.add(ws.cell(r, MASTER_CODE_COL).value)
        r += 1

    missing = []
    for record in df.itertuples(index=False):
        code, name = record[0], record[4]
        if code not in known_codes:
            missing.append({"코드": code, "계정명": name})
    return missing
