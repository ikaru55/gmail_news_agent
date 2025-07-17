# 1. 베이스 이미지로 Python 3.11 선택
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 소스코드 복사 전, 의존성 먼저 설치 (Docker 빌드 캐시 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 나머지 모든 소스 코드를 작업 디렉토리로 복사
COPY . .

# 5. Cloud Run이 제공하는 PORT 환경변수 설정
ENV PORT 8080

# 6. gunicorn 웹 서버 실행 (Cloud Run 표준 방식)
#    이 명령어로 컨테이너가 시작됩니다.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 main:app
