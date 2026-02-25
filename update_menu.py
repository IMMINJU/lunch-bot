"""
주간 식단표 이미지 다운로드 (주 1회 실행)
- 네이버 지도에서 식단표 이미지 크롤링
- 이미지 파일로 저장
"""

import os
import json
import requests
import re
import time
import urllib.parse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import NAVER_PLACE_URL

# 저장 경로
SAVE_DIR = os.path.dirname(__file__)
MENU_IMAGE_PATH = os.path.join(SAVE_DIR, "menu_image.jpg")
MENU_INFO_PATH = os.path.join(SAVE_DIR, "menu_info.json")


def get_menu_image_url():
    """네이버 지도 피드에서 최신 식단표 이미지 URL 가져오기"""
    print("[1/3] Getting menu image from feed...")

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # headless 감지 우회
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    image_url = None

    try:
        driver.get(NAVER_PLACE_URL)
        time.sleep(7)

        # iframe 전환
        try:
            wait = WebDriverWait(driver, 10)
            entry_iframe = wait.until(EC.presence_of_element_located((By.ID, 'entryIframe')))
            driver.switch_to.frame(entry_iframe)
            print("   iframe ok")
        except Exception as e:
            print(f"   iframe fail: {e}")

        time.sleep(5)
        page_source = driver.page_source

        # 피드 이미지에서 원본 URL 추출
        pattern = r'size=678x452[^"]*src=(https%3A%2F%2Fldb-phinf\.pstatic\.net%2F[^"&]+)'
        matches = re.findall(pattern, page_source)

        if matches:
            # URL에서 날짜(YYYYMMDD)를 파싱해서 가장 최신 이미지 선택
            decoded_urls = [urllib.parse.unquote(m) for m in matches]
            date_pattern = r'ldb-phinf\.pstatic\.net/(\d{8})_'

            best_url = decoded_urls[0]
            best_date = ""
            for url in decoded_urls:
                date_match = re.search(date_pattern, url)
                if date_match and date_match.group(1) > best_date:
                    best_date = date_match.group(1)
                    best_url = url

            original_url = best_url
            image_url = f"https://search.pstatic.net/common/?autoRotate=true&quality=100&type=f&size=1920x1280&src={urllib.parse.quote(original_url, safe='')}"
            print(f"   Image URL found! (date: {best_date}, {len(matches)} candidates)")
        else:
            pattern = r'https://search\.pstatic\.net/common/\?[^"]+size=678x452[^"]+\.jpeg'
            matches = re.findall(pattern, page_source)
            if matches:
                image_url = matches[0].replace('&amp;', '&')
                print("   Image URL found (fallback)")
            else:
                print("   Image not found")

        return image_url

    finally:
        driver.quit()


def download_image(url):
    """이미지 다운로드 및 저장"""
    print("[2/2] 이미지 다운로드 중...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://map.naver.com/'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(MENU_IMAGE_PATH, 'wb') as f:
            f.write(response.content)
        print(f"   이미지 저장 완료: {MENU_IMAGE_PATH} ({len(response.content)} bytes)")
        return True
    else:
        print(f"   다운로드 실패: {response.status_code}")
        return False


def save_menu_info(image_url):
    """메뉴 정보 저장"""
    today = datetime.now()

    # 주차 계산
    week_num = (today.day - 1) // 7 + 1
    week_info = f"{today.month}월 {week_num}째주"

    info = {
        "week_info": week_info,
        "updated_at": today.isoformat(),
        "image_url": image_url,
        "image_path": MENU_IMAGE_PATH
    }

    with open(MENU_INFO_PATH, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    print(f"   Saved: {week_info}")


def main():
    print("=" * 50)
    print("[Weekly Menu Update]")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. Get image URL from feed
    try:
        image_url = get_menu_image_url()
    except Exception as e:
        print(f"\n[FAIL] Image crawling error: {e}")
        return False

    if not image_url:
        print("\n[FAIL] Image URL not found")
        return False

    # 2. Download image
    print("[2/2] Downloading image...")
    if not download_image(image_url):
        print("\n[FAIL] Image download failed")
        return False

    # 3. Save info
    save_menu_info(image_url)

    print("\n[DONE] Weekly menu update complete!")
    return True


if __name__ == "__main__":
    main()
