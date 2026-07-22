"""Unifies every "automation couldn't finish this" signal from
build_workpaper() into one common shape for the review UI (2페이지), so the
UI renders every flag type through the same logic regardless of what kind of
gap it represents.

Two genuinely different kinds of gap exist, and they're kept visually
distinct rather than forced into one interaction:

- 알림형 (notify-only): e.g. missing_account_codes -- a brand-new account
  code with nowhere in a firm-wide chart of accounts to classify it. There's
  no way to derive "what should happen" from data alone, so this is a plain
  flag with no evidence panel and no accept/reject action.
- 승인형 (evidence + approve/reject): a value where a human can look at
  original evidence and decide whether to apply a change. Today this has
  exactly one example, and it's built from a JSON fixture manifest rather
  than genuine detection -- see demo_fee_contract_item's docstring.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FlaggedItem:
    id: str
    account_name: str
    reason: str
    evidence_type: str  # "none" | "source_pbc_table" | "document"
    evidence_ref: dict | None
    decision_required: bool
    status: str = "pending"  # "pending" | "approved" | "rejected"


def from_missing_account_codes(missing: list[dict]) -> list[FlaggedItem]:
    """알림형, real logic -- from gijunkagyeok.find_missing_account_codes()."""
    return [
        FlaggedItem(
            id=f"missing::{item['코드']}",
            account_name=item["계정명"],
            reason=(
                f"계정코드 {item['코드']}가 통합기준가격대장에 없습니다. "
                "회사 전체 계정과목 체계 없이는 어느 재무제표 항목에 반영할지 "
                "판단할 수 없어, 자동 반영 없이 확인 요청만 표시합니다."
            ),
            evidence_type="none",
            evidence_ref=None,
            decision_required=False,
        )
        for item in missing
    ]


def from_drifted_prior_year_rows(drifted: list[tuple]) -> list[FlaggedItem]:
    """Wired up but not yet real: `drifted_prior_year_rows` is a template
    label-integrity check (core/settlement_sheet.py), not a prior-year value
    diff, and per core/assemble.py's docstring it's structurally always []
    until a genuine second reference workpaper exists (today both sides
    trace back to the same file). Kept here so it starts flowing into the
    same review queue automatically once that's true, instead of needing a
    second code path added later.
    """
    return [
        FlaggedItem(
            id=f"drift::{row}",
            account_name=str(expected_label),
            reason=(
                f"참조 조서의 {row}행 라벨이 예상({expected_label})과 다릅니다"
                f"(실제: {actual_label}). 템플릿이 바뀌었을 수 있어 확인이 필요합니다."
            ),
            evidence_type="none",
            evidence_ref=None,
            decision_required=False,
        )
        for row, expected_label, actual_label in drifted
    ]


def demo_document_item(manifest_path: str | Path, id_prefix: str) -> FlaggedItem:
    """승인형 데모 항목을 JSON 매니페스트로 구성한다 -- 실제 탐지 로직이 아니라
    데모용으로 구성된 항목임을 evidence_ref/화면 양쪽에서 명확히 구분해야
    한다. `demo_fee_contract_item`("수수료비용 약관 변경")이 원래 이 패턴의
    유일한 예시였는데, 특수관계자거래/담보제공자산도 같은 이유로 값을
    비워두는 항목이라(원본 PBC 자료 없음) 같은 패턴을 재사용한다."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    return FlaggedItem(
        id=f"demo::{id_prefix}",
        account_name=manifest["account_name"],
        reason=manifest["reason"],
        evidence_type="document",
        evidence_ref={
            "doc_paths": manifest["doc_paths"],
            "query": manifest["search_query"],
        },
        decision_required=True,
    )


def demo_fee_contract_item(manifest_path: str | Path) -> FlaggedItem:
    """승인형 데모 항목 ("수수료비용 약관 변경"). 실제 전기 조서 실물이 없어
    drifted_prior_year_rows가 이런 케이스를 감지할 수 없으므로(위 함수 참고),
    JSON 매니페스트로 명시 구성한다."""
    return demo_document_item(manifest_path, "수수료비용")


def build_flagged_items(
    build_result: dict,
    demo_manifest_path: str | Path | None = None,
    teuksu_manifest_path: str | Path | None = None,
    dambo_manifest_path: str | Path | None = None,
) -> list[FlaggedItem]:
    """`build_result` is exactly what build_workpaper() returns.
    `demo_manifest_path`/`teuksu_manifest_path`/`dambo_manifest_path`, if
    given, each append one staged 승인형 demo item -- 수수료비용
    (tests/fixtures/synthetic_pbc/fee_contract_demo.json), 특수관계자거래
    (teuksu_demo.json), 담보제공자산(dambo_demo.json). 셋 다 core/c5_*_note.py가
    원본 PBC 자료 부재로 값을 비워두는 항목이라(각 모듈 docstring 참고)
    같은 "AI가 근거문서를 찾아 제안, 사람이 승인/거절" 패턴으로 노출한다."""
    items = from_missing_account_codes(build_result.get("missing_account_codes", []))
    items += from_drifted_prior_year_rows(build_result.get("drifted_prior_year_rows", []))
    if demo_manifest_path is not None:
        items.append(demo_fee_contract_item(demo_manifest_path))
    if teuksu_manifest_path is not None:
        items.append(demo_document_item(teuksu_manifest_path, "특수관계자거래"))
    if dambo_manifest_path is not None:
        items.append(demo_document_item(dambo_manifest_path, "담보제공자산"))
    return items
