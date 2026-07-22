import { useEffect, useState } from "react"
import { fetchBuildStatus } from "@/api"

/** 이번 서버 프로세스에서 /api/build가 실제로 실행된 적 있는지 -- null이면
 * 아직 백엔드 응답을 기다리는 중, 그 다음엔 true/false로 확정된다. 1단계를
 * 실행하지 않고 2/3단계로 들어가면 서버에 남아있는 예시/이전 결과가 그대로
 * 보이던 문제(사용자 피드백)를 막는 데 TopBar와 각 단계 페이지가 공통으로
 * 쓴다. */
export function useBuildStatus(): boolean | null {
  const [built, setBuilt] = useState<boolean | null>(null)

  useEffect(() => {
    fetchBuildStatus()
      .then((s) => setBuilt(s.built))
      .catch(() => setBuilt(false))
  }, [])

  return built
}
