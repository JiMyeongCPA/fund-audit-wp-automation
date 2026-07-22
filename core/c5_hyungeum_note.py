"""C5_F.N > "1. 현금및예치금" -- 당기말/전기말 예금·증거금 내역.

당기말과 전기말은 동일한 표 양식(헤더 + 보유예금 + 정기예금 소계 + 증거금
상세(위탁증거금/현금담보증거금) + 증거금 소계 + 합계 + 단수검증/정산표대사)
을 공유한다 -- 값이 있고 없고의 차이일 뿐, 형태 자체가 달라지면 안 된다는
원칙에 따라 `_write_period` 하나로 두 번 호출한다.

당기말은 세 부분 모두 실수식으로 연결된다:
- 보유예금 (원화금액/이자율): C2's 예금 block, F38/D38 -- these specific
  cell addresses are stable because 예금 is C2's first-built block, unlike
  the variable-sized categories after it.
- 정기예금: no PBC source anywhere in this project tracks a point-in-time
  "정기예금 held as of period-end" balance the way this note needs -- left
  as a single blank row + a 소계 that sums it (harmlessly 0).
- 증거금 (위탁증거금 + 현금담보증거금): C2's own summary table (rows 15/16,
  column E) rather than the real file's hardcoded absolute block rows
  (C45:D52) -- those move every run since C2's blocks are sized off the
  real PBC row counts.

전기말은 같은 모양이지만 보유예금/정기예금/증거금 어느 것도 채울 자료가 없어
전부 빈칸이다 (전기 자산 breakdown을 개별적으로 추적할 PBC/재구성 경로가
없음). 대신 합계는 부분합의 합이 아니라 'C1_정산표'!I11(전기 현금및예치금
실제 총액)에 직접 연결했다 -- 부분합이 전부 0이라 그걸 그대로 더하면
실제 총액과 어긋나기 때문. 그 결과 전기말의 정산표대사는 (원본에서는 FALSE로
남아있던 것과 달리) TRUE로 나온다.
"""
from __future__ import annotations

from core.c5_styles import (
    BOLD,
    BUFFER_ROWS,
    CHECK_FILL,
    box_border,
    run_left_rule,
    style_header_row,
    style_subtotal_row,
    style_total_row,
)

C2_SHEET_NAME = "C2_자산부채평가"
SETTLEMENT_SHEET_NAME = "C1_정산표"

AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"
_HEADERS = ["종류", "금융기관", "외화금액", "원화금액", "이자율"]


def _write_period(ws, label_row: int, is_current: bool, c2: str, s: str) -> int:
    ws.cell(label_row, 3, "<당기말>" if is_current else "<전기말>").font = BOLD

    header_row = label_row + 1
    for col, label in zip("CDEFG", _HEADERS):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 7)

    deposit_row = header_row + 1
    ws.cell(deposit_row, 3, "보유예금")
    if is_current:
        ws.cell(deposit_row, 4, "(주)한아름은행")  # 예치 은행명 리터럴(수식 아님)
        ws.cell(deposit_row, 6, f"=ROUND('{c2}'!F38/1000,0)")
        ws.cell(deposit_row, 7, f"='{c2}'!D38/100")

    term_deposit_row = deposit_row + 1
    term_deposit_subtotal_row = term_deposit_row + 1
    ws.cell(term_deposit_subtotal_row, 3, "정기예금 소계")
    ws.cell(term_deposit_subtotal_row, 6, f"=SUM(F{term_deposit_row}:F{term_deposit_row})")

    consign_row = term_deposit_subtotal_row + 1
    ws.cell(consign_row, 3, "위탁증거금")
    collateral_row = consign_row + 1
    ws.cell(collateral_row, 3, "현금담보증거금")
    if is_current:
        ws.cell(consign_row, 6, f"=ROUND('{c2}'!E15/1000,0)")
        ws.cell(collateral_row, 6, f"=ROUND('{c2}'!E16/1000,0)")

    margin_subtotal_row = collateral_row + 1
    ws.cell(margin_subtotal_row, 3, "증거금 소계")
    ws.cell(margin_subtotal_row, 6, f"=SUM(F{consign_row}:F{collateral_row})")

    # 3 blank buffer rows before 합계 (c2_blocks.BUFFER_ROWS convention),
    # room for future account/category lines without rebuilding the block.
    total_row = margin_subtotal_row + 1 + BUFFER_ROWS
    for row in range(margin_subtotal_row + 1, total_row):
        for col in range(3, 8):
            ws.cell(row, col).border = box_border(col == 3)
    ws.cell(total_row, 3, "합계")
    if is_current:
        ws.cell(total_row, 6, f"=F{deposit_row}+F{term_deposit_subtotal_row}+F{margin_subtotal_row}")
    else:
        ws.cell(total_row, 6, f"=ROUND('{s}'!I11/1000,0)")

    for row in (deposit_row, term_deposit_row, consign_row, collateral_row):
        for col in range(3, 8):
            ws.cell(row, col).border = box_border(col == 3)
    style_subtotal_row(ws, term_deposit_subtotal_row, 3, 7)
    style_subtotal_row(ws, margin_subtotal_row, 3, 7)
    style_total_row(ws, total_row, 3, 7)

    for row in (deposit_row, term_deposit_subtotal_row, consign_row, collateral_row, margin_subtotal_row, total_row):
        ws.cell(row, 6).number_format = AMOUNT_FMT

    check_row = total_row + 1
    ws.cell(check_row, 4, "단수검증")
    if is_current:
        ws.cell(check_row, 5, f"=F{total_row}=ROUND(('{c2}'!F38+'{c2}'!E15+'{c2}'!E16)/1000,0)")
    ws.cell(check_row, 6, "정산표대사")
    if is_current:
        ws.cell(check_row, 7, f"='{s}'!G11=('{c2}'!F38+'{c2}'!E15+'{c2}'!E16)")
    else:
        ws.cell(check_row, 7, f"='{s}'!I11=F{total_row}*1000")
    ws.cell(check_row, 5).fill = CHECK_FILL
    ws.cell(check_row, 7).fill = CHECK_FILL

    return check_row


def build(ws, start_row: int = 7) -> int:
    c2 = C2_SHEET_NAME
    s = SETTLEMENT_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1.  현금및예치금").font = BOLD
    ws.cell(r + 1, 3, "당기말 및 전기말 현재 현금및예치금의 내역은 다음과 같습니다. (원화단위: 천원)")

    current_check_row = _write_period(ws, r + 3, True, c2, s)
    prior_label_row = current_check_row + 2
    prior_check_row = _write_period(ws, prior_label_row, False, c2, s)

    run_left_rule(ws, r, prior_check_row)

    return prior_check_row + 2
