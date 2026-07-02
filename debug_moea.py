"""Debug script for MOEA website data extraction.

Usage: python debug_moea.py

This script performs step-by-step browser automation on the MOEA website
and outputs raw HTML/data for inspection.
"""
import time
import subprocess
import sys
import os


def get_chrome_version() -> int | None:
    """Auto-detect Chrome browser major version."""
    candidates = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
    for cmd in candidates:
        try:
            out = subprocess.check_output([cmd, "--version"], stderr=subprocess.DEVNULL, text=True)
            for part in out.split():
                if part[0].isdigit():
                    return int(part.split(".")[0])
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError, IndexError):
            continue
    return None


def step1_check_browser():
    """Check Chrome and chromedriver availability."""
    print("=" * 60)
    print("Step 1: Browser Check")
    print("=" * 60)

    chrome_ver = get_chrome_version()
    print(f"Chrome version: {chrome_ver}")

    try:
        import undetected_chromedriver as uc
        print(f"undetected_chromedriver: {uc.__version__}")
    except ImportError:
        print("ERROR: undetected_chromedriver not installed")
        return False

    try:
        from selenium import webdriver
        print(f"selenium: {webdriver.__version__}")
    except ImportError:
        print("ERROR: selenium not installed")
        return False

    return True


def step2_load_page():
    """Load the MOEA website."""
    print("\n" + "=" * 60)
    print("Step 2: Load MOEA Website")
    print("=" * 60)

    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Keep browser visible for debugging (remove --headless)
    # options.add_argument("--headless=new")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    version = get_chrome_version()
    try:
        if version:
            driver = uc.Chrome(options=options, version_main=version)
            print(f"Driver started (Chrome {version})")
        else:
            driver = uc.Chrome(options=options)
            print("Driver started (auto-detect)")
    except Exception as e:
        print(f"ERROR: Failed to start browser: {e}")
        return None

    try:
        url = "https://service.moea.gov.tw/EE520/investigate/InvestigateBA.aspx"
        driver.get(url)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        time.sleep(3)

        title = driver.title
        print(f"Page title: {title}")

        # Check for Cloudflare block
        if "Cloudflare" in title or "blocked" in driver.page_source.lower():
            print("WARNING: Page blocked by Cloudflare!")
            return driver

        # Check for key elements
        elements_to_check = [
            ("ContentPlaceHolder1_ddlDateBeg", By.ID, "date dropdown"),
            ("ContentPlaceHolder1_tvItem1n0CheckBox", By.ID, "checkbox 1"),
            ("ContentPlaceHolder1_tvItem2n1CheckBox", By.ID, "checkbox 2"),
            ("ContentPlaceHolder1_tvItem3n1CheckBox", By.ID, "checkbox 3"),
            ("ContentPlaceHolder1_btnQuery", By.ID, "query button"),
            ("ContentPlaceHolder1_panVaule", By.ID, "data panel"),
        ]

        print("\nElement detection:")
        for elem_id, by_type, desc in elements_to_check:
            try:
                el = driver.find_element(by_type, elem_id)
                print(f"  ✓ {desc}: FOUND (id={elem_id})")
            except Exception as e:
                print(f"  ✗ {desc}: NOT FOUND ({e})")

        return driver

    except Exception as e:
        print(f"ERROR loading page: {e}")
        driver.quit()
        return None


def step3_interact(driver):
    """Perform the interaction steps."""
    if not driver:
        return

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select as SelSelect

    print("\n" + "=" * 60)
    print("Step 3: Interaction Steps")
    print("=" * 60)

    wait = WebDriverWait(driver, 15)

    # Step 1: Date selection
    print("\n[3a] Selecting date '73年9月'...")
    try:
        ddl = driver.find_element(By.ID, "ContentPlaceHolder1_ddlDateBeg")
        select = SelSelect(ddl)

        all_options = ddl.find_elements(By.TAG_NAME, "option")
        print(f"  Available date options ({len(all_options)}):")
        for i, opt in enumerate(all_options[:30]):
            marker = " <-- TARGET" if "73年9月" in opt.text else ""
            print(f"    [{i}] {opt.text}{marker}")

        # Try to select '73年9月'
        found = False
        for opt in all_options:
            if "73年9月" in opt.text:
                select.select_by_visible_text("73年9月")
                print(f"  Selected: {opt.text}")
                found = True
                break

        if not found:
            # Fallback: try selecting by index (first data option)
            print("  '73年9月' not found, using first data option as fallback...")
            select.select_by_index(1)

    except Exception as e:
        print(f"  ERROR selecting date: {e}")

    time.sleep(1)

    # Steps 2-4: Check checkboxes
    print("\n[3b] Checking tree-view checkboxes...")
    checkbox_ids = [
        "ContentPlaceHolder1_tvItem1n0CheckBox",
        "ContentPlaceHolder1_tvItem2n1CheckBox",
        "ContentPlaceHolder1_tvItem3n1CheckBox",
    ]

    for cb_id in checkbox_ids:
        try:
            cb = driver.find_element(By.ID, cb_id)
            is_selected = cb.is_selected()
            print(f"  {cb_id}: selected={is_selected}")
            if not is_selected:
                cb.click()
                time.sleep(0.3)
                print(f"    -> clicked, now selected={cb.is_selected()}")
        except Exception as e:
            print(f"  {cb_id}: NOT FOUND ({e})")

    # Step 5: Click query button
    print("\n[3c] Clicking query button...")
    try:
        btn = driver.find_element(By.ID, "ContentPlaceHolder1_btnQuery")
        btn.click()
        print("  Query button clicked, waiting for results...")

        # Wait for page to settle
        time.sleep(5)

        # Check if there's a postback or loading state
        current_url = driver.current_url
        print(f"  Current URL: {current_url}")

    except Exception as e:
        print(f"  ERROR clicking query button: {e}")

    time.sleep(3)


