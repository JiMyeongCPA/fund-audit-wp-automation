import { AlertTriangle, CheckCircle2, Download, XCircle } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { WORKPAPER_DOWNLOAD_URL } from "@/api"
import type { ReviewRow } from "@/types"

export function CompletionPanel({ rows }: { rows: ReviewRow[] }) {
  const flagged = rows.filter((r): r is Extract<ReviewRow, { kind: "flag" }> => r.kind === "flag")
  const unresolved = flagged.filter((r) => r.status !== "approved")

  return (
    <div className="flex h-full flex-col gap-5 overflow-y-auto p-1">
      <div className="flex shrink-0 items-center justify-between rounded-md border bg-muted/30 p-4">
        <div>
          <h3 className="text-lg font-semibold">조서 다운로드</h3>
        </div>
        <Button asChild className="gap-1.5 bg-blue-600 hover:bg-blue-700">
          <a href={WORKPAPER_DOWNLOAD_URL} download>
            <Download className="h-4 w-4" /> 다운로드
          </a>
        </Button>
      </div>

      <div className="shrink-0">
        <h3 className="text-lg font-semibold">검토하실 항목</h3>
        <p className="text-sm text-muted-foreground mt-1">추가적으로 검토하실 것을 권장드립니다.</p>
      </div>

      {unresolved.length === 0 ? (
        <div className="flex items-center gap-2 rounded-md border border-dashed p-4 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          미해결 항목이 없습니다. 제출 준비가 됐습니다.
        </div>
      ) : (
        <div className="flex flex-col divide-y rounded-md border">
          {unresolved.map((item) => (
            <div key={item.id} className="flex items-start justify-between gap-3 p-3">
              <div>
                <p className="flex items-center gap-1.5 text-sm font-medium">
                  {item.status === "rejected" ? (
                    <XCircle className="h-3.5 w-3.5 text-destructive" />
                  ) : (
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                  )}
                  {item.accountName}
                </p>
                <p className="text-sm text-muted-foreground mt-1">{item.reason}</p>
              </div>
              {item.status === "rejected" ? (
                <Badge variant="destructive" className="shrink-0 gap-1">
                  <XCircle className="h-3 w-3" /> 반려됨
                </Badge>
              ) : (
                <Badge variant="outline" className="shrink-0 gap-1 border-amber-500 text-amber-600">
                  <AlertTriangle className="h-3 w-3" /> 확인 필요
                </Badge>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
