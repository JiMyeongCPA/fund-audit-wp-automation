# ---- 1단계: React 프론트엔드 빌드 -----------------------------------------
FROM node:20-slim AS frontend
WORKDIR /app/frontend
# 의존성 먼저 설치(레이어 캐시). package-lock.json 기준으로 재현 가능하게 ci.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build      # -> /app/frontend/dist

# ---- 2단계: Python 백엔드 + 빌드된 프론트를 한 서비스로 서빙 ----------------
FROM python:3.12-slim AS runtime
WORKDIR /app

# 파이썬 의존성 먼저(레이어 캐시). pywin32는 requirements에서 win32 전용으로
# 걸려 있어 리눅스에선 자동으로 건너뛴다.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 소스 + 표본 데이터 + 커밋된 완성본(조립결과.xlsx) + 합성 근거자료.
COPY api.py ./
COPY core/ ./core/
COPY sample_data/ ./sample_data/
COPY sample_output/ ./sample_output/
COPY tests/ ./tests/

# 1단계에서 빌드한 프론트 정적 파일을 백엔드가 서빙할 위치로 복사.
COPY --from=frontend /app/frontend/dist ./frontend/dist

# Render 등은 $PORT로 포트를 주입한다. 없으면 8000.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
