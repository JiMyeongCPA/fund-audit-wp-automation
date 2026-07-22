import { StrictMode } from 'react'
import type { ComponentType } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import CompletionPage from './CompletionPage.tsx'
import UploadPage from './UploadPage.tsx'

// 라우팅 라이브러리를 쓰기엔 페이지가 딱 3개(업로드/검토/완료)뿐이라, 경로만
// 보고 어느 페이지를 렌더링할지 고르는 걸로 충분하다. Vite 개발 서버는 기본
// appType이 "spa"라 /review, /complete로 직접 들어와도 이 index.html이
// 그대로 서빙된다.
// 루트("/")는 1단계(업로드) -- 실제 작업 흐름의 첫 화면이 브라우저를 열자마자
// 보여야 하니까, 2단계(검토)는 /review로 옮겼다.
const PAGES: Record<string, ComponentType> = {
  '/review': App,
  '/complete': CompletionPage,
}
const Page = PAGES[window.location.pathname] ?? UploadPage

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Page />
  </StrictMode>,
)
