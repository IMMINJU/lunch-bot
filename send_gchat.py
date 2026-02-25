"""
오늘의 점심 메뉴 Google Chat 발송 (GitHub Actions에서 실행)
- 네이버에서 식단표 이미지 다운로드
- 오늘 요일 컬럼 크롭
- ImgBB에 업로드
- Google Chat 웹훅으로 카드 발송
"""

import os
import sys
import json
import base64
import io
import requests
from datetime import datetime
from PIL import Image

from config import GCHAT_WEBHOOK_URL, IMGBB_API_KEY, NAVER_PLACE_URL, HOLIDAYS

# 파일 경로
SAVE_DIR = os.path.dirname(__file__)
MENU_INFO_PATH = os.path.join(SAVE_DIR, "menu_info.json")


def load_menu_info():
    """메뉴 정보 로드"""
    if not os.path.exists(MENU_INFO_PATH):
        return None
    with open(MENU_INFO_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def download_image(url):
    """네이버에서 식단표 이미지 다운로드 (메모리)"""
    print("[1/4] 이미지 다운로드 중...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://map.naver.com/'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"   다운로드 실패: {response.status_code}")
        return None

    print(f"   다운로드 완료 ({len(response.content)} bytes)")
    return Image.open(io.BytesIO(response.content))


def crop_today_menu(img, weekday):
    """오늘 요일의 중식 메뉴만 크롭"""
    print("[2/4] 오늘 메뉴 크롭 중...")
    width, height = img.size

    # 표 영역 설정 (send_menu.py와 동일)
    table_left = int(width * 0.09)
    table_right = int(width * 0.95)
    table_top = int(height * 0.18)
    table_bottom = int(height * 0.62)

    table_width = table_right - table_left
    col_width = table_width // 5

    # 여유 패딩 (15%)
    padding = int(col_width * 0.15)

    col_left = table_left + (weekday * col_width) - padding
    col_right = table_left + ((weekday + 1) * col_width) + padding

    col_left = max(0, col_left)
    col_right = min(width, col_right)

    cropped = img.crop((col_left, table_top, col_right, table_bottom))
    print(f"   크롭 완료: {cropped.size[0]}x{cropped.size[1]}")
    return cropped


def upload_to_imgbb(img, name_suffix=""):
    """이미지를 ImgBB에 업로드"""
    print("   ImgBB 업로드 중...")

    # 이미지를 base64로 인코딩
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    name = f'lunch_{datetime.now().strftime("%Y%m%d")}'
    if name_suffix:
        name += f"_{name_suffix}"

    response = requests.post(
        'https://api.imgbb.com/1/upload',
        data={
            'key': IMGBB_API_KEY,
            'image': image_data,
            'name': name,
        }
    )

    if response.status_code != 200:
        print(f"   업로드 실패: {response.status_code}")
        print(f"   {response.text}")
        return None

    data = response.json()
    image_url = data['data']['url']
    print(f"   업로드 완료: {image_url}")
    return image_url


def send_gchat_card(image_url, week_info, title="오늘의 점심", subtitle_extra=""):
    """Google Chat 웹훅으로 카드 메시지 발송"""
    print(f"   Google Chat 발송 중... ({title})")

    today = datetime.now()
    weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][today.weekday()]
    date_str = f"{today.month}월 {today.day}일 ({weekday_kr}요일)"

    subtitle = f"{date_str} · {week_info} · 양재타워 B2"
    if subtitle_extra:
        subtitle = f"{subtitle_extra} · {subtitle}"

    payload = {
        "cardsV2": [
            {
                "cardId": "lunchMenu",
                "card": {
                    "header": {
                        "title": title,
                        "subtitle": subtitle,
                        "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/restaurant/default/48px.svg",
                        "imageType": "CIRCLE"
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "image": {
                                        "imageUrl": image_url,
                                        "altText": title
                                    }
                                }
                            ]
                        },
                        {
                            "widgets": [
                                {
                                    "buttonList": {
                                        "buttons": [
                                            {
                                                "text": "원본 보기",
                                                "onClick": {
                                                    "openLink": {
                                                        "url": NAVER_PLACE_URL
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }

    response = requests.post(
        GCHAT_WEBHOOK_URL,
        json=payload,
        headers={'Content-Type': 'application/json; charset=UTF-8'}
    )

    if response.status_code == 200:
        print("   발송 완료!")
        return True
    else:
        print(f"   발송 실패: {response.status_code}")
        print(f"   {response.text}")
        return False


def main():
    print("=" * 50)
    print("[Google Chat 점심 메뉴 발송]")
    print(f"   실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 환경변수 체크
    if not GCHAT_WEBHOOK_URL:
        print("\n[오류] GCHAT_WEBHOOK_URL 환경변수가 설정되지 않았습니다.")
        sys.exit(1)
    if not IMGBB_API_KEY:
        print("\n[오류] IMGBB_API_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    today = datetime.now()
    weekday = today.weekday()

    # 주말 체크
    if weekday >= 5:
        print("\n주말은 운영하지 않습니다.")
        return

    # 휴무일 체크
    today_str = today.strftime('%Y-%m-%d')
    if today_str in HOLIDAYS:
        print(f"\n[휴무일] 오늘({today_str})은 휴무일입니다.")
        return

    # 메뉴 정보 로드
    menu_info = load_menu_info()
    if not menu_info:
        print("\n[오류] menu_info.json이 없습니다.")
        print("   먼저 update_menu.py를 실행해주세요.")
        sys.exit(1)

    image_url = menu_info.get('image_url')
    if not image_url:
        print("\n[오류] 이미지 URL이 없습니다.")
        sys.exit(1)

    week_info = menu_info.get('week_info', '')
    weekday_kr = ['월', '화', '수', '목', '금'][weekday]
    print(f"\n오늘: {weekday_kr}요일 ({week_info})")

    # 1. 이미지 다운로드
    img = download_image(image_url)
    if not img:
        sys.exit(1)

    # 2. 월요일: 전체 식단표 먼저 발송
    if weekday == 0:
        print("\n[월요일] 전체 식단표 발송...")
        full_url = upload_to_imgbb(img, name_suffix="full")
        if full_url:
            send_gchat_card(full_url, week_info, title="이번주 식단표", subtitle_extra="주간 전체")

    # 3. 오늘 메뉴 크롭
    cropped = crop_today_menu(img, weekday)

    # 4. ImgBB 업로드
    imgbb_url = upload_to_imgbb(cropped)
    if not imgbb_url:
        sys.exit(1)

    # 5. Google Chat 발송
    success = send_gchat_card(imgbb_url, week_info)
    if not success:
        sys.exit(1)

    print("\n[완료]")


if __name__ == "__main__":
    main()
