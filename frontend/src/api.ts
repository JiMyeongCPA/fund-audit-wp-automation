import type { ReviewRow } from "./types"

const API_BASE = "http://localhost:8000"

export function documentUrl(docName: string): string {
  return `${API_BASE}/api/documents/${encodeURIComponent(docName)}`
}

export const WORKPAPER_DOWNLOAD_URL = `${API_BASE}/api/workpaper/download`

export async function fetchItems(): Promise<ReviewRow[]> {
  const res = await fetch(`${API_BASE}/api/items`)
  if (!res.ok) throw new Error(`GET /api/items failed: ${res.status}`)
  return res.json()
}

/** 이번 서버 프로세스에서 /api/build를 실제로 한 번이라도 돌렸는지 --
 * 1단계를 실행하지 않고 2/3단계로 바로 들어가면 서버에 남아있는 예시/이전
 * 결과가 그대로 보이는 문제가 있어서, 2/3단계가 이 값으로 진입 자체를
 * 막는 데 쓴다. */
export async function fetchBuildStatus(): Promise<{ built: boolean }> {
  const res = await fetch(`${API_BASE}/api/build-status`)
  if (!res.ok) throw new Error(`GET /api/build-status failed: ${res.status}`)
  return res.json()
}

export interface SheetCell {
  v: string
  f: string | null
}

export interface SheetData {
  name: string
  rows: SheetCell[][]
  truncated: boolean
}

export async function fetchSheetNames(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/workpaper/sheets`)
  if (!res.ok) throw new Error(`GET /api/workpaper/sheets failed: ${res.status}`)
  return res.json()
}

export async function fetchSheet(name: string): Promise<SheetData> {
  const res = await fetch(`${API_BASE}/api/workpaper/sheets/${encodeURIComponent(name)}`)
  if (!res.ok) throw new Error(`GET sheet ${name} failed: ${res.status}`)
  return res.json()
}

export interface PbcPreview {
  sheet: string
  sourceName: string
  columns: string[]
  sampleRows: Record<string, string>[]
}

export async function fetchPbcPreview(sheet: string): Promise<PbcPreview> {
  const res = await fetch(`${API_BASE}/api/pbc-preview?sheet=${encodeURIComponent(sheet)}`)
  if (!res.ok) throw new Error(`no PBC file for sheet ${sheet}: ${res.status}`)
  return res.json()
}

export interface PriorYearItem {
  label: string
  amount: number
  row: number
}

export interface PriorYearFinancials {
  section: string
  items: PriorYearItem[]
}

export async function fetchPriorYearFinancials(section: string): Promise<PriorYearFinancials> {
  const res = await fetch(`${API_BASE}/api/prior-year-financials?section=${encodeURIComponent(section)}`)
  if (!res.ok) throw new Error(`prior-year-financials failed for ${section}: ${res.status}`)
  return res.json()
}

export interface CapitalStatementRow {
  label: string
  principal: number
  retainedEarnings: number
  total: number
}

export interface PriorYearCapitalStatement {
  items: CapitalStatementRow[]
}

export async function fetchPriorYearCapitalStatement(): Promise<PriorYearCapitalStatement> {
  const res = await fetch(`${API_BASE}/api/prior-year-capital-statement`)
  if (!res.ok) throw new Error(`prior-year-capital-statement failed: ${res.status}`)
  return res.json()
}

export interface BuildResult {
  ok: boolean
  missingAccountCount: number
  usedSampleFallback: string[]
}

export const BUILD_FIELDS = [
  { field: "gijunkagyeok", label: "기준가격대장(결산후)", keyword: "기준가격대장" },
  { field: "gungnaeyudong", label: "국내유동명세", keyword: "국내유동명세" },
  { field: "gungnaejusik", label: "국내주식명세", keyword: "국내주식명세" },
  { field: "pundbyeolmyeongse", label: "펀드별명세", keyword: "펀드별명세" },
  { field: "sooikjeunggwon", label: "국내집합투자증권명세", keyword: "국내집합투자증권명세" },
  { field: "seonmul", label: "국내선물명세", keyword: "국내선물명세" },
  { field: "chaegwon", label: "채권명세", keyword: "채권명세" },
  { field: "gajungpyeonggyunjwasu", label: "일별좌수순자산현황", keyword: "일별좌수순자산현황" },
  { field: "bosubunbae", label: "판매보수내역", keyword: "판매보수내역" },
  { field: "ilbyeoljasan", label: "일별자산내역", keyword: "일별자산내역" },
  { field: "seoljeongheji", label: "설정해지내역", keyword: "설정해지내역" },
  { field: "reference_workpaper", label: "전기 조서", keyword: null },
] as const

/** 파일 여러 개를 한 번에 드롭했을 때, 파일명에 든 키워드로 어느 필드인지
 * 자동으로 맞춰준다 (참조 워크북만 키워드가 없어서 .xlsx 확장자로 구분).
 * 키워드가 서로의 부분 문자열이 아니라서(예: "일별자산내역"과
 * "일별좌수순자산현황") 순서 상관없이 안전하게 매칭된다. */
export function matchFilesToFields(fileList: FileList | File[]): {
  matched: Partial<Record<string, File>>
  unmatched: File[]
} {
  const matched: Partial<Record<string, File>> = {}
  const unmatched: File[] = []
  for (const file of Array.from(fileList)) {
    const hit = BUILD_FIELDS.find(({ keyword }) => keyword && file.name.includes(keyword))
    if (hit) {
      matched[hit.field] = file
    } else if (file.name.toLowerCase().endsWith(".xlsx")) {
      matched.reference_workpaper = file
    } else {
      unmatched.push(file)
    }
  }
  return { matched, unmatched }
}

/** files에 없는 필드는 백엔드가 sample_data/의 샘플로 대신 채운다 --
 * "샘플로 전체 흐름 확인"과 "실제 파일 업로드" 둘 다 이 함수 하나로 처리. */
export async function runBuild(files: Partial<Record<string, File>>): Promise<BuildResult> {
  const form = new FormData()
  for (const { field } of BUILD_FIELDS) {
    const file = files[field]
    if (file) form.append(field, file)
  }
  const res = await fetch(`${API_BASE}/api/build`, { method: "POST", body: form })
  if (!res.ok) {
    const detail = await res.json().catch(() => null)
    throw new Error(detail?.detail ?? `POST /api/build failed: ${res.status}`)
  }
  return res.json()
}

export async function postDecision(
  id: string,
  status: "approved" | "rejected"
): Promise<ReviewRow> {
  const res = await fetch(`${API_BASE}/api/items/${encodeURIComponent(id)}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  })
  if (!res.ok) throw new Error(`POST decision failed: ${res.status}`)
  return res.json()
}
