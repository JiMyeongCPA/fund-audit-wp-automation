"""Assemble C2_자산부채평가 fresh, block by block, instead of copying it
verbatim from the reference workpaper. Each detail block's row count matches
this run's real PBC data (N real rows + 3 blank buffer + 1 total), so it
never silently runs out of capacity the way a copied, row-frozen template
can (verified against the real file: 채권명세's block had zero spare rows).

Categories with no real data this period are built as empty blocks, hidden
outright, and don't advance the running section number -- see
c2_numbering.SectionNumberer and c2_blocks.write_block's `hidden` param, both
verified against the real file's own hidden-row + conditional-numbering
pattern for 콜론/REPO매수/매입어음/전자단기사채.

외화위탁증거금 has no matching PBC source and stays out of scope for this
domestically-focused fund (user's call) -- not built at all.
"""
from __future__ import annotations

from core import (
    c2_blocks,
    c2_chaegwon_block,
    c2_empty_block,
    c2_gungnaejusik_block,
    c2_numbering,
    c2_seonmul_filtered_block,
    c2_sooikjeunggwon_block,
    c2_summary,
    c2_yudong_filtered_block,
)

SHEET_NAME = "C2_자산부채평가"

TOTAL_COL_LETTER = {
    "예금": "F",
    "위탁증거금": "D",
    "현금담보증거금": "E",
    "콜론": "F",
    "REPO매수": "F",
    "매입어음": "F",
    "전자단기사채": "F",
    "거래소주식": "F",
    "코스닥주식": "D",
    "수익증권": "F",
    "선물미수입금": "I",
    "선물미지급금": "I",
    "옵션매수": "D",
    "옵션매도": "D",
    "매도유가증권": "D",
    "REPO매도": "F",
}


