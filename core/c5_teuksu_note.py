"""C5_F.N > "1. 집합투자업자와 그 특수관계자와의 거래" -- structure only,
values left empty. The row shape (거래처/계정과목 pairs) matches the template
so a reviewer can see exactly what needs filling in, but the amounts aren't
derived from c5_bosu_note: the 거래처/계정과목 labels here ("한빛증권(주)",
"미지급판매회사보수" 등) don't map 1:1 onto c5_bosu_note's own 구분/지급처
labels ("판매회사"/"한빛증권 등") --
reusing those numbers under a re-typed counterparty name would be a guess
about which entity is which, not something this pipeline can verify. Also,
deciding *which* counterparties even count as 특수관계자 (related parties)
requires knowing the asset manager's corporate group structure -- not
something derivable from any PBC transaction file. Review status is
surfaced by the React UI (NEEDS_REVIEW), not written into the sheet itself.
"""
from __future__ import annotations

from core.c5_styles import BOLD, box_border, left_rule, style_header_row

NEEDS_REVIEW = True
NEEDS_REVIEW_REASON = "특수관계자거래: 관계사 목록 판단 및 금액 확인이 필요해 자동 산출 불가"

_BOLD = BOLD

# (거래처, 계정과목) -- matches the real file's own row shape; counterparty
# left blank on a row that shares the previous row's 거래처 (같은 회사, 다른
# 계정과목), same as the real file's own C1141=None-style skip.
_ROWS = [
    ("한빛자산운용(주)", "미지급집합투자업자보수"),
    (None, "집합투자보수"),
    ("한빛증권(주)", "미지급판매회사보수"),
    (None, "판매보수"),
    ("한빛생명(주)", "미지급판매회사보수"),
    (None, "판매보수"),
    ('다솜펀드파트너스(주)\n(구, "한빛펀드서비스(주)")', "미지급사무관리회사보수"),
    (None, "사무관리보수"),
]


def build(ws, start_row: int) -> int:
    r = start_row

    ws.cell(r, 3, "1. 집합투자업자와 그 특수관계자와의 거래").font = _BOLD
    ws.cell(r + 2, 3, "당기 및 전기 중 집합투자업자와 그 특수관계자와의 거래내용은 다음과 같습니다. (단위: 천원)")
    left_rule(ws, r)
    for row in range(r + 1, r + 4):
        left_rule(ws, row)

    header_row = r + 4
    for col, label in zip("CDEF", ["거래처", "계정과목", "당기", "전기"]):
        ws.cell(header_row, ord(col) - ord("A") + 1, label)
    style_header_row(ws, header_row, 3, 6)

    first_data_row = header_row + 1
    for i, (counterparty, account) in enumerate(_ROWS):
        row = first_data_row + i
        if counterparty is not None:
            ws.cell(row, 3, counterparty)
            ws.merge_cells(start_row=row, start_column=3, end_row=row + 1, end_column=3)
        ws.cell(row, 4, account)
        for col in (3, 4, 5, 6):
            ws.cell(row, col).border = box_border(col == 3)

    return first_data_row + len(_ROWS) + 1
