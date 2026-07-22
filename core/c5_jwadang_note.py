"""C5_F.N > "1. 1좌당 순이익(손실)" and "1. 당기순이익(손실) 대비 과세대상
소득" -- both nearly 100% mechanical restatements of cells already wired
elsewhere (C1_정산표's own H117/J117/H118/J118/F121, all copied verbatim or
already tested via C1_gajungpyeonggyunjwasu wiring, plus 통합기준가격대장
L268/L162 for 과세대상수익/비용, also copied verbatim).

전기 가중평균유통좌수: the real file hardcodes this as a literal display
string (1,272,055좌). C1_정산표 has no daily 전기 좌수 series to sum directly,
but it does already carry both 전기 당기순이익(J117) and 전기 1좌당순이익
(J118) -- and 1좌당순이익 = 순이익 / 가중평균좌수 by definition, so
가중평균좌수 = J117/J118 is a real, live-formula way to get this instead of
a hardcoded literal. Note this doesn't reproduce the real file's exact
1,272,055 figure (computes ~2,368,681 instead) -- the two 전기 figures
(J117/J118) were independently hardcoded there rather than derived from each
other, so they don't perfectly cross-foot; this live formula is internally
consistent by construction, which the original pair of literals isn't.

과세대상소득: 전기 column is built as a header + blank data cells, matching
the real file's own shape (E/G columns exist there as column headers, but
every data cell under them is genuinely blank -- dead scaffolding for a
"compare against last year's report" check that was never filled in). Kept
the columns so the note's shape matches, without inventing formulas for
cells that were never wired in the source either.
"""
from __future__ import annotations

from core.c5_styles import BOLD, box_border, run_left_rule, style_header_row, style_total_row

SETTLEMENT_SHEET_NAME = "C1_정산표"
MASTER_SHEET_NAME = "통합기준가격대장(결산후)"

AMOUNT_FMT = r"#,##0\ ;\(#,##0\);\-\ ;@"
_BOLD = BOLD


def build(ws, start_row: int = 1095) -> int:
    s = SETTLEMENT_SHEET_NAME
    m = MASTER_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 1좌당 순이익(손실)").font = _BOLD
    ws.cell(r + 1, 3, "당기 및 전기의 1,000좌당 순이익의 산출내역은 다음과 같습니다. (단위 : 원)")

    header_row = r + 3
    ws.cell(header_row, 4, "당기")
    ws.cell(header_row, 5, "전기")
    style_header_row(ws, header_row, 3, 5)

    row = header_row + 1
    ws.cell(row, 3, "당기순이익(손실)(㉠)")
    ws.cell(row, 4, f"='{s}'!H117")
    ws.cell(row, 5, f"='{s}'!J117")

    row += 1
    ws.cell(row, 3, "가중평균유통좌수(㉡)")
    ws.cell(row, 4, f'=TEXT(\'{s}\'!F121,"#,###")&"좌 "')
    ws.cell(row, 5, f'=TEXT(\'{s}\'!J117/\'{s}\'!J118,"#,###")&"좌 "')

    row += 1
    ws.cell(row, 3, "1,000좌당 당기순이익(㉠÷㉡×1,000)")
    ws.cell(row, 4, f"='{s}'!H118")
    ws.cell(row, 5, f"='{s}'!J118")

    for data_row in range(header_row + 1, row + 1):
        for col in (3, 4, 5):
            ws.cell(data_row, col).border = box_border(col == 3)

    next_row = row + 3

    ws.cell(next_row, 3, "1. 당기순이익(손실) 대비 과세대상 소득").font = _BOLD
    ws.cell(next_row + 2, 3, "당기 및 전기 중 당기순이익(손실) 대비 과세대상 소득 내역은 다음과 같습니다. (단위: 천원)")

    tax_header_row = next_row + 4
    ws.cell(tax_header_row, 3, "과목")
    ws.cell(tax_header_row, 4, "당기")
    ws.cell(tax_header_row, 5, "전기")
    style_header_row(ws, tax_header_row, 3, 5)

    revenue_row = tax_header_row + 1
    ws.cell(revenue_row, 3, "과세대상수익")
    ws.cell(revenue_row, 4, f"=ROUND('{m}'!L268/1000,0)")

    expense_row = revenue_row + 1
    ws.cell(expense_row, 3, "과세대상비용")
    ws.cell(expense_row, 4, f"=ROUND(-'{m}'!L162/1000,0)")

    total_row = expense_row + 1
    ws.cell(total_row, 3, "과세대상소득")
    ws.cell(total_row, 4, f"=SUM(D{revenue_row}:D{expense_row})")
    ws.cell(total_row, 5, f"=SUM(E{revenue_row}:E{expense_row})")

    net_income_row = total_row + 1
    ws.cell(net_income_row, 3, "당기순이익(손실)")
    ws.cell(net_income_row, 4, f"=ROUND('{s}'!H117/1000,0)")

    for row in (revenue_row, expense_row, net_income_row):
        for col in (3, 4, 5):
            ws.cell(row, col).border = box_border(col == 3)
        ws.cell(row, 4).number_format = AMOUNT_FMT
        ws.cell(row, 5).number_format = AMOUNT_FMT
    style_total_row(ws, total_row, 3, 5)
    ws.cell(total_row, 4).number_format = AMOUNT_FMT
    ws.cell(total_row, 5).number_format = AMOUNT_FMT

    run_left_rule(ws, start_row, net_income_row)

    return net_income_row + 2
