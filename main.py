from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import pytz
import psycopg2
from psycopg2 import pool
import os
import requests
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import datetime

load_dotenv()
scheduler = BackgroundScheduler(timezone=pytz.timezone("Asia/Seoul"))

# --- 📋 로거 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# --- 🔌 커넥션 풀 설정 ---
db_pool: pool.SimpleConnectionPool = None

def init_db_pool():
    global db_pool
    db_pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )
    logger.info("✅ DB 커넥션 풀 초기화 완료")

def init_db_tables():
    """필요한 테이블들을 생성합니다."""
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # 1. air_quality 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS air_quality (
                id SERIAL PRIMARY KEY,
                measure_time TIMESTAMP,
                station_name TEXT,
                pm10 INTEGER,
                pm25 INTEGER,
                status TEXT,
                UNIQUE(measure_time, station_name)
            );
        """)
        
        # 2. daily_air_stats 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_air_stats (
                id SERIAL PRIMARY KEY,
                stats_date DATE,
                station_name TEXT,
                avg_pm10 NUMERIC,
                avg_pm25 NUMERIC,
                max_pm10 INTEGER,
                data_count INTEGER,
                UNIQUE(stats_date, station_name)
            );
        """)
        
        # 3. guests 테이블
        cur.execute("CREATE TABLE IF NOT EXISTS guests (name TEXT);")
        
        conn.commit()
        logger.info("✅ DB 테이블 초기화 완료")
    except Exception as e:
        logger.error(f"❌ DB 테이블 초기화 실패: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)

def get_db_conn():
    """풀에서 커넥션을 빌려옴"""
    return db_pool.getconn()

def release_db_conn(conn):
    """사용한 커넥션을 풀에 반납"""
    db_pool.putconn(conn)


# --- ⚙️ 스케줄 태스크 ---

def task_collect_air():
    logger.info("📢 [SYSTEM] 데이터 수집을 시작합니다...")
    API_KEY = os.getenv("SEOUL_API_KEY")
    url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/RealtimeCityAir/1/25/"

    # [수정] conn, cur 모두 None으로 미리 선언 → finally에서 NameError 방지
    conn = None
    cur = None
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        rows = result.get("RealtimeCityAir", {}).get("row", [])

        if not rows:
            masked_key = API_KEY[:4] + "****" if API_KEY else "None"
            logger.error(f"❌ API 데이터 없음. Key 앞 4자리: {masked_key}")
            return

        conn = get_db_conn()
        cur = conn.cursor()

        count = 0
        for row in rows:
            dt_raw = row.get("MSRMT_DT")  # "202604281700"
            dt = datetime.strptime(dt_raw, "%Y%m%d%H%M") if dt_raw else None  # → 2026-04-28 17:00:00
            name   = row.get("MSRSTN_NM")
            pm10   = row.get("PM")
            pm25   = row.get("FPM")
            status = row.get("CAI_GRD")

            cur.execute(
                """
                INSERT INTO air_quality (measure_time, station_name, pm10, pm25, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (measure_time, station_name)
                DO UPDATE SET
                    pm10   = EXCLUDED.pm10,
                    pm25   = EXCLUDED.pm25,
                    status = EXCLUDED.status;
                """,
                (dt, name, pm10, pm25, status)
            )
            count += 1

        conn.commit()
        logger.info(f"✅ [SYSTEM] 수집 및 저장 완료! ({count}건)")

    except requests.RequestException as e:
        logger.error(f"❌ 외부 API 요청 실패: {type(e).__name__}")
        if conn:
            conn.rollback()
    except Exception as e:
        logger.error(f"❌ [ERROR] 수집 중 오류 발생: {e}")
        if conn:
            conn.rollback()
    finally:
        # [수정] 'cur in locals()' 대신 'cur is not None'으로 안전하게 체크
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)


