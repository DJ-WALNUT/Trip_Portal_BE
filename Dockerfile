# 1. 파이썬 3.9 버전 기반 (가볍고 안정적)
FROM python:3.9-slim

# 2. 작업 폴더 설정
WORKDIR /app

# 3. 라이브러리 설치 (캐시 문제 방지)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 현재 폴더의 모든 파일(app.py, data 폴더 등)을 컨테이너로 복사
COPY . .

# 5. Flask가 사용할 포트 노출 (문서상의 의미)
EXPOSE 5000

# 6. 서버 실행 명령어
CMD ["python", "app.py"]