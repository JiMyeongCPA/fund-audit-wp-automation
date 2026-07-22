"""C5_F.N > "1. 지분증권" (당기말만) -- mechanical restatement of every
domestic stock holding, referencing C2_자산부채평가's own stock detail block
directly (already fully wired/tested there). Row position is read off the
built C2 sheet at call time (`c2_stock_first_row`) rather than hardcoded,
since C2's block sizing is dynamic -- unlike the real file's own hardcoded
absolute rows, which would silently point at the wrong cells once any
earlier C2 block's size changes.

코스닥주식 sub-group and 전기말 are both skipped: verified (same as C2's own
finding) that this fund has zero 코스닥 holdings and zero prior-period stock
holdings -- the real file carries ~285 blank template rows for 코스닥 alone,
pure dead capacity for a group this fund doesn't use, and no PBC source
exists to reconstruct last year's stock-by-stock holdings.

One rounding quirk fixed: the real file's 결산전 장부금액 (E) column uses
`ROUND(x/1000,0) - IF(MOD(x,1000)=500,1,0)` (round exact .5-thousand
remainders down instead of up) for every stock row except the very first
one, which is missing the adjustment -- a copy-paste gap, not an
intentional exception. Applied uniformly here.

Row capacity: N real stock rows + 3 blank buffer rows before 합계, same
convention as c2_blocks.BUFFER_ROWS -- next period's stock count growing or
shrinking doesn't require rebuilding this block by hand.
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, box_border, run_left_rule, style_header_row, style_total_row

C2_SHEET_NAME = "C2_자산부채평가"
AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"
RATIO_FMT = "0.00%"
_BOLD = BOLD


def build(ws, c2_stock_first_row: int, num_stocks: int, start_row: int = 64) -> int:
    c2 = C2_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 지분증권").font = _BOLD
    ws.cell(r + 1, 3, "당기말 현재 지분증권의 내역은 다음과 같습니다")
    ws.cell(r + 3, 3, "<당기말>").font = _BOLD

    header_row = r + 4
    for col, label in zip("CDEFGH", ["종목", "수량(주)", "결산전 장부금액", "결산후 장부금액", "평가손익", "구성비"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 8)

    subcaption_row = header_row + 1
    ws.cell(subcaption_row, 3, "<유가증권시장주식>")

    first_data_row = header_row + 2
    total_row = first_data_row + num_stocks + BUFFER_ROWS
    for i in range(num_stocks):
        row = first_data_row + i
        c2_row = c2_stock_first_row + i
        ws.cell(row, 3, f"='{c2}'!C{c2_row}")
        ws.cell(row, 4, f"='{c2}'!D{c2_row}")
        ws.cell(row, 5, f"=ROUND('{c2}'!E{c2_row}/1000,0)-IF(MOD('{c2}'!E{c2_row},1000)=500,1,0)")
        ws.cell(row, 6, f"=ROUND('{c2}'!F{c2_row}/1000,0)")
        ws.cell(row, 7, f"=F{row}-E{row}")
        ws.cell(row, 8, f"=F{row}/$F${total_row}")
        for col in (5, 6, 7):
            ws.cell(row, col).number_format = AMOUNT_FMT
        ws.cell(row, 8).number_format = RATIO_FMT

    for row in range(first_data_row, total_row):
        for col in range(3, 9):
            ws.cell(row, col).border = box_border(col == 3)

    ws.cell(total_row, 3, "합계")
    for col_letter in "EFG":
        ws.cell(total_row, ord(col_letter) - ord("A") + 1, f"=SUM({col_letter}{first_data_row}:{col_letter}{total_row - 1})")
        ws.cell(total_row, ord(col_letter) - ord("A") + 1).number_format = AMOUNT_FMT
    ws.cell(total_row, 8, f"=SUM(H{first_data_row}:H{total_row - 1})")
    ws.cell(total_row, 8).number_format = RATIO_FMT
    style_total_row(ws, total_row, 3, 8)
    run_left_rule(ws, start_row, total_row)

    return total_row + 2
