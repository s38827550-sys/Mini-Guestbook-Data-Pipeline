import requests
import sys

# 테스트할 서버 주소 (로컬 실행 시 기본 8000번 포트)
BASE_URL = "http://localhost:8000"

def test_root():
    print("\n--- [GET /] 루트 엔드포인트 테스트 ---")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
    except Exception as e:
        print(f"❌ 실패: {e}")

def test_visit(name):
    print(f"\n--- [POST /visit/{name}] 방문자 등록 테스트 ---")
    try:
        response = requests.post(f"{BASE_URL}/visit/{name}")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
    except Exception as e:
        print(f"❌ 실패: {e}")

def test_guests():
    print("\n--- [GET /guests] 방문자 목록 조회 테스트 ---")
    try:
        response = requests.get(f"{BASE_URL}/guests")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
    except Exception as e:
        print(f"❌ 실패: {e}")

def test_collect_air():
    print("\n--- [GET /collect-air] 대기질 데이터 수집(수동) 테스트 ---")
    try:
        response = requests.get(f"{BASE_URL}/collect-air")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
    except Exception as e:
        print(f"❌ 실패: {e}")

def test_air_data():
    print("\n--- [GET /air-data] 대기질 데이터 조회 테스트 ---")
    try:
        response = requests.get(f"{BASE_URL}/air-data?limit=5")
        print(f"상태 코드: {response.status_code}")
        data = response.json()
        print(f"조회 건수: {data.get('count', 0)}")
        if data.get('data'):
            print(f"첫 번째 데이터 샘플: {data['data'][0]}")
    except Exception as e:
        print(f"❌ 실패: {e}")

def test_air_summary():
    print("\n--- [GET /air-summary] 대기질 데이터 요약 테스트 ---")
    try:
        response = requests.get(f"{BASE_URL}/air-summary")
        print(f"상태 코드: {response.status_code}")
        print(f"응답 내용: {response.json()}")
    except Exception as e:
        print(f"❌ 실패: {e}")

if __name__ == "__main__":
    print("🚀 FastAPI 엔드포인트 통합 테스트를 시작합니다.")
    
    test_root()
    test_visit("TestUser_Gemini")
    test_guests()
    test_collect_air()
    test_air_data()
    test_air_summary()
    
    print("\n✅ 모든 테스트 시도가 완료되었습니다.")
