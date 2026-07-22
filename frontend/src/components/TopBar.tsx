import { Bot } from "lucide-react"
import { useBuildStatus } from "@/hooks/useBuildStatus"

// 1단계(초벌 작업)도 이제 이 React 앱 안에서 실제로 build_workpaper()를
// 돌린다(POST /api/build) -- 예전엔 별도 Streamlit 프로토타입(8767)이었지만,
// 세 단계 다 같은 앱 안에서 페이지 이동으로 이어지게 통합했다. 루트("/")는
// 1단계 -- 실제 작업 흐름의 첫 화면이 브라우저를 열자마자 보여야 하니까.
const STEP_HREF: Record<1 | 2 | 3, string> = {
  1: "/",
  2: "/review",
  3: "/complete",
}

function StepIndicator({ currentStep, built }: { currentStep: 1 | 2 | 3; built: boolean | null }) {
  return (
    <div className="flex items-center gap-1">
      {([1, 2, 3] as const).map((step, i) => {
        // 앞 단계로 넘어가는 원(2/3)을 언제 잠글지:
        //  - 1단계 화면에 있을 때는(currentStep===1) 항상 잠근다. 1단계는
        //    "실행" 버튼으로만 앞으로 나가는 화면이라, 이미 빌드한 적이
        //    있더라도 원을 눌러 건너뛰게 두지 않는다(사용자 피드백).
        //  - 그 외(2/3단계 화면)에는 이번 프로세스에서 /api/build를 한 번도
        //    안 돌렸으면(built=false, 확정 전 null 포함) 잠근다 -- 실행 없이
        //    URL로 바로 들어와 예시/이전 결과가 보이는 걸 막기 위함.
        //  - 지금 보고 있는 단계 자신은 잠그지 않는다(현재 표시용).
        const locked = step > 1 && step !== currentStep && (currentStep === 1 || !built)
        return (
          <div key={step} className="flex items-center gap-1">
            {i > 0 && <span className="text-muted-foreground/50 text-xs">→</span>}
            {locked ? (
              <span
                title="1단계를 먼저 실행해야 이동할 수 있습니다"
                className="flex h-5 w-5 cursor-not-allowed items-center justify-center rounded-full bg-muted text-[11px] font-semibold text-muted-foreground/40"
              >
                {step}
              </span>
            ) : (
              <a
                href={STEP_HREF[step]}
                title={`${step}단계로 이동`}
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-semibold transition-colors ${
                  step === currentStep
                    ? "bg-blue-600 text-white"
                    : "bg-muted text-muted-foreground hover:bg-muted-foreground/20"
                }`}
              >
                {step}
              </a>
            )}
          </div>
        )
      })}
    </div>
  )
}

export function TopBar({ currentStep }: { currentStep: 1 | 2 | 3 }) {
  const built = useBuildStatus()
  return (
    <header className="flex h-10 shrink-0 items-center gap-2 rounded-md border bg-background px-3 text-sm">
      <div className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-600 text-white">
        <Bot className="h-3.5 w-3.5" />
      </div>
      <span className="font-semibold">조서자동화</span>
      <StepIndicator currentStep={currentStep} built={built} />
    </header>
  )
}
