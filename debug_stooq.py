#!/usr/bin/env python
"""Stooq 除錯測試腳本"""
import time
import os
import glob
import re
import pandas as pd
import io
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

try:
    from openai import OpenAI
    client = OpenAI(
        base_url="http://localhost:12345/v1",
        api_key="not-needed",
    )
    print("LLM OCR 就緒: Qwen3.6-27B via llama.cpp")
except Exception as e:
    print(f"LLM OCR 不可用: {e}")

_FREQUENCY_TO_VALUE = {
    "1d": "d", "1wk": "w", "1mo": "m", "3mo": "q", "1y": "y",
}

_MONTH_MAP = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}


def has_captcha(driver):
    try:
        return driver.find_element(By.CSS_SELECTOR, "#cpt_cd img").is_displayed()
    except Exception:
        return False


def ocr_captcha(image_path):
    import base64
    from openai import OpenAI

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    client = OpenAI(
        base_url="http://localhost:12345/v1",
        api_key="not-needed",
    )

    response = client.chat.completions.create(
        model="qwen3.5-9b",
        messages=[
            {
                "role": "system",
                "content": "You are a CAPTCHA recognition assistant. Only output the letters and numbers you see, nothing else."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "識別圖片中的驗證碼，只返回大寫字母和數字，不要返回任何其他內容。"
                    }
                ]
            }
        ],
        max_tokens=512,
        temperature=0.1,
    )

    text = response.choices[0].message.content.strip()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text.upper()


def solve_captcha(driver, max_attempts=5):
    for attempt in range(max_attempts):
        try:
            captcha_img = driver.find_element(By.CSS_SELECTOR, "#cpt_cd img")
            tmp_path = ".captcha_tmp.png"
            captcha_img.screenshot(tmp_path)
            print(f"  圖片已截圖: {os.path.abspath(tmp_path)}")
            print(f"  請用圖片查看器打開比對")

            text = ocr_captcha(tmp_path)
            print(f"  OCR 辨識結果: '{text}'")
            print(f"  圖片已保留，可手動刪除")

            if not text or len(text) < 3:
                print(f"  結果太短，重新嘗試...")
                continue

            input_field = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/table/tbody/tr[2]/td[2]/table/tbody/tr/td[1]/table/tbody/tr/td/table[5]/tbody/tr/td/table/tbody/tr/td[3]/div[1]/div[1]/table/tbody/tr/td/table/tbody/tr[5]/td/input"))
            )
            input_field.clear()
            input_field.send_keys(text)
            time.sleep(1)

            approve_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=submit][value=Approve]"))
            )
            driver.execute_script("arguments[0].click();", approve_btn)
            time.sleep(3)

            # Check for refresh link after Approve
            try:
                refresh_link = driver.find_element(By.ID, "cpt_gh")
                if refresh_link.is_displayed():
                    print("  偵測到 Refresh page 連結，點擊中...")
                    driver.execute_script("arguments[0].click();", refresh_link)
                    time.sleep(3)
            except Exception:
                pass

            if not has_captcha(driver):
                print("  CAPTCHA 驗證成功!")
                return True
            print(f"  驗證失敗，重新嘗試...")
        except Exception as e:
            print(f"  CAPTCHA 錯誤: {e}")
            time.sleep(1)
    print("  CAPTCHA 多次嘗試失敗!")
    return False


def remove_overlay(driver):
    overlays = driver.find_elements(By.ID, "drk_scr")
    for o in overlays:
        driver.execute_script("arguments[0].remove();", o)
    return len(overlays)


def set_input_value(driver, name, value):
    driver.execute_script(f"document.querySelector('input[name=\"{name}\"]').value = '{value}';")


