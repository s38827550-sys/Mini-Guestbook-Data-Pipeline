# 🌡️ Seoul Air Quality Data Pipeline & Mini Guestbook

서울시 실시간 대기질 데이터를 수집, 가공하고 방문자 기록을 관리하는 통합 데이터 파이프라인 프로젝트입니다. 
자동화된 스케줄링(APScheduler), 데이터 영속성 관리, 그리고 클라우드 배포(Render) 지원 기능이 포함되어 있습니다.

## 🛠 기술 스택

| 분류 | 기술 |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Database** | PostgreSQL 15 |
| **Scheduling** | APScheduler (Background Tasks) |
| **Frontend** | Jinja2 Templates (HTML/CSS) |
| **Infrastructure** | Docker, Docker Compose, Render (Cloud) |
| **Monitoring** | Healthcheck API, Docker Healthcheck |

## 📁 프로젝트 구조

```text
Mini-Guestbook-Data-Pipeline/
├── main.py              # FastAPI 앱 (스케줄러, API 정의, DB 초기화, 배포 최적화)
├── Dockerfile           # 웹 서버 컨테이너 빌드 설정
├── docker-compose.yml   # DB(Healthcheck 포함) + 웹 서비스 오케스트레이션
├── requirements.txt     # Python 패키지 목록
├── .env.example         # 환경 변수 샘플 양식
├── test_api.py          # 전체 엔드포인트 통합 테스트 스크립트
├── templates/
│   ├── index.html       # 대기질 대시보드 템플릿
│   └── report.html      # 대기질 분석 리포트 템플릿
└── .gitignore           # 보안 및 데이터 파일 관리
```

## 🚀 시작하기

### 1. 환경 변수 설정

`.env` 파일을 생성하고 아래 내용을 설정하세요. 로컬 실행과 클라우드 배포 환경 모두 지원합니다.

```text
# 로컬 개발 환경용 (Docker Compose)
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=guestbook
DB_HOST=db
DB_PORT=5432

# 클라우드 배포용 (Render 등)
DATABASE_URL=your_database_url_here

# 공통 설정
SEOUL_API_KEY=your_seoul_api_key
```

### 2. 실행 (Docker Compose)

```bash
# 컨테이너 빌드 및 백그라운드 실행
docker-compose up -d --build
```

- **대시보드**: [http://localhost:8000/view-air](http://localhost:8000/view-air)
- **분석 리포트**: [http://localhost:8000/report](http://localhost:8000/report)
- **헬스체크**: [http://localhost:8000/health](http://localhost:8000/health)

## 📡 주요 API 엔드포인트

### 🌬️ 대기질 데이터 (Air Quality)
- **GET /view-air** : 실시간 대기질 현황 대시보드
- **GET /report** : 대기질 통계 분석 리포트 (TOP 5 측정소 등)
- **GET /air-data** : 대기질 원본 데이터 조회 (JSON)
- **GET /air-summary** : 데이터 통계 요약 정보
- **GET /health** : 시스템 상태 모니터링

### ✍️ 방명록 (Guestbook)
- **POST /visit/{name}** : 방문자 이름 등록
- **GET /guests** : 전체 방문자 목록 조회

## ⚙️ 시스템 설계 특징

### 🕒 자동화된 데이터 파이프라인
- **데이터 수집/가공**: 매시간 API 수집 및 매일 자정 통계 생성을 자동화했습니다.
- **배포 최적화**: `DATABASE_URL` 감지 로직을 통해 클라우드 DB(Render 등)와 로컬 DB를 유연하게 전환합니다.

### 🛡️ 견고한 인프라 및 운영
- **DB 자동 초기화**: 서버 시작 시 필요한 테이블을 자동 생성하여 초기 설정 부담을 줄였습니다.
- **오류 복구**: DB 연결 실패 시 상세 로깅 및 Lifespan 예외 처리를 통해 시스템 다운타임을 최소화합니다.
- **검증**: `test_api.py`를 통해 모든 기능을 안정적으로 테스트할 수 있습니다.

### 🔌 효율적인 자원 관리
- **Connection Pooling**: 다중 접속 상황에서도 DB 성능을 유지하도록 설계되었습니다.
- **Graceful Shutdown**: 서버 종료 시 스케줄러와 DB 연결을 안전하게 해제합니다.
