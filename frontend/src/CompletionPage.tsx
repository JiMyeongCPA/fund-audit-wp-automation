import { useEffect, useState } from "react"
import { AlertTriangle, ArrowLeft } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { CompletionPanel } from "@/components/CompletionPanel"
import { TopBar } from "@/components/TopBar"
import { useBuildStatus } from "@/hooks/useBuildStatus"
import { fetchItems } from "@/api"
import type { ReviewRow } from "@/types"

function CompletionPage() {
  const built = useBuildStatus()
  const [rows, setRows] = useState<ReviewRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchItems()
      .then(setRows)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  // 1단계(/api/build)를 실행하지 않고 들어오면 서버에 남아있는 예시/이전
  // 결과가 그대로 보이던 문제(사용자 피드백) -- built가 확정될 때까지
  // 기다렸다가, 아니면 이 화면을 아예 막는다.
  if (built === null) {
    return <div className="p-3 text-sm text-muted-foreground">확인하는 중...</div>
  }
  if (built === false) {
    return (
      <div className="flex h-screen flex-col gap-2 bg-slate-50 p-2">
        <TopBar currentStep={3} />
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
        {error} — 백엔드(http://localhost:8000)가 실행 중인지 확인하세요.
      </div>
    )
  }

  if (loading) {
    return <div className="p-3 text-sm text-muted-foreground">불러오는 중...</div>
  }

  return (
    <div className="flex h-screen flex-col gap-2 bg-slate-50 p-2">
      <TopBar currentStep={3} />
      <a href="/review" className="flex w-fit shrink-0 items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-3.5 w-3.5" /> 2단계로 이동하기
      </a>
      <Card className="min-h-0 flex-1 overflow-hidden">
        <CardContent className="h-full p-4">
          <CompletionPanel rows={rows} />
        </CardContent>
      </Card>
    </div>
  )
}

export default CompletionPage