def main():
    download_dir = os.path.join(os.getcwd(), ".stooq_downloads")
    os.makedirs(download_dir, exist_ok=True)

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = uc.Chrome(options=options)

    try:
        symbol = "dx.c"
        start = "2024-01-01"
        end = "2024-12-31"
        frequency = "1d"

        # Step 1: 開啟頁面
        print("[Step 1] 開啟頁面...")
        driver.get(f"https://stooq.com/q/d/?s={symbol}")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.NAME, "i"))
        )
        time.sleep(2)
        print(f"  URL: {driver.current_url}")
        input(">>> 按 Enter 繼續...")

        # Step 1.5: 檢查 CAPTCHA
        print("[Step 1.5] 檢查 CAPTCHA...")
        if has_captcha(driver):
            print("  偵測到 CAPTCHA!")
            solve_captcha(driver)
        else:
            print("  無 CAPTCHA")
        input(">>> 按 Enter 繼續...")

        # Step 2: 移除遮罩
        print("[Step 2] 移除遮罩層...")
        n = remove_overlay(driver)
        print(f"  移除 {n} 個遮罩")
        input(">>> 按 Enter 繼續...")

        # Step 3: 設定頻率
        print(f"[Step 3] 設定頻率 {frequency}...")
        freq_value = _FREQUENCY_TO_VALUE[frequency]
        radio = driver.find_element(
            By.CSS_SELECTOR, f"input[type=radio][name=i][value={freq_value}]"
        )
        driver.execute_script("arguments[0].click();", radio)
        time.sleep(1)
        print(f"  已選擇 {freq_value}")
        input(">>> 按 Enter 繼續...")

        # Step 4: 設定日期
        print(f"[Step 4] 設定日期範圍 {start} ~ {end}...")
        year, month, day = start.split("-")
        set_input_value(driver, "d7", day.zfill(2))
        set_input_value(driver, "d3", year)
        month_sel = Select(driver.find_element(By.NAME, "d5"))
        month_sel.select_by_visible_text(_MONTH_MAP[month.zfill(2)])

        year2, month2, day2 = end.split("-")
        set_input_value(driver, "d8", day2.zfill(2))
        set_input_value(driver, "d4", year2)
        month_sel2 = Select(driver.find_element(By.NAME, "d6"))
        month_sel2.select_by_visible_text(_MONTH_MAP[month2.zfill(2)])

        # 驗證設定結果
        d7 = driver.find_element(By.NAME, "d7").get_attribute("value")
        d3 = driver.find_element(By.NAME, "d3").get_attribute("value")
        d8 = driver.find_element(By.NAME, "d8").get_attribute("value")
        d4 = driver.find_element(By.NAME, "d4").get_attribute("value")
        print(f"  d7(day_start)={d7}, d3(year_start)={d3}")
        print(f"  d8(day_end)={d8}, d4(year_end)={d4}")
        input(">>> 按 Enter 繼續...")

        # Step 5: 點擊 Show 按鈕，檢查 CSV 下載連結
        print("[Step 5] 點擊 Show 按鈕...")
        csv_link_found = False
        for i in range(5):
            show_btn = driver.find_element(By.CSS_SELECTOR, "input[type=submit][value=Show]")
            driver.execute_script("arguments[0].click();", show_btn)
            time.sleep(3)
            print(f"  第 {i+1} 次點擊完成")

            src = driver.page_source
            if "Download data in csv" in src:
                print("  CSV 下載連結存在!")
                csv_link_found = True
                break
            else:
                print("  CSV 下載連結不存在，等待後重試...")
                time.sleep(3)

        if not csv_link_found:
            print("  多次嘗試後仍未找到 CSV 下載連結")
        if has_captcha(driver):
            print("  CAPTCHA 仍然存在!")
        input(">>> 按 Enter 繼續...")

        # Step 6: 點擊下載 CSV
        print("[Step 6] 點擊 CSV 下載連結...")
        dl_link = driver.find_element(By.CSS_SELECTOR, "a[href^='q/d/l/']")
        csv_url = dl_link.get_attribute("href")
        print(f"  CSV URL: {csv_url}")
        driver.execute_script("arguments[0].click();", dl_link)
        time.sleep(5)
        input(">>> 按 Enter 繼續 (檢查檔案是否下載)...")

        # Step 7: 讀取下載的 CSV
        print("[Step 7] 讀取下載的 CSV 檔案...")
        csv_files = glob.glob(os.path.join(download_dir, "*.csv"))
        if csv_files:
            csv_file = max(csv_files, key=os.path.getctime)
            print(f"  檔案: {csv_file}")
            with open(csv_file, "r", encoding="utf-8") as f:
                csv_content = f.read()
            print(f"  前 500 字元:\n{csv_content[:500]}")

            df = pd.read_csv(io.StringIO(csv_content))
            df.columns = [c.strip() for c in df.columns]
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            print(f"\n  前 5 筆:\n{df.head()}")

            print(f"\n  刪除 {csv_file}...")
            os.remove(csv_file)
            print("  已刪除")
        else:
            print("  找不到下載的 CSV 檔案")

    finally:
        print("\n關閉瀏覽器...")
        driver.quit()


if __name__ == "__main__":
    main()
