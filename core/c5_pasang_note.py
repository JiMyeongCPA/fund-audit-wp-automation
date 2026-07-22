"""C5_F.N > "1. 파생상품" (당기말, KOSPI 200 선물만) -- mechanical
restatement of each counterparty's futures position, referencing '선물명세'
directly (already a stable, PBC-built sheet -- not routed through C2, since
the real file's own note references 선물명세 directly too).

Scope: only the "KOSPI 200 선물" 부채 sub-table is built (5 real
counterparty rows). The real file also carries an "자산" sub-group and a
duplicate-looking "주가지수선물" template group, both entirely zero for this
fund (no 자산-side futures, no separate 주가지수선물 position) -- same
"genuinely inapplicable, not a gap" reasoning as 코스닥주식/외화위탁증거금
elsewhere. 전기말 also skipped: no PBC source for last year's futures book.

Rounding quirk fixed: the real file hand-patches 2 of the 5 rows (`+1`)
so the column foots correctly under independent per-row rounding -- same
"footing plug" issue as c5_bosu_note's -1 patch. Fixed the same way: the
last row absorbs the rounding residual via a formula instead of two
hardcoded +1s on arbitrary rows.

Row capacity: N real contract rows + 3 blank buffer rows before 합계, same
c2_blocks.BUFFER_ROWS convention as c5_jibun_note.
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, box_border, left_rule, run_left_rule, style_header_row, style_total_row

SEONMUL_SHEET_NAME = "선물명세"
SEONMUL_FIRST_DATA_ROW = 3
AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"
_BOLD = BOLD


def build(ws, num_contracts: int, start_row: int) -> int:
    sm = SEONMUL_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 파생상품").font = _BOLD
    ws.cell(r + 1, 3, "당기말 현재 파생상품의 내역은 다음과 같습니다.")
    left_rule(ws, r)
    left_rule(ws, r + 1)
    ws.cell(r + 3, 3, "<당기말>").font = _BOLD
    left_rule(ws, r + 3)

    header_row = r + 4
    headers = ["종류", "수량(계약)", "매매구분", "미결제약정금액", "계", "정산평가손익", "미정산평가손익", "장내외구분"]
    for col, label in zip("CDEFGHIJ", headers):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 10)

    ws.cell(header_row + 1, 3, "<KOSPI 200 선물>")
    left_rule(ws, header_row + 1)

    first_data_row = header_row + 2
    total_row = first_data_row + num_contracts + BUFFER_ROWS
    for i in range(num_contracts):
        row = first_data_row + i
        src_row = SEONMUL_FIRST_DATA_ROW + i
        ws.cell(row, 3, f"='{sm}'!E{src_row}")
        ws.cell(row, 4, f"='{sm}'!G{src_row}")
        ws.cell(row, 5, f"='{sm}'!F{src_row}")
        ws.cell(row, 6, f"=ROUND('{sm}'!J{src_row}/1000,0)")
        ws.cell(row, 7, f"=ROUND('{sm}'!K{src_row}/1000,0)")
        ws.cell(row, 8, f"=ROUND(('{sm}'!K{src_row}-('{sm}'!L{src_row}-'{sm}'!M{src_row}))/1000,0)")
        if i < num_contracts - 1:
            ws.cell(row, 9, f"=ROUND(('{sm}'!L{src_row}-'{sm}'!M{src_row})/1000,0)")
        else:
            # plug row: absorbs the rounding residual so G842-style totals
            # foot exactly, instead of hand-patching arbitrary rows with +1.
            prev_rows = range(first_data_row, row)
            raw_total = f"SUM('{sm}'!L{SEONMUL_FIRST_DATA_ROW}:L{SEONMUL_FIRST_DATA_ROW + num_contracts - 1})-SUM('{sm}'!M{SEONMUL_FIRST_DATA_ROW}:M{SEONMUL_FIRST_DATA_ROW + num_contracts - 1})"
            ws.cell(row, 9, f"=ROUND({raw_total}/1000,0)-SUM(I{prev_rows.start}:I{prev_rows.stop - 1})")
        ws.cell(row, 10, "장내")
        for col in (6, 7, 8, 9):
            ws.cell(row, col).number_format = AMOUNT_FMT

    for row in range(first_data_row, total_row):
        for col in range(3, 11):
            ws.cell(row, col).border = box_border(col == 3)

    ws.cell(total_row, 3, "KOSPI 200 선물 합계")
    for col_letter in "DGHI":
        col_idx = ord(col_letter) - ord("A") + 1
        ws.cell(total_row, col_idx, f"=SUM({col_letter}{first_data_row}:{col_letter}{total_row - 1})")
    for col in (7, 8, 9):
        ws.cell(total_row, col).number_format = AMOUNT_FMT
    style_total_row(ws, total_row, 3, 10)
    run_left_rule(ws, start_row, total_row)

    return total_row + 2
