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

# 휴무일 목록 (YYYY-MM-DD 형식)
HOLIDAYS = [
    "2026-02-16",  # 설날 연휴
    "2026-02-17",
    "2026-02-18",
    "2026-03-01",  # 삼일절
]