def build_c2(wb, ref_wb, yudong_df, jusik_df, sooik_df, seonmul_df, chaegwon_df):
    ws = wb.create_sheet(SHEET_NAME)
    results = {}
    row = 36
    numberer = c2_numbering.SectionNumberer(start=1)
    R = c2_summary.ROW_FOR_CATEGORY  # category -> its summary-table row

    def place(name, result):
        results[name] = result
        return result["next_row"]

    n = numberer.use()
    r = c2_yudong_filtered_block.build(ws, row, yudong_df, f"{n}. 예금", "예금", summary_row=R["예금"])
    row = place("예금", r)
    numberer.advance(r["hidden"])

    # 위탁증거금/현금담보증거금 are sub-items of 예금 ("1-1."/"1-2."), tied to
    # 예금's own number regardless of emptiness -- not part of the running count.
    row = place(
        "위탁증거금",
        c2_empty_block.build(
            ws, row, f"{n}-1. 위탁증거금", ["매매처명", "원화증거금"], ["D"], summary_row=R["위탁증거금"]
        ),
    )
    row = place(
        "현금담보증거금",
        c2_empty_block.build(
            ws,
            row,
            f"{n}-2. 현금담보증거금",
            ["종목명", "발행률", "수량"],
            ["E"],
            summary_row=R["현금담보증거금"],
        ),
    )

    n = numberer.use()
    r = c2_yudong_filtered_block.build(ws, row, yudong_df, f"{n}. 콜론", "콜론", summary_row=R["콜론"])
    row = place("콜론", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_yudong_filtered_block.build(
        ws, row, yudong_df, f"{n}. REPO(매수)", "RP매수", summary_row=R["REPO매수"]
    )
    row = place("REPO매수", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_yudong_filtered_block.build(
        ws, row, yudong_df, f"{n}. 매입어음", "매입어음", summary_row=R["매입어음"]
    )
    row = place("매입어음", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_yudong_filtered_block.build(
        ws, row, yudong_df, f"{n}. 전자단기사채", "전자단기사채", summary_row=R["전자단기사채"]
    )
    row = place("전자단기사채", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_chaegwon_block.build(ws, row, chaegwon_df, section_number=n, summary_row=R["국채"])
    row = place("채권", r)
    numberer.advance(r["hidden"])

    # 거래소주식/코스닥주식/수익증권 all share this one slot ("(1)"/"(2)" sub-
    # items plus 수익증권 reusing the same top-level number) -- only one
    # advance() call for the whole group, so the number isn't consumed twice.
    n = numberer.use()

    # Group header row -- a pure caption (no columns/data of its own), with
    # the same tie-out check + fill as every other caption row.
    ws.cell(row, 3, f"{n}. 거래소주식, 코스닥주식")
    ws.cell(row, 1, f'=IF($G{R["거래소주식"]}=0,"O","X")')
    ws.cell(row, 2).fill = c2_blocks.COLUMN_B_FILL
    row += 2  # blank gap, then "(1) 거래소주식" starts

    r = c2_gungnaejusik_block.build(
        ws, row, jusik_df, "(1) 거래소주식", summary_row=R["거래소주식"]
    )
    row = place("거래소주식", r)

    row = place(
        "코스닥주식",
        c2_empty_block.build(
            ws,
            row,
            "(2) 코스닥주식",
            ["종목명", "수량", "결산전장부가액", "결산후장부가액"],
            ["D"],
            summary_row=R["코스닥주식"],
        ),
    )

    r = c2_sooikjeunggwon_block.build(ws, row, sooik_df, section_number=n, summary_row=R["수익증권"])
    row = place("수익증권", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_seonmul_filtered_block.build(
        ws, row, seonmul_df, f"{n}. 선물미수입금", "선물매수", summary_row=R["선물미수입금"]
    )
    row = place("선물미수입금", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_seonmul_filtered_block.build(
        ws, row, seonmul_df, f"{n}. 선물미지급금", "선물매도", summary_row=R["선물미지급금"]
    )
    row = place("선물미지급금", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_empty_block.build(
        ws, row, f"{n}. 옵션매수", ["종목명", "계약수", "평가금액"], ["D"], summary_row=R["옵션매수"]
    )
    row = place("옵션매수", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_empty_block.build(
        ws, row, f"{n}. 옵션매도", ["종목명", "계약수", "평가금액"], ["D"], summary_row=R["옵션매도"]
    )
    row = place("옵션매도", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_empty_block.build(
        ws,
        row,
        f"{n}. 매도유가증권",
        ["종목명", "수량", "평가금액"],
        ["D"],
        summary_row=R["매도유가증권"],
    )
    row = place("매도유가증권", r)
    numberer.advance(r["hidden"])

    n = numberer.use()
    r = c2_yudong_filtered_block.build(
        ws, row, yudong_df, f"{n}. REPO(매도)", "REPO발행(차입)", summary_row=R["REPO매도"]
    )
    row = place("REPO매도", r)
    numberer.advance(r["hidden"])

    c2_summary.build(
        ws,
        ref_wb[SHEET_NAME],
        {
            "예금": results["예금"],
            "위탁증거금": results["위탁증거금"],
            "현금담보증거금": results["현금담보증거금"],
            "콜론": results["콜론"],
            "REPO매수": results["REPO매수"],
            "매입어음": results["매입어음"],
            "전자단기사채": results["전자단기사채"],
            "국채": results["채권"],
            "특수채": results["채권"],
            "통안채": results["채권"],
            "회사채": results["채권"],
            "거래소주식": results["거래소주식"],
            "코스닥주식": results["코스닥주식"],
            "수익증권": results["수익증권"],
            "선물미수입금": results["선물미수입금"],
            "선물미지급금": results["선물미지급금"],
            "옵션매수": results["옵션매수"],
            "옵션매도": results["옵션매도"],
            "매도유가증권": results["매도유가증권"],
            "REPO매도": results["REPO매도"],
        },
        total_col_letter=TOTAL_COL_LETTER,
    )

    return ws, results
