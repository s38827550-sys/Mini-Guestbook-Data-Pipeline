# 🌡️ Seoul Air Quality Data Pipeline & Mini Guestbook

서울시 실시간 대기질 데이터를 수집, 가공하고 방문자 기록을 관리하는 통합 데이터 파이프라인 프로젝트입니다. 
자동화된 스케줄링(APScheduler), 데이터 영속성 관리, 그리고 시스템 안정성을 위한 헬스체크 기능이 포함되어 있습니다.

## 🛠 기술 스택

| 분류 | 기술 |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Database** | PostgreSQL 15 |
| **Scheduling** | APScheduler (Background Tasks) |
| **Frontend** | Jinja2 Templates (HTML/CSS) |
| **Infrastructure** | Docker, Docker Compose |
| **Monitoring** | Healthcheck API, Docker Healthcheck |

## 📁 프로젝트 구조

```text
Mini-Guestbook-Data-Pipeline/
├── main.py              # FastAPI 앱 (스케줄러, API 정의, DB 초기화)
├── Dockerfile           # 웹 서버 컨테이너 빌드 설정
├── docker-compose.yml   # DB(Healthcheck 포함) + 웹 서비스 오케스트레이션
├── requirements.txt     # Python 패키지 목록
├── .env.example         # 환경 변수 샘플 양식
├── test_api.py          # 전체 엔드포인트 통합 테스트 스크립트
├── templates/
│   └── index.html       # 대기질 대시보드 템플릿
└── .gitignore           # 보안 및 데이터 파일 관리
```

## 🚀 시작하기

### 1. 환경 변수 설정

`.env` 파일을 생성하고 아래 내용을 설정하세요. (Seoul Open API 키가 필요합니다)

```text
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=guestbook
DB_HOST=db
DB_PORT=5432
SEOUL_API_KEY=your_seoul_api_key
```

### 2. 실행 (Docker Compose)

본 프로젝트는 Docker Healthcheck를 사용하여 DB가 완전히 준비된 후 웹 서버가 실행되도록 설계되었습니다.

```bash
# 컨테이너 빌드 및 백그라운드 실행
docker-compose up -d --build
```

- **대시보드**: [http://localhost:8000/view-air](http://localhost:8000/view-air)
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **헬스체크**: [http://localhost:8000/health](http://localhost:8000/health)

## 📡 주요 API 엔드포인트

### 🌬️ 대기질 데이터 (Air Quality)
- **GET /view-air** : 실시간 대기질 대시보드 (HTML)
- **GET /air-data** : 대기질 원본 데이터 조회 (JSON)
- **GET /air-summary** : 데이터 통계 요약 (평균, 최대, 최소 등)
- **GET /health** : 서버 및 DB 연결 상태 모니터링

### ✍️ 방명록 (Guestbook)
- **POST /visit/{name}** : 방문자 이름 등록
- **GET /guests** : 전체 방문자 목록 조회

## ⚙️ 시스템 설계 특징

### 🕒 자동화된 데이터 파이프라인
- **수집 (Hourly)**: 매시간 서울시 API에서 데이터를 수집하며, `ON CONFLICT`를 통해 중복 데이터를 방지합니다.
- **가공 (Daily)**: 매일 자정에 전날의 데이터를 요약하여 통계 테이블을 생성합니다.

### 🛡️ 견고한 인프라 및 운영
- **DB 자동 초기화**: 서버 시작 시 필요한 테이블(`air_quality`, `daily_air_stats`, `guests`)이 없을 경우 자동으로 생성합니다.
- **Docker Healthcheck**: `pg_isready`를 통해 DB 상태를 체크하며, 웹 서버는 DB가 'Healthy' 상태일 때만 가동되어 접속 오류를 방지합니다.
- **통합 테스트**: `test_api.py`를 통해 모든 API 엔드포인트의 정상 작동 여부를 일괄 검증할 수 있습니다.

### 🔌 효율적인 자원 관리
- **Connection Pooling**: `psycopg2.pool`을 통해 데이터베이스 연결을 효율적으로 관리합니다.
- **Lifespan Management**: 서버 종료 시 스케줄러와 DB 풀을 안전하게 닫아 자원 누수를 방지합니다.
