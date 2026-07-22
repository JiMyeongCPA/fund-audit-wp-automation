"""C5_F.N > "12. 담보제공자산" (당기말) -- which of the fund's stock/ETF
holdings are pledged as collateral. No PBC source exists for this (no
대용현황/담보 내역 file in this project's fixtures), so only the structure
(title/caption/header) is built; the data rows stay empty. This note's
"needs review" status is surfaced by the future React review UI (from the
NEEDS_REVIEW list this module exposes), not written into the Excel file
itself -- the workpaper should look like a normal, unfinished note, not one
with review chrome baked into the cells.
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, box_border, run_left_rule, style_header_row, style_total_row

NEEDS_REVIEW = True
NEEDS_REVIEW_REASON = "담보제공자산: 원본 자료(대용현황 등)가 없어 자동 산출 불가"

_BOLD = BOLD


def build(ws, start_row: int) -> int:
    r = start_row

    ws.cell(r, 3, "12. 담보제공자산").font = _BOLD
    ws.cell(r + 2, 3, "당기말 현재 투자신탁이 보유하고 있는 유가증권 중 담보로 제공되어 있는 내역은 다음과 같습니다.")
    ws.cell(r + 4, 3, "(당기말)").font = _BOLD

    header_row = r + 5
    for col, label in zip("CDEF", ["구분", "종목", "담보제공 수량", "담보제공 장부가액"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 6)

    # 3 blank buffer rows before 합계 (c2_blocks.BUFFER_ROWS convention),
    # same "table shape built even with no data" treatment as
    # c5_wonbon_note's 종류별 발행좌수 table.
    total_row = header_row + 1 + BUFFER_ROWS
    for row in range(header_row + 1, total_row):
        for col in range(3, 7):
            ws.cell(row, col).border = box_border(col == 3)
    ws.cell(total_row, 3, "합계")
    style_total_row(ws, total_row, 3, 6)

    run_left_rule(ws, start_row, total_row)

    return total_row + 2
