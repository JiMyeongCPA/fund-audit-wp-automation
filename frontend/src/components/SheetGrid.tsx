import { useEffect, useMemo, useState } from "react"
import { Minus, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { fetchSheet } from "@/api"
import type { SheetCell, SheetData } from "@/api"

const MIN_ZOOM = 0.5
const MAX_ZOOM = 2
const ZOOM_STEP = 0.1

/** 0-based 열 인덱스를 엑셀 열 이름(A, B, ..., Z, AA, AB, ...)으로 변환. */
function columnLetter(index: number): string {
  let n = index + 1
  let s = ""
  while (n > 0) {
    const rem = (n - 1) % 26
    s = String.fromCharCode(65 + rem) + s
    n = Math.floor((n - 1) / 26)
  }
  return s
}

// build_workpaper()가 만드는 raw-PBC 시트 11개 -- 수식이 이 중 하나를
// 가리키면 AI 검색 없이 그 파일을 바로 확정적으로 보여줄 수 있다.
const KNOWN_PBC_SHEETS = new Set([
  "기준가격대장(결산후)",
  "국내유동명세",
  "국내주식명세",
  "펀드별명세",
  "수익증권명세",
  "선물명세",
  "채권명세",
  "가중평균좌수",
  "보수분배내역",
  "일별자산내역",
  "설정해지내역",
])
// 단순 참조(=시트!셀)뿐 아니라 SUMIF(시트!$C:$C, ...) 같이 함수 안에 시트
// 참조가 들어간 경우도 잡기 위해 문자열 시작에 고정하지 않고 어디든 찾는다.
// 두 갈래로 나뉜다: ①따옴표로 감싼 시트명('기준가격대장(결산후)'!F345처럼
// 이름 자체에 괄호/공백이 들어간 경우 -- 따옴표 안은 통째로 캡처해야 하므로
// 괄호를 제외하면 안 된다) ②안 감싼 단순 이름(국내주식명세!B3, 또는
// SUMIF(국내유동명세!$C:$C,...)) -- "="와 "(" 둘 다 제외 문자에 넣어야
// "=국내주식명세!B3"에서 "="까지 같이 캡처되거나 SUMIF( 안쪽 참조를 놓치는
// 걸 막는다. 문자열에서 먼저 나오는 쪽이 매치된다.
const FORMULA_SHEET_REF = /'([^']+)'!|([^'!(),\s=]+)!/
const FORMULA_SHEET_REF_G = /'([^']+)'!|([^'!(),\s=]+)!/g

function formulaSheetRef(formula: string | null): string | null {
  if (!formula) return null
  const m = FORMULA_SHEET_REF.exec(formula)
  const sheet = m?.[1] ?? m?.[2]
  return sheet && KNOWN_PBC_SHEETS.has(sheet) ? sheet : null
}

/** 주어진 행 범위(엑셀 1-based, 양끝 포함)에서 참조된 원본 PBC 시트를 전부
 * (중복 없이) 모은다. C2/C1처럼 어느 시트인지 하드코딩 없이 확정할 수 있는
 * 경우와 달리, 아직 조서가 미완성이라 그 블록 자체가 여러 원본 중 뭐가
 * 맞는지 애매한 블록(C3_수익의 "이자수익 재계산" 등)을 위한 것 -- 행마다
 * 다르게 좁히지 않고, 그 블록에서 발견되는 모든 후보를 통째로 보여준다. */
function allKnownSheetsInExcelRange(rows: SheetCell[][], [start, end]: [number, number]): string[] {
  const found: string[] = []
  for (let excelRow = start; excelRow <= end; excelRow++) {
    const row = rows[excelRow - 1]
    if (!row) continue
    for (const cell of row) {
      if (!cell.f) continue
      for (const m of cell.f.matchAll(FORMULA_SHEET_REF_G)) {
        const sheet = m[1] ?? m[2]
        if (sheet && KNOWN_PBC_SHEETS.has(sheet) && !found.includes(sheet)) found.push(sheet)
      }
    }
  }
  return found
}

// C2_자산부채평가의 각 블록은 "N. 블록명" / "(N) 블록명" / "N-1. 블록명" 같은
// 캡션 행으로 시작한다 (core/c2_blocks.py의 write_block 컨벤션). 캡션/합계
// 행 자체는 수식이 없어서, 아래 computeRowFormulaSheets가 블록 범위를 훑어서
// 채워준다. 예금/거래소주식/채권/수익증권 전부 이 방식 하나로만 처리된다 --
// 예전엔 항목별로 하드코딩된 "결정형"/AI 검색 경로가 따로 있었지만, C2 데이터
// 셀들이 원본 PBC 시트를 전부 수식으로 직접 참조한다는 게 확인되면서
// (2026-07-22) 전부 여기로 통합됐다.
const CAPTION_ROW_PATTERN = /^\(?\d+(-\d+)?\)?\.?\s*\S/

