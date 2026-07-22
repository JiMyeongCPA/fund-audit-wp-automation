import { useState } from "react"
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { documentUrl } from "@/api"

/** 브라우저의 PDF+#page= 조합은 iframe 안에서 스크롤/페이지 이동이 안 되거나
 * 딱 그 페이지만 보이고 갇히는 경우가 있어서(브라우저 설정과 무관하게), 직접
 * 이전/다음 버튼으로 iframe src를 다시 그려서 페이지 이동을 확실하게 제어한다.
 * "브라우저에서 바로 전체 문서를 볼 수 있어야 한다"는 요구사항 그대로. */
export function PdfPageViewer({
  docName,
  initialPage,
  pageCount,
}: {
  docName: string
  initialPage?: number | null
  pageCount?: number | null
}) {
  const total = pageCount ?? 1
  const [page, setPage] = useState(initialPage ?? 1)
  const src = `${documentUrl(docName)}#page=${page}&toolbar=0&navpanes=0`

  return (
    <div className="mt-2 flex flex-col gap-1">
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-6 w-6"
          disabled={page <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          <ChevronLeft className="h-3.5 w-3.5" />
        </Button>
        <span className="text-xs text-muted-foreground">
          {page} / {total}페이지
        </span>
        <Button
          variant="outline"
          size="icon"
          className="h-6 w-6"
          disabled={page >= total}
          onClick={() => setPage((p) => Math.min(total, p + 1))}
        >
          <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </div>
      <iframe key={page} src={src} title={docName} className="h-[560px] w-full rounded border" />
    </div>
  )
}
