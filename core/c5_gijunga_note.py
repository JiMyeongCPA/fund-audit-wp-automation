"""C5_F.N > "1. 수익증권 기준가격" -- fully mechanical: 재무상태표자산/부채,
신탁재산순자산총액, 총좌수, 좌당 기준가격, all tracing back to cells already
copied verbatim in 'C1_정산표' (H37/J37, H55/J55, H57/J57, H68/J68). The one
cross-note dependency: "분배전 좌당 기준가격" adds back this period's
미지급이익분배금 총계 (already built by c5_ibunbae_note), so this module
takes that row number as a parameter rather than a hardcoded row.

Kept as-is despite an inconsistency already present in the real file: the
label "1,000좌당 수익증권기준가격" but its formula computes a plain per-단위
(1좌당) value with no x1,000 anywhere, while the very next line's formula
("분배전 1,000좌당...") *does* multiply by 1,000. Not something to silently
"fix" -- it's disclosure wording/formula as the real file has it, not a
calculation bug in the sense the earlier rounding-plug ones were.
"""
from __future__ import annotations

from core.c5_styles import BOLD, CHECK_FILL, box_border, run_left_rule, style_header_row

SETTLEMENT_SHEET_NAME = "C1_정산표"
_BOLD = BOLD


def build(ws, ibunbae_total_row: int, start_row: int = 1118) -> int:
    s = SETTLEMENT_SHEET_NAME
    r = start_row

    ws.cell(r, 3, "1. 수익증권 기준가격").font = _BOLD
    ws.cell(r + 1, 3, "당기말 및 전기말 현재 수익증권 기준가격의 계산내역은 다음과 같습니다. (단위 : 원)")

    header_row = r + 3
    ws.cell(header_row, 3, "과목")
    ws.cell(header_row, 4, "당기")
    ws.cell(header_row, 5, "전기")
    style_header_row(ws, header_row, 3, 5)

    asset_row = header_row + 1
    ws.cell(asset_row, 3, "재무상태표자산")
    ws.cell(asset_row, 4, f"='{s}'!H37")
    ws.cell(asset_row, 5, f"='{s}'!J37")

    liab_row = asset_row + 1
    ws.cell(liab_row, 3, "재무상태표부채")
    ws.cell(liab_row, 4, f"='{s}'!H55")
    ws.cell(liab_row, 5, f"='{s}'!J55")

    net_asset_row = liab_row + 1
    ws.cell(net_asset_row, 3, "신탁재산순자산총액")
    ws.cell(net_asset_row, 4, f"=D{asset_row}-D{liab_row}")
    ws.cell(net_asset_row, 5, f"=E{asset_row}-E{liab_row}")

    units_row = net_asset_row + 1
    ws.cell(units_row, 3, "수익증권총좌수")
    ws.cell(units_row, 4, f'=TEXT(\'{s}\'!$H$57/10000,"#,###")&"좌 "')
    ws.cell(units_row, 5, f'=TEXT(\'{s}\'!J57/10000,"#,###")&"좌 "')

    price_row = units_row + 1
    ws.cell(price_row, 3, "1,000좌당 수익증권기준가격")
    ws.cell(price_row, 4, f"=D{net_asset_row}/('{s}'!$H$57/10000)")
    ws.cell(price_row, 5, f"=E{net_asset_row}/('{s}'!J57/10000)")

    pre_dist_price_row = price_row + 1
    ws.cell(pre_dist_price_row, 3, "분배전 1,000좌당 수익증권기준가격")
    ws.cell(pre_dist_price_row, 4, (
        f"=(D{net_asset_row}+D{ibunbae_total_row})/('{s}'!$H$57/10000)*1000"
    ))
    ws.cell(pre_dist_price_row, 5, (
        f"=(E{net_asset_row}+E{ibunbae_total_row})/('{s}'!J57/10000)*1000"
    ))

    for row in (asset_row, liab_row, net_asset_row, units_row, price_row, pre_dist_price_row):
        for col in (3, 4, 5):
            ws.cell(row, col).border = box_border(col == 3)

    check_row = pre_dist_price_row + 2
    ws.cell(check_row, 4, f"='{s}'!H68=D{price_row}")
    ws.cell(check_row, 5, f"='{s}'!J68=E{price_row}")
    ws.cell(check_row, 4).fill = CHECK_FILL
    ws.cell(check_row, 5).fill = CHECK_FILL

    run_left_rule(ws, start_row, check_row)

    return check_row + 2
