from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

# DB 연결 설정 (환경변수 활용)
def get_db_conn():
    return psycopg2.connect(
        host="db", # 도커 컴포즈의 서비스 이름이 호스트가 됩니다.
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to Guestbook API"}

@app.post("/visit/{name}")
def add_visit(name: str):
    conn = get_db_conn()
    cur = conn.cursor()
    # 테이블이 없으면 생성하고 이름 저장 (SQL 문법 활용)
    cur.execute("CREATE TABLE IF NOT EXISTS guests (name TEXT);")
    cur.execute("INSERT INTO guests (name) VALUES (%s);", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "success", "added": name}

@app.get("/guests")
def get_guests():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM guests;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"guest_list": [row[0] for row in rows]}