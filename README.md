# 🌡️ Seoul Air Quality Data Pipeline & Mini Guestbook

서울시 실시간 대기질 데이터를 수집, 가공하고 방문자 기록을 관리하는 통합 데이터 파이프라인 프로젝트입니다. 
자동화된 스케줄링(APScheduler)과 데이터 영속성 관리가 핵심입니다.

## 🛠 기술 스택

| 분류 | 기술 |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Database** | PostgreSQL 15 |
| **Scheduling** | APScheduler (Background Tasks) |
| **Frontend** | Jinja2 Templates (HTML/CSS) |
| **Infrastructure** | Docker, Docker Compose |
| **Security** | Dotenv (.env) 환경변수 분리 |

## 📁 프로젝트 구조

```text
Mini-Guestbook-Data-Pipeline/
├── main.py              # FastAPI 앱 (스케줄러, API 정의, DB 연동)
├── Dockerfile           # 웹 서버 컨테이너 빌드 설정
├── docker-compose.yml   # DB + 웹 서비스 오케스트레이션
├── requirements.txt     # Python 패키지 목록
├── .env.example         # 환경 변수 샘플 양식
├── templates/
│   └── index.html       # 대기질 대시보드 템플릿
├── postgres_data/       # PostgreSQL 데이터 저장소 (Git 제외)
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

```bash
# 컨테이너 빌드 및 백그라운드 실행
docker-compose up -d --build
```

- **대시보드**: [http://localhost:8000/view-air](http://localhost:8000/view-air)
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📡 주요 API 엔드포인트

### 🌬️ 대기질 데이터 (Air Quality)
- **GET /view-air** : 실시간 대기질 대시보드 (HTML)
- **GET /air-data** : 대기질 원본 데이터 조회 (JSON, 페이지네이션 지원)
- **GET /air-search** : 특정 측정소 검색 및 정렬
- **GET /air-summary** : 수집된 데이터의 통계 요약 (평균, 최대, 최소)
- **GET /collect-air** : 대기질 데이터 즉시 수집 (수동)

### ✍️ 방명록 (Guestbook)
- **POST /visit/{name}** : 방문자 이름 등록
- **GET /guests** : 전체 방문자 목록 조회

## ⚙️ 시스템 설계 특징

### 🕒 자동화된 데이터 파이프라인
APScheduler를 사용하여 데이터 생명주기를 관리합니다.
1. **수집 (Hourly)**: 매시간 서울시 Open API에서 실시간 대기질 데이터를 수집하여 DB에 적재합니다 (`ON CONFLICT` 처리를 통해 중복 방지).
2. **가공 (Daily)**: 매일 자정(00:05)에 전날의 데이터를 요약하여 일간 통계 테이블(`daily_air_stats`)을 생성합니다.

### 🔌 효율적인 DB 관리
- **Connection Pooling**: `psycopg2.pool`을 사용하여 다중 요청 환경에서도 안정적인 DB 연결을 유지합니다.
- **Lifespan Management**: FastAPI의 lifespan 기능을 사용하여 서버 시작 시 커넥션 풀을 초기화하고, 종료 시 스케줄러와 연결을 안전하게 해제합니다.

### 🌐 데이터 시각화
Jinja2 템플릿 엔진을 활용하여 서버 사이드 렌더링 방식의 간결한 대시보드를 제공합니다.