/** 셀 단위 수식 인식을 블록 단위로 확장한다. 캡션 행 자체는 수식이 없어서
 * 못 잡히니까, 캡션마다 범위를 훑어서 그 안에서 처음 발견되는 수식의 참조
 * 시트를 그 블록 전체(캡션+빈 줄 포함)에 적용한다.
 *
 * 캡션은 "N. 이름"(최상위, depth 0)과 "(N) 이름"(하위, depth 1) 두 단계로
 * 중첩된다 (예: "3. 거래소주식, 코스닥주식" 안에 "(1) 거래소주식"/
 * "(2) 코스닥주식"이 들어있고, 실제 데이터/수식은 하위 캡션 밑에 있음).
 * 그래서 "다음 캡션 아무거나"에서 범위를 끊으면 최상위 캡션 행은 하위
 * 캡션 직전의 빈 구간만 보게 되어 수식을 못 찾는다 -- 대신 "depth가 같거나
 * 낮은 다음 캡션"까지 훑어야 최상위 캡션도 자기 하위 블록의 데이터까지
 * 도달한다.
 *
 * 블록마다 다음 블록과 한 행씩 공백을 두는 게 원래 조서 설계다 -- 그 공백
 * 행까지 이 블록 것으로 채워버리면 블록 사이 경계가 시각적으로 안 보이게
 * 된다. 그래서 다음 캡션 직전에 완전히 빈 행(어느 컬럼에도 값이 없는 행)이
 * 있으면 그만큼 뒤에서부터 잘라내고 채운다.
 *
 * 상위 캡션은 하위 캡션들 속까지 훑어서 수식을 "찾기"는 하지만(그래야
 * "3. 거래소주식, 코스닥주식"처럼 자기 자신은 수식이 없는 상위 캡션도 클릭됨),
 * 그 결과를 "채우는" 범위는 첫 하위 캡션 직전까지로 제한한다 -- 안 그러면
 * 하위 캡션들 사이(예: "(1) 거래소주식"과 "(2) 코스닥주식" 사이) 공백까지
 * 상위 블록이 대신 채워버려서, 그 공백에 대한 트리밍이 무력화된다. 하위
 * 캡션 자기 영역은 각자 자기 차례에 알아서 채운다(자기 수식이 없으면 안
 * 채워지는 것도 맞음 -- 다른 보유 0 블록들과 같은 원칙). */
/** 캡션 기반 블록 탐색의 공통 뼈대 -- "이 블록은 어느 시트에서 왔는가"를
 * 판단하는 방법(resolveRow)만 갈아끼울 수 있게 분리했다. C2는 셀 자기
 * 수식만 보면 되지만(resolveRow = formulaSheetRef 스캔), C5_F.N은 그것만으론
 * 부족해서(아래 참고) 직접 참조 + C2 경유 2단계 참조를 모두 시도하는
 * resolveRow를 넘겨 재사용한다. */
function computeBlockFormulaSheets(
  rows: SheetCell[][],
  resolveRow: (row: SheetCell[]) => string | null
): (string | null)[] {
  const captions: { row: number; depth: number }[] = []
  rows.forEach((row, r) => {
    const text = row[2]?.v.trim() ?? ""
    if (CAPTION_ROW_PATTERN.test(text)) captions.push({ row: r, depth: text.startsWith("(") ? 1 : 0 })
  })

  const result: (string | null)[] = new Array(rows.length).fill(null)
  captions.forEach(({ row: start, depth }, i) => {
    let end = rows.length
    for (let j = i + 1; j < captions.length; j++) {
      if (captions[j].depth <= depth) {
        end = captions[j].row
        break
      }
    }
    let sheet: string | null = null
    for (let r = start; r < end && !sheet; r++) {
      sheet = resolveRow(rows[r])
    }
    // 다음 블록과의 경계에 있는 빈 행(공백 한 칸)은 이 블록 범위에서 뺀다.
    let fillEnd = end
    while (fillEnd > start && rows[fillEnd - 1].every((cell) => cell.v.trim() === "")) fillEnd--
    // 바로 다음 캡션이 이것보다 깊으면(=자기 하위 캡션이면), 거기서부터는
    // 그 하위 캡션이 스스로 책임질 영역이니 이 블록은 거기까지만 채운다.
    const next = captions[i + 1]
    if (next && next.row < end && next.depth > depth) fillEnd = Math.min(fillEnd, next.row)
    // 얕은(상위) 캡션부터 처리되므로, 하위 캡션이 나중에 자기 범위를 더
    // 좁고 정확하게 덮어써도 안전하다.
    if (sheet) for (let r = start; r < fillEnd; r++) result[r] = sheet
  })
  return result
}

