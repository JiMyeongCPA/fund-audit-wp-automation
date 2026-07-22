"""이번 펀드(샘플펀드)의 실제 PBC 원자료 11개를 AI 검색 대상 풀로 구성한다.

fee_contract_search.search_texts()/stub_search_texts()에 넣을
(라벨, 검색용 요약 텍스트) 목록을 만든다. 요약 텍스트는 파일 원본 전체가
아니라 컬럼명 + 샘플 몇 행만 담는다 -- CSV 원본을 통째로 임베딩하면 숫자
위주라 의미 검색에 별 도움이 안 되고, 파일 하나가 수백~수천 행이라
비효율적이기도 하다. label은 실제 파일 경로(str)라서, 검색 후 바로 그
파일을 다시 읽어 원본 데이터를 보여주는 데 그대로 쓸 수 있다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from core import (
    bosubunbae,
    chaegwon,
    gajungpyeonggyunjwasu,
    gijunkagyeok,
    gungnaejusik,
    gungnaeyudong,
    ilbyeoljasan,
    pundbyeolmyeongse,
    seoljeongheji,
    seonmul,
    sooikjeunggwon,
)

# 모듈별 실제 fixture 파일명에 포함된 키워드 -- module.SHEET_NAME(조서 내
# 시트명)이랑 실제 PBC 파일명이 다른 경우가 있어서 (예: sooikjeunggwon의
# SHEET_NAME은 "수익증권명세"인데 파일명은 "국내집합투자증권명세") 따로 명시.
_FIXTURE_KEYWORDS = {
    gijunkagyeok: "기준가격대장(결산후)",
    gungnaeyudong: "국내유동명세",
    gungnaejusik: "국내주식명세",
    pundbyeolmyeongse: "펀드별명세",
    sooikjeunggwon: "국내집합투자증권명세",
    seonmul: "국내선물명세",
    chaegwon: "채권명세",
    gajungpyeonggyunjwasu: "일별좌수순자산현황",
    bosubunbae: "판매보수내역",
    ilbyeoljasan: "일별자산내역",
    seoljeongheji: "설정해지내역",
}


def _find_fixture(fixtures_dir: Path, keyword: str) -> Path | None:
    matches = [p for p in fixtures_dir.glob("*.csv") if keyword in p.name]
    return matches[0] if matches else None


def find_by_sheet_name(fixtures_dir: Path, sheet_name: str) -> str | None:
    """C2 등의 수식이 참조하는 워크북 시트명(예: '수익증권명세', module.SHEET_NAME
    과 동일)으로 원본 PBC 파일을 찾는다 -- AI 검색 없이 수식만으로 100%
    확정적으로 원본을 찾을 수 있는 경우에 쓴다."""
    for module, keyword in _FIXTURE_KEYWORDS.items():
        if module.SHEET_NAME == sheet_name:
            path = _find_fixture(fixtures_dir, keyword)
            return str(path) if path else None
    return None


def build_library(fixtures_dir: Path, sample_n: int = 3) -> list[tuple[str, str]]:
    """[(파일 경로, 검색용 요약)] 목록을 반환. 파싱 실패하거나 파일이 없는
    항목은 조용히 건너뛴다 (다른 세션이 아직 안 만든 fixture일 수도 있음)."""
    items: list[tuple[str, str]] = []
    for module, keyword in _FIXTURE_KEYWORDS.items():
        path = _find_fixture(fixtures_dir, keyword)
        if path is None:
            continue
        try:
            df = module.parse(str(path))
        except Exception:  # noqa: BLE001
            continue

        cols = ", ".join(str(c).strip() for c in df.columns[:10])
        sample_lines = [
            ", ".join(str(v) for v in row.values[:8]) for _, row in df.head(sample_n).iterrows()
        ]
        summary = f"{module.SHEET_NAME} ({path.name})\n컬럼: {cols}\n샘플 데이터:\n" + "\n".join(sample_lines)
        items.append((str(path), summary))
    return items


def load_table_preview(path: str, sample_n: int | None = None) -> dict:
    """검색으로 찾아낸 파일 경로 하나를 받아서, 사람에게 보여줄 실제 데이터
    미리보기(컬럼+행)를 만든다. build_library()의 요약 텍스트는 검색
    전용이라 사람이 보기엔 부족해서, 후보로 뽑힌 파일은 이 함수로 원본
    그대로 다시 읽는다. `sample_n=None`(기본값)이면 전체 행/컬럼을 다 보여준다
    -- 원본 PBC 표를 일부만 보여줄 이유가 없고, 프론트엔드 DataTable이
    확대/스크롤을 이미 지원한다."""
    p = Path(path)
    module = next((m for m, kw in _FIXTURE_KEYWORDS.items() if kw in p.name), None)
    if module is None:
        return {"columns": [], "sampleRows": []}

    df = module.parse(str(p))
    col_idx = list(range(len(df.columns)))
    seen: dict[str, int] = {}
    clean_names = []
    for i in col_idx:
        name = str(df.columns[i]).strip() or f"col{i}"
        seen[name] = seen.get(name, 0) + 1
        clean_names.append(name if seen[name] == 1 else f"{name}_{seen[name]}")

    view = df if sample_n is None else df.head(sample_n)
    rows = []
    for _, row in view.iterrows():
        rows.append(
            {name: ("" if pd.isna(row.iloc[idx]) else str(row.iloc[idx])) for name, idx in zip(clean_names, col_idx)}
        )
    return {"columns": clean_names, "sampleRows": rows}
