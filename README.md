# 📒 Mini Guestbook Data Pipeline

방문자 이름을 기록하고 조회하는 미니 방명록 REST API입니다.
인프라 구축의 핵심인 **Docker 환경 격리**와 **환경 변수(.env)를 통한 보안 관리**가 적용되어 있습니다.

## 🛠 기술 스택

| 분류 | 기술 |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **Database** | PostgreSQL 15 |
| **Infrastructure** | Docker, Docker Compose |
| **Security** | Dotenv (.env) 환경변수 분리 |

## 📁 프로젝트 구조

```text
Mini-Guestbook-Data-Pipeline/
├── main.py              # FastAPI 앱 (환경변수 로드 및 API 정의)
├── Dockerfile           # 웹 서버 컨테이너 빌드 설정
├── docker-compose.yml   # DB + 웹 서비스 오케스트레이션
├── requirements.txt     # Python 패키지 목록
├── .env.example         # 환경 변수 샘플 양식
├── .gitignore           # 데이터 및 보안 파일 제외 설정
└── .dockerignore        # 도커 빌드 제외 설정
```

## 🚀 시작하기

### 1\. 환경 변수 설정 (필수)

보안을 위해 민감 정보는 코드와 분리되어 있습니다.
예시 파일(.env.example)을 참고하여 만들면 조금 더 쉽게 만들 수 있습니다.

```text
DB_USER=your_user_here
DB_PASSWORD=your_password_here
DB_NAME=guestbook
DB_HOST=db
DB_PORT=5432
```

### 2\. 컨테이너 빌드 및 실행

```bash
# 컨테이너 빌드 및 백그라운드 실행
docker-compose up -d --build
```

서버가 실행되면 [http://localhost:8000](https://www.google.com/search?q=http://localhost:8000) 으로 접속할 수 있습니다.

## 📡 API 엔드포인트

  - **GET /** : 서버 상태 확인
  - **POST /visit/{name}** : 방명록에 이름 추가 (자동 테이블 생성 포함)
  - **GET /guests** : 등록된 전체 방문자 목록 조회
  - **Swagger UI** : [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)

## ⚙️ 주요 설계 특징

### 🔐 보안 및 설정 분리

  - **Hard-coding 방지**: `main.py`와 `docker-compose.yml`에서 직접적인 비밀번호 노출을 제거하고 `os.getenv()`를 통해 값을 주입받습니다.
  - **Git 위생 관리**: `.env` 파일과 `postgres_data/` 폴더를 `.gitignore`에 등록하여 민감 정보와 대용량 데이터의 유출을 원천 차단했습니다.

### 💾 데이터 영속성 (Persistence)

  - Docker Volume 매핑을 통해 컨테이너가 중지되거나 삭제되어도 PostgreSQL에 저장된 데이터가 유실되지 않도록 설계했습니다.

## 📝 Trouble Shooting

  - **Git Cache Issue**: `.gitignore` 등록 전 추적된 데이터 폴더가 Git 로그에 남는 문제를 `git rm -r --cached` 명령어로 해결하여 소스코드와 데이터를 완벽히 분리함.
  - **Connection Error**: 서비스 간 의존성(`depends_on`)을 설정하여 DB 컨테이너가 준비된 후 API 서버가 가동되도록 안정성을 높임.
