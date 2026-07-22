"""C5_F.N > "1. 환매조건부매도" (RP, 당기말만) -- the fund's short-term repo
borrowing (같은 성격의 거래가 C2의 REPO매도 카테고리), referencing
'국내유동명세' directly via SUMIF filtered on 유동종류="REPO발행(차입)" (same
filter c2_yudong_filtered_block uses for its own REPO매도 block), rather
than a hardcoded row -- consistent with this project's row-count-driven
building elsewhere.

Only 1 real row exists for this fund today, so SUMIF-ing 이자율/만기일 (not
just 수량) works out to the same single value; if a future period has more
than one repo counterparty, those two columns would need an actual
row-by-row block instead of a sum, since averaging/summing rates or dates
across multiple rows wouldn't be meaningful. Noting this rather than
over-building for a case with no real example yet.

전기말 skipped: 국내유동명세 has no PBC concept of "last period's" repo
book (it's a snapshot of the current period only).
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, box_border, left_rule, run_left_rule, style_header_row

YUDONG_SHEET_NAME = "국내유동명세"
REPO_KIND = "REPO발행(차입)"
AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"
_BOLD = BOLD


def build(ws, start_row: int) -> int:
    y = YUDONG_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 환매조건부매도").font = _BOLD
    ws.cell(r + 1, 3, "당기말 현재 환매조건부매도의 내역은 다음과 같습니다")
    left_rule(ws, r)
    left_rule(ws, r + 1)
    ws.cell(r + 3, 3, "<당기말>").font = _BOLD
    left_rule(ws, r + 3)

    header_row = r + 4
    for col, label in zip("CDEF", ["중개기관", "이자율", "수량", "만기일"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 6)

    data_row = header_row + 1
    ws.cell(data_row, 3, f"=INDEX('{y}'!C:C,MATCH(\"{REPO_KIND}\",'{y}'!D:D,0))")
    ws.cell(data_row, 4, f"=SUMIF('{y}'!D:D,\"{REPO_KIND}\",'{y}'!E:E)")
    ws.cell(data_row, 5, f"=ROUND(SUMIF('{y}'!D:D,\"{REPO_KIND}\",'{y}'!K:K)/1000,0)")
    ws.cell(data_row, 6, f"=TEXT(SUMIF('{y}'!D:D,\"{REPO_KIND}\",'{y}'!O:O),\"yyyy.mm.dd\")")
    ws.cell(data_row, 4).number_format = "0.00%"
    ws.cell(data_row, 5).number_format = AMOUNT_FMT
    for col in range(3, 7):
        ws.cell(data_row, col).border = box_border(col == 3)

    # 3 blank buffer rows after the aggregate row, room for a future
    # itemized counterparty block (see module docstring) without rebuilding.
    buffer_first_row = data_row + 1
    buffer_last_row = buffer_first_row + BUFFER_ROWS - 1
    for row in range(buffer_first_row, buffer_last_row + 1):
        for col in range(3, 7):
            ws.cell(row, col).border = box_border(col == 3)

    run_left_rule(ws, start_row, buffer_last_row)

    return buffer_last_row + 2
