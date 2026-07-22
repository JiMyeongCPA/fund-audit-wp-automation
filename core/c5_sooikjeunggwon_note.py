"""C5_F.N > "1. 수익증권" (당기말만) -- mechanical restatement of the fund's
collective-investment-security (ETF) holding(s), referencing
C2_자산부채평가's own 수익증권 block directly. Same reasoning as
c5_chaegwon_note/c5_jibun_note: row range read off the built C2 sheet, not
hardcoded, and 전기말 skipped (no PBC source for last year's holdings).

Row capacity: N real holding rows + 3 blank buffer rows before 합계, same
c2_blocks.BUFFER_ROWS convention as c5_jibun_note.
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, box_border, left_rule, run_left_rule, style_header_row, style_total_row

C2_SHEET_NAME = "C2_자산부채평가"
AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"
_BOLD = BOLD


def build(ws, c2_sooikjeunggwon_first_row: int, num_holdings: int, start_row: int) -> int:
    c2 = C2_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 수익증권").font = _BOLD
    ws.cell(r + 2, 3, "당기말 현재 수익증권의 내역은 다음과 같습니다.")
    left_rule(ws, r)
    for row in (r + 1, r + 2):
        left_rule(ws, row)
    ws.cell(r + 4, 3, "<당기말>").font = _BOLD
    left_rule(ws, r + 3)
    left_rule(ws, r + 4)

    header_row = r + 5
    for col, label in zip("CDEFG", ["종목", "좌수(좌)", "결산전 장부금액", "결산후 장부금액", "평가손익"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 7)

    first_data_row = header_row + 1
    total_row = first_data_row + num_holdings + BUFFER_ROWS
    for i in range(num_holdings):
        row = first_data_row + i
        c2_row = c2_sooikjeunggwon_first_row + i
        ws.cell(row, 3, f"='{c2}'!C{c2_row}")
        ws.cell(row, 4, f"='{c2}'!D{c2_row}")
        ws.cell(row, 5, f"=ROUND('{c2}'!E{c2_row}/1000,0)")
        ws.cell(row, 6, f"=ROUND('{c2}'!F{c2_row}/1000,0)")
        ws.cell(row, 7, f"=F{row}-E{row}")
        for col in (5, 6, 7):
            ws.cell(row, col).number_format = AMOUNT_FMT

    for row in range(first_data_row, total_row):
        for col in range(3, 8):
            ws.cell(row, col).border = box_border(col == 3)

    ws.cell(total_row, 3, "합계")
    for col_letter in "EFG":
        ws.cell(total_row, ord(col_letter) - ord("A") + 1, f"=SUM({col_letter}{first_data_row}:{col_letter}{total_row - 1})")
        ws.cell(total_row, ord(col_letter) - ord("A") + 1).number_format = AMOUNT_FMT
    style_total_row(ws, total_row, 3, 7)
    run_left_rule(ws, start_row, total_row)

    return total_row + 2
