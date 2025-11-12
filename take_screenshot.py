from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    page.goto('http://localhost:8501')
    time.sleep(3)
    
    nav_links = page.query_selector_all('a')
    team_trends_link = None
    for link in nav_links:
        text = link.inner_text()
        if 'Team Trends' in text or '📉' in text:
            team_trends_link = link
            break
    
    if team_trends_link:
        team_trends_link.click()
        time.sleep(8)
        
        page.screenshot(path='/workspace/team_trends_screenshot.png', full_page=True)
        print("Screenshot saved successfully!")
    else:
        print("Could not find Team Trends link")
    
    browser.close()
