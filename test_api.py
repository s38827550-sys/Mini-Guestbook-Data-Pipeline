import requests
import os
from dotenv import load_dotenv

# 1. .env 파일 로드 (1주차에 만든 파일에 SEOUL_API_KEY="본인키" 추가 필수!)
load_dotenv()
API_KEY = os.getenv("SEOUL_API_KEY")

# 2. 서울시 대기오염 정보 API 주소
# /json/RealtimeCityAir/1/5/ -> JSON 형식, 1번부터 5번 데이터까지 요청
url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/RealtimeCityAir/1/5/"

try:
    # 3. 데이터 요청 및 응답 확인
    response = requests.get(url)
    data = response.json()

    # 4. JSON 데이터 파싱 (명세서의 'RealtimeCityAir' 키 내부에 'row' 리스트가 들어있음)
    if "RealtimeCityAir" in data:
        rows = data["RealtimeCityAir"]["row"]
        
        print(f"{'측정일시':<15} | {'측정소':<10} | {'미세먼지':<5} | {'초미세먼지':<5} | {'상태'}")
        print("-" * 50)
        
        for row in rows:
            dt = row.get("MSRMT_DT")      # 측정일시
            name = row.get("MSRSTN_NM") # 측정소명
            pm10 = row.get("PM")      # 미세먼지
            pm25 = row.get("FPM")      # 초미세먼지
            status = row.get("CAI_GRD")

            print(f"{dt:<15} | {name:<10} | {pm10:<8} | {pm25:<8} | {status}")
    else:
        print("API 응답에 문제가 있습니다. 키값이나 주소를 확인해주세요.")
        print(data)

except Exception as e:
    print(f"에러가 발생했습니다: {e}")