"""AI 근거검색 -- '수수료비용' 같은 승인형 플래그 항목에 대해, 후보 근거문서
몇 개를 찾아서 원문 그대로 보여주기 위한 임베딩 기반 검색, 그리고 1등 후보의
실제 내용에 근거한 반영 제안 한 줄까지 생성한다.

AI의 역할은 "찾기 + 순위 매기기 + (원문에 근거한) 제안"까지다. 제안은 반드시
후보 원문에 실제로 있는 내용만 인용해야 하고, 없는 걸 지어내면 안 된다 --
사람은 그 제안에 대해 승인/거절만 한다 (audit-copilot의 감사기준서 RAG와
같은 원칙: 모델이 지어내지 않고 원문에 근거해서만 말한다. 2026-07-22 대화에서
"결론 초안"이 아니라 "이렇게 반영하면 될 것 같은데 승인하시겠습니까?" 형태로
명확히 하기로 함).

audit-copilot/rag_search.py의 cosine-similarity 패턴과
bank-recon-agent/gemini_agent.py의 429 재시도 패턴을 재사용한다. 이 코퍼스는
문서 6개짜리 작은 데모 자료라, audit-copilot처럼 임베딩을 파일로 저장해두지
않고 호출마다 새로 임베딩한다.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pypdf
from google import genai
from google.genai import errors as genai_errors

EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MAX_QUOTA_RETRIES = 2


def read_document_text(path: str | Path) -> str:
    """실물 계약서는 PDF로 온다는 걸 보여주기 위해 데모 자료를 PDF로 바꿨다 --
    .txt는 그대로 읽고 .pdf는 텍스트를 추출한다 (임베딩 검색용 텍스트가
    필요할 뿐, 레이아웃은 필요 없어서 pypdf 정도로 충분)."""
    return "\n".join(read_document_pages(path))


def read_document_pages(path: str | Path) -> list[str]:
    """페이지별로 텍스트를 나눠 읽는다 -- 실제 계약서처럼 여러 조항 중
    필요한 조항이 특정 페이지에만 있는 경우, AI가 "몇 페이지인지"까지
    답하게 하려면 페이지 경계가 필요하다. txt는 페이지 개념이 없어서
    통째로 1페이지 취급."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        reader = pypdf.PdfReader(str(p))
        return [page.extract_text() or "" for page in reader.pages]
    return [p.read_text(encoding="utf-8")]


@dataclass(frozen=True)
class Candidate:
    doc_path: str
    text: str
    score: float


def _retry_delay_seconds(error: genai_errors.ClientError, default: float = 20.0) -> float:
    """429 응답의 RetryInfo에서 권장 대기 시간을 읽는다. 못 찾으면 기본값을 쓴다."""
    try:
        for detail in error.details.get("error", {}).get("details", []):
            if detail.get("@type", "").endswith("RetryInfo"):
                delay = detail.get("retryDelay", "")
                return float(delay.rstrip("s")) + 1
    except (AttributeError, ValueError):
        pass
    return default


def _embed_with_retry(client: genai.Client, *, contents) -> np.ndarray:
    for attempt in range(MAX_QUOTA_RETRIES + 1):
        try:
            result = client.models.embed_content(model=EMBEDDING_MODEL, contents=contents)
            return np.array([e.values for e in result.embeddings], dtype=np.float32)
        except genai_errors.ClientError as e:
            if e.code != 429 or attempt == MAX_QUOTA_RETRIES:
                raise
            time.sleep(_retry_delay_seconds(e))


def search_texts(query: str, items: list[tuple[str, str]], top_k: int = 3) -> list[Candidate]:
    """query와 가장 관련 있는 항목 top_k개를 (label, searchable_text) 목록에서 찾는다.

    범용 코어 -- PDF/txt 원문이든, CSV 파일을 요약한 텍스트(파일명+컬럼+샘플행)든
    상관없이 "검색에 쓸 텍스트"만 주면 된다. 실제 사용자에게 뭘 보여줄지(원문
    그대로 vs 그 파일의 실제 데이터 표)는 호출하는 쪽이 label로 후속 조회해서
    알아서 결정한다 -- 이 함수는 "가장 관련 있는 걸 찾기"까지만 담당.

    확신도 임계값을 따로 두지 않는다 -- 상위 top_k개를 항상 후보로 반환하고,
    최종적으로 어느 게 맞는지는 사람이 원문을 보고 고른다.
    """
    client = genai.Client()
    labels = [label for label, _ in items]
    texts = [text for _, text in items]

    doc_embeddings = _embed_with_retry(client, contents=texts)
    query_embedding = _embed_with_retry(client, contents=[query])[0]

    norms = np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
    scores = (doc_embeddings @ query_embedding) / norms

    top_idx = np.argsort(-scores)[:top_k]
    return [
        Candidate(doc_path=labels[i], text=texts[i], score=float(scores[i]))
        for i in top_idx
    ]


