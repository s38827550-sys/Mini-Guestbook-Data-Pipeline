# 🌡️ Seoul Air Quality Data Pipeline

> 서울시 실시간 대기질 데이터를 **수집 → 저장 → 가공 → 배포**하는 end-to-end 데이터 파이프라인입니다.  
> 단순한 CRUD를 넘어, 멱등성 보장·클라우드 인프라 대응·가동성 확보라는 세 가지 엔지니어링 문제를 직접 해결했습니다.

**🔗 라이브 데모:** https://mini-guestbook-data-pipeline.onrender.com/view-air

---

## 🏗️ 시스템 아키텍처

```
[서울시 공공 API]
      │  매시간 자동 수집 (APScheduler)
      ▼
[FastAPI 수집 레이어]
      │  ON CONFLICT → Upsert (중복 방지)
      ▼
[PostgreSQL - Raw 테이블]
      │  매일 자정 집계 (AVG, MAX, GROUP BY)
      ▼
[PostgreSQL - Mart 테이블]
      │
      ▼
[Jinja2 대시보드 / REST API]  ←→  UptimeRobot (Health Check)
```

전체 파이프라인은 Docker 컨테이너 위에서 동작하며, Render.com 클라우드에 배포되어 24시간 운영됩니다.

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | PostgreSQL 15 |
| Scheduling | APScheduler (lifespan 기반 비동기 실행) |
| Frontend | Jinja2 Templates |
| Infrastructure | Docker, Docker Compose, Render.com |
| Monitoring | `/health` 엔드포인트, UptimeRobot |

---

## 💡 핵심 엔지니어링 포인트

### 1. 멱등성(Idempotency) 확보

서버가 재시작되거나 스케줄러가 중복 실행되어도 데이터가 꼬이지 않도록 두 겹의 안전망을 설계했습니다.

**스케줄러 레벨** — `replace_existing=True` 옵션으로 서버 재시작 시 동일한 Job이 중복 등록되는 것을 방지합니다.

```python
scheduler.add_job(
    fetch_air_quality,
    "interval",
    hours=1,
    replace_existing=True,   # 재시작해도 Job은 항상 1개
    misfire_grace_time=300,  # 지연 실행 허용 (서버 슬립 대응)
    coalesce=True            # 누적된 실행 요청을 1회로 병합
)
```

**DB 레벨** — `ON CONFLICT (측정소, 측정시간) DO UPDATE` 구문으로 같은 데이터가 들어와도 덮어쓰기만 하고 중복 행을 생성하지 않습니다.

```sql
INSERT INTO air_quality (station, measured_at, pm10, pm25)
VALUES (%s, %s, %s, %s)
ON CONFLICT (station, measured_at)
DO UPDATE SET pm10 = EXCLUDED.pm10, pm25 = EXCLUDED.pm25;
```

---

### 2. 클라우드 인프라 대응 (로컬 ↔ 클라우드 DB 자동 전환)

로컬 개발(Docker Compose)과 클라우드 배포(Render)는 DB 연결 방식이 다릅니다. 환경 변수 하나로 두 환경을 코드 수정 없이 전환할 수 있도록 설계했습니다.

```python
# main.py
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # 클라우드 환경 (Render): 단일 URL 방식
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
else:
    # 로컬 환경 (Docker Compose): 개별 파라미터 방식
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
```

`DATABASE_URL` 유무만으로 분기되므로, 개발자는 `.env` 파일 하나만 바꾸면 됩니다.

---

### 3. 가동성 보장 (Idling 문제 해결)

Render 무료 플랜은 일정 시간 요청이 없으면 서버를 슬립 상태로 전환합니다. 이로 인해 스케줄러가 멈추고 데이터 수집이 중단되는 문제가 발생합니다.

**해결책:** `/health` 엔드포인트를 설계하고, UptimeRobot이 5분마다 이 엔드포인트를 호출하도록 설정했습니다. 서버는 항상 깨어 있는 상태를 유지하고, 스케줄러는 끊김 없이 실행됩니다.

```python
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "scheduler_running": scheduler.running,
        "timestamp": datetime.now(KST).isoformat()
    }
```

| 구성 요소 | 역할 |
|-----------|------|
| `/health` 엔드포인트 | 스케줄러 상태·DB 연결 여부를 JSON으로 노출 |
| UptimeRobot | 5분 간격으로 `/health` 호출 → 서버 슬립 방지 |
| Docker Healthcheck | 컨테이너 레벨에서 앱 상태를 주기적으로 확인 |

---

## 📁 프로젝트 구조

```
Mini-Guestbook-Data-Pipeline/
├── main.py              # FastAPI 앱 (스케줄러, API, DB 초기화)
├── Dockerfile           # 웹 서버 컨테이너 빌드 설정
├── docker-compose.yml   # DB + 웹 서비스 오케스트레이션
├── requirements.txt     # Python 패키지 목록
├── .env.example         # 환경 변수 샘플 양식
├── test_api.py          # 전체 엔드포인트 통합 테스트
├── templates/
│   ├── index.html       # 대기질 대시보드 템플릿
│   └── report.html      # 대기질 분석 리포트 템플릿
└── .gitignore
```

---

## 🚀 시작하기

### 1. 환경 변수 설정

`.env` 파일을 생성하고 아래 내용을 채워넣으세요.

```env
# 로컬 개발 (Docker Compose)
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=guestbook
DB_HOST=db
DB_PORT=5432

# 클라우드 배포 (Render 등) — 설정 시 자동으로 우선 적용됨
DATABASE_URL=your_database_url_here

# 공통
SEOUL_API_KEY=your_seoul_api_key
```

### 2. Docker로 실행

```bash
docker-compose up -d --build
```

| 경로 | 설명 |
|------|------|
| `http://localhost:8000/view-air` | 실시간 대기질 대시보드 |
| `http://localhost:8000/report` | 구별 통계 분석 리포트 |
| `http://localhost:8000/health` | 시스템 상태 모니터링 |

---

## 📡 API 엔드포인트

### 대기질 (Air Quality)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/view-air` | 실시간 대기질 대시보드 (HTML) |
| GET | `/report` | 구별 통계 리포트 — TOP 5 측정소 포함 |
| GET | `/air-data` | 원본 데이터 조회 (JSON) |
| GET | `/air-summary` | 통계 요약 정보 (JSON) |
| GET | `/health` | 스케줄러·DB 상태 모니터링 |

### 방명록 (Guestbook)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/visit/{name}` | 방문자 이름 등록 |
| GET | `/guests` | 전체 방문자 목록 |

---

## ⚙️ 시스템 설계 상세

### 자동화 파이프라인 스케줄

| 작업 | 주기 | 설명 |
|------|------|------|
| 대기질 수집 | 매시간 | 서울시 공공 API → Raw 테이블 저장 |
| 일일 통계 생성 | 매일 자정 | Raw 데이터 → Mart 테이블 집계 |

### 안정성 설계

- **DB 자동 초기화**: 서버 시작 시 필요한 테이블을 자동 생성
- **Connection Pooling**: 다중 접속 상황에서도 DB 성능 유지
- **Graceful Shutdown**: FastAPI `lifespan`으로 서버 종료 시 스케줄러·DB 연결을 안전하게 해제
- **상세 로깅**: `PYTHONUNBUFFERED=1` 설정으로 컨테이너 로그 실시간 모니터링
