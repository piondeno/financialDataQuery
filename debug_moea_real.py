"""Debug MOEA website - save raw HTML for inspection."""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select as SelSelect
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# NO headless - user can see what's happening
options.add_experimental_option("excludeSwitches", ["enable-automation"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    print("1. Loading MOEA website...")
    driver.get("https://service.moea.gov.tw/EE520/investigate/InvestigateBA.aspx")
    time.sleep(3)
    print(f"   Title: {driver.title}")
    
    # Check if blocked by Cloudflare
    if "Cloudflare" in driver.title or "blocked" in driver.page_source.lower():
        print("   !!! BLOCKED BY CLOUDFLARE !!!")
        with open("/tmp/moea_blocked.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("   Saved to /tmp/moea_blocked.html")
    else:
        # Step 1: Select date '73年9月' from dropdown
        print("\n2. Selecting date...")
        ddl = driver.find_element(By.ID, "ContentPlaceHolder1_ddlDateBeg")
        select = SelSelect(ddl)
        
        all_opts = ddl.find_elements(By.TAG_NAME, "option")
        print(f"   Found {len(all_opts)} options:")
        for i, opt in enumerate(all_opts[:5]):
            marker = "<-- TARGET" if "73年9月" in opt.text else ""
            print(f"     [{i}] {opt.text} {marker}")
        
        found = False
        for opt in all_opts:
            if "73年9月" in opt.text:
                select.select_by_visible_text("73年9月")
                print(f"   Selected: {opt.text}")
                found = True
                break
        
        if not found:
            try:
                select.select_by_index(1)
                print("   (fallback) Selected index 1")
            except Exception as e:
                print(f"   Error selecting: {e}")
        
        time.sleep(1)

        # Steps 2-4: Check checkboxes
        print("\n3. Checking tree-view checkboxes...")
        checkbox_ids = [
            "ContentPlaceHolder1_tvItem1n0CheckBox",
            "ContentPlaceHolder1_tvItem2n1CheckBox",
            "ContentPlaceHolder1_tvItem3n1CheckBox",
        ]
        
        for cb_id in checkbox_ids:
            try:
                cb = driver.find_element(By.ID, cb_id)
                is_sel = cb.is_selected()
                print(f"   {cb_id}: selected={is_sel}")
                if not is_sel:
                    cb.click()
                    time.sleep(0.3)
            except Exception as e:
                print(f"   {cb_id}: NOT FOUND ({e})")

        # Step 5: Click query button
        print("\n4. Clicking query button...")
        btn = driver.find_element(By.ID, "ContentPlaceHolder1_btnQuery")
        btn.click()
        time.sleep(5)
        
        current_url = driver.current_url
        title = driver.title
        print(f"   Title: {title}")
        print(f"   URL: {current_url}")

        # Check panVaule panel
        print("\n5. Checking data panel...")
        try:
            panel = driver.find_element(By.ID, "ContentPlaceHolder1_panVaule")
            inner_html = panel.get_attribute("innerHTML")
            
            # Save full page HTML
            with open("/tmp/moea_full.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"   Full page saved to /tmp/moea_full.html ({len(driver.page_source)} bytes)")
            
            # Save panel HTML
            with open("/tmp/moea_panel.html", "w", encoding="utf-8") as f:
                f.write(inner_html)
            print(f"   Panel saved to /tmp/moea_panel.html ({len(inner_html)} bytes)")

            # Show first 2000 chars of panel
            print("\n6. Panel HTML preview:")
            print(inner_html[:3000])
            
            # Find tables in page
            tables = driver.find_elements(By.TAG_NAME, "table")
            print(f"\n   Tables found: {len(tables)}")
            for i, t in enumerate(tables):
                rows = t.find_elements(By.TAG_NAME, "tr")
                print(f"     Table {i+1}: {len(rows)} rows")
                
        except Exception as e:
            print(f"   panVaule NOT FOUND: {e}")

finally:
    input("\nBrowser is still open. Press Enter to close...")
    driver.quit()
    
print("Done.")
