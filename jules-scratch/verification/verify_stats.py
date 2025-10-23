from playwright.sync_api import sync_playwright, expect, Error as PlaywrightError
import time

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()

    # --- Robust Connection Polling ---
    max_retries = 5
    for i in range(max_retries):
        try:
            page.goto("http://localhost:5003/hot", timeout=5000)
            print("Successfully connected to the server.")
            break
        except PlaywrightError as e:
            print(f"Connection attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(2)
            else:
                raise

    # 1. Navigate to the stats page
    page.get_by_role("link", name="Network Stats").click()

    # 2. Wait for the stats to load and verify
    expect(page.get_by_role("heading", name="📊 P2P Network Statistics")).to_be_visible()
    # Since this is a local test, we expect 0 connected peers.
    expect(page.get_by_text("Connected Peers: 0")).to_be_visible(timeout=10000) # Increased timeout for stat loading

    # 3. Take a screenshot
    page.screenshot(path="jules-scratch/verification/stats_page.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