function directSheetInRow(row: SheetCell[]): string | null {
  for (const cell of row) {
    const sheet = formulaSheetRef(cell.f)
    if (sheet) return sheet
  }
  return null
}

function computeRowFormulaSheets(rows: SheetCell[][]): (string | null)[] {
  return computeBlockFormulaSheets(rows, directSheetInRow)
}

/** 캡션 텍스트로 그 캡션이 담당하는 행 범위([start, end), 0-based)를 찾는다.
 * 특수관계자거래/담보제공자산처럼 원본 PBC 참조가 아예 없는(AI 근거검색
 * 데모 문서로 대신하는) 블록을 통째로 식별하는 데 쓴다 -- computeBlockFormulaSheets와
 * 같은 "얕거나 같은 depth의 다음 캡션까지" 규칙을 그대로 따른다. */
function captionBlockRange(rows: SheetCell[][], captionSubstring: string): [number, number] | null {
  const captions: { row: number; depth: number }[] = []
  rows.forEach((row, r) => {
    const text = row[2]?.v.trim() ?? ""
    if (CAPTION_ROW_PATTERN.test(text)) captions.push({ row: r, depth: text.startsWith("(") ? 1 : 0 })
  })
  const idx = captions.findIndex((c) => (rows[c.row][2]?.v ?? "").includes(captionSubstring))
  if (idx === -1) return null
  const { row: start, depth } = captions[idx]
  let end = rows.length
  for (let j = idx + 1; j < captions.length; j++) {
    if (captions[j].depth <= depth) {
      end = captions[j].row
      break
    }
  }
  // 다음 블록과의 경계에 있는 빈 행(공백 한 칸)은 이 블록 범위에서 뺀다 --
  // computeBlockFormulaSheets와 같은 규칙(그 함수에선 이미 하고 있었는데,
  // 이 함수엔 빠져 있어서 특수관계자거래/담보제공자산 블록 사이 공백 행이
  // 앞 블록 것으로 잘못 딸려가 "근거 있음"으로 보였던 버그).
  while (end > start && rows[end - 1].every((cell) => cell.v.trim() === "")) end--
  return [start, end]
}

// C1_정산표는 원본 PBC 파일로 근거를 찾는 시트가 아니다 -- 여기서 하는
// 작업 자체가 전기 재무제표 값을 손으로 입력하는 것이라, 근거는
// core/prior_year_source.py가 같은 참조 워크북의 전기(I/J) 컬럼에서
// 재구성한 "전기 재무상태표"/"전기 손익계산서" 데이터다. 행 범위는
// prior_year_source.py의 BS_RANGE/IS_RANGE(9~66, 73~118, Excel 1-based)를
// 그대로 따른다 -- 이 시트는 build_workpaper()에서도 참조 워크북에서
// 그대로 복사되기 때문에(c2처럼 새로 조립되지 않음) 행 번호가 안정적이다.
// <C.E>(자본변동표, Statement of Changes in Equity) 구간도 마찬가지 원리 --
// core/prior_year_source.py의 CAPITAL_STATEMENT_ROWS(126~132, Excel
// 1-based)를 담고 있는 시각적 블록(<C.E> 라벨~전기 주석 캡션)과, 바로 이어지는
// 당기 자본변동 내역 블록(135~146행, "2023년1월1일(당기초)"~"(주석11)")까지
// 함께 클릭 범위로 잡는다 -- B/S·I/S와 마찬가지로, 당기 쪽을 클릭해도 보여줄
// "근거"는 재구성 가능한 전기 값 하나뿐이라 같은 전기 자본변동표를 보여준다.
const C2_ASSET_SHEET = "C2_자산부채평가"
const C1_SETTLEMENT_SHEET = "C1_정산표"
const C1_BS_RANGE: [number, number] = [9, 66]
const C1_IS_RANGE: [number, number] = [73, 118]
const C1_CE_RANGE: [number, number] = [123, 146]

// 자펀드1~10 목록(153~167행, core/prior_year_source.py가 다루지 않는 별도
// 구간): 실제로는 자펀드1만 =SUM(설정해지내역!...) 수식을 갖고 있고 나머지는
// 빈 템플릿 행이다. 블록 전체 어디를 클릭해도 그 수식을 찾아 보여주도록,
// C2의 캡션 기반 블록 탐색과 같은 원리를 고정된 행 범위로 적용한다.
const C1_SUBFUND_RANGE: [number, number] = [153, 167]

