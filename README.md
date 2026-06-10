# 🌡️ Seoul Air Quality Data Pipeline

> 서울시 실시간 대기질 데이터를 **수집 → 저장 → 가공 → 배포**하는 end-to-end 데이터 파이프라인입니다.  
> 단순한 CRUD를 넘어, 멱등성 보장·클라우드 인프라 대응·가동성 확보라는 세 가지 엔지니어링 문제를 직접 해결했습니다.

**🔗 라이브 데모:** https://mini-guestbook-data-pipeline.onrender.com/view-air

---

## ✨ 최근 업데이트 (Recent Updates)

- **UI 시각화 개선**: `index.html` 대시보드에서 대기질 등급(좋음, 보통, 나쁨 등)에 따른 컬러 코딩을 적용하여 가시성을 높였습니다.
- **분석 리포트 강화**: `report.html`을 통해 어제 하루 동안 가장 공기가 깨끗했던 '청정 구역 TOP 5'를 자동으로 집계하여 보여줍니다.
- **스케줄러 안정화**: APScheduler의 크론 트리거 설정을 최적화하여 정시 데이터 수집의 정확도를 높였습니다.
- **예외 처리 보강**: 외부 API 장애나 DB 연결 일시 중단 시에도 서버가 중단되지 않도록 `try-except-finally` 블록과 리소스 반납 로직을 전면 재검토했습니다.

---

## 🏗️ 시스템 아키텍처

```
[서울시 공공 API]
      │  매시 정각 자동 수집 (APScheduler cron)
      ▼
[FastAPI 수집 레이어]  ─── lifespan으로 스케줄러 생명주기 관리
      │  ON CONFLICT (measure_time, station_name) DO UPDATE
      ▼
[PostgreSQL - air_quality 테이블]   ← Raw 데이터
      │  매일 00:05 집계 (AVG, MAX, GROUP BY)
      ▼
[PostgreSQL - daily_air_stats 테이블]  ← Mart 데이터
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
| Database | PostgreSQL 15 (SimpleConnectionPool) |
| Scheduling | APScheduler — BackgroundScheduler, cron 트리거 |
| Frontend | Jinja2 Templates |
| Infrastructure | Docker, Docker Compose, Render.com |
| Monitoring | `/health` 엔드포인트 (GET + HEAD), UptimeRobot |

---

## 💡 핵심 엔지니어링 포인트

### 1. 멱등성(Idempotency) 확보

서버가 재시작되거나 스케줄러가 중복 실행되어도 데이터가 꼬이지 않도록 두 겹의 안전망을 설계했습니다.

**스케줄러 레벨** — `replace_existing=True` 옵션으로, 서버가 재시작될 때 동일한 Job이 중복 등록되는 것을 방지합니다.

```python
scheduler.add_job(
    task_collect_air,
    'cron',
    minute=0,               # 매시 정각 실행
    id="air_collector",
    replace_existing=True,  # 재시작해도 Job은 항상 1개
    timezone=pytz.timezone("Asia/Seoul")
)

scheduler.add_job(
    task_calculate_daily_stats,
    'cron',
    hour=0,
    minute=5,               # 매일 00:05 실행
    id="air_stats_daily",
    replace_existing=True,
    timezone=pytz.timezone("Asia/Seoul")
)
```

**DB 레벨** — `UNIQUE(measure_time, station_name)` 제약 조건과 `ON CONFLICT DO UPDATE` 구문으로, 같은 측정소·같은 시각의 데이터가 들어와도 중복 행을 생성하지 않고 값만 갱신합니다.

```sql
INSERT INTO air_quality (measure_time, station_name, pm10, pm25, status)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (measure_time, station_name)
DO UPDATE SET
    pm10   = EXCLUDED.pm10,
    pm25   = EXCLUDED.pm25,
    status = EXCLUDED.status;
```

일일 통계 테이블(`daily_air_stats`)도 동일한 패턴을 적용해, 재실행 시 기존 통계를 덮어쓰고 중복 집계를 막습니다.

---

### 2. 클라우드 인프라 대응 (로컬 ↔ 클라우드 DB 자동 전환)

Render가 제공하는 `DATABASE_URL`은 `postgres://` 스킴을 사용하지만, psycopg2는 `postgresql://`을 요구합니다. 이 차이를 코드 레벨에서 자동 교정하고, 환경 변수 유무만으로 로컬과 클라우드 연결을 분기합니다.

```python
# 1단계: postgres:// → postgresql:// 스킴 자동 교정
raw_uri = os.getenv("DATABASE_URL")
if raw_uri and raw_uri.startswith("postgres://"):
    DATABASE_URL = raw_uri.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_uri

# 2단계: DATABASE_URL 유무로 환경 자동 분기
def init_db_pool():
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        # 클라우드 (Render): 단일 URL 방식
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=dsn)
    else:
        # 로컬 (Docker Compose): 개별 파라미터 방식
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1, 10,
            host=os.getenv("DB_HOST", "db"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT", "5432")
        )
```

