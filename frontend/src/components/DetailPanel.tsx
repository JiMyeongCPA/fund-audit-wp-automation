import { AlertTriangle, CheckCircle2, FileSearch, FileText, Sparkles, ThumbsDown, ThumbsUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DataTable } from "@/components/DataTable"
import { PdfPageViewer } from "@/components/PdfPageViewer"
import type { PbcPreview, PriorYearCapitalStatement, PriorYearFinancials } from "@/api"
import type { ReviewRow } from "@/types"

export function DetailPanel({
  row,
  noEvidence,
  formulaPreview,
  multiFormulaPreview,
  priorYearPreview,
  capitalPreview,
  onDecision,
}: {
  row: ReviewRow | null
  noEvidence?: boolean
  formulaPreview?: PbcPreview | null
  multiFormulaPreview?: PbcPreview[] | null
  priorYearPreview?: PriorYearFinancials | null
  capitalPreview?: PriorYearCapitalStatement | null
  onDecision: (id: string, status: "approved" | "rejected") => void
}) {
  if (formulaPreview) {
    return (
      <div className="flex h-full flex-col gap-4">
        <div className="shrink-0">
          <h3 className="flex items-center gap-1.5 text-lg font-semibold">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            {formulaPreview.sheet}
          </h3>
        </div>
        <DataTable columns={formulaPreview.columns} rows={formulaPreview.sampleRows} />
      </div>
    )
  }

  if (multiFormulaPreview && multiFormulaPreview.length > 0) {
    return (
      <div className="flex h-full flex-col gap-4">
        <div className="shrink-0">
          <h3 className="flex items-center gap-1.5 text-lg font-semibold">
            <FileSearch className="h-4 w-4 text-blue-600" />
            원본 후보 {multiFormulaPreview.length}개
          </h3>
        </div>
        <div className="pbc-scroll min-h-0 flex-1 overflow-y-auto rounded-md border">
          <div className="divide-y">
            {multiFormulaPreview.map((p, i) => (
              <details key={p.sheet} open={i === 0} className="p-3">
                <summary className="flex cursor-pointer items-center gap-1.5 text-sm font-medium">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  후보 {i + 1}: {p.sheet}
                </summary>
                <div className="mt-2 h-96">
                  <DataTable columns={p.columns} rows={p.sampleRows} className="h-full" />
                </div>
              </details>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (priorYearPreview) {
    const columns = ["과목", "금액"]
    const rows = priorYearPreview.items.map((i) => ({ 과목: i.label, 금액: i.amount.toLocaleString() }))
    return (
      <div className="flex h-full flex-col gap-4">
        <div className="shrink-0">
          <h3 className="flex items-center gap-1.5 text-lg font-semibold">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            전기 {priorYearPreview.section}
          </h3>
        </div>
        <DataTable columns={columns} rows={rows} />
      </div>
    )
  }

  if (capitalPreview) {
    const columns = ["구분", "원본", "이익잉여금", "총계"]
    const rows = capitalPreview.items.map((i) => ({
      구분: i.label,
      원본: i.principal.toLocaleString(),
      이익잉여금: i.retainedEarnings.toLocaleString(),
      총계: i.total.toLocaleString(),
    }))
    return (
      <div className="flex h-full flex-col gap-4">
        <div className="shrink-0">
          <h3 className="flex items-center gap-1.5 text-lg font-semibold">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            전기 자본변동표 (C.E)
          </h3>
        </div>
        <DataTable columns={columns} rows={rows} />
      </div>
    )
  }

  if (!row) {
    if (noEvidence) {
      return (
        <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          이 셀/행에 연결된 근거 자료가 없습니다.
        </div>
      )
    }
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        왼쪽 표에서 항목을 클릭하면 근거자료가 여기 표시됩니다.
      </div>
    )
  }

  if (row.kind === "origin") {
    const columns = row.sampleRows.length > 0 ? Object.keys(row.sampleRows[0]) : []
    return (
      <div className="flex h-full flex-col gap-4">
        <div className="shrink-0">
          <h3 className="flex items-center gap-1.5 text-lg font-semibold">
            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            {row.blockName}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            {row.c2Sheet} {row.c2FirstRow}~{row.c2LastRow}행 ← {row.sourceSheet} {row.sourceFirstRow}~
            {row.sourceLastRow}행
          </p>
        </div>
        <DataTable columns={columns} rows={row.sampleRows} />
      </div>
    )
  }

  // flagged item
  return (
    <div className="flex h-full flex-col gap-4">
      <div className="shrink-0">
        <h3 className="flex items-center gap-1.5 text-lg font-semibold">
          {row.evidenceType === "none" ? (
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          ) : (
            <FileSearch className="h-4 w-4 text-blue-600" />
          )}
          {row.accountName}
        </h3>
        <p className="text-sm mt-2">{row.reason}</p>
      </div>

      {row.evidenceType === "none" && (
        <div className="flex shrink-0 items-start gap-2 rounded-md border border-dashed p-4 text-sm text-muted-foreground">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-500" />
          자동으로 연결할 근거자료가 없습니다. 담당자가 직접 확인해야 합니다.
        </div>
      )}

      {row.evidenceType === "document" && row.candidates && (
        <div className="flex min-h-0 flex-1 flex-col gap-3">
          {row.aiProposal && (
            <div className="flex shrink-0 items-start gap-2 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm">
              <Sparkles className="h-4 w-4 shrink-0 text-blue-600" />
              <div>
                <p className="font-medium text-blue-900">AI 제안</p>
                <p className="mt-0.5 text-blue-900">{row.aiProposal}</p>
                {row.aiProposalIsFallback && (
                  <p className="mt-1 text-xs text-blue-700/70">
                    ※ 현재 Gemini API 사용량 제한으로 사전 정의된 제안을 사용 중입니다 (AI 근거검색 기능은 구현되어 있음).
                  </p>
                )}
              </div>
            </div>
          )}

          <div className="pbc-scroll min-h-0 flex-1 overflow-y-auto rounded-md border">
            <div className="divide-y">
              {row.candidates.map((c, i) => {
                // AI 제안은 1등 후보(i===0)의 특정 페이지 내용에 근거해서 만들어졌다 --
                // PDF를 그 페이지로 바로 열어줘야 "찾아주고 이동까지" 의미가 있다.
                const jumpPage = i === 0 ? row.aiProposalPage : null
                return (
                  <details key={c.docName} className="p-3">
                    <summary className="flex cursor-pointer items-center gap-1.5 text-sm font-medium">
                      <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                      후보 {i + 1}: {c.docName}
                    </summary>
                    {c.sampleRows && c.sampleRows.length > 0 ? (
                      <div className="mt-2 h-96">
                        <DataTable columns={c.columns ?? []} rows={c.sampleRows} className="h-full" />
                      </div>
                    ) : c.docName.toLowerCase().endsWith(".pdf") ? (
                      <PdfPageViewer docName={c.docName} initialPage={jumpPage} pageCount={c.pageCount} />
                    ) : (
                      <pre className="mt-2 whitespace-pre-wrap text-xs text-muted-foreground font-sans">{c.text}</pre>
                    )}
                  </details>
                )
              })}
            </div>
          </div>

          {/* 승인/반려는 "AI가 제안한 이 구체적인 반영안을 적용할지"에 대한
              결정이다 -- 제안 자체가 없으면(aiProposal 없음) 승인/반려할
              대상도 없으므로 버튼을 아예 보여주지 않는다(사용자 피드백:
              "ai가 뭘 추천하지 못했으면 승인/반려는 나오면 안되지"). */}
          {row.aiProposal &&
            (row.status === "pending" ? (
              <div className="flex shrink-0 gap-2">
                <Button className="flex-1 gap-1.5 bg-blue-600 hover:bg-blue-700" onClick={() => onDecision(row.id, "approved")}>
                  <ThumbsUp className="h-4 w-4" /> 이 제안대로 반영
                </Button>
                <Button variant="outline" className="flex-1 gap-1.5" onClick={() => onDecision(row.id, "rejected")}>
                  <ThumbsDown className="h-4 w-4" /> 제안 반려
                </Button>
              </div>
            ) : (
              <p className="flex shrink-0 items-center gap-1.5 text-sm text-emerald-600">
                <CheckCircle2 className="h-4 w-4" />
                이미 처리됨: {row.status === "approved" ? "반영됨" : "반려됨"}
              </p>
            ))}
        </div>
      )}
    </div>
  )
}
