# 🌡️ Seoul Air Quality Data Pipeline (Phase 1: Backend Roadmap)

이 프로젝트는 단순히 API를 만드는 것에 그치지 않고, 백엔드 개발자의 필수 역량인 **[데이터 수집 - 저장 - 가공 - 배포 - 모니터링]**의 전 과정을 실전 데이터(서울시 공기질 Open API)로 직접 구현한 백엔드 엔지니어링 프로젝트입니다.

---

## 🏆 완료된 백엔드 로드맵 (Phase 1: 데이터 엔지니어링 & 클라우드)

| 단계 | 핵심 성취 (Milestones) | 적용된 기술 |
| :--- | :--- | :--- |
| **1. 언어 & 환경** | Python 3.12 기반의 가상환경 구축 및 의존성 관리 | `Python`, `venv`, `pip` |
| **2. API 설계** | REST API 엔드포인트 설계 및 비동기 처리 | `FastAPI`, `Pydantic`, `Jinja2` |
| **3. DB 설계** | 관계형 DB 설계, PK 설정 및 데이터 정규화 | `PostgreSQL`, `psycopg2-pool` |
| **4. 자동화** | Cron 방식을 활용한 주기적 배치(Batch) 작업 구현 | `APScheduler`, `pytz` |
| **5. 배포 (DevOps)** | Docker 컨테이너라이징 및 클라우드 서비스 배포 | `Docker`, `Docker Compose`, `Render.com` |
| **6. 안정성** | 환경 변수 관리 및 서버 상태 모니터링 | `.env`, `Health Check API`, `Docker Healthcheck` |

---

## ⚙️ 데이터 사이클 및 핵심 기능

### 1. 데이터 수집 & 저장 (Collection & Storage)
- **Hourly Batch**: APScheduler를 통해 매시간 서울시 Open API에서 실시간 공기질 데이터를 수집합니다.
- **Data Integrity**: `ON CONFLICT` 로직을 적용하여 중복 데이터 적재를 방지하고 데이터의 무결성을 유지합니다.

### 2. 데이터 가공 (Processing)
- **Daily Analytics**: 매일 자정, 수집된 로우 데이터를 가공하여 일간 통계(`daily_air_stats`)를 생성합니다.
- **Reporting**: 가공된 데이터를 바탕으로 공기질이 가장 깨끗한 지역 TOP 5 분석 리포트를 제공합니다.

### 3. 클라우드 배포 & 인프라 (DevOps)
- **Containerization**: `Dockerfile`과 `docker-compose.yml`을 통해 환경에 구애받지 않는 실행 환경을 구축했습니다.
- **Multi-Environment Support**: 로컬 DB와 클라우드(Render) DB를 유연하게 전환할 수 있는 연결 로직을 포함합니다.

### 4. 안정성 및 모니터링 (Stability)
- **Self-Healing Infrastructure**: Docker Healthcheck(`pg_isready`)를 적용하여 DB가 준비된 후 서버가 실행되도록 설계했습니다.
- **Monitoring API**: `/health` 엔드포인트를 통해 서버와 DB의 연결 상태를 실시간으로 확인할 수 있습니다.

---

## 📁 프로젝트 구조

```text
Mini-Guestbook-Data-Pipeline/
├── main.py              # FastAPI 앱 (수집, 가공, 배포 로직 통합)
├── Dockerfile           # 컨테이너 빌드 설정
├── docker-compose.yml   # 인프라(DB + Web) 오케스트레이션
├── requirements.txt     # 의존성 관리
├── .env.example         # 환경 변수 가이드
├── test_api.py          # 통합 테스트 스크립트
└── templates/           # SSR을 위한 HTML 템플릿 (Dashboard, Report)
```

---

## 🚀 시작하기

1.  **환경 설정**: `.env.example`을 참고하여 `.env` 파일을 작성합니다.
2.  **실행**: `docker-compose up -d --build` 명령어로 전체 시스템을 가동합니다.
3.  **확인**: 
    - 대시보드: `http://localhost:8000/view-air`
    - 분석 리포트: `http://localhost:8000/report`
    - API 상태: `http://localhost:8000/health`