`.env` 파일에서 `DATABASE_URL` 한 줄만 바꾸면 환경 전환이 완료됩니다. 별도의 코드 수정이 필요 없습니다.

---

### 3. 가동성 보장 (Idling 문제 해결)

Render 무료 플랜은 일정 시간 요청이 없으면 서버를 슬립 상태로 전환합니다. 이로 인해 스케줄러가 멈추고 매시간 데이터 수집이 중단되는 문제가 발생합니다.

**해결책:** DB 연결 상태를 실제로 쿼리하는 `/health` 엔드포인트를 설계하고, UptimeRobot이 5분마다 이를 호출하도록 설정했습니다. `HEAD` 메서드도 함께 지원해 모니터링 도구의 경량 핑에도 대응합니다.

```python
@app.get("/health")
@app.head("/health")
def health_check():
    db_status = "offline"
    conn = None
    try:
        conn = get_db_conn()
        conn.cursor().execute("SELECT 1;")
        db_status = "online"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    finally:
        if conn:
            release_db_conn(conn)

    return {
        "status": "up",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }
```

| 구성 요소 | 역할 |
|-----------|------|
| `/health` 엔드포인트 | DB에 `SELECT 1` 쿼리를 실행해 실제 연결 상태를 JSON으로 노출 |
| `@app.head("/health")` | 모니터링 도구의 경량 핑 요청 지원 |
| UptimeRobot | 5분 간격 호출 → 서버 슬립 방지 |
| Docker Healthcheck | 컨테이너 레벨에서 앱 상태 주기적 확인 |

---

## 📁 프로젝트 구조

```
Mini-Guestbook-Data-Pipeline/
├── main.py              # FastAPI 앱 (스케줄러, API, DB 초기화, 커넥션 풀)
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
| GET | `/report` | 구별 통계 리포트 — PM10 기준 하위 TOP 5 |
| GET | `/air-data` | 원본 데이터 조회 (JSON, `limit` / `offset` 페이징 지원) |
| GET | `/air-search` | 측정소명 필터 + PM10 정렬 검색 (`station`, `order` 파라미터) |
| GET | `/air-summary` | 전체 데이터 통계 요약 — 평균·최대·최솟값 |
| GET/HEAD | `/health` | DB 연결 상태 모니터링 |
| GET | `/collect-air` | 수동 데이터 수집 트리거 |
| GET | `/calculate-stats` | 수동 일일 통계 가공 트리거 |

### 방명록 (Guestbook)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/visit/{name}` | 방문자 이름 등록 |
| GET | `/guests` | 전체 방문자 목록 |

---

## ⚙️ 시스템 설계 상세

### 자동화 파이프라인 스케줄

| Job ID | 실행 주기 | 작업 내용 |
|--------|-----------|-----------|
| `air_collector` | 매시 정각 (`cron minute=0`) | 서울시 공공 API 호출 → `air_quality` Upsert |
| `air_stats_daily` | 매일 00:05 (`cron hour=0, minute=5`) | `air_quality` 집계 → `daily_air_stats` Upsert |

통계 쿼리는 오늘 이전의 모든 날짜를 대상으로 집계하므로, 서버 장애 후 재가동 시 누락된 날짜의 통계도 자동으로 채워집니다.

### DB 테이블 구조

```sql
-- Raw 데이터
CREATE TABLE air_quality (
    id           SERIAL PRIMARY KEY,
    measure_time TIMESTAMP,
    station_name TEXT,
    pm10         INTEGER,
    pm25         INTEGER,
    status       TEXT,
    UNIQUE(measure_time, station_name)
);

-- Mart 데이터 (집계)
CREATE TABLE daily_air_stats (
    id           SERIAL PRIMARY KEY,
    stats_date   DATE,
    station_name TEXT,
    avg_pm10     NUMERIC,
    avg_pm25     NUMERIC,
    max_pm10     INTEGER,
    data_count   INTEGER,
    UNIQUE(stats_date, station_name)
);
```

### 안정성 설계

- **DB 자동 초기화**: `lifespan` 시작 시 `init_db_tables()`가 실행되어 테이블을 자동 생성합니다. 신규 환경에서도 별도 마이그레이션이 필요 없습니다.
- **Connection Pooling**: `SimpleConnectionPool(minconn=1, maxconn=10)`으로 다중 요청 상황에서도 DB 연결을 효율적으로 재사용합니다.
- **Graceful Shutdown**: `lifespan`의 `yield` 이후 블록에서 스케줄러를 안전하게 종료합니다.
- **상세 로깅**: `logging` 모듈로 수집 건수, DB 연결 방식, 오류를 실시간으로 기록하며 APScheduler 내부 로그도 DEBUG 레벨로 노출합니다.
