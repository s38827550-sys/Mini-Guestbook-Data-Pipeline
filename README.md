# 🚀 Guestbook Data Pipeline: Phase 1
> **Docker 기반의 확장 가능한 데이터 백엔드 인프라 구축**
> **보안(Environment Variables)**과 **격리(Containerization)**를 핵심 원칙으로 설계되었습니다.

---

## 🏗 System Architecture
본 시스템은 서비스 간 결합도를 낮추고 데이터의 영속성을 보장하기 위해 다음과 같이 구성되었습니다.

- **FastAPI**: 유저 요청을 처리하는 백엔드 API 서버. 
- **PostgreSQL**: 데이터의 안정적 저장을 위한 관계형 데이터베이스.
- **Docker Network**: 서비스 간 내부 통신을 격리하여 보안 강화.
- **Docker Volumes**: 컨테이너 재시작 시에도 데이터가 유실되지 않도록 로컬 저장소와 동기화.



---

## 🛠 Tech Stack
| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Framework** | FastAPI |
| **Database** | PostgreSQL 15 |
| **Infrastructure** | Docker, Docker Compose |
| **Database Driver** | psycopg2-binary |

---

## 🔐 Key Features & Implementation
1. **환경 변수 분리 (.env)**:
   - DB 비밀번호, 포트, 호스트 등 민감 정보를 소스코드에서 완전히 분리하여 보안 사고를 방지했습니다.
   - `.gitignore`를 통해 민감 정보가 GitHub에 노출되지 않도록 관리합니다.
2. **Infrastructure as Code (IaC)**:
   - `docker-compose.yml`을 통해 복잡한 설치 과정 없이 명령어 한 줄로 동일한 개발 환경을 복제할 수 있습니다.
3. **데이터 영속성 보장**:
   - `postgres_data` 볼륨 매핑을 통해 컨테이너 삭제 후에도 DB 내용이 유지되도록 설계했습니다.

---

## 📖 실행 방법 (Getting Started)

1. **레포지토리 클론**
   ```bash
   git clone https://github.com/사용자아이름/프로젝트이름.git
   cd 프로젝트이름
   ```

2. **환경 변수 설정**
   프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 입력합니다.
   ```text
   DB_USER=your_user_here
   DB_PASSWORD=your_password_here
   DB_NAME=guestbook
   DB_HOST=db
   DB_PORT=5432
   ```

3. **시스템 실행**
   ```bash
   docker-compose up -d --build
   ```

4. **API 확인**
   - API 서버: `http://localhost:8000`
   - Swagger 문서: `http://localhost:8000/docs`

---

## 🧠 Troubleshooting & Lessons Learned

### 1. `.gitignore` 우선순위 문제 해결
- **문제**: `.gitignore` 작성 전 `git add`를 수행하여 `postgres_data` 폴더가 추적 대상에 포함됨.
- **해결**: `git rm -r --cached` 명령어를 통해 Git 캐시를 비우고, 인덱스를 재구성하여 데이터와 코드를 완벽히 분리함.

### 2. 줄바꿈 문자(LF/CRLF) 경고 대응
- **문제**: Windows 환경과 Docker(Linux) 환경 간의 줄바꿈 방식 차이로 인한 Git Warning 발생.
- **해결**: 데이터 폴더를 Git 관리 대상에서 제외함으로써 인프라 의존성 문제를 근본적으로 차단함.

### 3. 하드코딩 탈피 (Secret Management)
- **문제**: `main.py`와 `docker-compose.yml`에 DB 정보가 노출됨.
- **해결**: 모든 민감 정보를 `${VARIABLE}` 형식과 `os.getenv()`로 교체하여 보안 표준을 준수함.

---

## 📅 Next Step
- [ ] **2주차**: Apache Airflow를 도입하여 공공데이터 API 수집 파이프라인 자동화

---