def search(query: str, doc_paths: list[str], top_k: int = 3) -> list[Candidate]:
    """search_texts()의 파일 경로 버전 -- 파일 전체를 그대로 검색 텍스트로 쓴다
    (수수료비용 데모처럼 파일 자체가 짧은 원문 텍스트일 때 적합)."""
    items = [(p, read_document_text(p)) for p in doc_paths]
    return search_texts(query, items, top_k=top_k)


@dataclass(frozen=True)
class Proposal:
    text: str
    page: int | None  # 1-based -- 문서 안에서 근거를 찾은 페이지. 못 찾으면 None.


def _parse_proposal_json(raw: str) -> Proposal:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
        page = data.get("page")
        return Proposal(text=str(data.get("proposal", "")).strip(), page=int(page) if page else None)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        # JSON 파싱이 실패해도 사람이 읽을 텍스트는 그대로 살려서 보여준다.
        return Proposal(text=raw, page=None)


def generate_proposal(query: str, doc_path: str) -> Proposal:
    """후보 문서 전체(페이지별로 라벨링)를 AI에게 주고, ①"{query}"와 관련된
    조항이 몇 페이지에 있는지, ②그 페이지 내용에만 근거한 반영 제안을
    한 번에 받는다. 실제 계약서처럼 관련 없는 조항도 여러 개 섞여 있는
    상황을 전제로 한다 -- AI가 몇 페이지인지 직접 찾아야 프론트에서 PDF
    뷰어를 그 페이지로 바로 넘겨줄 수 있다.

    프롬프트로 "그 페이지에 없는 내용은 지어내지 말 것"을 강제하지만, LLM
    출력이라 100% 보장은 아니다 -- 그래서 원본 문서를 항상 같이 보여주고,
    사람이 검토 후 승인/거절하는 구조를 유지한다."""
    pages = read_document_pages(doc_path)
    labeled = "\n\n".join(f"[{i + 1}페이지]\n{text}" for i, text in enumerate(pages))
    client = genai.Client()
    prompt = f"""당신은 회계감사 보조원입니다. 아래는 "{query}"와 관련해서 찾은 원본 문서 전체입니다
(페이지별로 표시됨). 이 문서에는 관련 없는 다른 조항들도 섞여 있습니다.

---
{labeled}
---

1. 이 문서에서 "{query}"와 직접 관련된 조항이 있는 페이지 번호를 찾으세요.
2. 그 페이지 내용에만 근거해서, 담당 회계사가 승인/거절 버튼만 누르면 되도록
   한국어 1~2문장으로 반영 제안을 작성하세요. 그 페이지에 실제로 나온 숫자·
   사실만 인용하고, 지어내지 마세요. 반드시 "...것으로 확인되어, ...하는
   것을 제안합니다" 형태의 문장으로 끝내세요.

다음 JSON 형식으로만 답하세요 (다른 텍스트 없이):
{{"page": <페이지번호(정수)>, "proposal": "<제안 문장>"}}"""
    for attempt in range(MAX_QUOTA_RETRIES + 1):
        try:
            result = client.models.generate_content(model=GENERATION_MODEL, contents=prompt)
            return _parse_proposal_json((result.text or "").strip())
        except genai_errors.ClientError as e:
            if e.code != 429 or attempt == MAX_QUOTA_RETRIES:
                raise
            time.sleep(_retry_delay_seconds(e))
    return Proposal(text="", page=None)


def stub_search_texts(query: str, items: list[tuple[str, str]], top_k: int = 3) -> list[Candidate]:
    """API 키가 없거나 호출이 실패할 때 쓰는 키워드매칭 폴백.
    search_texts()와 같은 인터페이스 -- 진짜 임베딩 검색 대신 텍스트에 검색어
    단어가 몇 번 등장하는지로 순위를 매긴다."""
    keywords = [w for w in query.replace("(", " ").replace(")", " ").split() if len(w) > 1]
    scored = [
        Candidate(doc_path=label, text=text, score=float(sum(text.count(k) for k in keywords)))
        for label, text in items
    ]
    scored.sort(key=lambda c: -c.score)
    return scored[:top_k]
