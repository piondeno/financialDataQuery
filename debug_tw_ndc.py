#!/usr/bin/env python
"""NDC 台灣經濟指標除錯測試腳本"""
import io
import re
import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


def main():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)

    try:
        print("選擇資料來源:")
        print("  1: tw_eco (景氣指標)")
        print("  2: tw_pmi (PMI)")
        choice = input("> ").strip()
        if choice == "2":
            base_url = "https://index.ndc.gov.tw/n/zh_tw/data/PMI#/"
            source = "tw_pmi"
        else:
            base_url = "https://index.ndc.gov.tw/n/zh_tw/data/eco#/"
            source = "tw_eco"
        print(f"  選擇: {source}")

        # Step 1: 開啟頁面
        print("\n[Step 1] 開啟頁面...")
        driver.get(base_url)
        WebDriverWait(driver, 30).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "#select_all_1")
        )
        print(f"  URL: {driver.current_url}")
        print(f"  頁面標題: {driver.title}")
        input(">>> 按 Enter 繼續...")

        # Step 2: 全選
        print("\n[Step 2] 點擊全選...")
        select_all = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#select_all_1"))
        )
        select_all.click()
        time.sleep(1)
        print("  已點擊全選")
        input(">>> 按 Enter 繼續...")

        # Step 3: 年度滑桿
        print("\n[Step 3] 操作年度滑桿...")
        slider = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".ui-slider-handle.ui-corner-all.ui-state-default")
            )
        )
        slider.click()
        time.sleep(0.5)
        for i in range(10):
            slider.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.3)
            print(f"  PageDown {i+1}/10")
        print("  滑桿操作完成")
        input(">>> 按 Enter 繼續...")

        # Step 4: 月份 + 表格視圖
        print("\n[Step 4] 設定月份範圍 + 切換表格...")
        month_start = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, '月 起') and contains(text(), '1')]"))
        )
        month_start.click()
        print("  已點擊 1月(起)")
        time.sleep(0.5)

        month_end = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@title, '月 迄') and contains(text(), '12')]"))
        )
        month_end.click()
        print("  已點擊 12月(迄)")
        time.sleep(0.5)

        table_view = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "table__view"))
        )
        table_view.click()
        print("  已切換表格視圖")
        time.sleep(3)
        input(">>> 按 Enter 繼續...")

        # Step 5: 解析表格
        print("\n[Step 5] 解析表格...")
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"  找到 {len(tables)} 個表格")

        df = None
        for i, table in enumerate(tables):
            table_html = table.get_attribute("outerHTML")
            if table_html and "<tbody>" in table_html:
                try:
                    dfs = pd.read_html(io.StringIO(table_html))
                    print(f"  表格 {i}: shape={dfs[0].shape}")
                    print(f"  表頭: {list(dfs[0].columns)}")
                    print(f"  前5行:\n{dfs[0].head()}")
                    tbody_el = table.find_element(By.TAG_NAME, "tbody")
                    tbody_html = tbody_el.get_attribute("innerHTML")
                    print(f"  tbody innerHTML (前1000字元):")
                    print(tbody_html[:1000])
                    if dfs and len(dfs[0]) > 0:
                        print(f"  使用表格 {i} (有資料)")
                        df = dfs[0]
                        break
                    else:
                        print(f"  表格 {i}: 無資料行")
                except Exception as e:
                    print(f"  表格 {i}: 解析失敗 ({e})")

        if df is None:
            print("  找不到有效表格!")
            input("\n>>> 按 Enter 關閉瀏覽器...")
        else:
            first_col = df.columns[0]
            df[first_col] = df[first_col].astype(str).str.strip()
            df = df[df[first_col] != ""]
            df[first_col] = pd.to_datetime(df[first_col], format="%Y-%m", errors="coerce")
            df = df.dropna(subset=[first_col])
            df.set_index(first_col, inplace=True)

            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            df = df.dropna(how="all")
            df = df[~df.index.duplicated(keep="first")]

            print(f"  Shape: {df.shape}")
            if len(df) == 0:
                print("  表格無有效資料行")
            else:
                print(f"  日期範圍: {df.index[0]} ~ {df.index[-1]}")
                print(f"\n  可用的指標 ({len(df.columns)} 個):")
                for idx, col in enumerate(df.columns, 1):
                    print(f"    {idx}. {col}")
                print(f"\n  前 5 筆資料:\n{df.head()}")

        input("\n>>> 按 Enter 關閉瀏覽器...")

    finally:
        print("\n關閉瀏覽器...")
        driver.quit()


if __name__ == "__main__":
    main()