# 1. 파이썬 3.12 슬림 버전을 기반으로 시작 (이미 파이썬이 깔려 있음)
FROM python:3.12-slim

# 2. 컨테이너 내부에서 작업할 폴더 생성 및 이동
WORKDIR /app

# 3. 라이브러리 목록 파일을 먼저 복사
COPY requirements.txt .

# 4. 필요한 라이브러리 설치
RUN pip install --no-cache-dir -r requirements.txt

# 5. 나머지 소스 코드(main.py 등) 전체 복사
COPY . .

# 6. 컨테이너가 켜질 때 실행할 명령어
# --host 0.0.0.0으로 설정해야 외부(윈도우)에서 접속이 가능합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]