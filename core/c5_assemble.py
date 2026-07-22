"""C5_F.N: 주석사항 검토 -- a long disclosure document (1200+ rows in the
real file) covering many distinct notes (현금및예치금, 지분증권/채무증권/
수익증권/파생상품 상세명세, 보수, 원본, 이익분배금, 특수관계자거래 등).

Built one note at a time rather than all at once, mirroring c2_assemble's
role of orchestrating separately-built blocks: each note gets its own module
(e.g. c5_bosu_note.py for "1. 보수"), and this function creates the sheet,
writes the shared title block, then calls each note builder in sequence,
chaining each one's returned "next free row" into the next -- same pattern
as c2_blocks' `next_row`. Notes not yet built simply aren't called here, so
they don't take up any rows; as earlier notes (현금및예치금 등, which sit
before "1. 보수" in the real file's row order) get added in future sessions,
"1. 보수" will naturally shift down to make room, rather than staying pinned
to the real file's row 1000 for a document that isn't fully built yet.
"""
from __future__ import annotations

from core import (
    c5_bosu_note,
    c5_chaegwon_note,
    c5_dambo_note,
    c5_daechul_note,
    c5_gijunga_note,
    c5_hwanmae_note,
    c5_hyungeum_note,
    c5_ibunbae_note,
    c5_jibun_note,
    c5_jwadang_note,
    c5_maedoyu_note,
    c5_pasang_note,
    c5_sooikjeunggwon_note,
    c5_teuksu_note,
    c5_wonbon_note,
)

SHEET_NAME = "C5_F.N"
SETTLEMENT_SHEET_NAME = "C1_정산표"


def build_c5(
    wb,
    fee_rate_items,
    c2_stock_first_row: int,
    num_stocks: int,
    c2_bond_first_row: int,
    num_bonds: int,
    c2_sooikjeunggwon_first_row: int,
    num_sooikjeunggwon: int,
    num_futures_contracts: int,
):
    ws = wb.create_sheet(SHEET_NAME)
    s = SETTLEMENT_SHEET_NAME

    ws["A1"] = f"='{s}'!B1"
    ws["A2"] = f"='{s}'!B2"
    ws["A3"] = "주석사항 검토"

    next_row = c5_hyungeum_note.build(ws, start_row=6)
    next_row = c5_daechul_note.build(ws, start_row=next_row)
    next_row = c5_jibun_note.build(ws, c2_stock_first_row, num_stocks, start_row=next_row)
    next_row = c5_chaegwon_note.build(ws, c2_bond_first_row, num_bonds, start_row=next_row)
    next_row = c5_sooikjeunggwon_note.build(
        ws, c2_sooikjeunggwon_first_row, num_sooikjeunggwon, start_row=next_row
    )
    next_row = c5_pasang_note.build(ws, num_futures_contracts, start_row=next_row)
    next_row = c5_hwanmae_note.build(ws, start_row=next_row)
    next_row = c5_maedoyu_note.build(ws, c2_bond_first_row, num_bonds, start_row=next_row)
    next_row = c5_bosu_note.build(ws, fee_rate_items, start_row=next_row)
    next_row = c5_wonbon_note.build(ws, start_row=next_row)
    next_row = c5_ibunbae_note.build(ws, start_row=next_row)
    ibunbae_total_row = next_row - 3  # c5_ibunbae_note always returns total_row + 3 (check row + 2)
    next_row = c5_jwadang_note.build(ws, start_row=next_row)
    next_row = c5_gijunga_note.build(ws, ibunbae_total_row, start_row=next_row)
    next_row = c5_teuksu_note.build(ws, start_row=next_row)
    c5_dambo_note.build(ws, start_row=next_row)

    # Notes with no mechanical way to fill in (no PBC source, or requires
    # human judgment like related-party identification) -- surfaced here for
    # whatever reads this, e.g. a future review UI, rather than written into
    # the sheet itself. See feedback_data_provenance memory.
    needs_review = [
        c5_teuksu_note.NEEDS_REVIEW_REASON,
        c5_dambo_note.NEEDS_REVIEW_REASON,
    ]

    return ws, needs_review