def task_calculate_daily_stats():
    logger.info("📊 [SYSTEM] 일간 통계 가공을 시작합니다...")

    # [수정] cur도 None으로 미리 선언
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        # 수정된 쿼리: 어제 하루치만 하는 게 아니라, 통계 테이블에 없는 날짜들을 다 찾아서 채움
        insert_query = """
        INSERT INTO daily_air_stats (stats_date, station_name, avg_pm10, avg_pm25, max_pm10, data_count)
        SELECT 
            CAST(measure_time AS DATE) as stats_date,
            station_name,
            ROUND(AVG(pm10)::numeric, 2),
            ROUND(AVG(pm25)::numeric, 2),
            MAX(pm10),
            COUNT(*)
        FROM air_quality
        -- 조건 변경: 오늘 데이터를 제외한 모든 과거 데이터를 대상으로 집계
        WHERE CAST(measure_time AS DATE) < CURRENT_DATE 
        GROUP BY stats_date, station_name
        ON CONFLICT (stats_date, station_name) 
        DO UPDATE SET 
            avg_pm10 = EXCLUDED.avg_pm10,
            avg_pm25 = EXCLUDED.avg_pm25,
            max_pm10 = EXCLUDED.max_pm10,
            data_count = EXCLUDED.data_count;
        """
        cur.execute(insert_query)
        conn.commit()
        logger.info("✅ [SYSTEM] 일간 통계 저장 완료!")

    except Exception as e:
        logger.error(f"❌ [ERROR] 통계 가공 중 오류 발생: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)


# --- 🚀 Lifespan 설정 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 [SYSTEM] 서버가 시작되었습니다.")
    init_db_pool()    # 1. 커넥션 풀 초기화
    init_db_tables()  # 2. 테이블 초기화 (없으면 생성)

    scheduler.add_job(
        task_collect_air,
        'interval',
        hours=1,
        id="air_collector",
        replace_existing=True,
        misfire_grace_time=3600,
        coalesce=True,
        next_run_time=datetime.now(pytz.timezone("Asia/Seoul"))
    )
    scheduler.add_job(
        task_calculate_daily_stats,
        'cron',
        hour=0,
        minute=5,
        id="air_stats_daily",
        replace_existing=True
    )

    if not scheduler.running:
        scheduler.start()

    yield  # 서버 실행 중

    logger.info("🛑 [SYSTEM] 서버 종료 프로세스 시작")
    scheduler.shutdown()
    if db_pool:
        db_pool.closeall()
        logger.info("🔌 DB 커넥션 풀 종료 완료")


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


# --- 📡 엔드포인트 ---

@app.get("/")
def read_root():
    return {"message": "Welcome to Guestbook API"}


@app.get("/health")
def health_check():
    """서버 및 데이터베이스 연결 상태를 확인합니다."""
    db_status = "offline"
    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
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


@app.get("/collect-air")
def collect_air_data():
    try:
        task_collect_air()
        return {"status": "success", "message": "수동 저장 완료!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/calculate-stats")
def calculate_stats():
    try:
        task_calculate_daily_stats()
        return {"status": "success", "message": "어제자 통계 가공 완료!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/view-air", response_class=HTMLResponse)
def view_air_data(request: Request):
    # [수정] cur = None 미리 선언 + except 블록 추가
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT measure_time, station_name, pm10, pm25, status FROM air_quality ORDER BY measure_time DESC LIMIT 25;"
        )
        rows = cur.fetchall()
        data_list = [
            {"time": r[0], "station": r[1], "pm10": r[2], "pm25": r[3], "status": r[4]}
            for r in rows
        ]
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"count": len(data_list), "data": data_list}
        )
    except Exception as e:
        logger.error(f"❌ [ERROR] view-air 오류: {e}")
        raise  # HTTP 500으로 FastAPI에 위임
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)