// 재무제표검증도 C1_정산표와 같은 이유로 원본 PBC가 아니라 참조 워크북에서
// 그대로 복사된 시트(core/assemble.py 참고) -- 재무상태표/손익계산서/
// 자본변동표 형식으로 원본 재무제표 리터럴 수치를 재배열해 대사하는 용도라,
// 여기서 보여줄 "근거"도 C1과 동일하게 prior_year_source가 재구성한 전기
// 값이다. 행 범위는 build된 시트를 직접 훑어 확인(안정적 -- 참조 워크북에서
// 그대로 복사되므로 c2처럼 행 수가 안 바뀜).
const FS_CHECK_SHEET = "재무제표검증"
const FS_BS_RANGE: [number, number] = [8, 43]
const FS_IS_RANGE: [number, number] = [52, 83]
const FS_CE_RANGE: [number, number] = [92, 109]

function fsCheckSectionForExcelRow(excelRow: number): string | null {
  if (excelRow >= FS_BS_RANGE[0] && excelRow <= FS_BS_RANGE[1]) return "재무상태표"
  if (excelRow >= FS_IS_RANGE[0] && excelRow <= FS_IS_RANGE[1]) return "손익계산서"
  if (excelRow >= FS_CE_RANGE[0] && excelRow <= FS_CE_RANGE[1]) return "자본변동표"
  return null
}

// C3_수익의 "이자수익 재계산" 블록만 -- 시트 맨 위 펀드명/작성자 같은 머리말
// 행(1~7행)이나 다른 향후 블록까지 싸잡아 후보를 보여주면 안 된다. "이자수익
// 재계산" 캡션 행(13행) 자체는 빼고, 14행부터 "합계"(26행)까지만 범위로 잡는다.
const C3_INCOME_SHEET = "C3_수익"
const C3_INTEREST_RECALC_RANGE: [number, number] = [14, 26]

// C5_F.N(주석) C열은 대부분 짧은 라벨/숫자지만, 서술형 주석 문단이 섞여 있는
// 행이 있어서(예: 신탁계약기간 관련 문장 하나가 160자+) 그 한 셀 때문에 HTML
// 표 특성상 열 전체 폭이 늘어난다 -- 이 시트의 C열만 줄바꿈을 허용하고 폭을
// 제한한다 (다른 시트는 nowrap 그대로 유지).
const C5_NOTES_SHEET = "C5_F.N"
const C5_WRAP_COLUMN_INDEX = 2

// 특수관계자거래/담보제공자산은 원본 PBC 참조가 아예 없어(core/c5_teuksu_note.py,
// core/c5_dambo_note.py) C2 경유든 직접참조든 이 파일의 다른 근거 해소
// 방식으로는 절대 못 찾는다 -- 대신 api.py가 core/flagged_items.py를 통해
// AI 근거검색 데모 항목(fee_contract_search 패턴)으로 노출해둔 것과
// 정확히 같은 항목을 가리킨다. id는 core/flagged_items.py의
// demo_document_item(..., id_prefix)가 만드는 "demo::<id_prefix>"와 일치해야
// 한다.
const TEUKSU_CAPTION = "특수관계자와의 거래"
const TEUKSU_ITEM_ID = "demo::특수관계자거래"
const DAMBO_CAPTION = "담보제공자산"
const DAMBO_ITEM_ID = "demo::담보제공자산"

// C5_F.N의 각 주석은 PBC 원본을 직접 참조하지 않고 이미 조립된
// 'C2_자산부채평가'!<셀>을 참조한다(core/c5_*_note.py 전부 이 패턴) -- 그래서
// C5 수식만 봐서는 KNOWN_PBC_SHEETS에 안 걸린다. 참조된 C2 행 번호를 뽑아서,
// C2에서 이미 쓰는 캡션 블록 조회(computeRowFormulaSheets)를 그 행에 대해
// 한 번 더 태우면(2단계 조회) 원본 PBC 시트까지 따라갈 수 있다.
const C2_ROW_REF = /'C2_자산부채평가'!\$?[A-Z]+\$?(\d+)/

function extractC2RowRef(formula: string | null): number | null {
  if (!formula) return null
  const m = C2_ROW_REF.exec(formula)
  return m ? parseInt(m[1], 10) : null
}

function rowWideC2RowRef(row: SheetCell[]): number | null {
  for (const cell of row) {
    const rowNum = extractC2RowRef(cell.f)
    if (rowNum != null) return rowNum
  }
  return null
}

function priorYearSectionForExcelRow(excelRow: number): string | null {
  if (excelRow >= C1_BS_RANGE[0] && excelRow <= C1_BS_RANGE[1]) return "재무상태표"
  if (excelRow >= C1_IS_RANGE[0] && excelRow <= C1_IS_RANGE[1]) return "손익계산서"
  if (excelRow >= C1_CE_RANGE[0] && excelRow <= C1_CE_RANGE[1]) return "자본변동표"
  return null
}

