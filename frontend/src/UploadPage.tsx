import { useRef, useState } from "react"
import type { DragEvent } from "react"
import { AlertTriangle, FileStack, Loader2, PlayCircle, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { TopBar } from "@/components/TopBar"
import { BUILD_FIELDS, matchFilesToFields, runBuild } from "@/api"

function UploadPage() {
  const [files, setFiles] = useState<Partial<Record<string, File>>>({})
  const [unmatched, setUnmatched] = useState<File[]>([])
  const [dragOver, setDragOver] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const multiInputRef = useRef<HTMLInputElement>(null)

  const applyDroppedFiles = (fileList: FileList | File[]) => {
    const { matched, unmatched: rest } = matchFilesToFields(fileList)
    setFiles((prev) => ({ ...prev, ...matched }))
    setUnmatched(rest)
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    if (e.dataTransfer.files.length > 0) applyDroppedFiles(e.dataTransfer.files)
  }

  const runAndGo = async (chosenFiles: Partial<Record<string, File>>) => {
    setRunning(true)
    setError(null)
    try {
      await runBuild(chosenFiles)
      window.location.href = "/review"
    } catch (e) {
      setError(String(e))
      setRunning(false)
    }
  }

  const filledCount = Object.values(files).filter(Boolean).length

  return (
    <div className="flex h-screen flex-col gap-2 bg-slate-50 p-2">
      <TopBar currentStep={1} />

      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-4 overflow-y-auto py-4">
        <div>
          <h2 className="text-xl font-semibold">1단계</h2>
          <p className="text-sm text-muted-foreground mt-1">
            첨부하신 자료를 바탕으로 1차 자동화 작업을 수행합니다.
          </p>
        </div>

        <Card>
          <CardContent className="flex items-center justify-between gap-3 p-4">
            <h3 className="font-medium">샘플 데이터로 실행</h3>
            <Button disabled={running} className="shrink-0 gap-1.5 bg-blue-600 hover:bg-blue-700" onClick={() => runAndGo({})}>
              {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <PlayCircle className="h-4 w-4" />}
              실행
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex flex-col gap-3 p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="font-medium">파일 업로드</h3>
              <span className="text-xs text-muted-foreground">
                {filledCount}/{BUILD_FIELDS.length}개 선택됨
              </span>
            </div>

            <div
              onDragOver={(e) => {
                e.preventDefault()
                setDragOver(true)
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => multiInputRef.current?.click()}
              className={`flex cursor-pointer flex-col items-center gap-1.5 rounded-md border-2 border-dashed p-6 text-center transition-colors ${
                dragOver ? "border-blue-500 bg-blue-50" : "border-muted-foreground/30 hover:bg-muted/30"
              }`}
            >
              <FileStack className="h-6 w-6 text-muted-foreground" />
              <p className="text-sm font-medium">여기에 파일 12개를 한 번에 드래그하세요</p>
              <p className="text-xs text-muted-foreground">또는 클릭해서 여러 개 선택</p>
              <input
                ref={multiInputRef}
                type="file"
                multiple
                accept=".csv,.xlsx"
                className="hidden"
                onChange={(e) => e.target.files && applyDroppedFiles(e.target.files)}
              />
            </div>

            {unmatched.length > 0 && (
              <div className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-800">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                <span>
                  파일명으로 어느 항목인지 못 알아낸 파일 {unmatched.length}개: {unmatched.map((f) => f.name).join(", ")}
                  {" "}-- 아래에서 해당 항목에 직접 선택해 주세요.
                </span>
              </div>
            )}

            <div className="flex flex-col rounded-md border">
              {BUILD_FIELDS.map(({ field, label }) => {
                const picked = files[field]
                return (
                  <div
                    key={field}
                    className={`flex items-center gap-2 border-b p-1.5 text-sm last:border-b-0 ${
                      picked ? "border-l-2 border-l-blue-500 bg-blue-50/50" : "border-l-2 border-l-transparent"
                    }`}
                  >
                    <span className={`w-40 shrink-0 truncate font-medium ${picked ? "text-blue-700" : "text-muted-foreground"}`}>
                      {label}
                    </span>
                    <span className="flex-1 truncate text-xs text-blue-700">{picked?.name}</span>
                  </div>
                )
              })}
            </div>
            <Button
              disabled={running}
              className="gap-1.5 bg-blue-600 hover:bg-blue-700"
              onClick={() => runAndGo(files)}
            >
              {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              업로드한 파일로 실행
            </Button>
          </CardContent>
        </Card>

        {error && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/5 p-3 text-sm text-destructive">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

export default UploadPage