@app.get("/air-data")
def get_all_air_data(
    limit:  int = Query(default=100, ge=1, le=1000, description="한 페이지 최대 조회 수"),
    offset: int = Query(default=0,   ge=0,          description="조회 시작 위치")
):
    # [수정] cur = None 미리 선언
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT measure_time, station_name, pm10, pm25, status FROM air_quality ORDER BY measure_time DESC LIMIT %s OFFSET %s;",
            (limit, offset)
        )
        rows = cur.fetchall()
        result = [
            {"time": r[0], "station": r[1], "pm10": r[2], "pm25": r[3], "status": r[4]}
            for r in rows
        ]
        return {"count": len(result), "limit": limit, "offset": offset, "data": result}
    except Exception as e:
        logger.error(f"❌ [ERROR] air-data 오류: {e}")
        return {"error": str(e)}
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)


@app.get("/air-search")
def search_air_data(
    station: str = None,
    order:   str = Query(default="desc", pattern="^(asc|desc)$")
):
    # [수정] cur = None 미리 선언
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()

        query  = "SELECT measure_time, station_name, pm10, pm25, status FROM air_quality"
        params = []

        if station:
            query += " WHERE station_name = %s"
            params.append(station)

        query += " ORDER BY pm10 ASC" if order == "asc" else " ORDER BY pm10 DESC"

        cur.execute(query, params)
        rows = cur.fetchall()
        result = [
            {"time": r[0], "station": r[1], "pm10": r[2], "pm25": r[3], "status": r[4]}
            for r in rows
        ]
        return {"search_count": len(result), "data": result}
    except Exception as e:
        logger.error(f"❌ [ERROR] air-search 오류: {e}")
        return {"error": str(e)}
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)


@app.get("/air-summary")
def get_air_summary():
    # [수정] cur = None 미리 선언
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                ROUND(AVG(pm10), 2) AS avg_pm10,
                MAX(pm10)           AS max_pm10,
                MIN(pm10)           AS min_pm10,
                COUNT(*)            AS total_records
            FROM air_quality;
        """)
        row = cur.fetchone()
        return {
            "average_pm10":     row[0],
            "highest_pm10":     row[1],
            "lowest_pm10":      row[2],
            "total_data_count": row[3],
            "message": "현재 DB에 기록된 전체 데이터의 분석 결과입니다."
        }
    except Exception as e:
        logger.error(f"❌ [ERROR] air-summary 오류: {e}")
        return {"error": str(e)}
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)


# --- 기존 방명록 기능 ---

@app.post("/visit/{name}")
def add_visit(name: str):
    # [수정] cur = None 미리 선언
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS guests (name TEXT);")
        cur.execute("INSERT INTO guests (name) VALUES (%s);", (name,))
        conn.commit()
        return {"status": "success", "added": name}
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ [ERROR] visit 오류: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)


@app.get("/guests")
def get_guests():
    # [수정] cur = None 미리 선언
    conn = None
    cur = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM guests;")
        rows = cur.fetchall()
        return {"guest_list": [row[0] for row in rows]}
    except Exception as e:
        logger.error(f"❌ [ERROR] guests 오류: {e}")
        return {"error": str(e)}
    finally:
        if cur:
            cur.close()
        if conn:
            release_db_conn(conn)

@app.get("/report", response_class=HTMLResponse)
async def get_report(request: Request):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        # 1. 랭킹 데이터 (가장 공기 좋은 곳 TOP 5)
        cur.execute("""
            SELECT station_name, avg_pm10, avg_pm25 
            FROM daily_air_stats 
            WHERE stats_date = (SELECT MAX(stats_date) FROM daily_air_stats)
            ORDER BY avg_pm10 ASC LIMIT 5
        """)
        top_stats = [{"station": r[0], "pm10": float(r[1]), "pm25": float(r[2])} for r in cur.fetchall()]
        
        return templates.TemplateResponse(
            request=request, 
            name="report.html", 
            context={"top_stats": top_stats}
        )
    finally:
        cur.close()
        conn.close()