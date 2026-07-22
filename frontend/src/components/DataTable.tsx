import { useState } from "react"
import { Minus, Plus } from "lucide-react"
import { Button } from "@/components/ui/button"

const MIN_ZOOM = 0.5
const MAX_ZOOM = 2
const ZOOM_STEP = 0.1

/** 확대/축소 + 좌우/상하 스크롤이 되는 표. SheetGrid(왼쪽 원본 시트)와 같은
 * 조작감을 오른쪽 근거 패널의 표에도 그대로 주기 위한 공용 컴포넌트. */
export function DataTable({
  columns,
  rows,
  className = "min-h-0 flex-1",
}: {
  columns: string[]
  rows: Record<string, string>[]
  className?: string
}) {
  const [zoom, setZoom] = useState(1)

  return (
    <div className="flex h-full flex-col gap-1.5">
      <div className="flex shrink-0 items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-6 w-6"
          onClick={() => setZoom((z) => Math.max(MIN_ZOOM, +(z - ZOOM_STEP).toFixed(1)))}
        >
          <Minus className="h-3 w-3" />
        </Button>
        <button className="w-12 text-center text-xs text-muted-foreground hover:underline" onClick={() => setZoom(1)}>
          {Math.round(zoom * 100)}%
        </button>
        <Button
          variant="outline"
          size="icon"
          className="h-6 w-6"
          onClick={() => setZoom((z) => Math.min(MAX_ZOOM, +(z + ZOOM_STEP).toFixed(1)))}
        >
          <Plus className="h-3 w-3" />
        </Button>
      </div>

      <div className={`${className} pbc-scroll overflow-auto rounded-md border`} style={{ fontSize: `${12 * zoom}px` }}>
        <table className="border-collapse">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} className="sticky top-0 whitespace-nowrap border-b bg-muted/60 px-2 py-1 text-left font-medium">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="even:bg-muted/20">
                {columns.map((col) => (
                  <td key={col} className="whitespace-nowrap border-b px-2 py-1">
                    {row[col]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
