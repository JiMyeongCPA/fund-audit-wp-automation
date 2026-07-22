"""Wire reconstructed 전기 재무제표 data (from prior_year_source) into a
copied C1_정산표 sheet, and recompute which rows should be hidden.

openpyxl never evaluates formulas, so C1_정산표's own
`=IF(AND(G=0,H=0,I=0,J=0),"공시제외","공시")` 공시여부 logic can't just be
read off the copied sheet -- its G/H cells are still unevaluated 당기
formulas after a plain copy. Rather than trust whatever hidden/visible state
happened to be baked into the reference file (stale relative to whatever 전기
data we just wrote), this module always starts every row visible and
recomputes hiding from the actual numbers once they're in place.
"""
from __future__ import annotations

from core.prior_year_source import (
    BS_RANGE,
    CAPITAL_PRINCIPAL_COL,
    CAPITAL_RETAINED_EARNINGS_COL,
    CAPITAL_STATEMENT_ROWS,
    CAPITAL_TOTAL_COL,
    DETAIL_VALUE_COL,
    DISCLOSURE_COL,
    IS_RANGE,
    LABEL_COL,
    SECTION_VALUE_COL,
    CapitalStatementRow,
    FinancialLineItem,
)

SHEET_NAME = "C1_정산표"
CURRENT_YEAR_DETAIL_COL = 7  # G열 (당기, detail rows)
CURRENT_YEAR_SECTION_COL = 8  # H열 (당기, section-subtotal rows)


def apply_prior_year_financials(
    output_ws, reference_current_year_ws, items: list[FinancialLineItem]
) -> list[tuple[int, str, object]]:
    """Write 전기 line items into output_ws's 재무상태표/손익계산서 rows.

    Writes go by `item.row`, not by re-matching label text -- C1_정산표's
    labels are mostly running-counter formulas (e.g. `=L10&". 운용자산"`),
    and some of the literal ones repeat (e.g. "(0) 외환스왑" appears once
    under 자산 and once under 부채, at different rows), so matching by name
    alone can silently write the same value into two unrelated rows. Row
    position is stable as long as this fund's C1_정산표 template is unchanged
    period to period -- the same assumption the rest of this project already
    leans on (통합기준가격대장's fixed VLOOKUP ranges, C1_정산표's own C열
    formulas hardcoding 통합기준가격대장 row ranges).

    Before writing, each row's current 계정명 (read from
    `reference_current_year_ws`, a data_only=True load -- output_ws's own F
    column is usually an unevaluated formula) is compared against the label
    recorded when the item was extracted. A mismatch means the fixed-template
    assumption broke (template edited, revised, or wrong file) since the
    prior-year data was pulled -- rather than silently writing into what
    might now be a different line item, that row is skipped and reported.

    Returns (row, expected_label, actual_label) for every item that failed
    this check, so the caller can flag it for human review.
    """
    drifted: list[tuple[int, str, object]] = []

    for item in items:
        actual_label = reference_current_year_ws.cell(item.row, LABEL_COL).value
        if actual_label != item.label:
            drifted.append((item.row, item.label, actual_label))
            continue
        has_i = output_ws.cell(item.row, DETAIL_VALUE_COL).value is not None
        target_col = DETAIL_VALUE_COL if has_i else SECTION_VALUE_COL
        output_ws.cell(item.row, target_col).value = item.amount

    return drifted


def apply_prior_year_capital_statement(ws, capital_rows: list[CapitalStatementRow]) -> None:
    """Write the 전기초 + 5 movement rows into rows 126-131 (positional, not
    label-matched -- this block's row order is structural). The 전기말 row
    (last position, row 132) is left untouched: it's a live SUM formula that
    will correctly total whatever was just written once Excel recalculates,
    so overwriting it with a literal would throw that formula away."""
    movement_rows = CAPITAL_STATEMENT_ROWS[:-1]
    for row, data in zip(movement_rows, capital_rows[: len(movement_rows)]):
        ws.cell(row, CAPITAL_PRINCIPAL_COL).value = data.principal
        ws.cell(row, CAPITAL_RETAINED_EARNINGS_COL).value = data.retained_earnings
        ws.cell(row, CAPITAL_TOTAL_COL).value = data.total


def recompute_disclosure_hiding(output_ws, reference_current_year_ws) -> None:
    """Hide a row iff 당기 and 전기 are both zero, mirroring the sheet's own
    공시여부 formula -- but only for rows where that formula actually applies.
    Plenty of rows (bare section dividers like "자산", 소계/총계 rows, note
    captions) have a literal E cell ("공시") instead of the
    `=IF(AND(G=0,H=0,I=0,J=0),...)` formula, meaning they're always shown
    regardless of value; those are left as copy_sheet's unhide=True already
    set them (visible).

    `reference_current_year_ws` supplies cached 당기 (G/H) values from the
    reference workbook (data_only=True) -- valid as long as 당기 data wasn't
    changed in this pass; a run that also rewrites 당기 (new PBC data) would
    need those recalculated first. `output_ws` supplies both the E-column
    formula text (copied as-is, so still intact) and 전기 (I/J), just written
    by `apply_prior_year_financials`.
    """
    for first_row, last_row in (BS_RANGE, IS_RANGE):
        for row in range(first_row, last_row + 1):
            disclosure_formula = output_ws.cell(row, DISCLOSURE_COL).value
            if not (isinstance(disclosure_formula, str) and disclosure_formula.startswith("=IF(")):
                continue
            g = reference_current_year_ws.cell(row, CURRENT_YEAR_DETAIL_COL).value or 0
            h = reference_current_year_ws.cell(row, CURRENT_YEAR_SECTION_COL).value or 0
            i = output_ws.cell(row, DETAIL_VALUE_COL).value or 0
            j = output_ws.cell(row, SECTION_VALUE_COL).value or 0
            output_ws.row_dimensions[row].hidden = g == 0 and h == 0 and i == 0 and j == 0

    # 전기초/전기말 (first/last capital-statement rows) have a literal E
    # cell and are always shown regardless of value; only the 5 movement
    # rows between them carry the conditional formula.
    for row in CAPITAL_STATEMENT_ROWS:
        disclosure_formula = output_ws.cell(row, DISCLOSURE_COL).value
        if not (isinstance(disclosure_formula, str) and disclosure_formula.startswith("=IF(")):
            continue
        g = output_ws.cell(row, CAPITAL_PRINCIPAL_COL).value or 0
        h = output_ws.cell(row, CAPITAL_RETAINED_EARNINGS_COL).value or 0
        i = output_ws.cell(row, CAPITAL_TOTAL_COL).value or 0
        output_ws.row_dimensions[row].hidden = g == 0 and h == 0 and i == 0
