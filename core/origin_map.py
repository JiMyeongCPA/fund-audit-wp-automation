"""Maps C2_자산부채평가 detail-block cell ranges back to the raw PBC CSV rows
they were built from, for the review UI's "click block -> see original PBC
row" feature.

Only covers the three 1:1 blocks (거래소주식/채권/수익증권), where C2's row i
maps to source row FIRST_DATA_ROW+i in strict order (verified via
c2_gungnaejusik_block.py / c2_chaegwon_block.py / c2_sooikjeunggwon_block.py's
identical `_make_row_writer(source_row)` pattern -- each writes exactly one C2
row per source row, in the same order, with no filtering). The filtered
blocks (예금/콜론/... via c2_yudong_filtered_block, 선물미수/미지급 via
c2_seonmul_filtered_block) select a non-contiguous subset of their source
sheet and don't preserve row position anywhere -- deliberately not covered
here; callers should treat those rows as "no origin link" rather than guess.
"""
from __future__ import annotations

from dataclasses import dataclass

from core import chaegwon, gungnaejusik, sooikjeunggwon

# block_name (as used as a key in c2_assemble.build_c2's returned `results`
# dict) -> the raw-PBC parser module providing SHEET_NAME/FIRST_DATA_ROW for
# that block's source sheet.
_SOURCE_MODULE = {
    "거래소주식": gungnaejusik,
    "채권": chaegwon,
    "수익증권": sooikjeunggwon,
}


@dataclass(frozen=True)
class OriginEntry:
    block_name: str
    c2_sheet: str
    c2_first_row: int
    c2_last_row: int
    source_sheet: str
    source_csv_path: str
    source_first_row: int
    source_last_row: int


def build_origin_map(
    c2_block_results: dict,
    raw_csv_paths: dict[str, str],
    raw_row_counts: dict[str, int],
    c2_sheet_name: str = "C2_자산부채평가",
) -> list[OriginEntry]:
    """Build the origin map for one build_workpaper() run.

    `c2_block_results`, `raw_csv_paths`, `raw_row_counts` are exactly the
    dicts build_workpaper() now returns under those same keys.
    """
    entries: list[OriginEntry] = []
    for block_name, module in _SOURCE_MODULE.items():
        result = c2_block_results.get(block_name)
        if result is None or result["hidden"]:
            continue

        source_sheet = module.SHEET_NAME
        row_count = raw_row_counts.get(source_sheet, 0)
        if row_count == 0:
            continue

        # result["first_data_row"]/["last_data_row"] span N real rows + 3
        # blank buffer rows (core.c2_blocks.write_block's BUFFER_ROWS) -- use
        # the real row_count here, not last_data_row, to exclude the buffer.
        c2_first_row = result["first_data_row"]
        c2_last_row = c2_first_row + row_count - 1
        source_first_row = module.FIRST_DATA_ROW
        source_last_row = source_first_row + row_count - 1

        entries.append(
            OriginEntry(
                block_name=block_name,
                c2_sheet=c2_sheet_name,
                c2_first_row=c2_first_row,
                c2_last_row=c2_last_row,
                source_sheet=source_sheet,
                source_csv_path=raw_csv_paths[source_sheet],
                source_first_row=source_first_row,
                source_last_row=source_last_row,
            )
        )
    return entries


def lookup_by_c2_row(entries: list[OriginEntry], row: int) -> OriginEntry | None:
    for entry in entries:
        if entry.c2_first_row <= row <= entry.c2_last_row:
            return entry
    return None


def source_row_for_c2_row(entry: OriginEntry, c2_row: int) -> int:
    return entry.source_first_row + (c2_row - entry.c2_first_row)


_PARSE_FN = {
    "거래소주식": gungnaejusik.parse,
    "채권": chaegwon.parse,
    "수익증권": sooikjeunggwon.parse,
}


def load_source_dataframe(entry: OriginEntry):
    """Re-parse entry's source CSV fresh. Since the three supported blocks
    are always a full 1:1 match with their source sheet (row_count ==
    len(source_df), see build_origin_map), this returns exactly the rows
    that block's C2 output was built from -- no row-range slicing needed."""
    return _PARSE_FN[entry.block_name](entry.source_csv_path)
