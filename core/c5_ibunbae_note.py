"""C5_F.N > "1. 이익분배금": 미지급이익분배금 (당기말/전기말). 샘플펀드 has a
single unit class, so unlike the "종류별" tables skipped elsewhere, this one
only ever has one real row -- no separate per-class breakdown to build.

- 당기말 (D): '통합기준가격대장(결산후)'!I116 -- already copied verbatim.
- 전기말 (E): the real file leaves this as a blank cell reference (`=N1043`
  pointing at nothing), reconciling only because both sides happen to be 0.
  Wired here to `='C1_정산표'!I52` instead (the actual 전기 reconciliation
  target the file's own check row already compares against), so it stays
  correct if a future period's number isn't zero.
- 정산표대사 (check row): compares 합계 against 'C1_정산표'!G52 (당기) /
  I52 (전기) directly, same reconciliation the real file's own check row
  does.

(2) 종류별 배당금의 산출내용: same "single unit class, no per-class ledger"
gap as c5_wonbon_note's 종류별 발행좌수 table -- structure only (header + a
few blank rows + 합계), no formulas and no 정산표대사 check (the real file's
own check here is cached FALSE, meaningless with no real class data).
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, CHECK_FILL, box_border, run_left_rule, style_header_row, style_total_row

SETTLEMENT_SHEET_NAME = "C1_정산표"
MASTER_SHEET_NAME = "통합기준가격대장(결산후)"

_BOLD = BOLD
_CLASS_BREAKDOWN_BUFFER_ROWS = 3


def build(ws, start_row: int = 1038) -> int:
    s = SETTLEMENT_SHEET_NAME
    m = MASTER_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 이익분배금").font = _BOLD
    ws.cell(r + 2, 3, "(1) 당기말 및 전기말 현재 투자신탁의 미지급이익분배금은 다음과 같습니다.")

    header_row = r + 4
    ws.cell(header_row, 3, "종류")
    ws.cell(header_row, 4, "당기말")
    ws.cell(header_row, 5, "전기말")
    style_header_row(ws, header_row, 3, 5)

    data_row = header_row + 1
    ws.cell(data_row, 4, f"='{m}'!I116")
    ws.cell(data_row, 5, f"='{s}'!I52")
    for col in (3, 4, 5):
        ws.cell(data_row, col).border = box_border(col == 3)

    # 3 blank buffer rows before 합계 (c2_blocks.BUFFER_ROWS convention),
    # room for a future multi-class 미지급이익분배금 breakdown.
    total_row = data_row + 1 + BUFFER_ROWS
    for row in range(data_row + 1, total_row):
        for col in (3, 4, 5):
            ws.cell(row, col).border = box_border(col == 3)
    ws.cell(total_row, 3, "합계")
    ws.cell(total_row, 4, f"=SUM(D{data_row}:D{total_row - 1})")
    ws.cell(total_row, 5, f"=SUM(E{data_row}:E{total_row - 1})")
    style_total_row(ws, total_row, 3, 5)

    check_row = total_row + 1
    ws.cell(check_row, 3, "정산표대사")
    ws.cell(check_row, 4, f"=D{total_row}='{s}'!G52")
    ws.cell(check_row, 5, f"=E{total_row}='{s}'!I52")
    ws.cell(check_row, 4).fill = CHECK_FILL
    ws.cell(check_row, 5).fill = CHECK_FILL

    class_caption_row = check_row + 2
    ws.cell(class_caption_row, 3, "(2) 당기말 및 전기말 현재 종류별 배당금의 산출내용은 다음과 같습니다.")

    period_row = class_caption_row + 2
    for period_label in ("<당기말>", "<전기말>"):
        ws.cell(period_row, 3, period_label).font = _BOLD
        class_header_row = period_row + 1
        for col, label in zip(
            "CDEFGH",
            ["종류", "배당형태", "총좌수(좌)", "천좌당배당금", "배당률", "배당예정액"],
        ):
            ws.cell(class_header_row, ord(col) - ord("A") + 1, label)
        style_header_row(ws, class_header_row, 3, 8)

        class_total_row = class_header_row + 1 + _CLASS_BREAKDOWN_BUFFER_ROWS
        ws.cell(class_total_row, 3, "합계")
        style_total_row(ws, class_total_row, 3, 8)

        period_row = class_total_row + 2

    run_left_rule(ws, start_row, period_row - 2)

    return period_row
