"""요약표 (rows 1-34) for C2_자산부채평가: a title block (Prepared/Reviewed
by) plus a "구분/B.S/명세서/차액" table, one row per asset category.

The C/D/F/G columns (label, 당기 B/S value, 차액, 소계) are copied verbatim
from the reference workpaper -- they don't depend on how many rows any
detail block below ends up needing. Only the E column ("명세서" -- each
category's total, read off the matching detail block) gets rewritten, since
those detail blocks are now built fresh each run instead of living at fixed
rows. Categories whose detail block hasn't been built yet keep a literal 0
rather than a dangling reference to a block that doesn't exist.
"""
from __future__ import annotations

from core.sheet_copy import copy_row_range

FIRST_ROW = 1
LAST_ROW = 34

ROW_FOR_CATEGORY = {
    "예금": 13,
    "위탁증거금": 15,
    "현금담보증거금": 16,
    "콜론": 17,
    "REPO매수": 18,
    "매입어음": 19,
    "전자단기사채": 20,
    "국채": 21,
    "특수채": 22,
    "통안채": 23,
    "회사채": 24,
    "거래소주식": 25,
    "코스닥주식": 26,
    "수익증권": 27,
    "선물미수입금": 28,
    "선물미지급금": 29,
    "옵션매수": 30,
    "옵션매도": 31,
    "매도유가증권": 32,
    "REPO매도": 33,
}
BOND_CATEGORIES = {"국채", "특수채", "통안채", "회사채"}


def build(ws, ref_ws, block_results: dict, total_col_letter: dict | None = None) -> None:
    """`block_results` maps category name -> the dict returned by a block
    builder (`c2_blocks.write_block` or a wrapper around it). `total_col_letter`
    maps the same category names to which column letter holds that block's
    total (e.g. "F"), needed because different block layouts put their total
    in different columns; bond categories (국채/특수채/통안채/회사채, which
    share one 채권 block and use a SUMIF instead of a single total cell)
    don't need an entry. Any category not present in `block_results` is left
    at its literal-0 placeholder.
    """
    total_col_letter = total_col_letter or {}
    copy_row_range(ref_ws, ws, FIRST_ROW, LAST_ROW)

    for category, row in ROW_FOR_CATEGORY.items():
        if category not in block_results:
            ws.cell(row, 5, 0)
            continue

        result = block_results[category]
        if category in BOND_CATEGORIES:
            first, last = result["first_data_row"], result["last_data_row"]
            ws.cell(row, 5, f"=SUMIF($E${first}:$E${last},C{row},$J${first}:$J${last})")
        else:
            col_letter = total_col_letter[category]
            ws.cell(row, 5, f"={col_letter}{result['total_row']}")