def step4_extract_data(driver):
    """Extract and display data from the results panel."""
    if not driver:
        return

    print("\n" + "=" * 60)
    print("Step 4: Data Extraction")
    print("=" * 60)

    from selenium.webdriver.common.by import By

    # Try to get panVaule content
    try:
        panel = driver.find_element(By.ID, "ContentPlaceHolder1_panVaule")
        inner_html = panel.get_attribute("innerHTML")
        outer_html = panel.get_attribute("outerHTML")

        print(f"\npanVaule innerHTML length: {len(inner_html)}")
        print(f"panVaule outerHTML length: {len(outer_html)}")

        # Save full HTML to file for inspection
        output_file = "/tmp/moea_page_full.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"\nFull page saved to: {output_file}")

        # Save panel HTML to file
        panel_file = "/tmp/moea_panel.html"
        with open(panel_file, "w", encoding="utf-8") as f:
            f.write(inner_html)
        print(f"Panel HTML saved to: {panel_file}")

        # Try to find tables in the page
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"\nTables found on page: {len(tables)}")

        for i, table in enumerate(tables):
            table_html = table.get_attribute("outerHTML")
            tbody_count = table_html.count("<tbody>")
            tr_count = table_html.count("<tr>")
            first_row_text = ""

            # Try to get text from first few rows
            rows = table.find_elements(By.TAG_NAME, "tr")
            if rows:
                first_few = []
                for r in rows[:3]:
                    cells = r.find_elements(By.TAG_NAME, "td")
                    first_few.append([c.text for c in cells])

            print(f"\n  Table {i+1}:")
            print(f"    tbody tags: {tbody_count}")
            print(f"    tr rows: {tr_count}")
            if first_few:
                print(f"    First few rows:")
                for row_text in first_few:
                    print(f"      {row_text[:5]}")  # First 5 cells

        # Also dump the panVaule innerHTML content preview
        print("\npanVaule HTML preview (first 3000 chars):")
        print(inner_html[:3000])

    except Exception as e:
        print(f"ERROR extracting data panel: {e}")


def step5_dump_all_ids(driver):
    """Dump all element IDs on the page for reference."""
    if not driver:
        return

    print("\n" + "=" * 60)
    print("Step 5: All Element IDs")
    print("=" * 60)

    ids = driver.execute_script("""
        var els = document.querySelectorAll('[id]');
        var results = [];
        for (var i = 0; i < els.length; i++) {
            results.push(els[i].id + ' [' + els[i].tagName + ']');
        }
        return results;
    """)

    print(f"Total elements with IDs: {len(ids)}")
    for id_str in ids[:80]:
        print(f"  {id_str}")


def main():
    print("MOEA Website Debug Script")
    print("=" * 60)

    # Step 1: Check browser
    if not step1_check_browser():
        sys.exit(1)

    # Step 2: Load page
    driver = step2_load_page()
    if not driver:
        print("\nFailed to load page. Exiting.")
        sys.exit(1)

    try:
        # Step 3: Interact
        step3_interact(driver)

        # Step 4: Extract data
        step4_extract_data(driver)

        # Step 5: Dump all IDs
        step5_dump_all_ids(driver)

        print("\n" + "=" * 60)
        print("Debug complete.")
        print("Browser is still open for manual inspection.")
        print("Close browser manually or press Ctrl+C to exit.")
        print("=" * 60)

        # Keep browser open for inspection
        input("\nPress Enter to close browser and exit...")

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