function findFormulaSheetInExcelRange(rows: SheetCell[][], [start, end]: [number, number]): string | null {
  for (let excelRow = start; excelRow <= end; excelRow++) {
    const row = rows[excelRow - 1]
    if (!row) continue
    for (const cell of row) {
      const sheet = formulaSheetRef(cell.f)
      if (sheet) return sheet
    }
  }
  return null
}

export type CellSelectResult =
  | { kind: "formula"; sheet: string }
  | { kind: "formula-multi"; sheets: string[] }
  | { kind: "prior-year"; section: string }
  | { kind: "flagged-item"; id: string }
  | { kind: "none" }

export function SheetGrid({
  sheetName,
  onCellSelect,
  refreshToken,
}: {
  sheetName: string
  onCellSelect?: (result: CellSelectResult) => void
  // 승인/반려 후 시트 값이 바뀌면(특수관계자거래/담보제공자산) 이 값이 올라가고,
  // 그때 시트를 다시 불러온다.
  refreshToken?: number
}) {
  const [data, setData] = useState<SheetData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const [selected, setSelected] = useState<{ r: number; c: number; cell: SheetCell } | null>(null)

  useEffect(() => {
    setData(null)
    setError(null)
    setSelected(null)
    fetchSheet(sheetName)
      .then(setData)
      .catch((e) => setError(String(e)))
  }, [sheetName, refreshToken])

  const isSettlementSheet = sheetName === C1_SETTLEMENT_SHEET
  const isAssetSheet = sheetName === C2_ASSET_SHEET

  // 캡션 기반 블록 탐색(computeRowFormulaSheets)은 C2 전용이다 -- "N. 블록명"
  // 캡션 컨벤션이 C2에만 있고, 다른 시트(C3_수익 등)는 컬럼 C에 소수점 숫자
  // (예: "44110508.334246576")가 들어있어서 캡션 패턴이 우연히 매치돼버리는
  // 문제가 있었다 -- 그 시트들은 셀 자기 수식만으로 이미 충분하다.
  const rowFormulaSheets = useMemo(() => {
    if (!data || !onCellSelect || !isAssetSheet) return []
    return computeRowFormulaSheets(data.rows)
  }, [data, onCellSelect, isAssetSheet])

  const subfundFormulaSheet = useMemo(() => {
    if (!data || !onCellSelect || !isSettlementSheet) return null
    return findFormulaSheetInExcelRange(data.rows, C1_SUBFUND_RANGE)
  }, [data, onCellSelect, isSettlementSheet])

  const isFsCheckSheet = sheetName === FS_CHECK_SHEET
  const isNotesSheet = sheetName === C5_NOTES_SHEET

  // C5_F.N을 볼 때만, 화면에 표시하진 않지만 참조 해소용으로 C2_자산부채평가
  // 데이터를 따로 받아온다.
  const [c2Data, setC2Data] = useState<SheetData | null>(null)
  useEffect(() => {
    if (!onCellSelect || !isNotesSheet) {
      setC2Data(null)
      return
    }
    fetchSheet(C2_ASSET_SHEET)
      .then(setC2Data)
      .catch(() => setC2Data(null))
  }, [onCellSelect, isNotesSheet])

  const c2RowFormulaSheets = useMemo(() => {
    if (!c2Data) return []
    return computeRowFormulaSheets(c2Data.rows)
  }, [c2Data])

  // C5_F.N도 C2처럼 "N. 노트명" 캡션으로 블록이 나뉜다(core/c5_*_note.py
  // 전부 동일 컨벤션) -- 그런데 노트마다 원본을 찾는 방식이 다르다: 파생상품/
  // 환매조건부매도는 PBC 원본(선물명세/국내유동명세)을 직접 참조하고,
  // 지분증권/채권/수익증권은 C2_자산부채평가를 거쳐 참조한다(2단계). 그래서
  // 두 방식을 다 시도하는 resolveRow를 넘겨서, 캡션 블록 전체(합계 행·빈
  // 버퍼 행처럼 그 자체론 참조가 없는 행 포함)에 같은 근거를 채운다 -- C2에서
  // 이미 하는 것과 똑같은 이유(그 블록 어디를 클릭해도 같은 근거가 나와야
  // 자연스럽다).
  const c5RowFormulaSheets = useMemo(() => {
    if (!data || !onCellSelect || !isNotesSheet) return []
    return computeBlockFormulaSheets(data.rows, (row) => {
      const direct = directSheetInRow(row)
      if (direct) return direct
      const c2Row = rowWideC2RowRef(row)
      return c2Row != null ? c2RowFormulaSheets[c2Row - 1] ?? null : null
    })
  }, [data, onCellSelect, isNotesSheet, c2RowFormulaSheets])

  const teuksuRange = useMemo(() => {
    if (!data || !onCellSelect || !isNotesSheet) return null
    return captionBlockRange(data.rows, TEUKSU_CAPTION)
  }, [data, onCellSelect, isNotesSheet])

  const damboRange = useMemo(() => {
    if (!data || !onCellSelect || !isNotesSheet) return null
    return captionBlockRange(data.rows, DAMBO_CAPTION)
  }, [data, onCellSelect, isNotesSheet])

  const isIncomeSheet = sheetName === C3_INCOME_SHEET

  // C3_수익의 "이자수익 재계산" 블록: 그 블록 범위 안에서 원본 후보를 한 번만
  // 모아서, 블록 안 어디를 클릭하든 같은 후보 목록을 보여준다 -- 행마다
  // 다르게 보이면(어떤 행은 후보 1개, 어떤 행은 2개, 어떤 행은 0개) 오히려
  // 더 헷갈린다는 피드백 반영. 시트 전체가 아니라 이 블록에만 적용된다.
  const blockAllSheets = useMemo(() => {
    if (!data || !onCellSelect || !isIncomeSheet) return []
    return allKnownSheetsInExcelRange(data.rows, C3_INTEREST_RECALC_RANGE)
  }, [data, onCellSelect, isIncomeSheet])

  const columnCount = useMemo(() => {
    if (!data) return 0
    return data.rows.reduce((max, row) => Math.max(max, row.length), 0)
  }, [data])

  if (error) return <div className="p-4 text-sm text-destructive">{error}</div>
  if (!data) return <div className="p-4 text-sm text-muted-foreground">불러오는 중...</div>

  return (
    <div className="flex h-full flex-col gap-1.5">
      <div className="flex shrink-0 items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          <Button variant="outline" size="icon" className="h-6 w-6" onClick={() => setZoom((z) => Math.max(MIN_ZOOM, +(z - ZOOM_STEP).toFixed(1)))}>
            <Minus className="h-3 w-3" />
          </Button>
          <button
            className="w-12 text-center text-xs text-muted-foreground hover:underline"
            onClick={() => setZoom(1)}
          >
            {Math.round(zoom * 100)}%
          </button>
          <Button variant="outline" size="icon" className="h-6 w-6" onClick={() => setZoom((z) => Math.min(MAX_ZOOM, +(z + ZOOM_STEP).toFixed(1)))}>
            <Plus className="h-3 w-3" />
          </Button>
        </div>
        {onCellSelect && (
          <p className="text-[11px] text-blue-600">파란 배경인 셀을 클릭하면 관련 자료가 제시됩니다.</p>
        )}
        {data.truncated && (
          <p className="text-[11px] text-muted-foreground">앞부분 일부만 표시 (실제 시트는 더 많은 행/열 포함)</p>
        )}
      </div>

      <div
        className="flex min-h-0 flex-1 flex-col rounded-md border font-mono"
        style={{ fontSize: `${11 * zoom}px`, lineHeight: 1.5 }}
      >
        <div className="pbc-scroll min-h-0 flex-1 overflow-auto">
          <table className="border-collapse">
            <thead>
              <tr>
                <th className="sticky left-0 top-0 z-20 border-r border-b bg-muted/60 px-2 py-0.5 text-muted-foreground">
                  &nbsp;
                </th>
                {Array.from({ length: columnCount }, (_, c) => (
                  <th
                    key={c}
                    className="sticky top-0 z-10 border-r border-b bg-muted/60 px-2 py-0.5 text-center font-medium text-muted-foreground last:border-r-0"
                  >
                    {columnLetter(c)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row, r) => {
                const blockFormulaSheet = onCellSelect ? rowFormulaSheets[r] : undefined
                const priorYearSection = onCellSelect && isSettlementSheet ? priorYearSectionForExcelRow(r + 1) : undefined
                const fsCheckSection = onCellSelect && isFsCheckSheet ? fsCheckSectionForExcelRow(r + 1) : undefined
                // 클릭한 셀 자신에게 수식이 없어도, 같은 행의 다른 셀에 원본
                // PBC 시트를 참조하는 수식이 있을 수 있다 -- 예: C3_수익에서
                // 라벨 셀은 통합기준가격대장(원본 PBC 아님)을 참조하지만,
                // 바로 옆 "평균잔액" 셀은 AVERAGE(일별자산내역!...)를 쓴다.
                // C1의 자펀드1~10처럼 정산표 전용도 아니고, C2처럼 여러 행에
                // 걸친 캡션 블록도 아닌 -- 딱 "같은 행" 범위라 안전하다. 평가액검증
                // (주식/수익증권/선물) 세 시트도 데이터 행마다 원본 PBC 시트를
                // 직접 참조해서 별도 전용 로직 없이 이 하나로 충분하다.
                const rowWideFormulaSheet =
                  onCellSelect && !priorYearSection && !fsCheckSection
                    ? row.map((cell) => formulaSheetRef(cell.f)).find((s) => s != null) ?? null
                    : undefined
                // C2/C1처럼 하나로 확정할 수 없는 블록(C3_수익의 "이자수익
                // 재계산")은, 그 블록 범위 안에서 모은 원본 후보를 실제
                // 내용이 있는 행이면 어디를 클릭하든 똑같이 보여준다 -- 시트
                // 전체가 아니라 딱 그 블록만 (머리말 행이나 다른 블록까지
                // 파란 배경으로 표시하면 오히려 혼란스럽다).
                const rowHasContent = row.some((cell) => cell.v.trim() !== "")
                const excelRow = r + 1
                const isInIncomeRecalcBlock =
                  onCellSelect &&
                  isIncomeSheet &&
                  excelRow >= C3_INTEREST_RECALC_RANGE[0] &&
                  excelRow <= C3_INTEREST_RECALC_RANGE[1]
                const isSubfundRow =
                  onCellSelect && isSettlementSheet && excelRow >= C1_SUBFUND_RANGE[0] && excelRow <= C1_SUBFUND_RANGE[1]
                // C5_F.N: 셀/행 자기 참조(direct 또는 C2 경유)가 가장 정확하고,
                // 없으면(합계/버퍼/서브캡션 행 등) 캡션 블록 전체에 채워둔
                // c5RowFormulaSheets로 대체한다 -- C2의 ownSheet ?? blockFormulaSheet
                // 우선순위와 같은 원리.
                const notesRowC2Ref = onCellSelect && isNotesSheet ? rowWideC2RowRef(row) : null
                const notesRowIndirect = notesRowC2Ref != null ? c2RowFormulaSheets[notesRowC2Ref - 1] ?? null : null
                const notesBlockSheet = onCellSelect && isNotesSheet ? c5RowFormulaSheets[r] : undefined
                const notesResolvedSheet =
                  onCellSelect && isNotesSheet
                    ? rowWideFormulaSheet ?? notesRowIndirect ?? notesBlockSheet ?? null
                    : null
                // 특수관계자거래/담보제공자산은 원본 PBC 참조가 없어 위
                // notesResolvedSheet로는 절대 못 찾는다 -- 대신 AI 근거검색
                // 데모 항목(검토 항목 탭의 같은 항목)을 그대로 가리킨다.
                const inTeuksuBlock =
                  onCellSelect && isNotesSheet && !!teuksuRange && r >= teuksuRange[0] && r < teuksuRange[1]
                const inDamboBlock =
                  onCellSelect && isNotesSheet && !!damboRange && r >= damboRange[0] && r < damboRange[1]
                const hasEvidence =
                  onCellSelect &&
                  (blockFormulaSheet != null ||
                    priorYearSection != null ||
                    fsCheckSection != null ||
                    inTeuksuBlock ||
                    inDamboBlock ||
                    (isNotesSheet ? notesResolvedSheet != null : rowWideFormulaSheet != null) ||
                    (isInIncomeRecalcBlock && rowHasContent && blockAllSheets.length > 0) ||
                    (isSubfundRow && subfundFormulaSheet != null))
                return (
                  <tr
                    key={r}
                    className={hasEvidence ? "bg-blue-50 hover:bg-blue-100" : "even:bg-muted/30"}
                    title={hasEvidence ? "클릭하면 오른쪽에 근거자료가 표시됩니다" : undefined}
                  >
                    <td className="sticky left-0 z-10 border-r bg-background px-2 py-0.5 text-right text-muted-foreground">
                      {r + 1}
                    </td>
                    {row.map((cell, c) => {
                      const isSelected = selected?.r === r && selected?.c === c
                      return (
                        <td
                          key={c}
                          onClick={() => {
                            setSelected({ r, c, cell })
                            if (!onCellSelect) return
                            if (isSettlementSheet) {
                              if (priorYearSection) onCellSelect({ kind: "prior-year", section: priorYearSection })
                              else {
                                const ownSheet =
                                  formulaSheetRef(cell.f) ??
                                  rowWideFormulaSheet ??
                                  (isSubfundRow ? subfundFormulaSheet : null)
                                onCellSelect(ownSheet ? { kind: "formula", sheet: ownSheet } : { kind: "none" })
                              }
                              return
                            }
                            if (isAssetSheet) {
                              // C2: 우선순위 ①이 셀 자신의 수식(가장 정확) →
                              // ②같은 행의 다른 셀 수식 → ③캡션 블록 단위로
                              // 확장한 수식 참조 → ④근거 없음. 블록은 이미
                              // 확정적으로 하나를 찾도록 설계돼 있어 후보를
                              // 여러 개 보여줄 필요가 없다.
                              const ownSheet = formulaSheetRef(cell.f) ?? rowWideFormulaSheet ?? null
                              if (ownSheet) onCellSelect({ kind: "formula", sheet: ownSheet })
                              else if (blockFormulaSheet) onCellSelect({ kind: "formula", sheet: blockFormulaSheet })
                              else onCellSelect({ kind: "none" })
                              return
                            }
                            // 재무제표검증: C1_정산표와 같은 이유로 원본 PBC가
                            // 아니라 재구성된 전기 재무제표가 "근거"다 (재무상태표/
                            // 손익계산서/자본변동표 구간별로 C1과 동일한 prior-year
                            // 데이터를 그대로 보여준다).
                            if (isFsCheckSheet) {
                              onCellSelect(fsCheckSection ? { kind: "prior-year", section: fsCheckSection } : { kind: "none" })
                              return
                            }
                            // C5_F.N: 특수관계자거래/담보제공자산은 원본 PBC가
                            // 없어(formula 해소 불가) AI 근거검색 데모 항목을
                            // 대신 연다 -- 그 외 노트는 이 행이 참조하는 C2 행
                            // 번호를 찾아 C2 쪽 캡션 블록 조회 결과로 원본 PBC
                            // 시트를 2단계로 해소한다.
                            if (isNotesSheet) {
                              if (inTeuksuBlock) {
                                onCellSelect({ kind: "flagged-item", id: TEUKSU_ITEM_ID })
                              } else if (inDamboBlock) {
                                onCellSelect({ kind: "flagged-item", id: DAMBO_ITEM_ID })
                              } else {
                                onCellSelect(notesResolvedSheet ? { kind: "formula", sheet: notesResolvedSheet } : { kind: "none" })
                              }
                              return
                            }
                            // C3_수익의 "이자수익 재계산" 블록: 그 블록 범위
                            // 안이고 내용 있는 행이면 블록 전체에서 모은
                            // 후보를 그대로 보여준다 (몇 개든 후보 목록으로
                            // 통일 -- 딱 하나만 걸린 경우도 마찬가지). 블록
                            // 밖(머리말 등)이면 아래 일반 폴백으로 넘어간다.
                            if (isInIncomeRecalcBlock && rowHasContent && blockAllSheets.length > 0) {
                              onCellSelect({ kind: "formula-multi", sheets: blockAllSheets })
                              return
                            }
                            // 그 외 시트(평가액검증(주식/수익증권/선물) 등): 전용
                            // 로직 없이도, 데이터 행이 원본 PBC 시트를 직접
                            // 참조하는 경우가 많아 같은 행의 rowWideFormulaSheet
                            // 하나로 충분하다 (C4_수수료비용 등의 일별 표와 같은
                            // 패턴 -- 캡션 블록 같은 별도 구조 없이도 각 행 자체가
                            // 이미 확정적으로 원본을 가리킴).
                            onCellSelect(rowWideFormulaSheet ? { kind: "formula", sheet: rowWideFormulaSheet } : { kind: "none" })
                          }}
                          className={`cursor-pointer border-r px-2 py-0.5 last:border-r-0 ${
                            sheetName === C5_NOTES_SHEET && c === C5_WRAP_COLUMN_INDEX ? "" : "whitespace-nowrap"
                          } ${isSelected ? "bg-accent ring-1 ring-inset ring-primary" : ""} ${
                            cell.f ? "text-blue-700" : ""
                          }`}
                          title={cell.f ?? undefined}
                        >
                          {sheetName === C5_NOTES_SHEET && c === C5_WRAP_COLUMN_INDEX ? (
                            // td 자체에 width를 줘도 table-layout:auto에서는 다른 행의
                            // 짧은 셀들 때문에 무시되고 최소폭으로 눌린다 -- 대신 셀
                            // 안에 고정폭 블록을 넣어서 그 블록 크기로 열 폭을 강제한다.
                            <div className="w-[320px] max-w-[320px] whitespace-normal break-words">{cell.v}</div>
                          ) : (
                            cell.v
                          )}
                        </td>
                      )
                    })}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="flex shrink-0 items-center gap-2 border-t bg-muted/40 px-2 py-1 text-xs">
          <span className="font-medium text-muted-foreground">
            {selected ? `${columnLetter(selected.c)}${selected.r + 1}` : ""}
          </span>
          <span className="truncate text-blue-700">
            {selected ? (selected.cell.f ? selected.cell.f : selected.cell.v || "(비어 있음)") : "셀을 클릭하면 값/수식이 여기 표시됩니다"}
          </span>
        </div>
      </div>
    </div>
  )
}
