"""C5_F.N > "1. 채무증권" (당기말만) -- mechanical restatement of the
fund's bond holding(s), referencing C2_자산부채평가's own bond block
directly (already fully wired/tested there). Row range read off the built
C2 sheet at call time, same reasoning as c5_jibun_note (C2's block
positions are dynamic, so a hardcoded absolute row would be fragile).

전기말 skipped: no PBC source for last year's bond holdings, same as
지분증권's 전기말.

Row capacity: N real bond rows + 3 blank buffer rows before 합계, same
c2_blocks.BUFFER_ROWS convention as c5_jibun_note.
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, box_border, left_rule, run_left_rule, style_header_row, style_total_row

C2_SHEET_NAME = "C2_자산부채평가"
AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"
_BOLD = BOLD


def build(ws, c2_bond_first_row: int, num_bonds: int, start_row: int) -> int:
    c2 = C2_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 채무증권").font = _BOLD
    ws.cell(r + 1, 3, "당기말 현재 채무증권의 내역은 다음과 같습니다")
    left_rule(ws, r)
    left_rule(ws, r + 1)
    ws.cell(r + 3, 3, "<당기말>").font = _BOLD
    left_rule(ws, r + 3)
    ws.cell(r + 4, 3, "가. 원화채무증권")
    left_rule(ws, r + 4)

    header_row = r + 5
    for col, label in zip("CDEFGH", ["종목", "액면금액", "결산전 장부금액", "결산후 장부금액", "평가손익", "만기일"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 8)

    first_data_row = header_row + 1
    total_row = first_data_row + num_bonds + BUFFER_ROWS
    for i in range(num_bonds):
        row = first_data_row + i
        c2_row = c2_bond_first_row + i
        ws.cell(row, 3, f"='{c2}'!C{c2_row}")
        ws.cell(row, 4, f"=ROUND('{c2}'!H{c2_row}/1000,0)")
        ws.cell(row, 5, f"=ROUND('{c2}'!I{c2_row}/1000,0)")
        ws.cell(row, 6, f"=ROUND('{c2}'!J{c2_row}/1000,0)")
        ws.cell(row, 7, f"=F{row}-E{row}")
        ws.cell(row, 8, f"='{c2}'!G{c2_row}")
        ws.cell(row, 8).number_format = "yyyy.mm.dd"
        for col in (4, 5, 6, 7):
            ws.cell(row, col).number_format = AMOUNT_FMT

    for row in range(first_data_row, total_row):
        for col in range(3, 9):
            ws.cell(row, col).border = box_border(col == 3)

    ws.cell(total_row, 3, "합계")
    for col_letter in "DEF":
        ws.cell(total_row, ord(col_letter) - ord("A") + 1, f"=SUM({col_letter}{first_data_row}:{col_letter}{total_row - 1})")
        ws.cell(total_row, ord(col_letter) - ord("A") + 1).number_format = AMOUNT_FMT
    style_total_row(ws, total_row, 3, 8)
    run_left_rule(ws, start_row, total_row)

    return total_row + 2
