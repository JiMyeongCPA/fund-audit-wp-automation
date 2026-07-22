"""C5_F.N > "1. 대출채권" -- 콜론/REPO(매수). 당기말과 전기말은 동일한 표
양식(헤더 + 콜론 + REPO(매수) + 합계)을 공유한다 -- 값이 있고 없고의 차이일
뿐, 형태가 달라지면 안 된다는 원칙에 따라 `_write_period` 하나로 두 번
호출한다.

당기말은 C2_자산부채평가의 자체 요약표 총계(콜론/REPO매수, rows 17/18)에
실수식으로 연결된다 -- 둘 다 이 펀드는 0이지만, "지금은 0이어도 미래에
실제 잔액이 생기면 자동으로 반영되게" 하는 이 프로젝트의 원칙(C2 자체
콜론/REPO매수 블록, C3_수익의 콜/정기예금 행과 같은 논리).

전기말은 같은 두 줄(콜론/REPO매수) + 합계 구조지만 전부 빈칸이다 -- 전기
콜론/REPO매수 잔액을 추적할 PBC/재구성 경로가 없음.
"""
from __future__ import annotations

from core.c5_styles import BOLD, BUFFER_ROWS, box_border, run_left_rule, style_header_row, style_total_row

C2_SHEET_NAME = "C2_자산부채평가"
CALL_LOAN_SUMMARY_ROW = 17  # 콜론
REPO_BUY_SUMMARY_ROW = 18  # REPO(매수)
AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"


def _write_period(ws, label_row: int, is_current: bool, c2: str) -> int:
    ws.cell(label_row, 3, "<당기말>" if is_current else "<전기말>").font = BOLD

    header_row = label_row + 1
    for col, label in zip("CDEFG", ["종류", "금융기관 / 종목명", "금액", "만기", "연이자율"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 7)

    call_loan_row = header_row + 1
    ws.cell(call_loan_row, 3, "콜론")
    repo_buy_row = call_loan_row + 1
    ws.cell(repo_buy_row, 3, "REPO(매수)")
    if is_current:
        ws.cell(call_loan_row, 5, f"=ROUND('{c2}'!E{CALL_LOAN_SUMMARY_ROW}/1000,0)")
        ws.cell(repo_buy_row, 5, f"=ROUND('{c2}'!E{REPO_BUY_SUMMARY_ROW}/1000,0)")

    # 3 blank buffer rows before 합계 (c2_blocks.BUFFER_ROWS convention).
    total_row = repo_buy_row + 1 + BUFFER_ROWS
    ws.cell(total_row, 3, "합계")
    ws.cell(total_row, 5, f"=SUM(E{call_loan_row}:E{total_row - 1})")

    for row in (call_loan_row, repo_buy_row):
        for col in range(3, 8):
            ws.cell(row, col).border = box_border(col == 3)
        ws.cell(row, 5).number_format = AMOUNT_FMT
    for row in range(repo_buy_row + 1, total_row):
        for col in range(3, 8):
            ws.cell(row, col).border = box_border(col == 3)
    style_total_row(ws, total_row, 3, 7)
    ws.cell(total_row, 5).number_format = AMOUNT_FMT

    return total_row


def build(ws, start_row: int) -> int:
    c2 = C2_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 대출채권").font = BOLD
    ws.cell(r + 1, 3, "당기말 및 전기말 현재 대출채권의 내역은 다음과 같습니다. (원화단위: 천원)")

    current_total_row = _write_period(ws, r + 3, True, c2)
    prior_label_row = current_total_row + 2
    prior_total_row = _write_period(ws, prior_label_row, False, c2)

    run_left_rule(ws, start_row, prior_total_row)

    return prior_total_row + 2
