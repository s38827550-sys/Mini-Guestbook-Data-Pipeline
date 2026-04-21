from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

# DB 연결 설정 (환경변수 활용)
def get_db_conn():
    # os.getenv("변수명", "기본값") -> 환경변수가 없을 경우 대비
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), 
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT")
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to Guestbook API"}

# 브라우저 테스트를 위해 임시로 GET으로 변경하셔도 됩니다! (@app.get)
@app.post("/visit/{name}")
def add_visit(name: str):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("CREATE TABLE IF NOT EXISTS guests (name TEXT);")
        cur.execute("INSERT INTO guests (name) VALUES (%s);", (name,))
        conn.commit()
        return {"status": "success", "added": name}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        cur.close()
        conn.close()

@app.get("/guests")
def get_guests():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM guests;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"guest_list": [row[0] for row in rows]}