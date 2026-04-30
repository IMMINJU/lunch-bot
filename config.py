"""
점심 메뉴 봇 설정
"""

import os
from dotenv import load_dotenv

load_dotenv()

# 네이버 지도 URL
NAVER_PLACE_URL = "https://map.naver.com/p/entry/place/1125744770?placePath=/feed"

# Google Chat 웹훅
GCHAT_WEBHOOK_URL = os.environ.get("GCHAT_WEBHOOK_URL", "")

# ImgBB API
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "")

# 메뉴 JSON 저장 경로
MENU_JSON_PATH = os.path.join(os.path.dirname(__file__), "menu.json")

# 2026년 평일 공휴일 (YYYY-MM-DD 형식)
HOLIDAYS = [
    "2026-01-01",  # 신정
    "2026-02-16",  # 설날 연휴
    "2026-02-17",  # 설날
    "2026-02-18",  # 설날 연휴
    "2026-03-02",  # 대체공휴일 (삼일절)
    "2026-05-01",  # 근로자의 날
    "2026-05-05",  # 어린이날
    "2026-05-25",  # 대체공휴일 (부처님오신날)
    "2026-06-03",  # 전국동시지방선거
    "2026-08-17",  # 대체공휴일 (광복절)
    "2026-09-24",  # 추석 연휴
    "2026-09-25",  # 추석
    "2026-10-05",  # 대체공휴일 (개천절)
    "2026-10-09",  # 한글날
    "2026-12-25",  # 크리스마스
]
