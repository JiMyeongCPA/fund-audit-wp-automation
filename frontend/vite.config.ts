import path from "node:path"
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // 개발 서버: 프론트는 상대경로(/api/...)로 백엔드를 호출하므로, dev에서는
  // 그 요청을 로컬 FastAPI(8000)로 프록시한다. 배포본에서는 FastAPI가 dist를
  // 직접 서빙해 같은 오리진이라 이 프록시가 필요 없다.
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
})
