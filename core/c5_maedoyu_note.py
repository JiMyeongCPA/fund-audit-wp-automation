"""C5_F.N > "1. 매도유가증권" (당기말, [채권]만) -- securities lent out
under a securities-lending agreement (대차거래), referencing
C2_자산부채평가's own bond block directly -- same bond, same row source as
c5_chaegwon_note (this fund's single 국고채권 holding is both "held" and
"lent out" at once).

[주식] sub-section (stock lending) skipped: verified 0 for this fund, no
PBC-driven stock-lending activity this period, same "genuinely
inapplicable" reasoning as other empty categories. 전기말 skipped: no PBC
source for last year's securities-lending book.

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

    ws.cell(r, 3, "1. 매도유가증권").font = _BOLD
    ws.cell(r + 1, 3, "신탁계약 제18조에 따라 차입하여 대차거래한 채무증권으로써 당기말 현재 매도유가증권의 내역은 다음과 같습니다.")
    left_rule(ws, r)
    left_rule(ws, r + 1)
    ws.cell(r + 3, 3, "[채권]").font = _BOLD
    ws.cell(r + 4, 3, "<당기말>").font = _BOLD
    left_rule(ws, r + 3)
    left_rule(ws, r + 4)

    header_row = r + 5
    for col, label in zip("CDEF", ["종목", "수량(좌)", "액면가", "장부금액"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 6)

    first_data_row = header_row + 1
    total_row = first_data_row + num_bonds + BUFFER_ROWS
    for i in range(num_bonds):
        row = first_data_row + i
        c2_row = c2_bond_first_row + i
        ws.cell(row, 3, f"='{c2}'!C{c2_row}")
        ws.cell(row, 5, f"=ROUND('{c2}'!H{c2_row}/1000,0)")
        ws.cell(row, 6, f"=ROUND('{c2}'!J{c2_row}/1000,0)")
        for col in (5, 6):
            ws.cell(row, col).number_format = AMOUNT_FMT

    for row in range(first_data_row, total_row):
        for col in range(3, 7):
            ws.cell(row, col).border = box_border(col == 3)

    ws.cell(total_row, 3, "합계")
    ws.cell(total_row, 6, f"=SUM(F{first_data_row}:F{total_row - 1})")
    ws.cell(total_row, 6).number_format = AMOUNT_FMT
    style_total_row(ws, total_row, 3, 6)
    run_left_rule(ws, start_row, total_row)

    return total_row + 2
