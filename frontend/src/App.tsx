import { useEffect, useState } from "react"
import { AlertTriangle, ArrowLeft, ArrowRight } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ReviewTable } from "@/components/ReviewTable"
import { DetailPanel } from "@/components/DetailPanel"
import { SheetGrid } from "@/components/SheetGrid"
import type { CellSelectResult } from "@/components/SheetGrid"
import { TopBar } from "@/components/TopBar"
import { useBuildStatus } from "@/hooks/useBuildStatus"
import {
  fetchItems,
  fetchPbcPreview,
  fetchPriorYearCapitalStatement,
  fetchPriorYearFinancials,
  fetchSheetNames,
  postDecision,
} from "@/api"
import type { PbcPreview, PriorYearCapitalStatement, PriorYearFinancials } from "@/api"
import type { ReviewRow } from "@/types"

function App() {
  const built = useBuildStatus()
  const [rows, setRows] = useState<ReviewRow[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [noEvidence, setNoEvidence] = useState(false)
  const [formulaPreview, setFormulaPreview] = useState<PbcPreview | null>(null)
  const [multiFormulaPreview, setMultiFormulaPreview] = useState<PbcPreview[] | null>(null)
  const [priorYearPreview, setPriorYearPreview] = useState<PriorYearFinancials | null>(null)
  const [capitalPreview, setCapitalPreview] = useState<PriorYearCapitalStatement | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sheetNames, setSheetNames] = useState<string[]>([])
  // 승인/반려하면 C5_F.N 시트의 특수관계자거래/담보제공자산 값이 바뀌므로,
  // 지금 열려 있는 시트를 다시 불러오도록 강제하는 토큰.
  const [sheetRefreshToken, setSheetRefreshToken] = useState(0)

  const selectReviewItem = (id: string) => {
    setSelectedId(id)
    setNoEvidence(false)
    setFormulaPreview(null)
    setMultiFormulaPreview(null)
    setPriorYearPreview(null)
    setCapitalPreview(null)
  }

  const handleCellSelect = (result: CellSelectResult) => {
    if (result.kind === "formula") {
      setSelectedId(null)
      setNoEvidence(false)
      setMultiFormulaPreview(null)
      setPriorYearPreview(null)
      setCapitalPreview(null)
      fetchPbcPreview(result.sheet)
        .then(setFormulaPreview)
        .catch((e) => setError(String(e)))
    } else if (result.kind === "formula-multi") {
      setSelectedId(null)
      setNoEvidence(false)
      setFormulaPreview(null)
      setPriorYearPreview(null)
      setCapitalPreview(null)
      Promise.all(result.sheets.map(fetchPbcPreview))
        .then(setMultiFormulaPreview)
        .catch((e) => setError(String(e)))
    } else if (result.kind === "prior-year") {
      setSelectedId(null)
      setNoEvidence(false)
      setFormulaPreview(null)
      setMultiFormulaPreview(null)
      if (result.section === "자본변동표") {
        setPriorYearPreview(null)
        fetchPriorYearCapitalStatement()
          .then(setCapitalPreview)
          .catch((e) => setError(String(e)))
      } else {
        setCapitalPreview(null)
        fetchPriorYearFinancials(result.section)
          .then(setPriorYearPreview)
          .catch((e) => setError(String(e)))
      }
    } else if (result.kind === "flagged-item") {
      // 특수관계자거래/담보제공자산처럼 원본 PBC가 없어 검토 항목 탭의 AI
      // 근거검색 데모 항목을 그대로 여는 경우 -- selectReviewItem 하나로 그
      // 항목의 기존 렌더링(후보 문서/AI 제안/승인·반려)을 그대로 재사용한다.
      selectReviewItem(result.id)
    } else {
      setSelectedId(null)
      setFormulaPreview(null)
      setMultiFormulaPreview(null)
      setPriorYearPreview(null)
      setCapitalPreview(null)
      setNoEvidence(true)
    }
  }

  useEffect(() => {
    fetchItems()
      .then(setRows)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
    fetchSheetNames()
      .then(setSheetNames)
      .catch((e) => setError(String(e)))
  }, [])

  const selectedRow = rows.find((r) => r.id === selectedId) ?? null

  const handleDecision = async (id: string, status: "approved" | "rejected") => {
    // 낙관적 업데이트 먼저 반영하고, 백엔드 응답으로 다시 한 번 동기화한다.
    setRows((prev) =>
      prev.map((r) => (r.kind === "flag" && r.id === id ? { ...r, status } : r))
    )
    try {
      await postDecision(id, status)
      // 반영 결과가 시트에 나타나도록(특수관계자거래/담보제공자산) 현재 열린
      // 시트를 다시 불러온다.
      setSheetRefreshToken((t) => t + 1)
    } catch (e) {
      setError(String(e))
    }
  }

  // 1단계(/api/build)를 실행하지 않고 들어오면 서버에 남아있는 예시/이전
  // 결과가 그대로 보이던 문제(사용자 피드백) -- built가 확정될 때까지
  // 기다렸다가, 아니면 이 화면을 아예 막는다.
  if (built === null) {
    return <div className="p-3 text-sm text-muted-foreground">확인하는 중...</div>
  }
  if (built === false) {
    return (
      <div className="flex h-screen flex-col gap-2 bg-slate-50 p-2">
        <TopBar currentStep={2} />
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center text-sm text-muted-foreground">
          <AlertTriangle className="h-6 w-6 text-amber-500" />
          <p>아직 1단계를 실행하지 않았습니다. 1단계에서 실행한 뒤 다시 확인해 주세요.</p>
          <a href="/" className="text-blue-600 hover:underline">
            1단계로 이동하기
          </a>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-3 text-sm text-destructive">
        {error} — 백엔드 API가 응답하지 않습니다. 잠시 후 다시 시도해 주세요.
      </div>
    )
  }

  if (loading) {
    return <div className="p-3 text-sm text-muted-foreground">불러오는 중...</div>
  }

  return (
    <div className="flex h-screen flex-col gap-2 bg-slate-50 p-2">
      <TopBar currentStep={2} />
      <div className="flex shrink-0 items-center justify-between">
        <a href="/" className="flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3.5 w-3.5" /> 1단계로 이동하기
        </a>
        <a href="/complete" className="flex w-fit items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
          3단계로 이동하기 <ArrowRight className="h-3.5 w-3.5" />
        </a>
      </div>
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-2 lg:grid-cols-5">
        <Card className="overflow-hidden lg:col-span-3">
          <CardContent className="h-full p-2">
            <Tabs defaultValue="__review__" className="h-full gap-1.5">
              <TabsList className="w-full flex-nowrap justify-start overflow-x-auto overflow-y-hidden">
                <TabsTrigger value="__review__" className="flex-none shrink-0 px-3.5 py-2">
                  검토 항목
                </TabsTrigger>
                {sheetNames.map((name) => (
                  <TabsTrigger key={name} value={name} className="flex-none shrink-0 px-3.5 py-2">
                    {name}
                  </TabsTrigger>
                ))}
              </TabsList>
              <TabsContent value="__review__" className="min-h-0 flex-1 overflow-y-auto">
                <ReviewTable rows={rows} selectedId={selectedId} onSelect={selectReviewItem} />
              </TabsContent>
              {sheetNames.map((name) => (
                <TabsContent key={name} value={name} className="min-h-0 flex-1">
                  <SheetGrid
                    sheetName={name}
                    refreshToken={sheetRefreshToken}
                    onCellSelect={
                      [
                        "C1_정산표",
                        "C2_자산부채평가",
                        "C3_수익",
                        "C4_수수료비용 등",
                        "C5_F.N",
                        "평가액검증(주식)",
                        "평가액검증(수익증권)",
                        "평가액검증(선물)",
                        "재무제표검증",
                      ].includes(name)
                        ? handleCellSelect
                        : undefined
                    }
                  />
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        <Card className="overflow-hidden lg:col-span-2">
          <CardContent className="h-full p-3">
            <DetailPanel
              row={selectedRow}
              noEvidence={noEvidence}
              formulaPreview={formulaPreview}
              multiFormulaPreview={multiFormulaPreview}
              priorYearPreview={priorYearPreview}
              capitalPreview={capitalPreview}
              onDecision={handleDecision}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default App
